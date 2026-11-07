"""The $0 equation: family share + subsidies + fundraising (+ earned income) - cost to create = 0.

OWNER: Builder C (Money). Pure functions only, no Streamlit here, so tests stay fast.
Every default comes from data/processed/assumptions.json and is labelled ASSUMPTION there.
"""
from __future__ import annotations


def monthly_payment_cap(annual_income: float, housing_share: float) -> float:
    """Max monthly housing cost. housing_share is ~0.30-0.35 per the lane brief (ASSUMPTION)."""
    return annual_income * housing_share / 12


def loan_from_payment(monthly_payment: float, annual_rate: float, years: int = 30) -> float:
    """Largest principal a fixed monthly payment supports."""
    n = years * 12
    if monthly_payment <= 0:
        return 0.0
    r = annual_rate / 12
    if r == 0:
        return monthly_payment * n
    return monthly_payment * (1 - (1 + r) ** -n) / r


def payment_from_loan(principal: float, annual_rate: float, years: int = 30) -> float:
    n = years * 12
    r = annual_rate / 12
    if principal <= 0:
        return 0.0
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)


def family_price(
    annual_income: float,
    annual_rate: float,
    housing_share: float,
    monthly_other_costs: float,
    down_payment: float = 0.0,
    years: int = 30,
) -> dict:
    """What a family can pay for a home, from income.

    monthly_other_costs = property tax + insurance + HOA (ASSUMPTION unless sourced).
    NOTE: Health & Safety Code 50052.5 defines the legal affordable-cost cap; this simple
    share-of-income version is a stand-in until someone reads and codes the statute.
    """
    cap = monthly_payment_cap(annual_income, housing_share)
    for_loan = max(cap - monthly_other_costs, 0.0)
    loan = loan_from_payment(for_loan, annual_rate, years)
    return {
        "monthly_cap": cap,
        "monthly_for_loan": for_loan,
        "loan": loan,
        "price": loan + down_payment,
    }


def gap(cost_lines: dict[str, float], paid_by: dict[str, float]) -> dict:
    """Positive gap = money still missing. Negative = surplus."""
    total_cost = sum(v for v in cost_lines.values() if v is not None)
    total_paid = sum(v for v in paid_by.values() if v is not None)
    return {"total_cost": total_cost, "total_paid": total_paid, "gap": total_cost - total_paid}


def rate_sensitivity(
    annual_income: float,
    rates: list[float],
    housing_share: float,
    monthly_other_costs: float,
    total_cost: float,
    other_sources: float,
    years: int = 30,
) -> list[dict]:
    """Scenario M02: how the gap moves when the rate moves."""
    rows = []
    for rate in rates:
        fp = family_price(annual_income, rate, housing_share, monthly_other_costs, years=years)
        rows.append({
            "rate": rate,
            "family_price": fp["price"],
            "gap": total_cost - fp["price"] - other_sources,
        })
    return rows


def families_per_million(gap_per_home: float) -> float | None:
    """Impact ROI for funders: homes closed per $1M of gap funding."""
    if gap_per_home is None or gap_per_home <= 0:
        return None
    return 1_000_000 / gap_per_home


def gift_coverage(gift: float, cost_lines: dict[str, float]) -> list[dict]:
    """Scenario M03: map a donor's gift onto the one-home bill, largest line first."""
    out, left = [], gift
    for name, value in sorted(cost_lines.items(), key=lambda kv: -(kv[1] or 0)):
        if left <= 0 or not value:
            continue
        covered = min(left, value)
        out.append({"line": name, "covered": covered, "share_of_line": covered / value})
        left -= covered
    return out


def adu_cashflow(
    build_cost: float,
    monthly_rent: float,
    loan_rate: float,
    cash_in: float = 0.0,
    years: int = 30,
    vacancy_and_expense_share: float = 0.25,
    grants: float = 0.0,
) -> dict:
    """Homeowner mode: does a backyard home pay for itself?"""
    financed = max(build_cost - cash_in - grants, 0.0)
    pmt = payment_from_loan(financed, loan_rate, years)
    net_rent = monthly_rent * (1 - vacancy_and_expense_share)
    net_monthly = net_rent - pmt
    out_of_pocket = cash_in
    payback_years = (out_of_pocket / (net_monthly * 12)) if net_monthly > 0 and out_of_pocket > 0 else None
    simple_payback = (build_cost - grants) / (net_rent * 12) if net_rent > 0 else None
    return {
        "financed": financed,
        "monthly_loan_payment": pmt,
        "net_rent": net_rent,
        "net_monthly": net_monthly,
        "cash_payback_years": payback_years,
        "simple_payback_years": simple_payback,
    }
