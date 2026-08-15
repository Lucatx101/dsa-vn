"""Standardized opinion and synthesis schemas, ported from DSA's
multi-strategy contract."""

from pydantic import BaseModel, Field

SIGNALS: tuple[str, ...] = ("strong_sell", "sell", "hold", "buy", "strong_buy")

SIGNAL_SCORES: dict[str, float] = {
    "strong_sell": 1.0,
    "sell": 2.0,
    "hold": 3.0,
    "buy": 4.0,
    "strong_buy": 5.0,
}

NEUTRAL_SCORE = SIGNAL_SCORES["hold"]


def is_valid_strategy_signal(signal: str) -> bool:
    """Canonical signals are lowercase and drawn from SIGNALS."""
    return signal in SIGNAL_SCORES


class AgentOpinionOut(BaseModel):
    """Exactly what a strategy agent is asked to return.

    Kept separate from AgentOpinion so the LLM schema stays minimal — the
    agent must not be able to set agent_name, raw_data, or invalid_signal.
    """

    signal: str = Field(
        description=(
            "Tín hiệu, chọn đúng một trong: strong_buy, buy, hold, sell, strong_sell. "
            "Viết thường."
        )
    )
    confidence: float = Field(
        description="Độ tin cậy từ 0.0 đến 1.0.", ge=0.0, le=1.0
    )
    reasoning: str = Field(description="Lý do ngắn gọn bằng tiếng Việt.")
    key_levels: dict[str, float] = Field(
        default_factory=dict,
        description="Các mức giá quan trọng, ví dụ {'ho_tro': 100.0, 'khang_cu': 120.0}.",
    )


class AgentOpinion(BaseModel):
    """A strategy agent's opinion after enrichment and validation."""

    agent_name: str
    signal: str
    confidence: float
    reasoning: str
    key_levels: dict[str, float] = Field(default_factory=dict)
    raw_data: dict = Field(default_factory=dict)
    invalid_signal: bool = False
    invalid_reason: str | None = None


class StrategySynthesis(BaseModel):
    """Immutable aggregate. The decision agent explains it; nothing rewrites it."""

    final_signal: str
    weighted_score: float
    confidence: float
    consensus_level: str  # high | medium | low | insufficient
    conflict_severity: str  # none | low | medium | high
    supporting_skills: list[str] = Field(default_factory=list)
    opposing_skills: list[str] = Field(default_factory=list)
    summary_params: dict[str, int] = Field(default_factory=dict)
