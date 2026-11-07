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
    """ASSUMED HOUSEHOLD BUDGET: what a family could pay at a chosen share of its own income.

    monthly_other_costs = property tax + insurance + HOA (ASSUMPTION unless sourced).
    This is NOT the legal cap. The statutory benchmark is statutory_price() (HSC 50052.5(b)),
    which uses the size-adjusted area median, not this family's income. Show both, labelled.
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
    """Positive gap = money still missing. Negative = surplus.

    Unknown lines (None) are NOT treated as $0 silently: they are listed in `missing` and
    `complete` is False, so the UI can say the total is incomplete.
    """
    total_cost = sum(v for v in cost_lines.values() if v is not None)
    total_paid = sum(v for v in paid_by.values() if v is not None)
    missing = [k for k, v in {**cost_lines, **paid_by}.items() if v is None]
    return {"total_cost": total_cost, "total_paid": total_paid, "gap": total_cost - total_paid,
            "missing": missing, "complete": not missing}


# --- Statutory affordable housing cost (ownership) -------------------------------------------
# Source: Cal. Health & Safety Code 50052.5(b) and (h), read 2026-11-07 from the FindLaw copy
# ("current as of January 01, 2026"): https://codes.findlaw.com/ca/health-and-safety-code/hsc-sect-50052-5/
# leginfo.legislature.ca.gov blocks bots; confirm against it in a browser.
# "Housing cost" items: 25 CCR 6920 (a)-(g), read 2026-11-07 at
# https://www.law.cornell.edu/regulations/california/25-CCR-6920
# If federal funds (e.g. HOME) are in a deal, 50052.5(h) defers to federal rules: UNKNOWN here.

HSC_50052_5_B = {
    # tier: (share of income, multiple of AMI adjusted for family size appropriate for the unit, cite)
    "extremely_low": (0.30, 0.30, "HSC 50052.5(b)(1)"),
    "very_low": (0.30, 0.50, "HSC 50052.5(b)(2)"),
    "low": (0.30, 0.70, "HSC 50052.5(b)(3)"),
    "moderate": (0.35, 1.10, "HSC 50052.5(b)(4)"),
}
TIER_ORDER = ("extremely_low", "very_low", "low", "moderate")

HOUSING_COST_ITEMS_25_CCR_6920 = {
    "a": "Principal and interest (incl. rehab loans) and loan insurance fees",
    "b": "Property taxes and assessments",
    "c": "Fire and casualty insurance",
    "d": "Property maintenance and repairs",
    "e": "Utilities allowance (not telephone)",
    "f": "Homeowner association fees",
    "g": "Space rent, if on rented land",
}


def household_size_for_unit(bedrooms: int) -> int | None:
    """HSC 50052.5(h): studio = 1 person, 1BR = 2, 2BR = 3, 3BR = 4, 4BR = 5.

    The statute lists units up to four bedrooms; anything else returns None (UNKNOWN).
    """
    if bedrooms is None or bedrooms < 0 or bedrooms > 4:
        return None
    return int(bedrooms) + 1


def income_tier(annual_income: float, household_size: int, limits: dict) -> str | None:
    """Income category from the HCD State Income Limits table for this household size.

    Returns 'extremely_low' | 'very_low' | 'low' | 'moderate' | 'above_moderate', or None when the
    table has no row (or a blank value) for this size. Acutely-low households fall in 'extremely_low'.
    """
    row = limits.get("by_household_size", {}).get(str(household_size))
    if not row:
        return None
    for tier in TIER_ORDER:
        limit = row.get(tier)
        if limit is None:
            return None
        if annual_income <= limit:
            return tier
    return "above_moderate"


def statutory_monthly_cap(annual_income: float, household_size: int, bedrooms: int, limits: dict) -> dict:
    """Max monthly housing cost for an owner household under HSC 50052.5(b).

    cap = share x multiple x (HCD median for the household size appropriate for the unit) / 12.
    Always returns a dict; `monthly_cap` is None (with `reason`) when the law cannot be applied.
    Notes cover the moderate-income floor and the optional agency income-based limits in (b)(3)/(b)(4):
    which one a funder uses is a program choice, UNKNOWN here.
    """
    out = {"tier": None, "unit_household_size": None, "ami_adjusted_for_unit": None, "monthly_cap": None,
           "monthly_floor": None, "floor_exceeds_cap": False, "agency_option_monthly": None,
           "citation": None, "notes": [], "reason": None}
    unit_size = household_size_for_unit(bedrooms)
    if unit_size is None:
        out["reason"] = "Unit size outside HSC 50052.5(h) (studio to 4 bedrooms): UNKNOWN"
        return out
    tier = income_tier(annual_income, household_size, limits)
    out.update(tier=tier, unit_household_size=unit_size)
    if tier is None:
        out["reason"] = "No income-limit row for this household size: UNKNOWN"
        return out
    if tier == "above_moderate":
        out["reason"] = "Income is above the moderate limit: HSC 50052.5(b) caps do not apply"
        return out
    rows = limits["by_household_size"]
    ami_unit = (rows.get(str(unit_size)) or {}).get("median")
    ami_household = (rows.get(str(household_size)) or {}).get("median")
    if ami_unit is None:
        out["reason"] = "No size-adjusted median for this unit size: UNKNOWN"
        return out
    share, multiple, cite = HSC_50052_5_B[tier]
    out.update(ami_adjusted_for_unit=ami_unit, citation=cite,
               monthly_cap=share * multiple * ami_unit / 12)
    if tier == "moderate":
        out["monthly_floor"] = 0.28 * annual_income / 12
        out["floor_exceeds_cap"] = out["monthly_floor"] > out["monthly_cap"]
        out["notes"].append("(b)(4): cost shall not be less than 28% of gross income")
        if ami_household and annual_income > 1.10 * ami_household:
            out["agency_option_monthly"] = 0.35 * annual_income / 12
            out["notes"].append("(b)(4): income above 110% of AMI; a funding agency MAY instead require "
                                "cost not exceed 35% of gross income")
    if tier == "low" and ami_household and annual_income >= 0.70 * ami_household:
        out["agency_option_monthly"] = 0.30 * annual_income / 12
        out["notes"].append("(b)(3): income at or above 70% of AMI; a funding agency MAY instead require "
                            "cost not exceed 30% of gross income")
    return out


def statutory_price(
    annual_income: float,
    household_size: int,
    bedrooms: int,
    limits: dict,
    annual_rate: float,
    monthly_fixed_costs: float,
    property_tax_rate: float,
    down_payment: float = 0.0,
    years: int = 30,
) -> dict:
    """Highest home price whose 25 CCR 6920 housing cost fits the HSC 50052.5(b) cap.

    monthly_fixed_costs = insurance + maintenance + utilities allowance + HOA + loan insurance + space
    rent (25 CCR 6920 (a),(c)-(g); ASSUMPTION unless sourced). Property tax (6920(b)) depends on the price,
    so it is solved together: cap = P&I(loan) + fixed + tax_rate x (loan + down) / 12.
    This is a statutory housing-cost BENCHMARK, not a mortgage qualification.
    """
    c = statutory_monthly_cap(annual_income, household_size, bedrooms, limits)
    out = {**c, "monthly_fixed_costs": monthly_fixed_costs, "monthly_property_tax": None,
           "monthly_for_loan": None, "loan": None, "price": None, "feasible": None}
    if c["monthly_cap"] is None:
        return out
    k = loan_from_payment(1.0, annual_rate, years)  # loan supported per $1/month of P&I
    t = property_tax_rate / 12
    available = c["monthly_cap"] - monthly_fixed_costs - t * down_payment
    loan = max(k * available / (1 + k * t), 0.0)
    price = loan + down_payment
    tax = t * price
    out.update(loan=loan, price=price, monthly_property_tax=tax,
               monthly_for_loan=c["monthly_cap"] - monthly_fixed_costs - tax,
               feasible=available > 0)
    return out


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
    """Homeowner mode: does a backyard home pay for itself?

    `grants` should be money actually awarded; unconfirmed programs belong at $0.
    `assistance_exceeds_cost` flags cash + grants above the build cost (nothing to finance; check inputs).
    """
    financed = max(build_cost - cash_in - grants, 0.0)
    assistance_exceeds_cost = (cash_in + grants) > build_cost
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
        "assistance_exceeds_cost": assistance_exceeds_cost,
    }


def adu_build_cost(sqft: float, cost_per_sqft: float) -> float:
    """Hard-cost estimate: size x cost per sq ft (cost_per_sqft is an ASSUMPTION; see assumptions.json)."""
    if sqft is None or cost_per_sqft is None or sqft <= 0 or cost_per_sqft <= 0:
        return 0.0
    return sqft * cost_per_sqft


def adu_rate_sensitivity(build_cost: float, monthly_rent: float, rates: list[float], **kw) -> list[dict]:
    """Cash flow at several loan rates (same inputs as adu_cashflow)."""
    return [{"rate": r, **adu_cashflow(build_cost, monthly_rent, r, **kw)} for r in rates]
