# quilt-spreadsheet

> **The Quilt IDE as spreadsheet substrate.**
>
> Front-end: rows × cols. Each cell is a runnable program with hooks.
> Double-entry bookkeeping tracks every pull/push. Per-cell color
> namespaces. Backend porting across scales. Distributed clocks with
> skew tolerance.

## What this is

A runnable Python substrate where:

1. **Front-end is a spreadsheet** — `QuiltSpreadsheet(rows, cols)`. Each cell is a `SheetCell`.
2. **Each cell is a runnable program** with hooks (pulls wake it). No `main()`. Event-driven.
3. **Double-entry bookkeeping** — every pull/push pair is recorded as a ledger pair. Same UUID, same timestamp.
4. **Per-cell color namespaces** — cells can label anything anything. The substrate checks canonical agreement, not labels.
5. **Backend porting** — different cells can use different scales/units. The backend converts at the boundary.
6. **Distributed clocks with skew** — clocks can disagree. Time-between-events is the sync signal. Confidence rises with shared events.

## Quick start

```bash
# Run the canonical demo
python3 -m quilt_spreadsheet

# Or with custom dimensions
python3 -m quilt_spreadsheet --rows 4 --cols 4

# Run individual demos
PYTHONPATH=. python3 demos/demo_double_entry.py
PYTHONPATH=. python3 demos/demo_color_independent.py
PYTHONPATH=. python3 demos/demo_backend_conversion.py
PYTHONPATH=. python3 demos/demo_clock_skew.py
```

## Quick example

```python
from quilt_spreadsheet.grid import QuiltSpreadsheet

sheet = QuiltSpreadsheet(rows=4, cols=4)

def adder(*, source, hook, value):
    return (value or 0) + 1

def doubler(*, source, hook, value):
    return (value or 0) * 2

# Place programs into cells
sheet.place_cell(0, 0, adder)
sheet.place_cell(0, 1, doubler)

# Cell (0, 0) pulls from cell (0, 1) with value=5
result = sheet.pull(0, 0, 0, 1, hook="double", value=5)

print(result)
# {'response': 10, 'pair_id': '...', 'timestamp_ns': ..., 'cell': (0, 1)}
```

## The 4 demos

### 1. `demos/demo_double_entry.py`

Demonstrates the load-bearing ledger. Pulls and pushes are paired by UUID
+ timestamp. Unbalanced pulls are flagged but not prevented.

### 2. `demos/demo_color_independent.py`

Two cells with different color labels (red/blue) for the same canonical
(CRITICAL). The substrate verifies agreement at canonical level, not
labels.

### 3. `demos/demo_backend_conversion.py`

Backend ports values between scales (celsius → fahrenheit). Gates values
below threshold. Snaps approximations to discrete grid. Time is preserved
in same units on both sides.

### 4. `demos/demo_clock_skew.py`

Two cells share 10 events. Confidence rises asymptotically from 0.5 to 0.91.
Skew is observable but manageable.

## Architecture

```
QuiltSpreadsheet (rows × cols)
    ├── CellClock [per-cell, private]
    ├── Ledger [double-entry pair ledger]
    ├── Backend [conversions, gates, snaps]
    └── SheetCell (rows × cols)
        ├── program: Callable (no main, runs on pull)
        ├── axioms: frozenset (DNA)
        ├── dials: List[float] (16 mutable state slots)
        ├── color: ColorNamespace (private labels)
        ├── perception: Perception (own sort/group)
        ├── witness_log: List[dict]
        ├── pulls: Dict[cell, List[hook]]
        └── pushes: Dict[cell, List[hook]]
```

## The 3 commands

```python
# 1. Place a program into a cell
sheet.place_cell(row, col, program, axioms=None)

# 2. Pull from another cell (cell A at (r0, c0) wakes cell at (r1, c1))
sheet.pull(r0, c0, r1, c1, hook='name', value=...)

# 3. Inspect state
sheet.render()        # spreadsheet-shaped ascii view
sheet.summary()       # substrate state dict
sheet.ledger.summary()  # double-entry pair ledger
```

## Substrate transition

This repo is the substrate transition FROM `quilt-egg` (single cell) TO
`quilt-spreadsheet` (grid of cells with hooks). Same constants, same DNA.
More dimensions.

| quilt-egg | quilt-spreadsheet |
|---|---|
| 1 cell | rows × cols cells |
| 1 tick loop | pull-triggered wake |
| DNA + dials | DNA + dials + hooks + color + perception |
| 18 tests | 21 tests |
| 4 demos | 4 demos |

## Layered navigation

| Layer | Where |
|---|---|
| **CANON.md** | [CANON.md](CANON.md) — what this repo is, in 24 lines |
| **README** | [README.md](README.md) — quick start, navigation |
| **Spec** | [docs/SPEC.md](docs/SPEC.md) — half-canon, half-spec |
| **Source** | [quilt_spreadsheet/](quilt_spreadsheet/) — `clock.py`, `ledger.py`, `color.py`, `backend.py`, `perception.py`, `cell.py`, `grid.py` |
| **Demos** | [demos/](demos/) — 4 runnable demos |
| **Tests** | [tests/](tests/) — 21 unit tests |
| **Origin** | [quilt-egg](../quilt-egg/) — the prior substrate |

## Polyformalism

This substrate is canonically a polyformalism port. The canary
`fnv1a-64("café Δ 日本語") = 0x024a555471370b18d` is verified on every
Quilt port.

## Tests

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

21 tests covering:
- Clock skew tolerance and pairwise confidence
- Double-entry ledger pairing (and unbalanced-pull handling)
- Per-cell color namespaces
- Backend conversions, gates, snaps
- Spreadsheet pull/push wiring
- Perception sorting/grouping/filtering

## License

MIT — Casey / SuperInstance, Sept 23, 2026
