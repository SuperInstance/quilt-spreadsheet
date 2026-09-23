"""
perception.py — per-cell sorting and grouping of the spreadsheet around it.

Casey: "the relationship is cellular and sorting and grouping for that
cell's perception of the spreadsheet around it (there's no central program
within the cell's instance, it's just a program running so if it sorts
for it's own purpose by type instead of date so it can group with simple
excel terms."

Each cell has its OWN perception of the spreadsheet. A cell can sort
its view by type, by tag, by relevance, by age — whatever its program
needs. The substrate provides the raw view; the cell sorts as it sees fit.
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
from collections import defaultdict


class Perception:
    """A single cell's view of the spreadsheet around it.

    Cells pull from each other. When a cell pulls a slice of the spreadsheet,
    it gets the raw observations. Each cell has its own Perception that
    sorts those observations for its program's purpose.
    """

    __slots__ = ('owner', '_items', '_sort_key')

    def __init__(self, owner: Tuple[int, int]):
        self.owner = owner
        self._items: List[Dict[str, Any]] = []
        self._sort_key: Optional[Callable] = None

    def ingest(self, items: List[Dict[str, Any]]) -> None:
        """Add raw observations to this perception."""
        self._items.extend(items)

    def sort_by_type(self) -> 'Perception':
        """Sort observations by 'type' field (default perception sort).

        Casey: 'if it sorts for its own purpose by type instead of date'.
        The type-based sort groups by category — like Excel grouping
        rows by data type.
        """
        self._sort_key = lambda x: x.get('type', '')
        self._items.sort(key=self._sort_key)
        return self

    def sort_by(self, key: Callable) -> 'Perception':
        """Custom sort."""
        self._sort_key = key
        self._items.sort(key=key)
        return self

    def group_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group observations by 'type' field. Returns dict[group_name, items]."""
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for item in self._items:
            t = item.get('type', 'untyped')
            groups[t].append(item)
        return dict(groups)

    def filter(self, predicate: Callable[[Dict[str, Any]], bool]) -> 'Perception':
        """Keep only items where predicate returns True."""
        self._items = [i for i in self._items if predicate(i)]
        return self

    def items(self) -> List[Dict[str, Any]]:
        return list(self._items)

    def size(self) -> int:
        return len(self._items)
