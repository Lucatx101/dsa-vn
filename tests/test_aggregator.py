import pytest

from agent.aggregator import aggregate, partition_opinions, score_to_signal
from agent.schemas import AgentOpinion, is_valid_strategy_signal


def op(name, signal, confidence, invalid=False):
    return AgentOpinion(
        agent_name=name,
        signal=signal,
        confidence=confidence,
        reasoning="lý do thử nghiệm",
        key_levels={},
        raw_data={},
        invalid_signal=invalid,
    )


class TestSignalValidation:
    def test_canonical_signals_are_valid(self):
        for signal in ("strong_buy", "buy", "hold", "sell", "strong_sell"):
            assert is_valid_strategy_signal(signal)

    def test_uppercase_and_unknown_signals_are_invalid(self):
        assert not is_valid_strategy_signal("BUY")
        assert not is_valid_strategy_signal("maybe")
        assert not is_valid_strategy_signal("")


class TestPartition:
    def test_invalid_flag_moves_opinion_to_invalid_bucket(self):
        valid, invalid = partition_opinions(
            [op("a", "buy", 0.8), op("b", "buy", 0.5, invalid=True)]
        )
        assert [o.agent_name for o in valid] == ["a"]
        assert [o.agent_name for o in invalid] == ["b"]

    def test_noncanonical_signal_moves_opinion_to_invalid_bucket(self):
        valid, invalid = partition_opinions([op("a", "BUY", 0.8), op("b", "sell", 0.4)])
        assert [o.agent_name for o in valid] == ["b"]
        assert [o.agent_name for o in invalid] == ["a"]


class TestInsufficientConsensusBranches:
    def test_zero_valid_opinions(self):
        result = aggregate([op("a", "nonsense", 0.9), op("b", "buy", 0.9, invalid=True)])
        assert result.final_signal == "hold"
        assert result.confidence == pytest.approx(0.0)
        assert result.consensus_level == "insufficient"
        assert result.summary_params["opinion_count"] == 0
        assert result.summary_params["invalid_opinion_count"] == 2
        assert result.summary_params["total_opinion_count"] == 2

    def test_exactly_one_valid_opinion_is_always_insufficient(self):
        """Even a maximally confident lone opinion cannot reach consensus."""
        result = aggregate([op("a", "strong_buy", 1.0)])
        assert result.consensus_level == "insufficient"
        assert result.final_signal == "strong_buy"
        assert result.summary_params["opinion_count"] == 1

    def test_two_or_more_opinions_with_zero_total_confidence(self):
        result = aggregate([op("a", "buy", 0.0), op("b", "sell", 0.0)])
        assert result.final_signal == "hold"
        assert result.confidence == pytest.approx(0.0)
        assert result.consensus_level == "insufficient"

    def test_empty_input(self):
        result = aggregate([])
        assert result.final_signal == "hold"
        assert result.consensus_level == "insufficient"
        assert result.summary_params["total_opinion_count"] == 0


class TestWeightedScore:
    def test_unanimous_buy(self):
        result = aggregate([op("a", "buy", 1.0), op("b", "buy", 1.0)])
        assert result.weighted_score == pytest.approx(4.0)
        assert result.final_signal == "buy"

    def test_confidence_weighting_pulls_score_toward_confident_opinion(self):
        # buy(4.0)*0.9 + sell(2.0)*0.1 = 3.8 ; /1.0 = 3.8
        result = aggregate([op("a", "buy", 0.9), op("b", "sell", 0.1)])
        assert result.weighted_score == pytest.approx(3.8)
        assert result.final_signal == "buy"

    def test_symmetric_opposition_lands_on_hold(self):
        result = aggregate([op("a", "strong_buy", 0.5), op("b", "strong_sell", 0.5)])
        assert result.weighted_score == pytest.approx(3.0)
        assert result.final_signal == "hold"

    def test_confidence_is_mean_of_valid_opinions(self):
        result = aggregate([op("a", "buy", 0.8), op("b", "buy", 0.4)])
        assert result.confidence == pytest.approx(0.6)

    def test_invalid_opinions_do_not_affect_the_score(self):
        with_invalid = aggregate(
            [op("a", "buy", 1.0), op("b", "buy", 1.0), op("c", "strong_sell", 1.0, invalid=True)]
        )
        without = aggregate([op("a", "buy", 1.0), op("b", "buy", 1.0)])
        assert with_invalid.weighted_score == pytest.approx(without.weighted_score)
        assert with_invalid.summary_params["invalid_opinion_count"] == 1


class TestScoreToSignal:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (1.0, "strong_sell"),
            (1.4, "strong_sell"),
            (2.0, "sell"),
            (3.0, "hold"),
            (3.8, "buy"),
            (4.0, "buy"),
            (5.0, "strong_buy"),
        ],
    )
    def test_maps_score_to_nearest_canonical_signal(self, score, expected):
        assert score_to_signal(score) == expected
