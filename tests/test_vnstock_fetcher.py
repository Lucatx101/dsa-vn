from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from core.market_profile import Exchange
from data_provider.vnstock_fetcher import (
    FetchError,
    TickerData,
    fetch_ticker,
    history_summary,
)


def _fake_history(rows: int = 30) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=rows, freq="D"),
            "open": [100.0 + i for i in range(rows)],
            "high": [102.0 + i for i in range(rows)],
            "low": [99.0 + i for i in range(rows)],
            "close": [101.0 + i for i in range(rows)],
            "volume": [1_000_000 + i * 1000 for i in range(rows)],
        }
    )


def _fake_board() -> pd.DataFrame:
    """Mirrors the live shape: MultiIndex columns grouped listing/match."""
    return pd.DataFrame(
        [[69_200.0, 74_000.0, 64_400.0, 68_300.0, 800_000.0, 300_000.0, 12.5, 49.0]],
        columns=pd.MultiIndex.from_tuples(
            [
                ("listing", "ref_price"),
                ("listing", "ceiling"),
                ("listing", "floor"),
                ("match", "match_price"),
                ("match", "foreign_buy_volume"),
                ("match", "foreign_sell_volume"),
                ("match", "current_room"),
                ("match", "total_room"),
            ]
        ),
    )


def test_fetch_ticker_returns_populated_tickerdata():
    with (
        patch("data_provider.vnstock_fetcher.Quote") as quote_cls,
        patch("data_provider.vnstock_fetcher.Trading") as trading_cls,
    ):
        quote_cls.return_value.history.return_value = _fake_history()
        trading_cls.return_value.price_board.return_value = _fake_board()

        data = fetch_ticker("FPT", Exchange.HOSE)

    assert isinstance(data, TickerData)
    assert data.symbol == "FPT"
    assert data.exchange is Exchange.HOSE
    assert len(data.history) == 30
    assert data.reference_price == pytest.approx(69_200.0)
    assert data.foreign_buy_volume == pytest.approx(800_000.0)
    assert data.foreign_sell_volume == pytest.approx(300_000.0)
    assert data.current_room == pytest.approx(12.5)
    assert data.total_room == pytest.approx(49.0)


def test_fetch_ticker_captures_published_bands_not_computed_ones():
    """The exchange tick-rounds its bands, so the published pair must be kept
    verbatim rather than recomputed from the reference price."""
    with (
        patch("data_provider.vnstock_fetcher.Quote") as quote_cls,
        patch("data_provider.vnstock_fetcher.Trading") as trading_cls,
    ):
        quote_cls.return_value.history.return_value = _fake_history()
        trading_cls.return_value.price_board.return_value = _fake_board()

        data = fetch_ticker("FPT", Exchange.HOSE)

    assert data.board_ceiling == pytest.approx(74_000.0)
    assert data.board_floor == pytest.approx(64_400.0)
    # Not the naive ref * 1.07 == 74_044 / ref * 0.93 == 64_356
    assert data.board_ceiling != pytest.approx(69_200.0 * 1.07)
    assert data.board_floor != pytest.approx(69_200.0 * 0.93)


def test_foreign_net_volume_is_buy_minus_sell():
    with (
        patch("data_provider.vnstock_fetcher.Quote") as quote_cls,
        patch("data_provider.vnstock_fetcher.Trading") as trading_cls,
    ):
        quote_cls.return_value.history.return_value = _fake_history()
        trading_cls.return_value.price_board.return_value = _fake_board()

        data = fetch_ticker("FPT", Exchange.HOSE)

    assert data.foreign_net_volume == pytest.approx(500_000.0)


def test_foreign_net_volume_is_none_when_a_side_is_missing():
    data = TickerData(
        symbol="FPT",
        exchange=Exchange.HOSE,
        history=_fake_history(),
        board={},
        reference_price=None,
        board_ceiling=None,
        board_floor=None,
        foreign_buy_volume=800_000.0,
        foreign_sell_volume=None,
        current_room=None,
        total_room=None,
    )
    assert data.foreign_net_volume is None


def test_fetch_ticker_uses_vci_source_and_random_agent():
    """random_agent=True is required — the live API returns HTTP 418 without it."""
    with (
        patch("data_provider.vnstock_fetcher.Quote") as quote_cls,
        patch("data_provider.vnstock_fetcher.Trading") as trading_cls,
    ):
        quote_cls.return_value.history.return_value = _fake_history()
        trading_cls.return_value.price_board.return_value = _fake_board()

        fetch_ticker("FPT", Exchange.HOSE)

    assert quote_cls.call_args.kwargs["source"] == "vci"
    assert trading_cls.call_args.kwargs["source"] == "vci"
    assert trading_cls.call_args.kwargs["random_agent"] is True


def test_fetch_ticker_raises_fetcherror_when_history_empty():
    with (
        patch("data_provider.vnstock_fetcher.Quote") as quote_cls,
        patch("data_provider.vnstock_fetcher.Trading") as trading_cls,
    ):
        quote_cls.return_value.history.return_value = pd.DataFrame()
        trading_cls.return_value.price_board.return_value = _fake_board()

        with pytest.raises(FetchError):
            fetch_ticker("NOPE", Exchange.HOSE)


def test_fetch_ticker_raises_fetcherror_when_vnstock_throws():
    with patch("data_provider.vnstock_fetcher.Quote") as quote_cls:
        quote_cls.return_value.history.side_effect = RuntimeError("network down")

        with pytest.raises(FetchError):
            fetch_ticker("FPT", Exchange.HOSE)


def test_fetch_ticker_tolerates_missing_price_board():
    """Board failure degrades to None fields; it must not kill the whole ticker."""
    with (
        patch("data_provider.vnstock_fetcher.Quote") as quote_cls,
        patch("data_provider.vnstock_fetcher.Trading") as trading_cls,
    ):
        quote_cls.return_value.history.return_value = _fake_history()
        trading_cls.return_value.price_board.side_effect = RuntimeError("board down")

        data = fetch_ticker("FPT", Exchange.HOSE)

    assert len(data.history) == 30
    assert data.reference_price is None
    assert data.foreign_buy_volume is None
    assert data.foreign_net_volume is None


def test_history_summary_contains_price_and_ma():
    data = TickerData(
        symbol="FPT",
        exchange=Exchange.HOSE,
        history=_fake_history(60),
        board={},
        reference_price=130.0,
        board_ceiling=None,
        board_floor=None,
        foreign_buy_volume=None,
        foreign_sell_volume=None,
        current_room=None,
        total_room=None,
    )
    summary = history_summary(data)
    assert "FPT" in summary
    assert "MA20" in summary
    assert "MA50" in summary


def test_history_summary_reports_net_foreign_flow():
    data = TickerData(
        symbol="FPT",
        exchange=Exchange.HOSE,
        history=_fake_history(60),
        board={},
        reference_price=130.0,
        board_ceiling=None,
        board_floor=None,
        foreign_buy_volume=800_000.0,
        foreign_sell_volume=300_000.0,
        current_room=12.5,
        total_room=49.0,
    )
    summary = history_summary(data)
    assert "500,000" in summary  # net = buy - sell, thousands-separated
