"""
demo_double_entry.py — demonstrate the double-entry bookkeeping.

Casey: "there's a double-entry book keeping that for every pull is a
push somewhere else that simply needs an agreement and timestamp."

This demo shows:
  - A cell at (0, 0) pulls from (0, 1) and (0, 2)
  - Each pull becomes a pair: pull_entry + push_entry
  - The ledger is balanced — every pull has a matching push
  - If we drop a push, the ledger becomes unbalanced (substrate alert)
"""

import sys
sys.path.insert(0, '.')

from quilt_spreadsheet.grid import QuiltSpreadsheet


def main():
    sheet = QuiltSpreadsheet(rows=4, cols=4, name="double_entry_demo")

    def responder(*, source, hook, value):
        return {"echo": value, "hook": hook, "from": source}

    def quiet(*, source, hook, value):
        # A cell that doesn't push back (broken double-entry)
        return None

    # Place three cells
    sheet.place_cell(0, 0, responder)
    sheet.place_cell(0, 1, responder)
    sheet.place_cell(0, 2, quiet)  # this will be unbalanced

    # Pull twice from (0, 1) — both pulls should be paired
    sheet.pull(0, 0, 0, 1, hook="hello", value=42)
    sheet.pull(0, 0, 0, 1, hook="world", value="hi")
    # Pull once from (0, 2) — should be UNBALANCED (no push)
    sheet.pull(0, 0, 0, 2, hook="silent", value=None)

    print("=" * 60)
    print("DOUBLE-ENTRY LEDGER DEMO")
    print("=" * 60)
    print()
    print("Workload:")
    print("  cell(0,0) → cell(0,1) hook='hello' value=42     (paired)")
    print("  cell(0,0) → cell(0,1) hook='world' value='hi'    (paired)")
    print("  cell(0,0) → cell(0,2) hook='silent' value=None   (UNBALANCED)")
    print()
    print("Ledger summary:")
    print(f"  {sheet.ledger.summary()}")
    print()
    if sheet.ledger.unbalanced:
        print(f"  Unbalanced pulls: {len(sheet.ledger.unbalanced)}")
        for e in sheet.ledger.unbalanced:
            print(f"    → pair_id={e.pair_id[:8]}... hook={e.hook!r} target={e.target}")
    print()
    print("OBSERVATIONS:")
    print("  - ledger has 3 pulls and 2 pushes (one push missing)")
    print("  - ledger has 2 paired entries (matching pull+push)")
    print("  - ledger flags 1 unbalanced entry — substrate alert")
    print("  - the SUBSTRATE trusts the ledger to reveal inconsistency")
    print("    (it does not prevent the unbalanced pull; that would be hiding)")
    print()
    print("The pact: any cell can be quiet. The ledger reports.")
    print("The substrate's tolerance: it does not require participation.")
    print("It REQUIRES that the participation be honest — recorded.")


if __name__ == "__main__":
    main()
