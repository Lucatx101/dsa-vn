"""Consensus and conflict detection over the valid opinion set.

`insufficient` consensus is decided by the aggregator (zero opinions, one
opinion, or zero total confidence) and is never produced here.
"""

from agent.schemas import SIGNAL_SCORES, AgentOpinion

SUPPORT_DISTANCE = 1.0


def _conflict_severity(scores: list[float]) -> str:
    spread = max(scores) - min(scores)
    if spread < 1.0:
        return "none"
    if spread < 2.0:
        return "low"
    if spread < 3.0:
        return "medium"
    return "high"


def _consensus_level(alignment_ratio: float, conflict_severity: str) -> str:
    if alignment_ratio >= 2 / 3 and conflict_severity == "none":
        return "high"
    if conflict_severity == "high" or alignment_ratio < 0.5:
        return "low"
    return "medium"


def synthesize(
    valid: list[AgentOpinion], weighted_score: float
) -> tuple[list[str], list[str], str, str]:
    """Return (supporting_skills, opposing_skills, consensus_level, conflict_severity)."""
    supporting: list[str] = []
    opposing: list[str] = []

    for opinion in valid:
        distance = abs(SIGNAL_SCORES[opinion.signal] - weighted_score)
        if distance <= SUPPORT_DISTANCE:
            supporting.append(opinion.agent_name)
        else:
            opposing.append(opinion.agent_name)

    scores = [SIGNAL_SCORES[o.signal] for o in valid]
    conflict_severity = _conflict_severity(scores)
    alignment_ratio = len(supporting) / len(valid)

    return (
        supporting,
        opposing,
        _consensus_level(alignment_ratio, conflict_severity),
        conflict_severity,
    )
