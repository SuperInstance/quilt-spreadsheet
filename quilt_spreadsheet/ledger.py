"""
ledger.py — double-entry bookkeeping for spreadsheet pull/push pairs.

Casey: "there's a double-entry book keeping that for every pull is a push
somewhere else that simply needs an agreement and timestamp."

This is the SUBSTRATE-level ledger. Every pull from cell A to cell B is
recorded ONCE as a pair: a 'pull' entry in A's view, a 'push' entry in
B's view. Both share the SAME (source, target, hook, timestamp). The
agreement criterion: any matching pair (a, b) that matches (a, b, hook, ts)
is a successful ledger entry.

If there is a pull without a matching push, the ledger reports an
unbalanced entry (the substrate's "alert"). This is the substrate's
audit trail — the witness log at the spreadsheet level.
"""

from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Optional, Any
import time
import uuid


@dataclass(frozen=True)
class LedgerEntry:
    """A single ledger entry.

    A pull is one entry. A push that responds to a pull is another entry.
    Both share the same pair_id — that's the agreement.
    """
    pair_id: str       # UUID linking pull + push
    source: Tuple[int, int]   # cell rank
    target: Tuple[int, int]   # cell rank
    direction: str     # 'pull' or 'push'
    hook: str          # the hook name (the "what" of the request)
    value: Any         # the value being transferred
    timestamp_ns: int  # monotonic clock at the moment of recording
    seen_by: List[Tuple[int, int]] = field(default_factory=list)  # which cells' clocks recorded this


class Ledger:
    """The double-entry ledger.

    Every pull/push pair is recorded as TWO entries with the same pair_id.
    The ledger can verify that every pull has a matching push by walking
    all entries grouped by pair_id.
    """

    def __init__(self):
        self._entries: List[LedgerEntry] = []
        self._pair_count: int = 0

    def record_pull(
        self,
        source: Tuple[int, int],
        target: Tuple[int, int],
        hook: str,
        value: Any,
        timestamp_ns: int,
    ) -> LedgerEntry:
        """Record a 'pull' — a request from source to target."""
        pair_id = str(uuid.uuid4())
        entry = LedgerEntry(
            pair_id=pair_id,
            source=source,
            target=target,
            direction='pull',
            hook=hook,
            value=value,
            timestamp_ns=timestamp_ns,
            seen_by=[source],
        )
        self._entries.append(entry)
        return entry

    def record_push(
        self,
        source: Tuple[int, int],
        target: Tuple[int, int],
        hook: str,
        value: Any,
        timestamp_ns: int,
        pair_id: str,
    ) -> Optional[LedgerEntry]:
        """Record the matched 'push' response for a prior pull.

        The pair_id MUST match the pull's pair_id. If no pull exists yet,
        return None (the push without a pull is a substrate violation).
        """
        # Verify the pull exists
        pull = self._find_pull(pair_id)
        if pull is None:
            return None  # push without a pull — substrate violation
        entry = LedgerEntry(
            pair_id=pair_id,
            source=source,
            target=target,
            direction='push',
            hook=hook,
            value=value,
            timestamp_ns=timestamp_ns,
            seen_by=[source, target],
        )
        self._entries.append(entry)
        self._pair_count += 1
        return entry

    def _find_pull(self, pair_id: str) -> Optional[LedgerEntry]:
        for e in self._entries:
            if e.pair_id == pair_id and e.direction == 'pull':
                return e
        return None

    @property
    def total_pulls(self) -> int:
        return sum(1 for e in self._entries if e.direction == 'pull')

    @property
    def total_pushes(self) -> int:
        return sum(1 for e in self._entries if e.direction == 'push')

    @property
    def total_pairs(self) -> int:
        return self._pair_count

    @property
    def unbalanced(self) -> List[LedgerEntry]:
        """All pulls that don't have a matching push."""
        paired_pull_ids = {
            e.pair_id for e in self._entries if e.direction == 'push'
        }
        return [
            e for e in self._entries
            if e.direction == 'pull' and e.pair_id not in paired_pull_ids
        ]

    def all_entries(self) -> List[LedgerEntry]:
        return list(self._entries)

    def summary(self) -> dict:
        return {
            "total_entries": len(self._entries),
            "pulls": self.total_pulls,
            "pushes": self.total_pushes,
            "pairs": self.total_pairs,
            "unbalanced_pulls": len(self.unbalanced),
        }


# Module-level singleton
_default_ledger = None


def get_default_ledger() -> Ledger:
    global _default_ledger
    if _default_ledger is None:
        _default_ledger = Ledger()
    return _default_ledger


def reset_default_ledger() -> None:
    global _default_ledger
    _default_ledger = None
