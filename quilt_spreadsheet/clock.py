"""
clock.py — distributed clocks with skew tolerance.

Each cell has its own clock. Clocks may disagree. The substrate does NOT
require clocks to agree. The substrate DOES require that the time between
events be measurable.

Casey: "even if their clocks don't agree, the time between events extrapolates
the agreement with more and more confidence the longer they are in sync."

This is the load-bearing insight: clock synchronization is EMERGENT, not
required. Each cell's clock is private. The substrate walker tracks:
  - event timestamps (relative to the cell's t0)
  - delta between events (the time between events)
  - confidence score (rises the longer two cells have shared events)
"""

import time
from typing import Dict, Tuple, Optional


class CellClock:
    """A single cell's clock. Starts at cell's birth (t0)."""

    __slots__ = ('t0', 'last_event_ns', 'event_count')

    def __init__(self):
        self.t0: Optional[int] = None
        self.last_event_ns: Optional[int] = None
        self.event_count: int = 0

    def tick(self) -> int:
        """Advance the clock. Returns the cell-local time in nanoseconds."""
        if self.t0 is None:
            self.t0 = time.monotonic_ns()
        now = time.monotonic_ns()
        self.last_event_ns = now
        self.event_count += 1
        return now - self.t0


class DistributedClock:
    """A coordinator of cell clocks. Skew is allowed. Convergence is emergent."""

    def __init__(self):
        self._clocks: Dict[Tuple[int, int], CellClock] = {}
        # Pairwise confidence: tracks how long two cells have been in sync
        # {(a, b): confidence_score}, where confidence rises the longer
        # the pair has shared events.
        self._pairwise_time: Dict[Tuple, int] = {}
        self._pairwise_event_count: Dict[Tuple, int] = {}

    def tick(self, cell_rank: Tuple[int, int]) -> int:
        """Tick the named cell's clock. Returns cell-local time in ns."""
        if cell_rank not in self._clocks:
            self._clocks[cell_rank] = CellClock()
        return self._clocks[cell_rank].tick()

    def cell_local_time(self, cell_rank: Tuple[int, int]) -> int:
        """Read the cell-local time without ticking."""
        clk = self._clocks.get(cell_rank)
        if clk is None or clk.t0 is None:
            return 0
        return time.monotonic_ns() - clk.t0

    def time_between_events(self, ts_a: int, ts_b: int) -> int:
        """The time between two events.

        Casey: "the time between events extrapolates the agreement"
        The DELTA is the substrate's measurement. Clocks can disagree
        about absolute time; they cannot disagree about deltas (if events
        are time-stamped close enough).

        Returns absolute value so order doesn't matter.
        """
        return abs(ts_b - ts_a)

    def track_pair_sync(self, cell_a: Tuple[int, int], cell_b: Tuple[int, int]) -> None:
        """Record that two cells have shared another event.

        Every shared event raises the pairwise confidence. The longer
        cells are in sync, the more confident we are that time-between-
        events extrapolates.
        """
        key = tuple(sorted((cell_a, cell_b)))
        self._pairwise_time[key] = self._pairwise_time.get(key, 0) + 1
        self._pairwise_event_count[key] = self._pairwise_event_count.get(key, 0) + 1

    def pair_confidence(self, cell_a: Tuple[int, int], cell_b: Tuple[int, int]) -> float:
        """Confidence score for the time-between-events agreement.

        Confidence rises as the number of shared events rises.
        Capped at [0, 1].
        """
        key = tuple(sorted((cell_a, cell_b)))
        count = self._pairwise_event_count.get(key, 0)
        # asymptotic: confidence = 1 - 1/(count+1)
        if count == 0:
            return 0.0
        return min(1.0, 1.0 - 1.0 / (count + 1))

    def skew_estimate(self, cell_a: Tuple[int, int], cell_b: Tuple[int, int]) -> int:
        """Estimate the clock skew between two cells.

        Skew is computed by averaging per-event deltas — but we're clocking
        each cell independently, so skew emerges as the difference in
        'cell-local time' at the same wall moment.

        Returns estimated skew in nanoseconds. Positive = B's clock is ahead.
        """
        local_a = self.cell_local_time(cell_a)
        local_b = self.cell_local_time(cell_b)
        return local_b - local_a


# A module-level singleton — the substrate uses one clock
_default_clock = None


def get_default_clock() -> DistributedClock:
    global _default_clock
    if _default_clock is None:
        _default_clock = DistributedClock()
    return _default_clock


def reset_default_clock() -> None:
    """Reset for testing."""
    global _default_clock
    _default_clock = None
