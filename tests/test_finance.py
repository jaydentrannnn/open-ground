"""Run: pytest -q   (from the repo root)"""
import json
from pathlib import Path

import pytest

from core import finance

DEAL = Path(__file__).resolve().parents[1] / "lanes" / "3-fund-it" / "data" / "synthetic-example-deal.json"


def test_loan_from_payment_known_value():
    # $1,850/mo at 3% for 30 yrs supports ~ $438,800
    assert finance.loan_from_payment(1850, 0.03) == pytest.approx(438_800, abs=500)


def test_zero_rate():
    assert finance.loan_from_payment(1000, 0.0, 30) == 360_000


def test_higher_rate_lowers_family_price():
    lo = finance.family_price(90_000, 0.05, 0.30, 400)["price"]
    hi = finance.family_price(90_000, 0.07, 0.30, 400)["price"]
    assert hi < lo


@pytest.mark.skipif(not DEAL.exists(), reason="event synthetic deal not in this checkout")
def test_synthetic_deal_balances_to_zero():
    d = json.loads(DEAL.read_text())
    cost = {k: v["value"] for k, v in d["cost_to_create"].items() if k != "total"}
    paid = {k: v["value"] for k, v in d["paid_by"].items() if k != "total"}
    assert finance.gap(cost, paid)["gap"] == 0
    paid_without_fundraising = {k: v for k, v in paid.items() if k != "fundraising_the_gap"}
    assert finance.gap(cost, paid_without_fundraising)["gap"] == 95_000


def test_gift_coverage_never_exceeds_gift():
    lines = {"a": 100, "b": 50}
    assert sum(x["covered"] for x in finance.gift_coverage(120, lines)) == 120


def test_adu_cashflow_basic():
    r = finance.adu_cashflow(300_000, 2_600, 0.07, cash_in=50_000)
    assert r["financed"] == 250_000
    assert r["monthly_loan_payment"] > 0
    assert r["assistance_exceeds_cost"] is False


def test_adu_cashflow_flags_assistance_over_cost():
    r = finance.adu_cashflow(100_000, 2_000, 0.07, cash_in=80_000, grants=40_000)
    assert r["financed"] == 0 and r["assistance_exceeds_cost"] is True


def test_adu_build_cost_scales_with_size():
    assert finance.adu_build_cost(600, 250) == 150_000
    assert finance.adu_build_cost(800, 250) > finance.adu_build_cost(600, 250)
    assert finance.adu_build_cost(0, 250) == 0


def test_adu_rate_sensitivity_payment_rises_with_rate():
    rows = finance.adu_rate_sensitivity(200_000, 2_500, [0.06, 0.07, 0.08], cash_in=20_000)
    pays = [r["monthly_loan_payment"] for r in rows]
    assert pays == sorted(pays) and rows[1]["rate"] == 0.07


def test_assumptions_area_weights_match_area_py():
    from core import area
    a = json.loads((Path(__file__).resolve().parents[1] / "data" / "processed" / "assumptions.json").read_text())
    assert a["area_score"]["weights"]["value"] == area.DEFAULT_WEIGHTS


# --- HSC 50052.5 statutory cap (values from HCD 2026 State Income Limits, OC, p.11) ---------
LIMITS = json.loads((Path(__file__).resolve().parents[1] / "data" / "processed" / "income_limits_2026.json").read_text())


def test_gap_flags_unknown_lines():
    g = finance.gap({"land": 100, "fees": None}, {"family": 50})
    assert g["gap"] == 50 and g["complete"] is False and g["missing"] == ["cost:fees"]
    assert finance.gap({"land": 100}, {"family": 100})["complete"] is True
    # same key on both sides must not hide the unknown cost
    assert finance.gap({"x": None}, {"x": 50})["complete"] is False


def test_statutory_price_withheld_when_floor_exceeds_cap():
    # moderate 4p household in a studio: cap uses 1p median 97,000 -> 35% x 110% x 97,000 / 12 = 3,112.08;
    # floor 28% x 160,000 / 12 = 3,733.33 > cap
    p = finance.statutory_price(160_000, 4, 0, LIMITS, 0.07, 500, 0.011)
    assert p["floor_exceeds_cap"] is True and p["price"] is None and "policy" in p["reason"]


def test_statutory_rate_sensitivity_gap_grows_with_rate():
    rows = finance.statutory_rate_sensitivity(90_000, 4, 3, LIMITS, [0.06, 0.07, 0.08], 550, 0.011,
                                              total_cost=535_000, other_sources=155_000)
    gaps = [r["gap"] for r in rows]
    assert gaps == sorted(gaps)
    none = finance.statutory_rate_sensitivity(300_000, 4, 3, LIMITS, [0.07], 550, 0.011, 535_000, 0)
    assert none[0]["gap"] is None


def test_household_size_for_unit_matches_50052_5_h():
    assert [finance.household_size_for_unit(b) for b in range(5)] == [1, 2, 3, 4, 5]
    assert finance.household_size_for_unit(5) is None
    assert finance.household_size_for_unit(-1) is None


def test_income_tier_edges():
    # 4-person: very low limit 93,050; low 148,850; moderate 166,300
    assert finance.income_tier(90_000, 4, LIMITS) == "very_low"   # the demo family
    assert finance.income_tier(93_050, 4, LIMITS) == "very_low"
    assert finance.income_tier(93_051, 4, LIMITS) == "low"
    assert finance.income_tier(166_300, 4, LIMITS) == "moderate"
    assert finance.income_tier(166_301, 4, LIMITS) == "above_moderate"
    assert finance.income_tier(50_000, 9, LIMITS) is None


def test_cap_very_low_3br():
    # 3BR -> household of 4 -> median 138,600; very low = 30% x 50%
    c = finance.statutory_monthly_cap(90_000, 4, 3, LIMITS)
    assert c["tier"] == "very_low" and c["citation"] == "HSC 50052.5(b)(2)"
    assert c["monthly_cap"] == pytest.approx(1_732.50)


def test_cap_low_3br_up_to_70pct_ami():
    # 4p: low tier starts above 93,050; 70% of 4p median = 97,020. 30% x 70% x 138,600 / 12 = 2,425.50
    c = finance.statutory_monthly_cap(95_000, 4, 3, LIMITS)
    assert c["tier"] == "low" and c["monthly_cap"] == pytest.approx(2_425.50)
    assert c["agency_option_monthly"] is None


def test_cap_low_above_70pct_ami_is_unknown_not_guessed():
    # (b)(3) formula covers incomes "not exceeding 70 percent" of AMI; above it only an optional agency limit
    c = finance.statutory_monthly_cap(120_000, 4, 3, LIMITS)
    assert c["tier"] == "low" and c["monthly_cap"] is None and "funder" in c["reason"]
    assert c["formula_cap_if_applied"] == pytest.approx(2_425.50)
    assert c["agency_option_monthly"] == pytest.approx(0.30 * 120_000 / 12)
    assert finance.statutory_price(120_000, 4, 3, LIMITS, 0.07, 550, 0.011)["price"] is None
    # exactly 70% of AMI: the formula still applies
    assert finance.statutory_monthly_cap(97_020, 4, 3, LIMITS)["monthly_cap"] == pytest.approx(2_425.50)


def test_cap_uses_unit_size_not_family_size():
    # 2BR -> household of 3 -> median 124,750, even for a 4-person family
    c = finance.statutory_monthly_cap(90_000, 4, 2, LIMITS)
    assert c["ami_adjusted_for_unit"] == 124_750
    assert c["monthly_cap"] == pytest.approx(0.15 * 124_750 / 12)


def test_cap_moderate_floor():
    # 35% x 110% x 138,600 / 12 = 4,446.75 ; floor 28% of 160,000 / 12 = 3,733.33
    c = finance.statutory_monthly_cap(160_000, 4, 3, LIMITS)
    assert c["tier"] == "moderate"
    assert c["monthly_cap"] == pytest.approx(4_446.75)
    assert c["monthly_floor"] == pytest.approx(3_733.333, abs=0.01)
    assert c["floor_exceeds_cap"] is False


def test_cap_unknown_cases_return_none():
    assert finance.statutory_monthly_cap(90_000, 4, 6, LIMITS)["monthly_cap"] is None
    r = finance.statutory_monthly_cap(300_000, 4, 3, LIMITS)
    assert r["monthly_cap"] is None and "above the moderate" in r["reason"]


def test_statutory_price_solves_tax_consistently():
    p = finance.statutory_price(90_000, 4, 3, LIMITS, 0.07, monthly_fixed_costs=500,
                                property_tax_rate=0.011, down_payment=10_000)
    total = (finance.payment_from_loan(p["loan"], 0.07) + 500 + 0.011 * p["price"] / 12)
    assert total == pytest.approx(p["monthly_cap"], abs=0.01)
    assert p["price"] == pytest.approx(p["loan"] + 10_000)
    assert p["feasible"] is True


def test_statutory_price_falls_as_rate_rises_and_flags_infeasible():
    lo = finance.statutory_price(90_000, 4, 3, LIMITS, 0.05, 500, 0.011)["price"]
    hi = finance.statutory_price(90_000, 4, 3, LIMITS, 0.08, 500, 0.011)["price"]
    assert hi < lo
    bad = finance.statutory_price(40_000, 1, 0, LIMITS, 0.07, 5_000, 0.011)
    assert bad["feasible"] is False and bad["price"] is None and "cap" in bad["reason"]
