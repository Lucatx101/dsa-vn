"""Consensus and conflict detection. Fleshed out in Task 5."""

from agent.schemas import AgentOpinion


def synthesize(
    valid: list[AgentOpinion], weighted_score: float
) -> tuple[list[str], list[str], str, str]:
    """Return (supporting_skills, opposing_skills, consensus_level, conflict_severity)."""
    return ([o.agent_name for o in valid], [], "medium", "none")
