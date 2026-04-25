"""
Antifragile Discipline Tests — derived from specification.md.

These tests enforce that a Position formed from user-entered legs respects
the six antifragile design rules.  They are intentionally written against
an API that does not yet exist (Red phase of TDD).
"""

import pytest
from src.position_builder import Contract, Position, ShortPut, LongPut, ShortCall, LongCall


# ---------------------------------------------------------------------------
# Helper factories — keep test data simple and explicit
# ---------------------------------------------------------------------------

def _contract(strike, premium, volume=1):
    return Contract(strike=strike, unit_premium=premium, expiration="2026-05-01", volume=volume)


# ===========================================================================
# Test 1 — Positive Expected Value (概率 × 收益 的积分 > 0)
# ===========================================================================

# def test_position_must_have_positive_expected_value():
#     """
#     Rule 1 from spec: 组合是不是正期望(不是概率，是概率和收益损失的乘积)

#     A disciplined antifragile position must have mathematically positive
#     expected P&L when integrated over a reasonable price distribution.
#     """
#     # Arrange — a small long-put skew / convexity harvest structure
#     legs = [
#         LongPut(_contract(strike=90, premium=2.0, volume=1)),
#         ShortPut(_contract(strike=61, premium=204, volume=1)),
#         ShortPut(_contract(strike=62, premium=251, volume=1)),
#     ]
#     position = Position(legs=legs)
#     price_distribution = {80: 0.10, 90: 0.20, 100: 0.40, 110: 0.20, 120: 0.10}

#     # Act
#     ev = position.expected_value(price_distribution)

#     # Assert
#     assert ev > 0, f"Expected value {ev} must be positive for antifragile discipline"


