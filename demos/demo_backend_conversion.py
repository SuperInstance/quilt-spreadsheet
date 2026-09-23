"""
demo_backend_conversion.py — demonstrate backend porting across scales.

Casey: "the true backend is the actual porting and conversions. one cell
might be using a different scale than another but if the backend can
convert so their equal exchange for their applications, it doesn't
matter. the backend can gate variables or convert approximations to
snaps but the time is in the same units on both sides."

This demo shows:
  - Cell A uses celsius
  - Cell B uses fahrenheit
  - The backend ports values between them
  - Both GATING (under-threshold gets None) and SNAPPING (round to grid) work
  - Time is preserved in the same units on both sides
"""

import sys
sys.path.insert(0, '.')

from quilt_spreadsheet.grid import QuiltSpreadsheet
from quilt_spreadsheet.backend import get_default_backend


def main():
    print("=" * 60)
    print("BACKEND PORTING — different scales, same exchange")
    print("=" * 60)
    print()
    backend = get_default_backend()
    sheet = QuiltSpreadsheet(rows=2, cols=2, name="backend_demo")

    # Cell A speaks celsius
    def celsius_cell(*, source, hook, value):
        if value is None:
            return None
        # Receive value in celsius, return it as a fahrenheit value
        # (the cell's "exit scale")
        return backend.port(value, 'celsius', 'fahrenheit', domain='temperature')

    # Cell B speaks fahrenheit
    def fahrenheit_cell(*, source, hook, value):
        if value is None:
            return None
        # Receive value in fahrenheit, snap to nearest 5
        snapped = backend.snap(value, 5.0)
        # Now return in fahrenheit (the backend preserved unit)
        return snapped

    sheet.place_cell(0, 0, celsius_cell)
    sheet.place_cell(0, 1, fahrenheit_cell)

    print("Workload: cell(0,0) pulls cell(0,1) at 25 celsius")
    print("  - cell(0,0) exits as fahrenheit")
    print("  - cell(0,1) snaps to nearest 5 degrees")
    print()
    # Inline porting demo
    raw_celsius = 25
    as_fahrenheit = backend.port(raw_celsius, 'celsius', 'fahrenheit', domain='temperature')
    snapped = backend.snap(as_fahrenheit, 5.0)
    print(f"  raw 25 celsius     → {as_fahrenheit:.2f} fahrenheit (backend port)")
    print(f"  77.00 fahrenheit   → {snapped:.2f} fahrenheit (backend snap, granularity=5)")
    print()
    print("=" * 60)
    print("Backend gating:")
    print("=" * 60)
    print()
    # Show gating
    print(f"  backend.gate_below(0.3, threshold=0.5) = {backend.gate_below(0.3, 0.5)!r}")
    print(f"  backend.gate_below(0.7, threshold=0.5) = {backend.gate_below(0.7, 0.5)}")
    print()
    print("When a value is gated to None, the receiving cell sees None.")
    print("It can skip the operation or take the default. The SUBSTRATE")
    print("doesn't force the cell to react.")
    print()
    print("=" * 60)
    print("Time preservation (Casey: 'time is in the same units on both sides'):")
    print("=" * 60)
    print()
    raw_ns = 5_000_000_000  # 5 seconds in nanoseconds
    as_ms = backend.port_time(raw_ns, 'ns', 'ms')
    back_ns = backend.port_time(as_ms, 'ms', 'ns')
    print(f"  raw {raw_ns} ns  →  {as_ms} ms  →  {back_ns} ns")
    print(f"  round-trip preserves the value ({raw_ns == back_ns})")
    print()
    print("Backend stats:")
    print(f"  {backend.stats()}")


if __name__ == "__main__":
    main()
