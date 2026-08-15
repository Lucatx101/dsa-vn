from unittest.mock import MagicMock

import pandas as pd

from agent.decision_agent import run_decision
from agent.schemas import AgentOpinion, StrategySynthesis
from core.market_profile import Exchange
from data_provider.vnstock_fetcher import TickerData


def _data():
    rows = 30
    return TickerData(
        symbol="FPT",
        exchange=Exchange.HOSE,
        history=pd.DataFrame(
            {
                "time": pd.date_range("2026-01-01", periods=rows, freq="D"),
                "open": [100.0] * rows,
                "high": [102.0] * rows,
                "low": [99.0] * rows,
                "close": [101.0] * rows,
                "volume": [1_000_000.0] * rows,
            }
        ),
        board={},
        reference_price=100.0,
        board_ceiling=None,
        board_floor=None,
        foreign_buy_volume=None,
        foreign_sell_volume=None,
        current_room=None,
        total_room=None,
    )


def _synthesis():
    return StrategySynthesis(
        final_signal="buy",
        weighted_score=3.9,
        confidence=0.72,
        consensus_level="medium",
        conflict_severity="low",
        supporting_skills=["ma_trend", "volume_breakout"],
        opposing_skills=["price_band_risk"],
        summary_params={
            "opinion_count": 3,
            "invalid_opinion_count": 1,
            "total_opinion_count": 4,
        },
    )


def _opinions():
    return [
        AgentOpinion(
            agent_name="ma_trend",
            signal="buy",
            confidence=0.8,
            reasoning="MA20 trên MA50.",
            key_levels={},
            raw_data={},
        )
    ]


def _client_returning(text, stop_reason="end_turn"):
    client = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.stop_reason = stop_reason
    client.messages.create.return_value = response
    return client


def test_returns_model_text():
    client = _client_returning("Kết luận: mua thăm dò.")
    result = run_decision(_data(), _synthesis(), _opinions(), client)
    assert result == "Kết luận: mua thăm dò."


def test_prompt_carries_synthesis_fields_verbatim():
    client = _client_returning("ok")
    run_decision(_data(), _synthesis(), _opinions(), client)

    sent = client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "buy" in sent
    assert "3.9" in sent
    assert "medium" in sent
    assert "ma_trend" in sent


def test_system_prompt_forbids_overwriting_synthesis():
    client = _client_returning("ok")
    run_decision(_data(), _synthesis(), _opinions(), client)

    system = client.messages.create.call_args.kwargs["system"]
    assert "KHÔNG được thay đổi" in system


def test_api_failure_returns_fallback_not_exception():
    client = MagicMock()
    client.messages.create.side_effect = RuntimeError("boom")
    result = run_decision(_data(), _synthesis(), _opinions(), client)
    assert "boom" in result or "lỗi" in result.lower()


def test_refusal_returns_fallback():
    client = _client_returning("", stop_reason="refusal")
    result = run_decision(_data(), _synthesis(), _opinions(), client)
    assert "từ chối" in result.lower() or "refusal" in result.lower()


def test_no_text_blocks_returns_fallback():
    # A response whose content has no text-type block (e.g. only a
    # "thinking" block) must not silently render as an empty string via
    # "\n".join([]).strip() == "". This guards the `if not texts:` check
    # against a regression like `if texts is None:`, which would never be
    # true since the list comprehension can only ever produce a list.
    client = MagicMock()
    block = MagicMock()
    block.type = "thinking"
    block.text = "nội bộ, không phải câu trả lời cuối"
    response = MagicMock()
    response.content = [block]
    response.stop_reason = "end_turn"
    client.messages.create.return_value = response

    result = run_decision(_data(), _synthesis(), _opinions(), client)

    assert result == "_Mô hình không trả về nội dung văn bản._"


def test_prompt_construction_failure_returns_fallback_not_exception():
    # history_summary() indexes into the last row of the OHLCV history
    # (e.g. close.iloc[-1]); an empty history raises IndexError there.
    # fetch_ticker() never produces an empty history today, but run_decision
    # must still degrade to a fallback string rather than raise, since a
    # future caller (the Task 9 pipeline) has no try/except above this call.
    empty_data = TickerData(
        symbol="FPT",
        exchange=Exchange.HOSE,
        history=pd.DataFrame(
            {"time": [], "open": [], "high": [], "low": [], "close": [], "volume": []}
        ),
        board={},
        reference_price=100.0,
        board_ceiling=None,
        board_floor=None,
        foreign_buy_volume=None,
        foreign_sell_volume=None,
        current_room=None,
        total_room=None,
    )
    client = _client_returning("ok")

    result = run_decision(empty_data, _synthesis(), _opinions(), client)

    assert "lỗi" in result.lower()
    client.messages.create.assert_not_called()
