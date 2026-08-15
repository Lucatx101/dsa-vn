"""Aggregation half of the multi-strategy contract.

Invariant carried over from DSA: an invalid opinion lands in diagnostics. It is
never silently converted to `hold` and mixed into the evidence chain.
"""

from agent.schemas import (
    NEUTRAL_SCORE,
    SIGNAL_SCORES,
    AgentOpinion,
    StrategySynthesis,
    is_valid_strategy_signal,
)
from agent.synthesis import synthesize


def partition_opinions(
    opinions: list[AgentOpinion],
) -> tuple[list[AgentOpinion], list[AgentOpinion]]:
    """Split opinions into (valid, invalid)."""
    valid: list[AgentOpinion] = []
    invalid: list[AgentOpinion] = []
    for opinion in opinions:
        if opinion.invalid_signal or not is_valid_strategy_signal(opinion.signal):
            invalid.append(opinion)
        else:
            valid.append(opinion)
    return valid, invalid


def score_to_signal(score: float) -> str:
    """Map a weighted score back to the nearest canonical signal."""
    return min(SIGNAL_SCORES, key=lambda sig: abs(SIGNAL_SCORES[sig] - score))


def _summary_params(valid: list, invalid: list, total: int) -> dict[str, int]:
    return {
        "opinion_count": len(valid),
        "invalid_opinion_count": len(invalid),
        "total_opinion_count": total,
    }


def aggregate(opinions: list[AgentOpinion]) -> StrategySynthesis:
    """Combine strategy opinions into an immutable StrategySynthesis."""
    valid, invalid = partition_opinions(opinions)
    params = _summary_params(valid, invalid, len(opinions))

    # Branch 1: no valid evidence at all.
    if not valid:
        return StrategySynthesis(
            final_signal="hold",
            weighted_score=NEUTRAL_SCORE,
            confidence=0.0,
            consensus_level="insufficient",
            conflict_severity="none",
            summary_params=params,
        )

    # Branch 2: a single opinion can never establish consensus, however confident.
    if len(valid) == 1:
        only = valid[0]
        return StrategySynthesis(
            final_signal=only.signal,
            weighted_score=SIGNAL_SCORES[only.signal],
            confidence=only.confidence,
            consensus_level="insufficient",
            conflict_severity="none",
            supporting_skills=[only.agent_name],
            summary_params=params,
        )

    total_confidence = sum(o.confidence for o in valid)

    # Branch 3: multiple opinions but no confidence behind any of them.
    if total_confidence == 0:
        return StrategySynthesis(
            final_signal="hold",
            weighted_score=NEUTRAL_SCORE,
            confidence=0.0,
            consensus_level="insufficient",
            conflict_severity="none",
            summary_params=params,
        )

    weighted_score = (
        sum(SIGNAL_SCORES[o.signal] * o.confidence for o in valid) / total_confidence
    )

    supporting, opposing, consensus_level, conflict_severity = synthesize(
        valid, weighted_score
    )

    return StrategySynthesis(
        final_signal=score_to_signal(weighted_score),
        weighted_score=weighted_score,
        confidence=total_confidence / len(valid),
        consensus_level=consensus_level,
        conflict_severity=conflict_severity,
        supporting_skills=supporting,
        opposing_skills=opposing,
        summary_params=params,
    )
