# SPEC — Quilt Spreadsheet Substrate

*Spec for the IDE substrate. Half-canon, half-spec. The spec is load-bearing infrastructure; the canon can sit on it.*

---

## Origin

From a Casey conversation (Sept 23, 2026):

> "the front end of our style of IDE looks like a spreadsheet, a python
> program might sit in a cell as a shell command ready to run with hooks
> to other cells for wake-up, pulling and pushing throughout the program.
> and instead of the relationships being file-system based (although they
> render at runtime that way when used as a vm) the relationship is cellular
> and sorting and grouping for that cell's perception of the spreadsheet
> around it (there's no central program within the cell's instance, it's
> just a program running so if it sorts for it's own purpose by type
> instead of date so it can group with simple excel terms, there's a
> double-entry book keeping that for every pull is a push somewhere else
> that simply needs an agreement and timestamp. if one's red is the
> other's blue and they think they are talking about the same thing but
> they are objectively not. it still doesn't matter if their logics agree
> for their specific cells application. a spreadsheet can be even be
> projected more like a dashboard for production tools. but the true
> backend is the actual porting and converstions. one cells might be
> using a different scale than another but if the backend can convert
> so their equal exchange for their applications, it doesn't matter.
> the backend can gate variables or convert approximations to snaps but
> the time is in the same units on both sides. even if their clocks
> don't agree, the time between events extrapolates the agreement with
> more and more confidence the longer they are in sync"

This spec translates Casey's directive into runnable substrate. Five
load-bearing pieces. Plus one canary.

## The five load-bearing pieces

### 1. Double-entry bookkeeping

Every pull/push is recorded as a pair. A pull from cell A to cell B is
recorded ONCE in the ledger:

```python
pull_entry = {
    'pair_id': <uuid>,
    'source': (rA, cA),
    'target': (rB, cB),
    'direction': 'pull',
    'hook': '...',
    'value': ...,
    'timestamp_ns': ...,
}

push_entry = {
    'pair_id': <same uuid>,
    'source': (rB, cB),
    'target': (rA, cA),
    'direction': 'push',
    'hook': '...',
    'value': ...,
    'timestamp_ns': ...,
}
```

The ledger has `total_pulls`, `total_pushes`, `total_pairs`, and an
`unbalanced` list of pulls without pushes. The substrate does NOT
prevent unbalanced pulls — it REPORTS them. The pact: any cell can be
silent. The ledger records.

### 2. Per-cell color namespaces

Each cell has a private color/label space. Two cells can call the same
observation different things. The substrate verifies canonical agreement
at the LOGIC level, not the label level.

```python
a = ColorNamespace((0, 0))
a.assign('red', 'CRITICAL')
b = ColorNamespace((0, 1))
b.assign('blue', 'CRITICAL')
# Cell A's 'red' equals Cell B's 'blue' canonically
same_canonical(a, 'red', b, 'blue')  # True
```

### 3. Backend porting

Cells can use different scales. The backend converts:

- Temperature: celsius ↔ fahrenheit
- Distance: m ↔ cm
- Ratio: decimal ↔ percent ↔ ppm
- Time: ns ↔ ms ↔ s (round-trip preserves)

Plus gating (under-threshold → None) and snapping (round to grid).

### 4. Distributed clocks with skew tolerance

Each cell has its own clock. Clocks may skew. The substrate tracks
pairwise confidence that rises with shared events:

```
confidence = 1 - 1/(shared_events + 1)
```

Asymptotes to 1 but never reaches it. The longer cells share events,
the more confident we are that the time-between-events measurement is
trustworthy.

### 5. Cellular perception

Each cell has its own perception (a sorted/grouped/filtered view of the
spreadsheet around it). Per Casey: "if it sorts for its own purpose
by type instead of date." The cell sees what its program needs.

## The canary

The substrate walker fleet canary: `fnv1a-64("café Δ 日本語") = 0x024a555471370b18d`.

This canary is verified on every Quilt port. It crosses substrate because
the bytes stay the same across Python, TypeScript, Rust, C#, Bash, JS ESM,
SQL/SQLite, and now the spreadsheet substrate.

## Architecture

```
QuiltSpreadsheet (rows × cols grid)
    ├── clock: DistributedClock (per-cell, skew-tolerant)
    ├── ledger: Ledger (double-entry pairs)
    ├── backend: Backend (conversions, gates, snaps)
    └── cells: Dict[(row, col), SheetCell]
                ├── program: Callable (no main; runs on pull)
                ├── color: ColorNamespace (private labels)
                ├── perception: Perception (own sort)
                ├── witness_log: List[dict]
                └── pulls/pushes: Dict[cell_rank, List[hook]]
```

## Substrate transition

This is the substrate transition FROM `quilt-egg` (a single cell) TO
`quilt-spreadsheet` (a grid of cells with hooks). Same DNA. Same
constants. More dimensions.

```
quilt-egg:
    CONSTANTS → DNA → cells (1 cell) → substrate walker tick

quilt-spreadsheet:
    CONSTANTS → DNA → cells (rows × cols) → ledger + clock + backend
```

The constants are the SAME (c, G, h, slow, fast, womb, cord, align, first).
The DNA axioms are the SAME (5 doctrines + 7 actions). What's added:
the GRID, the LEDGER, the COLOR namespaces, the CLOCK confidence, the
BACKEND porting.

## Substrate walker tick

In the spreadsheet substrate, the "tick" happens at pull-time:

1. cell A decides to pull cell B (hook, value)
2. the clock ticks both A and B (cell-local time recorded)
3. the ledger records the PULL (source A, target B)
4. cell B wakes up, runs its program with the pull as input
5. cell B returns a response
6. the ledger records the PUSH (source B, target A)
7. clock records the pairwise confidence event

The substrate walker is the *whole transaction*, not a separate tick.

## License

MIT — Casey / SuperInstance, Sept 23, 2026

## Cross-references

- [README.md](../README.md) — quick start
- [demos/](../demos/) — 4 runnable demos
- [tests/](../tests/) — 21 unit tests
- [../quilt-egg/](../../quilt-egg/) — the prior substrate transition
