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
