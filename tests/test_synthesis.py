from agent.schemas import AgentOpinion
from agent.synthesis import synthesize


def op(name, signal, confidence=0.8):
    return AgentOpinion(
        agent_name=name,
        signal=signal,
        confidence=confidence,
        reasoning="lý do",
        key_levels={},
        raw_data={},
    )


class TestGrouping:
    def test_all_within_one_point_are_supporting(self):
        opinions = [op("a", "buy"), op("b", "buy"), op("c", "hold")]
        supporting, opposing, _, _ = synthesize(opinions, weighted_score=3.7)
        assert set(supporting) == {"a", "b", "c"}
        assert opposing == []

    def test_far_opinion_is_opposing(self):
        opinions = [op("a", "buy"), op("b", "buy"), op("c", "strong_sell")]
        supporting, opposing, _, _ = synthesize(opinions, weighted_score=4.0)
        assert set(supporting) == {"a", "b"}
        assert opposing == ["c"]

    def test_boundary_at_exactly_one_point_counts_as_supporting(self):
        opinions = [op("a", "buy"), op("b", "hold")]
        supporting, opposing, _, _ = synthesize(opinions, weighted_score=4.0)
        assert set(supporting) == {"a", "b"}
        assert opposing == []


class TestConflictSeverity:
    def test_none_when_all_agree(self):
        _, _, _, severity = synthesize([op("a", "buy"), op("b", "buy")], 4.0)
        assert severity == "none"

    def test_low_for_adjacent_signals(self):
        _, _, _, severity = synthesize([op("a", "buy"), op("b", "hold")], 3.5)
        assert severity == "low"

    def test_medium_for_two_step_spread(self):
        _, _, _, severity = synthesize([op("a", "buy"), op("b", "sell")], 3.0)
        assert severity == "medium"

    def test_high_for_opposite_extremes(self):
        _, _, _, severity = synthesize([op("a", "strong_buy"), op("b", "strong_sell")], 3.0)
        assert severity == "high"


class TestConsensusLevel:
    def test_high_requires_alignment_and_no_conflict(self):
        _, _, level, _ = synthesize([op("a", "buy"), op("b", "buy"), op("c", "buy")], 4.0)
        assert level == "high"

    def test_not_high_when_any_conflict_exists(self):
        _, _, level, severity = synthesize([op("a", "buy"), op("b", "hold")], 3.5)
        assert severity != "none"
        assert level != "high"

    def test_low_when_conflict_is_high(self):
        _, _, level, _ = synthesize([op("a", "strong_buy"), op("b", "strong_sell")], 3.0)
        assert level == "low"

    def test_low_when_fewer_than_half_align(self):
        """Alignment below 0.5 forces `low` even when conflict is only medium."""
        opinions = [op("a", "buy"), op("b", "sell"), op("c", "sell")]
        supporting, _, level, severity = synthesize(opinions, weighted_score=4.0)
        assert supporting == ["a"]  # 1/3 alignment
        assert severity == "medium"  # spread of 2.0, not high
        assert level == "low"

    def test_medium_between_the_extremes(self):
        opinions = [op("a", "buy"), op("b", "buy"), op("c", "sell")]
        _, _, level, _ = synthesize(opinions, weighted_score=3.5)
        assert level == "medium"

    def test_never_returns_insufficient(self):
        """insufficient is the aggregator's call, not the synthesizer's."""
        for opinions, score in (
            ([op("a", "buy"), op("b", "buy")], 4.0),
            ([op("a", "strong_buy"), op("b", "strong_sell")], 3.0),
        ):
            _, _, level, _ = synthesize(opinions, score)
            assert level != "insufficient"
