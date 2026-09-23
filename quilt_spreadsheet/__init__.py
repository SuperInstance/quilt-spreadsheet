"""
quilt-spreadsheet — the IDE substrate.

A spreadsheet-as-IDE where:
  - front-end looks like a spreadsheet (rows x cols)
  - each cell is a runnable program with hooks
  - double-entry bookkeeping tracks every pull/push pair
  - per-cell color namespaces (semantic heterogeneity is OK)
  - backend porting handles scale/unit conversions
  - distributed clocks allow skew; time-between-events converges

This is the SUBSTRATE TRANSITION from quilt-egg (a single cell) to
quilt-spreadsheet (a grid of cells with hooks).
"""

from .clock import (
    CellClock, DistributedClock, get_default_clock, reset_default_clock
)
from .ledger import (
    LedgerEntry, Ledger, get_default_ledger, reset_default_ledger
)
from .color import (
    ColorNamespace, same_canonical, labels_matter
)
from .backend import (
    Backend, get_default_backend, reset_default_backend,
    convert, REGISTRY,
)
from .perception import Perception
from .cell import (
    SheetCell, DOCTRINE_AXIOMS, ACTION_AXIOMS,
    register_cell, reset_registry, get_cell, all_cells,
)
from .grid import QuiltSpreadsheet, place_cell

__all__ = [
    "CellClock", "DistributedClock",
    "get_default_clock", "reset_default_clock",
    "LedgerEntry", "Ledger",
    "get_default_ledger", "reset_default_ledger",
    "ColorNamespace", "same_canonical", "labels_matter",
    "Backend", "get_default_backend", "reset_default_backend",
    "convert", "REGISTRY",
    "Perception",
    "SheetCell", "DOCTRINE_AXIOMS", "ACTION_AXIOMS",
    "register_cell", "reset_registry", "get_cell", "all_cells",
    "QuiltSpreadsheet", "place_cell",
]

__version__ = "0.1.0"
