import pandas as pd

from agent.schemas import AgentOpinion, StrategySynthesis
from core.market_profile import Exchange
from data_provider.vnstock_fetcher import TickerData
from formatters import render_dashboard, render_insufficient


def _data():
    rows = 30
    return TickerData(
        symbol="FPT",
        exchange=Exchange.HOSE,
        history=pd.DataFrame(
            {
                "time": pd.date_range("2026-01-01", periods=rows, freq="D"),
                "open": [100.0] * rows,
                "high": [102.0] * rows,
                "low": [99.0] * rows,
                "close": [101.0] * rows,
                "volume": [1_000_000.0] * rows,
            }
        ),
        board={},
        reference_price=100.0,
        board_ceiling=None,
        board_floor=None,
        foreign_buy_volume=None,
        foreign_sell_volume=None,
        current_room=None,
        total_room=None,
    )


def _synthesis():
    return StrategySynthesis(
        final_signal="buy",
        weighted_score=3.9,
        confidence=0.72,
        consensus_level="medium",
        conflict_severity="low",
        supporting_skills=["ma_trend", "volume_breakout"],
        opposing_skills=["price_band_risk"],
        summary_params={
            "opinion_count": 3,
            "invalid_opinion_count": 1,
            "total_opinion_count": 4,
        },
    )


def _opinions():
    return [
        AgentOpinion(
            agent_name="ma_trend",
            signal="buy",
            confidence=0.8,
            reasoning="MA20 trên MA50.",
            key_levels={},
            raw_data={},
        )
    ]


def test_dashboard_contains_symbol_signal_and_decision_text():
    md = render_dashboard(_data(), _synthesis(), _opinions(), "Kết luận: mua thăm dò.")
    assert "FPT" in md
    assert "buy" in md
    assert "Kết luận: mua thăm dò." in md


def test_dashboard_lists_supporting_and_opposing_agents():
    md = render_dashboard(_data(), _synthesis(), _opinions(), "x")
    assert "ma_trend" in md
    assert "price_band_risk" in md


def test_dashboard_surfaces_invalid_opinion_count():
    md = render_dashboard(_data(), _synthesis(), _opinions(), "x")
    assert "1" in md
    assert "không hợp lệ" in md.lower()


def test_render_insufficient_names_the_failed_agents():
    invalid = [
        AgentOpinion(
            agent_name="ma_trend",
            signal="",
            confidence=0.0,
            reasoning="",
            key_levels={},
            raw_data={},
            invalid_signal=True,
            invalid_reason="API call failed: timeout",
        )
    ]
    md = render_insufficient("FPT", invalid)
    assert "FPT" in md
    assert "ma_trend" in md
    assert "timeout" in md
