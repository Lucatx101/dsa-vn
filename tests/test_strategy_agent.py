from unittest.mock import MagicMock

import pandas as pd
import pytest

from agent.schemas import AgentOpinionOut
from agent.strategy_agent import Strategy, load_strategies, run_strategy
from core.market_profile import Exchange
from data_provider.vnstock_fetcher import TickerData

STRATEGY = Strategy(
    name="ma_trend",
    persona="Bạn là chuyên gia phân tích xu hướng đường trung bình động.",
    prompt="Phân tích xu hướng MA cho mã sau.\n\n{market_rules}\n\n{data_summary}",
)


def _ticker_data() -> TickerData:
    rows = 60
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


def _client_returning(parsed, stop_reason="end_turn"):
    client = MagicMock()
    response = MagicMock()
    response.parsed_output = parsed
    response.stop_reason = stop_reason
    client.messages.parse.return_value = response
    return client


class TestRunStrategy:
    def test_valid_response_becomes_valid_opinion(self):
        client = _client_returning(
            AgentOpinionOut(
                signal="buy",
                confidence=0.75,
                reasoning="MA20 cắt lên MA50.",
                key_levels={"ho_tro": 98.0},
            )
        )
        opinion = run_strategy(STRATEGY, _ticker_data(), client)

        assert opinion.agent_name == "ma_trend"
        assert opinion.signal == "buy"
        assert opinion.confidence == pytest.approx(0.75)
        assert opinion.invalid_signal is False
        assert opinion.key_levels == {"ho_tro": 98.0}

    def test_prompt_includes_market_rules_and_symbol(self):
        client = _client_returning(
            AgentOpinionOut(signal="hold", confidence=0.5, reasoning="x", key_levels={})
        )
        run_strategy(STRATEGY, _ticker_data(), client)

        sent = client.messages.parse.call_args.kwargs["messages"][0]["content"]
        assert "HOSE ±7%" in sent
        assert "FPT" in sent

    def test_noncanonical_signal_is_marked_invalid(self):
        client = _client_returning(
            AgentOpinionOut(signal="MUA", confidence=0.9, reasoning="x", key_levels={})
        )
        opinion = run_strategy(STRATEGY, _ticker_data(), client)

        assert opinion.invalid_signal is True
        assert opinion.invalid_reason is not None
        assert opinion.signal != "hold"  # must not be coerced

    def test_none_parsed_output_is_marked_invalid(self):
        opinion = run_strategy(STRATEGY, _ticker_data(), _client_returning(None))
        assert opinion.invalid_signal is True

    def test_refusal_is_marked_invalid(self):
        client = _client_returning(None, stop_reason="refusal")
        opinion = run_strategy(STRATEGY, _ticker_data(), client)
        assert opinion.invalid_signal is True
        assert "refusal" in (opinion.invalid_reason or "").lower()

    def test_api_exception_is_marked_invalid_and_does_not_raise(self):
        client = MagicMock()
        client.messages.parse.side_effect = RuntimeError("rate limited")
        opinion = run_strategy(STRATEGY, _ticker_data(), client)

        assert opinion.invalid_signal is True
        assert "rate limited" in (opinion.invalid_reason or "")

    def test_prompt_format_error_is_marked_invalid_and_does_not_raise(self):
        broken_strategy = Strategy(
            name="broken",
            persona="x",
            prompt="{market_rules} {data_summary} {unexpected}",
        )
        client = _client_returning(
            AgentOpinionOut(signal="hold", confidence=0.5, reasoning="x", key_levels={})
        )
        opinion = run_strategy(broken_strategy, _ticker_data(), client)

        assert opinion.invalid_signal is True
        assert "prompt construction failed" in (opinion.invalid_reason or "")
        client.messages.parse.assert_not_called()


class TestLoadStrategies:
    def test_loads_all_six_strategies(self):
        strategies = load_strategies("strategies")
        names = {s.name for s in strategies}
        assert names == {
            "ma_trend",
            "volume_breakout",
            "box_oscillation",
            "shrink_pullback",
            "foreign_flow",
            "price_band_risk",
        }

    def test_every_strategy_has_persona_and_placeholders(self):
        for strategy in load_strategies("strategies"):
            assert strategy.persona.strip()
            assert "{market_rules}" in strategy.prompt
            assert "{data_summary}" in strategy.prompt
