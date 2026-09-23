"""
demo_clock_skew.py — demonstrate clock skew tolerance.

Casey: "even if their clocks don't agree, the time between events
extrapolates the agreement with more and more confidence the longer
they are in sync."

This demo shows:
  - Two cells with clocks that disagree
  - They share many events
  - The pairwise confidence RISES the longer they share
  - The time-between-events is what carries info, not the absolute clock
"""

import sys
sys.path.insert(0, '.')
import time

from quilt_spreadsheet.clock import DistributedClock, CellClock, get_default_clock


def main():
    clock = get_default_clock()

    print("=" * 60)
    print("CLOCK SKEW TOLERANCE — distributed clocks, time-between-events")
    print("=" * 60)
    print()
    print("Cell A and Cell B share 10 events in a row.")
    print("Each shared event raises the pairwise confidence.")
    print()
    a = (0, 0)
    b = (0, 1)
    confidences = []
    for i in range(10):
        clock.tick(a)
        clock.tick(b)
        clock.track_pair_sync(a, b)
        conf = clock.pair_confidence(a, b)
        confidences.append(conf)
        # Time between events
        local_a = clock.cell_local_time(a)
        local_b = clock.cell_local_time(b)
        skew = clock.skew_estimate(a, b)
        print(f"  event {i+1}: confidence={conf:.4f}  "
              f"local_a={local_a}ns  local_b={local_b}ns  skew={skew:+d}ns")

    print()
    print("=" * 60)
    print("THE OBSERVATION")
    print("=" * 60)
    print()
    print(f"  Initial confidence: {confidences[0]:.4f}")
    print(f"  Final confidence:   {confidences[-1]:.4f}")
    print()
    print("Confidence asymptotes toward 1.0 — it never quite reaches 1.")
    print("The probability that two cells remain in sync forever is < 1.")
    print("But over many events, the time-between-events IS trustworthy.")
    print()
    print("The substrate does NOT require clocks to be in sync.")
    print("It REQUIRES that the time between events be measurable.")
    print("Long sync history → high confidence in the inter-event measurement.")
    print()
    print("This is how casey's 'the longer they are in sync' becomes")
    print("an empirical curve, not a metaphysical guarantee.")


if __name__ == "__main__":
    main()
