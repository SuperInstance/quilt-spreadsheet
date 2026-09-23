"""
demo_color_independent.py — demonstrate per-cell color independence.

Casey: "if one's red is the other's blue and they think they are talking
about the same thing but they are objectively not. it still doesn't matter
if their logics agree for their specific cells application."

This demo shows two cells with DIFFERENT color mappings for the same
canonical state. They each label things their own way. The substrate
DOES NOT enforce a global "red = blue". It DOES enforce canonical
agreement at the LOGIC level (when they agree, they both report
'CRITICAL' as their canonical — even if one's label is 'red' and the
other's is 'blue').
"""

import sys
sys.path.insert(0, '.')

from quilt_spreadsheet.color import ColorNamespace, same_canonical


def main():
    print("=" * 60)
    print("PER-CELL COLOR INDEPENDENCE")
    print("=" * 60)
    print()
    # Cell A: 'red' = CRITICAL
    a = ColorNamespace(owner=(0, 0))
    a.assign("red", "CRITICAL")
    a.assign("yellow", "WARNING")
    a.assign("green", "OK")
    # Cell B: 'blue' = CRITICAL (DIFFERENT label, same canonical!)
    b = ColorNamespace(owner=(0, 1))
    b.assign("blue", "CRITICAL")
    b.assign("amber", "WARNING")
    b.assign("olive", "OK")
    print()
    print(f"Cell A's namespace: {a.labels()}")
    print(f"Cell B's namespace: {b.labels()}")
    print()
    print(f"Cell A says 'red' is {a.canonical('red')!r}")
    print(f"Cell B says 'blue' is {b.canonical('blue')!r}")
    print()
    print("Are they the same?")
    print(f"  same_canonical(A, 'red', B, 'blue') = {same_canonical(a, 'red', b, 'blue')}")
    print(f"  same_canonical(A, 'red', B, 'olive') = {same_canonical(a, 'red', b, 'olive')}")
    print()
    print("Cell A's 'red' looks DIFFERENT from Cell B's 'blue'.")
    print("But they BOTH map to canonical 'CRITICAL'.")
    print()
    print("Cell A thinks they're talking about the same thing as Cell B's 'red'")
    print("(because both are 'red' to A), but objectively they're not.")
    print("It doesn't matter if their LOGICS agree: both call CRITICAL, critical.")
    print()
    print("=" * 60)
    print("THE LOAD-BEARING INSIGHT")
    print("=" * 60)
    print()
    print("The substrate does NOT enforce a global color/label namespace.")
    print("It DOES record each cell's private labels.")
    print("It DOES verify canonical agreement at the LOGIC level.")
    print()
    print("This is how two parts of the substrate can look totally")
    print("different but be talking about the same thing — and how")
    print("two parts can look identical and be NOT talking about")
    print("the same thing. The substrate doesn't judge by surface.")
    print("It judges by canonical agreement.")


if __name__ == "__main__":
    main()
