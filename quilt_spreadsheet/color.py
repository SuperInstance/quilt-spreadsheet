"""
color.py — per-cell local color/label namespaces.

Casey: "if one's red is the other's blue and they think they are talking
about the same thing but they are objectively not. it still doesn't matter
if their logics agree for their specific cells application."

This is the substrate's TOLERANCE for semantic heterogeneity. Each cell
has its own private color/label space. The substrate does NOT enforce
a global "red = blue = hot" naming convention. The substrate records
the labels used and the logic state, and it lets the application's
LOGIC (not the names) determine whether two cells agree.

In practice:
  - each cell has a ColorNamespace
  - when a cell labels something "red", it records its own private
    red->canonical mapping
  - the substrate's porting backend uses the CANONICAL value, not the label
  - the cell can re-label "red" to "critical" without coordinating
"""

from typing import Dict, Tuple, Optional, Any


class ColorNamespace:
    """A single cell's private color/label space.

    Each cell sees the world through its OWN labels. Two cells can call the
    same observation different things and still communicate correctly —
    because the substrate's porting/backend handles the canonical
    translation.
    """

    __slots__ = ('owner', '_label_to_canonical', '_canonical_to_label')

    def __init__(self, owner: Tuple[int, int]):
        self.owner = owner  # cell rank
        self._label_to_canonical: Dict[str, Any] = {}
        self._canonical_to_label: Dict[Any, str] = {}

    def assign(self, label: str, canonical_value: Any) -> None:
        """Assign a private label to a canonical value.

        e.g. color.assign('red', 'CRITICAL')
        e.g. color.assign('blue', 'CRITICAL')  # same canonical, different label
        """
        self._label_to_canonical[label] = canonical_value
        self._canonical_to_label[canonical_value] = label

    def canonical(self, label: str) -> Optional[Any]:
        """Look up the canonical value for a private label."""
        return self._label_to_canonical.get(label)

    def label(self, canonical_value: Any) -> Optional[str]:
        """Look up the private label for a canonical value (the inverse)."""
        return self._canonical_to_label.get(canonical_value)

    def labels(self) -> Dict[str, Any]:
        """Read-only view of all private labels."""
        return dict(self._label_to_canonical)

    def __repr__(self):
        return f"ColorNamespace(owner={self.owner}, labels={self.labels()!r})"


def same_canonical(ns_a: ColorNamespace, label_a: str,
                   ns_b: ColorNamespace, label_b: str) -> bool:
    """True iff two cells' labels resolve to the same canonical value.

    This is how the substrate verifies that two cells agree on the LOGIC,
    not the labels. Cell A's "red" and Cell B's "blue" agree iff both
    map to the same canonical value (e.g., 'CRITICAL').
    """
    a = ns_a.canonical(label_a)
    b = ns_b.canonical(label_b)
    return a is not None and a == b


def labels_matter(ns_a: ColorNamespace, ns_b: ColorNamespace) -> bool:
    """Whether the LABELS (not the canonical values) of two cells agree.

    This is intentionally weak. The substrate doesn't compare labels —
    it compares canonical values. labels_matter is FALSE in most cases.
    """
    if set(ns_a.labels().keys()) != set(ns_b.labels().keys()):
        return False
    for label in ns_a.labels():
        if not ns_b.canonical(label):
            return False
    return True
