"""One-off probe: confirm the vnstock API shape against the live VCI source.

Run once before building data_provider/. Records real column names so the
fetcher is written against reality rather than assumption.
"""

import traceback
from datetime import date, timedelta

from vnstock import Quote, Trading

SYMBOL = "FPT"


def probe_history() -> None:
    print("=== Quote.history(source='vci') ===")
    end = date.today()
    start = end - timedelta(days=200)
    df = Quote(source="vci", symbol=SYMBOL).history(
        start=start.isoformat(), end=end.isoformat(), interval="D"
    )
    print("columns:", list(df.columns))
    print("dtypes:\n", df.dtypes)
    print("rows:", len(df))
    print("tail:\n", df.tail(3))


def probe_price_board() -> None:
    print("\n=== Trading.price_board(source='vci') ===")
    df = Trading(source="vci").price_board(symbols_list=[SYMBOL, "VNM"])
    print("columns:", list(df.columns))
    print("shape:", df.shape)
    print(df.head())
    foreign_cols = [c for c in map(str, df.columns) if "foreign" in c.lower()]
    print("FOREIGN COLUMNS FOUND:", foreign_cols)


def probe_foreign_trade_is_unavailable() -> None:
    """Confirm foreign_trade() is a sponsor-only feature, as the source suggests."""
    print("\n=== Trading.foreign_trade() (expected to FAIL) ===")
    try:
        df = Trading(source="vci", symbol=SYMBOL).foreign_trade()
        print("UNEXPECTED SUCCESS - columns:", list(df.columns))
    except Exception as exc:  # noqa: BLE001 - probing, want the raw failure
        print(f"failed as expected: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    for probe in (probe_history, probe_price_board, probe_foreign_trade_is_unavailable):
        try:
            probe()
        except Exception:  # noqa: BLE001 - probe should keep going
            traceback.print_exc()
