"""Per-ticker orchestration.

Strategy agents are sync SDK calls run through asyncio.to_thread so several can
be in flight at once, bounded by a semaphore to respect API rate limits.
"""

import asyncio
import logging

from agent.aggregator import aggregate, partition_opinions
from agent.decision_agent import run_decision
from agent.schemas import AgentOpinion
from agent.strategy_agent import Strategy, run_strategy
from core.market_profile import Exchange
from data_provider.vnstock_fetcher import FetchError, fetch_ticker
from formatters import render_dashboard, render_insufficient

logger = logging.getLogger(__name__)


async def _run_one(strategy, data, client, semaphore) -> AgentOpinion:
    if semaphore is None:
        return await asyncio.to_thread(run_strategy, strategy, data, client)
    async with semaphore:
        return await asyncio.to_thread(run_strategy, strategy, data, client)


async def analyze_ticker(
    symbol: str,
    exchange: Exchange,
    strategies: list[Strategy],
    client,
    semaphore: asyncio.Semaphore | None,
) -> str | None:
    """Analyze one ticker. Returns Markdown, or None if the ticker was skipped."""
    try:
        data = await asyncio.to_thread(fetch_ticker, symbol, exchange)
    except FetchError as exc:
        logger.warning("skipping %s: %s", symbol, exc)
        return None

    opinions = await asyncio.gather(
        *(_run_one(strategy, data, client, semaphore) for strategy in strategies)
    )
    opinions = list(opinions)

    valid, invalid = partition_opinions(opinions)
    if not valid:
        logger.warning("%s: no valid opinions from %d strategies", symbol, len(opinions))
        return render_insufficient(symbol, invalid)

    synthesis = aggregate(opinions)
    decision_text = await asyncio.to_thread(
        run_decision, data, synthesis, valid, client
    )

    return render_dashboard(data, synthesis, valid, decision_text)


async def run_pipeline(
    symbols: list[str],
    exchange: Exchange,
    strategies: list[Strategy],
    client,
    max_concurrent: int,
) -> list[tuple[str, str]]:
    """Analyze every symbol. Returns [(symbol, markdown)] for tickers that produced one."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[tuple[str, str]] = []

    for symbol in symbols:
        # Defense-in-depth: analyze_ticker() already handles the *expected*
        # failure mode (FetchError -> None, handled inside analyze_ticker and
        # left untouched here). This except clause is the orchestration
        # layer's own backstop for anything *unexpected* -- a future bug in
        # aggregate(), a renderer, or any other function in the chain -- so
        # that one bad ticker still can never abort the rest of the
        # watchlist run, even if some downstream function's "never raise"
        # contract is ever broken by a later change.
        try:
            markdown = await analyze_ticker(symbol, exchange, strategies, client, semaphore)
        except Exception as exc:  # noqa: BLE001 - see comment above
            logger.error("unexpected error analyzing %s: %s", symbol, exc)
            continue

        if markdown is not None:
            results.append((symbol, markdown))

    return results
