"""Tunable constants for the preference updater (KAN-32, blueprint SS6).

Never hardcode these inline in updater.py -- they live here so the update
rules can be tuned without touching the logic that applies them.
"""
from __future__ import annotations

ALPHA = 0.15
"""swipe_right: learning rate for the positive style vector."""

ALPHA_STRONG = ALPHA * 2
"""save / open: a stronger signal than a plain swipe (AC: alpha x 2)."""

BETA = 0.15
"""swipe_left_style: learning rate for the negative style vector."""

PRICE_DISCOUNT = 0.9
"""swipe_left_price: new max_price_eur = min(current, product_price * PRICE_DISCOUNT)."""
