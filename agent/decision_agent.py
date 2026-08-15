"""Final synthesis call: one Claude request that explains the aggregate.

Contract invariant: this agent reads strategy_synthesis and never rewrites it.
The system prompt states that explicitly, and the renderer prints the
aggregator's own numbers rather than anything the model produced.
"""

import logging

from agent.llm import decision_model
from agent.schemas import AgentOpinion, StrategySynthesis
from core.market_profile import market_rules_text
from data_provider.vnstock_fetcher import TickerData, history_summary

logger = logging.getLogger(__name__)

MAX_TOKENS = 8000

SYSTEM_PROMPT = (
    "Bạn là chuyên gia phân tích chứng khoán Việt Nam, viết bản tổng hợp quyết "
    "định cuối cùng cho nhà đầu tư cá nhân.\n\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Kết quả tổng hợp đa chiến lược (strategy_synthesis) đã được tính toán "
    "sẵn. Bạn chỉ được GIẢI THÍCH nó. Bạn KHÔNG được thay đổi, ghi đè, hay đưa "
    "ra một tín hiệu cuối cùng khác với final_signal đã cho.\n"
    "2. Nếu consensus_level là 'insufficient' hoặc 'low', bạn PHẢI nêu rõ mức độ "
    "không chắc chắn này ngay ở phần đầu.\n"
    "3. Chỉ dùng dữ liệu được cung cấp. Không bịa số liệu, tin tức, hay báo cáo "
    "tài chính.\n"
    "4. Viết hoàn toàn bằng tiếng Việt.\n"
    "5. Đây là công cụ nghiên cứu tham khảo, không phải khuyến nghị đầu tư."
)

USER_TEMPLATE = """Hãy viết bản tổng hợp quyết định cho mã {symbol}.

{market_rules}

DỮ LIỆU THỊ TRƯỜNG:
{data_summary}

KẾT QUẢ TỔNG HỢP ĐA CHIẾN LƯỢC (không được thay đổi):
- final_signal: {final_signal}
- weighted_score: {weighted_score}
- confidence: {confidence}
- consensus_level: {consensus_level}
- conflict_severity: {conflict_severity}
- Chiến lược đồng thuận: {supporting}
- Chiến lược phản biện: {opposing}
- Số ý kiến hợp lệ / không hợp lệ / tổng: {n_valid} / {n_invalid} / {n_total}

Ý KIẾN CHI TIẾT TỪNG CHIẾN LƯỢC:
{opinion_details}

Hãy trình bày theo các mục sau:
## Kết luận cốt lõi
## Phân tích xu hướng
## Vùng giá đáng chú ý
## Cảnh báo rủi ro
## Việc cần làm
"""


def _format_opinions(opinions: list[AgentOpinion]) -> str:
    if not opinions:
        return "(không có ý kiến hợp lệ)"
    return "\n".join(
        f"- {o.agent_name}: {o.signal} (confidence {o.confidence:.2f}) — {o.reasoning}"
        for o in opinions
    )


def run_decision(
    data: TickerData,
    synthesis: StrategySynthesis,
    opinions: list[AgentOpinion],
    client,
) -> str:
    """Return the Vietnamese dashboard body, or a fallback message on failure."""
    params = synthesis.summary_params
    user_prompt = USER_TEMPLATE.format(
        symbol=data.symbol,
        market_rules=market_rules_text(),
        data_summary=history_summary(data),
        final_signal=synthesis.final_signal,
        weighted_score=f"{synthesis.weighted_score:.2f}",
        confidence=f"{synthesis.confidence:.2f}",
        consensus_level=synthesis.consensus_level,
        conflict_severity=synthesis.conflict_severity,
        supporting=", ".join(synthesis.supporting_skills) or "(không có)",
        opposing=", ".join(synthesis.opposing_skills) or "(không có)",
        n_valid=params.get("opinion_count", 0),
        n_invalid=params.get("invalid_opinion_count", 0),
        n_total=params.get("total_opinion_count", 0),
        opinion_details=_format_opinions(opinions),
    )

    try:
        response = client.messages.create(
            model=decision_model(),
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:  # noqa: BLE001 - degrade to a visible message
        logger.error("decision agent failed for %s: %s", data.symbol, exc)
        return f"_Không tạo được phần phân tích: lỗi khi gọi mô hình ({exc})._"

    if getattr(response, "stop_reason", None) == "refusal":
        logger.error("decision agent refusal for %s", data.symbol)
        return "_Mô hình đã từ chối tạo nội dung cho mã này (refusal)._"

    texts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    if not texts:
        return "_Mô hình không trả về nội dung văn bản._"
    return "\n".join(texts).strip()
