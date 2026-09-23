"""
grid.py — QuiltSpreadsheet — the spreadsheet-shaped substrate.

A spreadsheet-shaped substrate. Each cell is a runnable program with
hooks to other cells. The grid is the substrate walker canvas — cells
live INSIDE the grid, the grid is the IDE's front-end.

The substrate transition: from quilt-egg (1 cell) to quilt-spreadsheet
(grid of cells). Same DNA, same constants, more dimensions.
"""

from typing import Tuple, Optional, Callable, Dict, Any, List
import sys

from .cell import SheetCell, register_cell
from .clock import get_default_clock, reset_default_clock
from .ledger import get_default_ledger, reset_default_ledger
from .backend import get_default_backend, reset_default_backend


class QuiltSpreadsheet:
    """A spreadsheet-shaped substrate.

    The IDE front-end is rows × cols of cells. Each cell is a runnable
    program with hooks. Pulls and pushes between cells are recorded in
    the double-entry ledger.
    """

    def __init__(self, rows: int = 8, cols: int = 8, name: str = "spreadsheet"):
        self.rows = rows
        self.cols = cols
        self.name = name
        self._cells: Dict[Tuple[int, int], SheetCell] = {}
        # Bind module-level singletons to this substrate instance
        # (for testing — production uses the module-level clock/ledger)
        self.clock = get_default_clock()
        self.ledger = get_default_ledger()
        self.backend = get_default_backend()

    def place_cell(
        self,
        row: int,
        col: int,
        program: Callable,
        axioms=None,
    ) -> SheetCell:
        """Place a program into the substrate at (row, col).

        Casey: "a python program might sit in a cell as a shell command
        ready to run with hooks to other cells for wake-up."

        The cell is the program's home. It wakes when pulled.
        """
        if (row, col) in self._cells:
            raise ValueError(f"cell at ({row}, {col}) already exists")
        cell = SheetCell(row=row, col=col, program=program, axioms=axioms)
        self._cells[cell.rank] = cell
        register_cell(cell)
        return cell

    def get_cell(self, row: int, col: int) -> Optional[SheetCell]:
        return self._cells.get((row, col))

    def cells(self) -> List[SheetCell]:
        return list(self._cells.values())

    def render(self) -> str:
        """Render the substrate as a spreadsheet-shaped string.

        Each cell shows its row,col and a status indicator:
          '.' = dormant
          '*' = awake (has been pulled at least once)
          'P' = pulled (received a pull)
          'X' = pushed (sent a push)
        """
        rows_str = []
        for r in range(self.rows):
            line = "  "
            for c in range(self.cols):
                cell = self._cells.get((r, c))
                if cell is None:
                    mark = "."
                elif cell.awake_count > 0:
                    mark = "*"
                else:
                    mark = "_"
                line += f" {mark}  "
            rows_str.append(line)
        header = "  " + "  ".join(f"c{c}" for c in range(self.cols))
        return "\n".join([f"QuiltSpreadsheet '{self.name}' {self.rows}x{self.cols}", header] + rows_str)

    def pull(self, source_row, source_col, target_row, target_col,
             hook: str = "default", value: Any = None) -> dict:
        """Cell at (source) pulls from cell at (target).

        Records the pull/push pair in the ledger. Wakes the target.
        """
        source_cell = self._cells.get((source_row, source_col))
        target_cell = self._cells.get((target_row, target_col))
        if source_cell is None or target_cell is None:
            return {'error': f"cell(s) not found: source={(source_row, source_col)}, target={(target_row, target_col)}"}
        return source_cell.pull_from(target_cell.rank, hook=hook, value=value)

    def summary(self) -> dict:
        cells = self.cells()
        total_awake = sum(1 for c in cells if c.awake_count > 0)
        total_pulls = sum(len(hooks) for hooks in (c.pulls for c in cells))
        # Flatten the hooks lists
        total_pull_count = sum(len(v) for c in cells for v in c.pulls.values())
        total_push_count = sum(len(v) for c in cells for v in c.pushes.values())
        return {
            "name": self.name,
            "rows": self.rows,
            "cols": self.cols,
            "cells_placed": len(self._cells),
            "cells_awake": total_awake,
            "ledger": self.ledger.summary(),
            "backend_conversions_run": self.backend.stats()["conversions_run"],
        }


def place_cell(row: int, col: int, program: Callable, axioms=None) -> SheetCell:
    """Convenience: place a cell into the default registry."""
    cell = SheetCell(row=row, col=col, program=program, axioms=axioms)
    register_cell(cell)
    return cell


def reset_all() -> None:
    """Reset all singletons for testing."""
    reset_default_clock()
    reset_default_ledger()
    reset_default_backend()
    from .cell import reset_registry
    reset_registry()
