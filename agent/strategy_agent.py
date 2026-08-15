"""Strategy agents: one Claude call per strategy, per ticker.

run_strategy never raises. Every failure path produces an AgentOpinion with
invalid_signal=True so the aggregator can route it to diagnostics instead of
silently treating a broken agent as a `hold` vote.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

from agent.llm import strategy_model
from agent.schemas import AgentOpinion, AgentOpinionOut, is_valid_strategy_signal
from core.market_profile import market_rules_text
from data_provider.vnstock_fetcher import TickerData, history_summary

logger = logging.getLogger(__name__)

MAX_TOKENS = 4096


@dataclass
class Strategy:
    name: str
    persona: str
    prompt: str


def load_strategies(directory: str = "strategies") -> list[Strategy]:
    """Load every *.yaml in `directory` as a Strategy, sorted by filename."""
    strategies: list[Strategy] = []
    for path in sorted(Path(directory).glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        strategies.append(
            Strategy(
                name=raw["name"],
                persona=raw["persona"],
                prompt=raw["prompt"],
            )
        )
    return strategies


def _invalid(strategy: Strategy, reason: str, raw: dict | None = None) -> AgentOpinion:
    logger.warning("strategy %s invalid: %s", strategy.name, reason)
    return AgentOpinion(
        agent_name=strategy.name,
        signal="",
        confidence=0.0,
        reasoning="",
        key_levels={},
        raw_data=raw or {},
        invalid_signal=True,
        invalid_reason=reason,
    )


def run_strategy(strategy: Strategy, data: TickerData, client) -> AgentOpinion:
    """Run one strategy agent against one ticker."""
    summary = history_summary(data)
    user_prompt = strategy.prompt.format(
        market_rules=market_rules_text(), data_summary=summary
    )

    try:
        response = client.messages.parse(
            model=strategy_model(),
            max_tokens=MAX_TOKENS,
            system=strategy.persona,
            messages=[{"role": "user", "content": user_prompt}],
            output_format=AgentOpinionOut,
        )
    except Exception as exc:  # noqa: BLE001 - any failure becomes a diagnostics entry
        return _invalid(strategy, f"API call failed: {exc}")

    if getattr(response, "stop_reason", None) == "refusal":
        return _invalid(strategy, "Claude refusal (stop_reason=refusal)")

    parsed: AgentOpinionOut | None = getattr(response, "parsed_output", None)
    if parsed is None:
        return _invalid(strategy, "parsed_output was None")

    if not is_valid_strategy_signal(parsed.signal):
        return _invalid(
            strategy,
            f"non-canonical signal: {parsed.signal!r}",
            raw={"signal": parsed.signal, "reasoning": parsed.reasoning},
        )

    return AgentOpinion(
        agent_name=strategy.name,
        signal=parsed.signal,
        confidence=parsed.confidence,
        reasoning=parsed.reasoning,
        key_levels=parsed.key_levels,
        raw_data={"symbol": data.symbol, "summary": summary},
    )
