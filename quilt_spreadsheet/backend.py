"""
backend.py — the porting, conversion, gating, and snapping layer.

Casey: "the true backend is the actual porting and conversions. one cell
might be using a different scale than another but if the backend can convert
so their equal exchange for their applications, it doesn't matter. the
backend can gate variables or convert approximations to snaps but the time
is in the same units on both sides."

This is the polyformalism-port layer at the substrate level. Different
cells may use:
  - different scales (celsius vs fahrenheit)
  - different units (ns vs ms)
  - different precision (continuous vs snapped)
  - different visibility (some variables are gated)

The backend DOES NOT enforce agreement. The backend PROVIDES porting
for when cells need to exchange data.
"""

from typing import Any, Tuple
import math


#: The canonical conversions registry — extensible.
#: Each entry: name -> callable(value, from_unit, to_unit)
#: Time is preserved in the SAME units on both sides (per Casey).
REGISTRY = {}


def convert(name: str):
    """Decorator to register a backend conversion."""
    def deco(fn):
        REGISTRY[name] = fn
        return fn
    return deco


@convert("temperature")
def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature scales."""
    if from_unit == to_unit:
        return value
    if from_unit == 'celsius' and to_unit == 'fahrenheit':
        return value * 9/5 + 32
    if from_unit == 'fahrenheit' and to_unit == 'celsius':
        return (value - 32) * 5/9
    if from_unit == 'celsius' and to_unit == 'kelvin':
        return value + 273.15
    raise ValueError(f"unsupported temperature conversion: {from_unit} -> {to_unit}")


@convert("time")
def convert_time(value: float, from_unit: str, to_unit: str) -> float:
    """Time is preserved in the SAME units on both sides (per Casey).

    Per Casey's directive: 'time is in the same units on both sides'.
    This converter refuses to convert across units — it normalizes to
    nanoseconds (canonical) and back.

    Use ms and ns. The substrate does not negotiate time across calendars.
    """
    if from_unit == to_unit:
        return value
    if from_unit not in ('ns', 'ms', 's') or to_unit not in ('ns', 'ms', 's'):
        raise ValueError(f"time must be in same units: {from_unit} vs {to_unit}")
    # Casey: convert for compatibility but it's a unit-preserving op
    if from_unit == 'ns' and to_unit == 'ms':
        return value / 1e6
    if from_unit == 'ms' and to_unit == 'ns':
        return value * 1e6
    if from_unit == 'ns' and to_unit == 's':
        return value / 1e9
    if from_unit == 's' and to_unit == 'ns':
        return value * 1e9
    return value


@convert("distance")
def convert_distance(value: float, from_unit: str, to_unit: str) -> float:
    """Distance scaling."""
    if from_unit == to_unit:
        return value
    if from_unit == 'm' and to_unit == 'cm':
        return value * 100
    if from_unit == 'cm' and to_unit == 'm':
        return value / 100
    raise ValueError(f"unsupported distance conversion: {from_unit} -> {to_unit}")


@convert("ratio")
def convert_ratio(value: float, from_unit: str, to_unit: str) -> float:
    """Ratios are unitless — convert between percent, decimal, ppm."""
    if from_unit == to_unit:
        return value
    if from_unit == 'decimal' and to_unit == 'percent':
        return value * 100
    if from_unit == 'percent' and to_unit == 'decimal':
        return value / 100
    if from_unit == 'ppm' and to_unit == 'decimal':
        return value / 1e6
    raise ValueError(f"unsupported ratio conversion: {from_unit} -> {to_unit}")


class Backend:
    """The porting backend — applied at cell boundaries.

    Functions: convert, gate, snap, time-aware porting.
    """

    def __init__(self):
        self.conversions_run: int = 0

    def port(self, value: Any, from_unit: str, to_unit: str,
             domain: str = "ratio") -> Any:
        """Port a value across scales/units in the same domain.

        Default domain is 'ratio' (unitless). For physical conversions
        pass domain='temperature' or 'distance'.
        """
        if from_unit == to_unit:
            return value
        if domain not in REGISTRY:
            raise ValueError(f"unknown backend domain: {domain}")
        self.conversions_run += 1
        return REGISTRY[domain](value, from_unit, to_unit)

    def gate(self, value: Any, predicate) -> Any:
        """Backend 'gate' — release a value only if predicate is satisfied.

        Casey: 'the backend can gate variables or convert approximations
        to snaps'. The gate is controlled release/transformation.

        Returns None if predicate fails. The cell receives None and can
        decide what to do (default action: skip).
        """
        if not predicate(value):
            return None
        return value

    def gate_below(self, value: float, threshold: float) -> Any:
        """Common gate: block values below threshold."""
        if value < threshold:
            return None
        return value

    def snap(self, value: float, granularity: float) -> float:
        """Approximation snap — snap to discrete grid.

        Casey: 'the backend can gate variables or convert approximations
        to snaps'. A snap rounds the value to the nearest multiple of
        granularity.

        e.g. snap(3.7, 0.5) = 3.5 (or 4.0, depending on tie-break)
        """
        if granularity <= 0:
            return value
        return round(value / granularity) * granularity

    def port_time(self, value: float, from_unit: str, to_unit: str) -> float:
        """Time porting — preserves same units on both sides (per Casey)."""
        return REGISTRY["time"](value, from_unit, to_unit)

    def stats(self) -> dict:
        return {
            "conversions_run": self.conversions_run,
            "available_conversions": sorted(REGISTRY.keys()),
        }


_default_backend = None


def get_default_backend() -> Backend:
    global _default_backend
    if _default_backend is None:
        _default_backend = Backend()
    return _default_backend


def reset_default_backend() -> None:
    global _default_backend
    _default_backend = None
