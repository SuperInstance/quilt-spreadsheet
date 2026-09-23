"""
test_spreadsheet.py — unit tests for the Quilt spreadsheet substrate.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import time

from quilt_spreadsheet.clock import (
    CellClock, DistributedClock, get_default_clock, reset_default_clock,
)
from quilt_spreadsheet.ledger import (
    Ledger, LedgerEntry, get_default_ledger, reset_default_ledger,
)
from quilt_spreadsheet.color import (
    ColorNamespace, same_canonical, labels_matter,
)
from quilt_spreadsheet.backend import (
    Backend, REGISTRY, get_default_backend, reset_default_backend,
)
from quilt_spreadsheet.cell import (
    SheetCell, DOCTRINE_AXIOMS, ACTION_AXIOMS,
    register_cell, reset_registry, get_cell, all_cells,
)
from quilt_spreadsheet.grid import (
    QuiltSpreadsheet, place_cell, reset_all,
)
from quilt_spreadsheet.perception import Perception


class TestClock(unittest.TestCase):

    def setUp(self):
        reset_default_clock()

    def test_cell_clock_advances(self):
        clk = CellClock()
        t1 = clk.tick()
        # Time has passed (small but non-zero on most systems)
        self.assertGreaterEqual(t1, 0)
        self.assertEqual(clk.event_count, 1)

    def test_distributed_clock(self):
        clock = DistributedClock()
        a = (0, 0)
        b = (0, 1)
        t_a = clock.tick(a)
        t_b = clock.tick(b)
        self.assertGreaterEqual(t_a, 0)
        self.assertGreaterEqual(t_b, 0)

    def test_pairwise_confidence_rises(self):
        clock = DistributedClock()
        a = (0, 0)
        b = (0, 1)
        # No shared events
        self.assertEqual(clock.pair_confidence(a, b), 0)
        # Share 1 event
        clock.track_pair_sync(a, b)
        self.assertAlmostEqual(clock.pair_confidence(a, b), 0.5)
        # Share more events
        for _ in range(10):
            clock.track_pair_sync(a, b)
        self.assertGreater(clock.pair_confidence(a, b), 0.9)
        self.assertLess(clock.pair_confidence(a, b), 1.0)

    def test_time_between_events(self):
        clock = DistributedClock()
        delta = clock.time_between_events(100, 200)
        self.assertEqual(delta, 100)


class TestLedger(unittest.TestCase):

    def setUp(self):
        reset_default_ledger()

    def test_paired_pull_push(self):
        ledger = Ledger()
        ts = 1000
        pull = ledger.record_pull(
            source=(0, 0), target=(0, 1), hook='test',
            value=42, timestamp_ns=ts,
        )
        push = ledger.record_push(
            source=(0, 1), target=(0, 0), hook='test',
            value=99, timestamp_ns=ts, pair_id=pull.pair_id,
        )
        self.assertIsNotNone(push)
        self.assertEqual(ledger.total_pairs, 1)
        self.assertEqual(len(ledger.unbalanced), 0)

    def test_unbalanced_pull(self):
        ledger = Ledger()
        ts = 1000
        ledger.record_pull(
            source=(0, 0), target=(0, 1), hook='silent',
            value=None, timestamp_ns=ts,
        )
        self.assertEqual(ledger.total_pulls, 1)
        self.assertEqual(len(ledger.unbalanced), 1)

    def test_push_without_pull_rejected(self):
        ledger = Ledger()
        result = ledger.record_push(
            source=(0, 0), target=(0, 1), hook='orphan',
            value=42, timestamp_ns=1000, pair_id='nonexistent',
        )
        self.assertIsNone(result)


class TestColor(unittest.TestCase):

    def test_per_cell_independence(self):
        a = ColorNamespace((0, 0))
        b = ColorNamespace((0, 1))
        a.assign('red', 'CRITICAL')
        b.assign('blue', 'CRITICAL')
        self.assertEqual(a.canonical('red'), 'CRITICAL')
        self.assertEqual(b.canonical('blue'), 'CRITICAL')
        # Labels differ but canonical agrees
        self.assertTrue(same_canonical(a, 'red', b, 'blue'))

    def test_disagreeing_canonicals(self):
        a = ColorNamespace((0, 0))
        b = ColorNamespace((0, 1))
        a.assign('red', 'CRITICAL')
        b.assign('blue', 'WARNING')
        self.assertFalse(same_canonical(a, 'red', b, 'blue'))

    def test_labels_matter(self):
        a = ColorNamespace((0, 0))
        b = ColorNamespace((0, 1))
        a.assign('red', 'X')
        a.assign('yellow', 'Y')
        b.assign('blue', 'X')
        b.assign('amber', 'Y')
        # Labels are different. labels_matter should be False (we don't
        # compare labels, only canonicals)
        self.assertFalse(labels_matter(a, b))


class TestBackend(unittest.TestCase):

    def setUp(self):
        reset_default_backend()

    def test_temperature_port(self):
        backend = Backend()
        result = backend.port(100, 'celsius', 'fahrenheit', domain='temperature')
        self.assertAlmostEqual(result, 212, places=1)

    def test_snap(self):
        backend = Backend()
        self.assertEqual(backend.snap(3.7, 0.5), 3.5)
        self.assertEqual(backend.snap(3.7, 1), 4)

    def test_gate_below(self):
        backend = Backend()
        self.assertIsNone(backend.gate_below(0.3, 0.5))
        self.assertEqual(backend.gate_below(0.7, 0.5), 0.7)

    def test_time_preservation(self):
        backend = Backend()
        ns = 5_000_000_000
        ms = backend.port_time(ns, 'ns', 'ms')
        back = backend.port_time(ms, 'ms', 'ns')
        self.assertEqual(back, ns)


class TestSpreadsheet(unittest.TestCase):

    def setUp(self):
        reset_all()

    def test_place_and_pull(self):
        sheet = QuiltSpreadsheet(rows=4, cols=4)
        def adder(*, source, hook, value):
            return (value or 0) + 1
        sheet.place_cell(0, 0, adder)
        sheet.place_cell(0, 1, adder)
        result = sheet.pull(0, 0, 0, 1, hook="test", value=5)
        self.assertEqual(result['response'], 6)

    def test_double_entry_pairing(self):
        sheet = QuiltSpreadsheet(rows=4, cols=4)
        def responder(*, source, hook, value):
            return value
        sheet.place_cell(0, 0, responder)
        sheet.place_cell(0, 1, responder)
        for i in range(3):
            sheet.pull(0, 0, 0, 1, hook=f"r{i}", value=i)
        # 3 pulls, 3 pushes, 3 pairs
        self.assertEqual(sheet.ledger.total_pairs, 3)
        self.assertEqual(len(sheet.ledger.unbalanced), 0)

    def test_unbalanced(self):
        sheet = QuiltSpreadsheet(rows=4, cols=4)
        def respond(*, source, hook, value):
            return value
        def quiet(*, source, hook, value):
            return None
        sheet.place_cell(0, 0, respond)
        sheet.place_cell(0, 1, respond)
        sheet.place_cell(0, 2, quiet)
        sheet.pull(0, 0, 0, 1, hook="ok", value=1)
        sheet.pull(0, 0, 0, 2, hook="silent", value=None)
        # 1 unbalanced (the silent pull)
        self.assertEqual(len(sheet.ledger.unbalanced), 1)


class TestPerception(unittest.TestCase):

    def test_perception_sorts(self):
        p = Perception(owner=(0, 0))
        p.ingest([
            {'type': 'B', 'value': 2},
            {'type': 'A', 'value': 1},
            {'type': 'C', 'value': 3},
        ])
        p.sort_by_type()
        items = p.items()
        self.assertEqual([i['type'] for i in items], ['A', 'B', 'C'])

    def test_perception_groups(self):
        p = Perception(owner=(0, 0))
        p.ingest([
            {'type': 'A', 'value': 1},
            {'type': 'A', 'value': 2},
            {'type': 'B', 'value': 3},
        ])
        groups = p.group_by_type()
        self.assertEqual(len(groups['A']), 2)
        self.assertEqual(len(groups['B']), 1)

    def test_perception_filter(self):
        p = Perception(owner=(0, 0))
        p.ingest([
            {'type': 'A', 'value': 1},
            {'type': 'B', 'value': 2},
            {'type': 'A', 'value': 3},
        ])
        p.filter(lambda x: x['type'] == 'A')
        self.assertEqual(p.size(), 2)


class TestCanary(unittest.TestCase):
    """Polyformalism canary: same hash across all ports."""

    def test_fnv1a_64(self):
        h = 0xcbf29ce484222325
        for b in "café Δ 日本語".encode("utf-8"):
            h = h ^ b
            h = (h * 0x100000001b3) & 0xffffffffffffffff
        self.assertEqual(h, 0x024a555471370b18d)


if __name__ == "__main__":
    unittest.main()
