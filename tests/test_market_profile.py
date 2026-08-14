import pytest

from core.market_profile import (
    Exchange,
    ceiling_price,
    floor_price,
    market_rules_text,
    pct_from_reference,
    price_band,
)


def test_price_bands_per_exchange():
    assert price_band(Exchange.HOSE) == pytest.approx(0.07)
    assert price_band(Exchange.HNX) == pytest.approx(0.10)
    assert price_band(Exchange.UPCOM) == pytest.approx(0.15)


def test_ceiling_and_floor_hose():
    assert ceiling_price(100_000, Exchange.HOSE) == pytest.approx(107_000)
    assert floor_price(100_000, Exchange.HOSE) == pytest.approx(93_000)


def test_ceiling_and_floor_upcom():
    assert ceiling_price(20_000, Exchange.UPCOM) == pytest.approx(23_000)
    assert floor_price(20_000, Exchange.UPCOM) == pytest.approx(17_000)


def test_pct_from_reference():
    assert pct_from_reference(107_000, 100_000) == pytest.approx(7.0)
    assert pct_from_reference(93_000, 100_000) == pytest.approx(-7.0)


def test_pct_from_reference_rejects_zero_reference():
    with pytest.raises(ValueError):
        pct_from_reference(100.0, 0.0)


def test_market_rules_text_mentions_all_three_bands():
    text = market_rules_text()
    assert "7%" in text
    assert "10%" in text
    assert "15%" in text
    assert "T+2" in text


def test_market_rules_text_flags_computed_bands_as_approximate():
    """The exchange tick-rounds published bands, so the prompt must tell the
    model to prefer a published trần/sàn over the computed one."""
    text = market_rules_text()
    assert "ƯỚC LƯỢNG" in text
    assert "công bố" in text


def test_ceiling_and_floor_docstrings_warn_they_are_approximate():
    for fn in (ceiling_price, floor_price):
        assert "APPROXIMATE" in (fn.__doc__ or "") or "approximate" in (fn.__doc__ or "").lower()
