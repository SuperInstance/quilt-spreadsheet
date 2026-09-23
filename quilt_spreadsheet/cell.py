"""
cell.py — the SheetCell.

A SheetCell is:
  - Addressable by (row, col)
  - Has a program (a Python callable — "a python program might sit in a cell
    as a shell command ready to run")
  - Has DNA (alignment seed)
  - Has hooks to other cells (pull/push wake-up)
  - Has its own color/label namespace
  - Has its own perception (sorts the spreadsheet around it)

Casey: "there's no central program within the cell's instance, it's just
a program running so if [pulls happen], it runs."

The cell has NO main(). The cell's program runs ONLY when it is woken
(by pull or by push). The cell's program has the signature:
    program(*, source, hook, value) -> response_value
"""

from typing import Tuple, Optional, Callable, Dict, Any, List
import uuid

from .color import ColorNamespace
from .perception import Perception
from .clock import get_default_clock
from .ledger import get_default_ledger
from .backend import get_default_backend


#: The 5 bedrock doctrine axioms (substrate walker canon line)
DOCTRINE_AXIOMS = frozenset({
    'cells_are_scars',
    'witness_log_is_prediction',
    'oracle_is_heard',
    'canon_gate_is_chord',
    'substrate_quantum',
})

#: The action axioms — what a cell CAN do
ACTION_AXIOMS = frozenset({
    'pull',        # pull from another cell
    'push',        # push to another cell
    'witness',     # record to the witness log
    'perceive',    # sort the spreadsheet around it
    'label',       # assign a color label
    'convert',     # port values through backend
    'snap',        # approximate-snap values
})


class SheetCell:
    """A cell in the Quilt spreadsheet substrate.

    No main(). The cell RUNS when pulled. The cell RESPONDS when pushed.
    Between events, the cell is dormant.
    """

    NUM_DIALS = 16

    __slots__ = (
        'row', 'col', 'rank', 'program', 'axioms',
        'dials', 'color', 'perception', 'witness_log',
        'pulls', 'pushes', 'hooks_named',
        'awake_count', 'last_event_ns',
    )

    def __init__(
        self,
        row: int,
        col: int,
        program: Callable,
        axioms: Optional[frozenset] = None,
    ):
        if not callable(program):
            raise TypeError(f"program must be callable, got {type(program)}")
        if axioms is None:
            axioms = frozenset(DOCTRINE_AXIOMS | ACTION_AXIOMS)
        self.row = row
        self.col = col
        self.rank: Tuple[int, int] = (row, col)
        self.program = program
        self.axioms = axioms
        self.dials = [0.0] * self.NUM_DIALS
        self.color = ColorNamespace(self.rank)
        self.perception = Perception(self.rank)
        self.witness_log: List[dict] = []
        self.pulls: Dict[Tuple[int, int], List[str]] = {}  # source -> [hooks]
        self.pushes: Dict[Tuple[int, int], List[str]] = {}  # target -> [hooks]
        self.hooks_named: Dict[str, Any] = {}  # named hooks -> last known values
        self.awake_count: int = 0
        self.last_event_ns: int = 0

    def permits(self, action: str) -> bool:
        return action in self.axioms

    def label(self, label: str, canonical_value: Any) -> None:
        """Assign a private color label to a canonical state."""
        if not self.permits('label'):
            return
        self.color.assign(label, canonical_value)

    def ingest_observation(self, item: dict) -> None:
        """Add a raw observation to this cell's perception."""
        if not self.permits('perceive'):
            return
        self.perception.ingest([item])

    def on_pull(
        self,
        source: Tuple[int, int],
        hook: str,
        value: Any = None,
        timestamp_ns: int = 0,
    ) -> dict:
        """Wake the cell — a pull came in.

        The cell RUNS its program with the pull as input.
        Returns the cell's response (the push).
        """
        clock = get_default_clock()
        ledger = get_default_ledger()
        ts = clock.tick(self.rank)
        if timestamp_ns == 0:
            timestamp_ns = ts
        # Record the pull on the ledger
        pull_entry = ledger.record_pull(
            source=source,
            target=self.rank,
            hook=hook,
            value=value,
            timestamp_ns=timestamp_ns,
        )
        # Run the program (the cell has no main — it runs here)
        try:
            if not self.permits('witness'):
                response = None
            else:
                response = self.program(
                    source=source,
                    hook=hook,
                    value=value,
                )
        except Exception as e:
            response = {"_error": str(e), "_hook": hook, "_source": source}
        # Record the witness
        self.witness_log.append({
            'event': 'pull',
            'source': source,
            'hook': hook,
            'value': value,
            'response': response,
            'timestamp_ns': timestamp_ns,
        })
        self.awake_count += 1
        self.last_event_ns = timestamp_ns
        # Track pair sync between cells
        clock.track_pair_sync(source, self.rank)
        # Record push on ledger (paired with the pull)
        if response is not None:
            ledger.record_push(
                source=self.rank,
                target=source,
                hook=hook,
                value=response,
                timestamp_ns=ts,
                pair_id=pull_entry.pair_id,
            )
            self.pushes.setdefault(source, []).append(hook)
        if source not in self.pulls:
            self.pulls[source] = []
        self.pulls[source].append(hook)
        return {
            'response': response,
            'pair_id': pull_entry.pair_id,
            'timestamp_ns': ts,
            'cell': self.rank,
        }

    def pull_from(
        self,
        target: Tuple[int, int],
        hook: str,
        value: Any = None,
    ) -> dict:
        """Pull from another cell. The target wakes up via on_pull."""
        clock = get_default_clock()
        ts = clock.tick(self.rank)
        # Find the target
        target_cell = _find_cell_global(target)
        if target_cell is None:
            return {'error': 'target cell not found', 'target': target}
        # Wake the target
        result = target_cell.on_pull(
            source=self.rank,
            hook=hook,
            value=value,
            timestamp_ns=ts,
        )
        # Track sync
        clock.track_pair_sync(self.rank, target)
        return result

    def __repr__(self):
        awake = 'awake' if self.awake_count > 0 else 'dormant'
        return (f"SheetCell(rank={self.rank}, axioms={len(self.axioms)}, "
                f"awake={self.awake_count}, status={awake})")


# A module-level cell registry for the spreadsheet substrate
_cell_registry: Dict[Tuple[int, int], SheetCell] = {}


def register_cell(cell: SheetCell) -> None:
    _cell_registry[cell.rank] = cell


def _find_cell_global(rank: Tuple[int, int]) -> Optional[SheetCell]:
    return _cell_registry.get(rank)


def reset_registry() -> None:
    _cell_registry.clear()


def get_cell(rank: Tuple[int, int]) -> Optional[SheetCell]:
    return _cell_registry.get(rank)


def all_cells() -> List[SheetCell]:
    return list(_cell_registry.values())
