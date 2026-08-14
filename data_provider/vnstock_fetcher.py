"""vnstock wrapper. The only module that imports vnstock.

Source is pinned to "vci": it is the only free source whose price_board exposes
foreign-ownership columns. Trading.foreign_trade() is a sponsor-package feature
and is deliberately not used. Trading also needs random_agent=True — without it
the live API answers HTTP 418.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import pandas as pd
from vnstock import Quote, Trading

from core.market_profile import Exchange

logger = logging.getLogger(__name__)

SOURCE = "vci"


class FetchError(Exception):
    """Raised when a ticker cannot be fetched. Caller skips that ticker."""


@dataclass
class TickerData:
    symbol: str
    exchange: Exchange
    history: pd.DataFrame
    board: dict[str, Any]
    reference_price: float | None
    # Published by the exchange and tick-rounded. Authoritative — prefer these
    # over core.market_profile's computed approximations.
    board_ceiling: float | None
    board_floor: float | None
    foreign_buy_volume: float | None
    foreign_sell_volume: float | None
    current_room: float | None
    total_room: float | None

    @property
    def foreign_net_volume(self) -> float | None:
        """Net foreign flow. None when either side is missing — a missing side
        is unknown, not zero, and must not read as balanced trading."""
        if self.foreign_buy_volume is None or self.foreign_sell_volume is None:
            return None
        return self.foreign_buy_volume - self.foreign_sell_volume


def _first_present(row: dict[str, Any], *names: str) -> float | None:
    for name in names:
        value = row.get(name)
        if value is not None and not pd.isna(value):
            return float(value)
    return None


def _fetch_board_row(symbol: str) -> dict[str, Any]:
    """Price board for one symbol. Returns {} on any failure — board data is
    enrichment, not a hard requirement for the ticker.

    Live columns are a MultiIndex (listing / bid_ask / match), flattened here to
    'match_foreign_buy_volume' and friends.
    """
    try:
        board = Trading(source=SOURCE, random_agent=True).price_board(
            symbols_list=[symbol]
        )
    except Exception as exc:  # noqa: BLE001 - degrade, don't fail the ticker
        logger.warning("price_board failed for %s: %s", symbol, exc)
        return {}

    if board is None or board.empty:
        logger.warning("price_board returned empty for %s", symbol)
        return {}

    if isinstance(board.columns, pd.MultiIndex):
        board = board.copy()
        board.columns = [
            "_".join(str(part) for part in col if part) for col in board.columns
        ]

    return board.iloc[0].to_dict()


def fetch_ticker(symbol: str, exchange: Exchange, days: int = 200) -> TickerData:
    """Fetch OHLCV history plus price-board enrichment for one ticker."""
    end = date.today()
    start = end - timedelta(days=days)

    try:
        history = Quote(source=SOURCE, symbol=symbol).history(
            start=start.isoformat(), end=end.isoformat(), interval="D"
        )
    except Exception as exc:  # noqa: BLE001 - surface as FetchError to the caller
        raise FetchError(f"{symbol}: history fetch failed: {exc}") from exc

    if history is None or history.empty:
        raise FetchError(f"{symbol}: history is empty")

    row = _fetch_board_row(symbol)

    return TickerData(
        symbol=symbol,
        exchange=exchange,
        history=history,
        board=row,
        reference_price=_first_present(row, "listing_ref_price"),
        board_ceiling=_first_present(row, "listing_ceiling"),
        board_floor=_first_present(row, "listing_floor"),
        foreign_buy_volume=_first_present(row, "match_foreign_buy_volume"),
        foreign_sell_volume=_first_present(row, "match_foreign_sell_volume"),
        current_room=_first_present(row, "match_current_room"),
        total_room=_first_present(row, "match_total_room"),
    )


def _ma(series: pd.Series, window: int) -> float | None:
    if len(series) < window:
        return None
    return float(series.tail(window).mean())


def history_summary(data: TickerData, recent_rows: int = 10) -> str:
    """Compact Vietnamese text block describing recent price action.

    Injected verbatim into strategy-agent prompts, so it must stay short.
    """
    df = data.history
    close = df["close"]
    volume = df["volume"]

    ma20 = _ma(close, 20)
    ma50 = _ma(close, 50)
    avg_vol20 = _ma(volume, 20)

    lines = [
        f"Mã: {data.symbol} (sàn {data.exchange.value})",
        f"Giá đóng cửa gần nhất: {float(close.iloc[-1]):,.2f}",
        f"MA20: {ma20:,.2f}" if ma20 is not None else "MA20: không đủ dữ liệu",
        f"MA50: {ma50:,.2f}" if ma50 is not None else "MA50: không đủ dữ liệu",
        f"Khối lượng phiên gần nhất: {float(volume.iloc[-1]):,.0f}",
        (
            f"Khối lượng trung bình 20 phiên: {avg_vol20:,.0f}"
            if avg_vol20 is not None
            else "Khối lượng trung bình 20 phiên: không đủ dữ liệu"
        ),
        f"Cao nhất {len(df)} phiên: {float(df['high'].max()):,.2f}",
        f"Thấp nhất {len(df)} phiên: {float(df['low'].min()):,.2f}",
    ]

    if data.reference_price is not None:
        lines.append(f"Giá tham chiếu: {data.reference_price:,.2f}")
    if data.board_ceiling is not None:
        lines.append(f"Giá trần (sở công bố): {data.board_ceiling:,.2f}")
    if data.board_floor is not None:
        lines.append(f"Giá sàn (sở công bố): {data.board_floor:,.2f}")
    if data.foreign_buy_volume is not None:
        lines.append(f"Khối ngoại mua: {data.foreign_buy_volume:,.0f}")
    if data.foreign_sell_volume is not None:
        lines.append(f"Khối ngoại bán: {data.foreign_sell_volume:,.0f}")
    net = data.foreign_net_volume
    if net is not None:
        direction = "mua ròng" if net > 0 else ("bán ròng" if net < 0 else "cân bằng")
        lines.append(f"Khối ngoại {direction}: {net:,.0f}")
    if data.total_room is not None:
        lines.append(f"Room ngoại tổng: {data.total_room:,.2f}")
    if data.current_room is not None:
        lines.append(f"Room ngoại còn lại: {data.current_room:,.2f}")

    tail = df.tail(recent_rows)[["time", "open", "high", "low", "close", "volume"]]
    lines.append(f"\n{recent_rows} phiên gần nhất:\n{tail.to_string(index=False)}")

    return "\n".join(lines)
