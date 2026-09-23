"""
__main__.py — `python -m quilt_spreadsheet` runs a demo spreadsheet.
"""

import argparse
import sys

from .grid import QuiltSpreadsheet, reset_all


def demo_spreadsheet():
    """Build a 4×4 substrate with 4 programs that respond to pulls."""
    reset_all()
    sheet = QuiltSpreadsheet(rows=4, cols=4, name="canonical_demo")

    def adder(*, source, hook, value):
        # Cell that adds 1 to whatever is pulled
        return (value or 0) + 1

    def doubler(*, source, hook, value):
        return (value or 0) * 2

    def labeler(*, source, hook, value):
        # Cell that translates a label
        return "doubled" if hook == "double" else "added"

    def tally(*, source, hook, value):
        # Counts how many times it has been pulled
        return f"tally:{value}"

    # Place four programs
    sheet.place_cell(0, 0, adder)
    sheet.place_cell(0, 1, doubler)
    sheet.place_cell(1, 0, labeler)
    sheet.place_cell(1, 1, tally)

    # Wire a workflow: cell at (2, 2) pulls adder, then doubler
    def workflow(*, source, hook, value):
        return f"workflow[{hook}]={value}"

    sheet.place_cell(2, 2, workflow)
    # Pull adder
    sheet.pull(2, 2, 0, 0, hook="step1", value=5)
    # Pull doubler — note this uses ledger.record_pair
    sheet.pull(0, 0, 0, 1, hook="double", value=5)

    print(sheet.render())
    print()
    print("Summary:")
    for k, v in sheet.summary().items():
        print(f"  {k}: {v}")
    print()
    print("Pulls and pushes recorded in the ledger (double-entry pairs).")


def main():
    parser = argparse.ArgumentParser(
        prog="quilt_spreadsheet",
        description="The Quilt spreadsheet IDE substrate — double-entry bookkeeping, distributed clocks, per-cell color namespaces, backend porting.",
    )
    parser.add_argument("--rows", type=int, default=4, help="Spreadsheet rows (default: 4)")
    parser.add_argument("--cols", type=int, default=4, help="Spreadsheet cols (default: 4)")
    parser.add_argument("--demo", choices=["canonical"], default="canonical", help="Demo to run")
    args = parser.parse_args()
    if args.demo == "canonical":
        demo_spreadsheet()
        return 0


if __name__ == "__main__":
    sys.exit(main())
