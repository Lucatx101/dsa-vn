from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from agent.schemas import AgentOpinion
from agent.strategy_agent import Strategy
from core.market_profile import Exchange
from data_provider.vnstock_fetcher import FetchError, TickerData
from pipeline import analyze_ticker, run_pipeline

STRATEGIES = [
    Strategy(name="ma_trend", persona="p", prompt="{market_rules} {data_summary}"),
    Strategy(name="volume_breakout", persona="p", prompt="{market_rules} {data_summary}"),
]


def _data(symbol="FPT"):
    rows = 30
    return TickerData(
        symbol=symbol,
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


def _valid_opinion(name):
    return AgentOpinion(
        agent_name=name,
        signal="buy",
        confidence=0.8,
        reasoning="lý do",
        key_levels={},
        raw_data={},
    )


def _invalid_opinion(name):
    return AgentOpinion(
        agent_name=name,
        signal="",
        confidence=0.0,
        reasoning="",
        key_levels={},
        raw_data={},
        invalid_signal=True,
        invalid_reason="API call failed: timeout",
    )


class TestAnalyzeTicker:
    async def test_happy_path_returns_dashboard(self):
        with (
            patch("pipeline.fetch_ticker", return_value=_data()),
            patch("pipeline.run_strategy", side_effect=lambda s, d, c: _valid_opinion(s.name)),
            patch("pipeline.run_decision", return_value="Phân tích chi tiết."),
        ):
            md = await analyze_ticker("FPT", Exchange.HOSE, STRATEGIES, MagicMock(), None)

        assert md is not None
        assert "FPT" in md
        assert "Phân tích chi tiết." in md

    async def test_fetch_error_returns_none(self):
        with patch("pipeline.fetch_ticker", side_effect=FetchError("no such symbol")):
            md = await analyze_ticker("NOPE", Exchange.HOSE, STRATEGIES, MagicMock(), None)
        assert md is None

    async def test_all_opinions_invalid_returns_insufficient_and_skips_decision(self):
        with (
            patch("pipeline.fetch_ticker", return_value=_data()),
            patch("pipeline.run_strategy", side_effect=lambda s, d, c: _invalid_opinion(s.name)),
            patch("pipeline.run_decision") as decision,
        ):
            md = await analyze_ticker("FPT", Exchange.HOSE, STRATEGIES, MagicMock(), None)

        assert md is not None
        assert "không đủ dữ liệu" in md
        assert "timeout" in md
        decision.assert_not_called()

    async def test_every_strategy_is_invoked(self):
        calls = []

        def record(strategy, data, client):
            calls.append(strategy.name)
            return _valid_opinion(strategy.name)

        with (
            patch("pipeline.fetch_ticker", return_value=_data()),
            patch("pipeline.run_strategy", side_effect=record),
            patch("pipeline.run_decision", return_value="x"),
        ):
            await analyze_ticker("FPT", Exchange.HOSE, STRATEGIES, MagicMock(), None)

        assert sorted(calls) == ["ma_trend", "volume_breakout"]


class TestRunPipeline:
    async def test_returns_one_entry_per_successful_ticker(self):
        with (
            patch("pipeline.fetch_ticker", side_effect=lambda s, e, **kw: _data(s)),
            patch("pipeline.run_strategy", side_effect=lambda s, d, c: _valid_opinion(s.name)),
            patch("pipeline.run_decision", return_value="x"),
        ):
            results = await run_pipeline(
                ["FPT", "VNM"], Exchange.HOSE, STRATEGIES, MagicMock(), 4
            )

        assert [symbol for symbol, _ in results] == ["FPT", "VNM"]

    async def test_one_bad_ticker_does_not_stop_the_others(self):
        def fetch(symbol, exchange, **kwargs):
            if symbol == "BAD":
                raise FetchError("boom")
            return _data(symbol)

        with (
            patch("pipeline.fetch_ticker", side_effect=fetch),
            patch("pipeline.run_strategy", side_effect=lambda s, d, c: _valid_opinion(s.name)),
            patch("pipeline.run_decision", return_value="x"),
        ):
            results = await run_pipeline(
                ["BAD", "FPT"], Exchange.HOSE, STRATEGIES, MagicMock(), 4
            )

        assert [symbol for symbol, _ in results] == ["FPT"]

    async def test_unexpected_exception_does_not_stop_the_others(self):
        # Task 9 addition: run_pipeline's loop is defense-in-depth against an
        # exception that is *not* FetchError -- e.g. a future bug in
        # aggregate()/render_dashboard()/etc. This is deliberately distinct
        # from test_one_bad_ticker_does_not_stop_the_others above, which only
        # exercises the already-handled FetchError -> None path inside
        # analyze_ticker itself. Here, fetch_ticker raises a plain
        # RuntimeError that analyze_ticker does NOT catch, so it propagates
        # out of the `await analyze_ticker(...)` call in run_pipeline and
        # must be caught there instead.
        def fetch(symbol, exchange, **kwargs):
            if symbol == "BAD":
                raise RuntimeError("unexpected bug")
            return _data(symbol)

        with (
            patch("pipeline.fetch_ticker", side_effect=fetch),
            patch("pipeline.run_strategy", side_effect=lambda s, d, c: _valid_opinion(s.name)),
            patch("pipeline.run_decision", return_value="x"),
        ):
            results = await run_pipeline(
                ["BAD", "FPT"], Exchange.HOSE, STRATEGIES, MagicMock(), 4
            )

        assert [symbol for symbol, _ in results] == ["FPT"]
