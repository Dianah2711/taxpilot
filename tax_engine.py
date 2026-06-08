"""
tax_engine.py
Pure, deterministic Malaysian resident-individual tax engine.
No AI in the maths. Figures verified against LHDN / PwC for YA 2024 & YA 2025
(rates unchanged YA 2024 -> YA 2025).

Source of truth:
  - PIT bands: ITA 1967 Part II, Schedule 1 (YA 2024 onwards)
  - Reliefs:   ITA 1967 ss. 46-49, with Budget 2025 amendments
"""

# (upper_bound_of_band, marginal_rate, cumulative_tax_at_lower_bound)
TAX_BANDS = [
    (5_000,      0.00, 0),
    (20_000,     0.01, 0),
    (35_000,     0.03, 150),
    (50_000,     0.06, 600),
    (70_000,     0.11, 1_500),
    (100_000,    0.19, 3_700),
    (400_000,    0.25, 9_400),
    (600_000,    0.26, 84_400),
    (2_000_000,  0.28, 136_400),
    (float("inf"), 0.30, 528_400),
]


def compute_tax(chargeable: float) -> float:
    """Progressive tax on chargeable income (resident individual)."""
    if chargeable <= 0:
        return 0.0
    prev = 0
    for upto, rate, cum_below in TAX_BANDS:
        if chargeable <= upto:
            return round(cum_below + (chargeable - prev) * rate, 2)
        prev = upto
    return 0.0


def marginal_rate(chargeable: float) -> float:
    """Marginal rate that applies to the next ringgit of chargeable income."""
    prev = 0
    for upto, rate, _ in TAX_BANDS:
        if chargeable <= upto:
            return rate
        prev = upto
    return 0.30


if __name__ == "__main__":
    # quick sanity checks against the published band boundaries
    assert compute_tax(5_000) == 0
    assert compute_tax(50_000) == 1_500
    assert compute_tax(70_000) == 3_700
    assert compute_tax(100_000) == 9_400
    assert compute_tax(400_000) == 84_400
    print("tax_engine: band checks OK")
