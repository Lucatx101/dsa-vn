"""CLI entry point. Run manually or from cron."""

import argparse
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from agent.llm import get_client
from agent.strategy_agent import load_strategies
from core.market_profile import Exchange
from notification_sender.telegram_sender import send_markdown
from pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("dsa-vn")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DSA-VN stock analysis")
    parser.add_argument(
        "--symbols",
        help="Comma-separated tickers. Overrides STOCK_LIST from .env.",
    )
    parser.add_argument(
        "--exchange",
        default="HOSE",
        choices=[e.value for e in Exchange],
        help="Exchange for the whole watchlist (default: HOSE).",
    )
    parser.add_argument(
        "--no-send",
        action="store_true",
        help="Print dashboards to stdout instead of sending to Telegram.",
    )
    return parser.parse_args()


async def _main() -> int:
    load_dotenv()
    args = _parse_args()

    raw_symbols = args.symbols or os.getenv("STOCK_LIST", "")
    symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
    if not symbols:
        logger.error("No symbols. Set STOCK_LIST in .env or pass --symbols.")
        return 1

    strategies = load_strategies("strategies")
    if not strategies:
        logger.error("No strategies found in strategies/")
        return 1

    max_concurrent = int(os.getenv("MAX_CONCURRENT_AGENTS", "6"))
    exchange = Exchange(args.exchange)

    logger.info(
        "Analyzing %d symbols on %s with %d strategies",
        len(symbols),
        exchange.value,
        len(strategies),
    )

    results = await run_pipeline(
        symbols, exchange, strategies, get_client(), max_concurrent
    )

    if not results:
        logger.warning("No dashboards produced.")
        return 0

    if args.no_send:
        for _, markdown in results:
            print(markdown)
            print("\n---\n")
        return 0

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set. Use --no-send.")
        return 1

    for symbol, markdown in results:
        if send_markdown(markdown, token, chat_id):
            logger.info("sent %s", symbol)
        else:
            logger.error("failed to send %s", symbol)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
