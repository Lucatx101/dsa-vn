"""Markdown rendering. Prints the aggregator's numbers, not the model's."""

from datetime import datetime

from agent.schemas import AgentOpinion, StrategySynthesis
from data_provider.vnstock_fetcher import TickerData

DISCLAIMER = (
    "_Công cụ nghiên cứu cá nhân, tạo tự động. Không phải khuyến nghị đầu tư._"
)


def render_dashboard(
    data: TickerData,
    synthesis: StrategySynthesis,
    opinions: list[AgentOpinion],
    decision_text: str,
) -> str:
    params = synthesis.summary_params
    lines = [
        f"# {data.symbol} — {data.exchange.value}",
        f"_Tạo lúc {datetime.now():%Y-%m-%d %H:%M}_",
        "",
        "## Tổng hợp đa chiến lược",
        f"- **Tín hiệu cuối:** `{synthesis.final_signal}`",
        f"- **Điểm số trọng số:** {synthesis.weighted_score:.2f} / 5.00",
        f"- **Độ tin cậy:** {synthesis.confidence:.2f}",
        f"- **Mức đồng thuận:** {synthesis.consensus_level}",
        f"- **Mức mâu thuẫn:** {synthesis.conflict_severity}",
        f"- **Đồng thuận:** {', '.join(synthesis.supporting_skills) or '(không có)'}",
        f"- **Phản biện:** {', '.join(synthesis.opposing_skills) or '(không có)'}",
        (
            f"- **Số ý kiến:** {params.get('opinion_count', 0)} hợp lệ, "
            f"{params.get('invalid_opinion_count', 0)} không hợp lệ, "
            f"{params.get('total_opinion_count', 0)} tổng"
        ),
        "",
        "## Phân tích",
        decision_text,
        "",
        "## Chi tiết từng chiến lược",
    ]

    if opinions:
        for opinion in opinions:
            lines.append(
                f"- **{opinion.agent_name}** — `{opinion.signal}` "
                f"(tin cậy {opinion.confidence:.2f}): {opinion.reasoning}"
            )
    else:
        lines.append("- (không có ý kiến hợp lệ)")

    lines += ["", DISCLAIMER]
    return "\n".join(lines)


def render_insufficient(symbol: str, invalid: list[AgentOpinion]) -> str:
    """Rendered when no strategy produced a valid opinion for this ticker."""
    lines = [
        f"# {symbol} — không đủ dữ liệu",
        "",
        "Không có chiến lược nào đưa ra ý kiến hợp lệ. Chi tiết:",
    ]
    for opinion in invalid:
        lines.append(f"- **{opinion.agent_name}**: {opinion.invalid_reason}")
    lines += ["", DISCLAIMER]
    return "\n".join(lines)
