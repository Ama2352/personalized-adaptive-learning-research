"""Cơ chế chương trên fixture tự tạo, chưa là kết quả chạy hoặc matrix PDF."""

import unittest

from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem
from knowledge_tracing.paper1_pdf.simulator import (
    DIFFICULTIES, MASTERY_ELO, Paper1PdfController, dynamic_k, elo_probability,
)


def make_controller(nodes, chapters, edges, initial):
    bank = SimulatorBank('paper1-pdf-unverified-mechanism-fixture', tuple(
        SimulatorItem(f'{node}-{int(level)}', node, level)
        for node in nodes for level in DIFFICULTIES))
    return Paper1PdfController(bank, chapters=chapters, edges=edges,
                              traversal_order=nodes, initial_estimates=initial)


def mastered(state):
    return {node for node, value in state['estimated_elo'].items() if value >= MASTERY_ELO}


def blocks(history):
    return tuple(value for i, value in enumerate(history) if i == 0 or value != history[i-1])


class ReentryMechanismTests(unittest.TestCase):
    def test_intra_chapter_branches_absorbing_mastery_despite_wrong_responses(self):
        nodes = ('m', 'a', 'b', 'c', 'd', 'e')
        chapters = dict(m='A', a='A', b='A', c='A', d='B', e='B')
        edges = (('m', 'a'), ('m', 'b'), ('a', 'c'), ('b', 'c'), ('d', 'e'))
        value = make_controller(nodes, chapters, edges, {node: 1300. if node == 'm' else 1249. for node in nodes})
        wrong_count = 0
        for label in (0, 0)+(1,)*38:
            before = value.snapshot()
            predicted = value.predict_next()
            if predicted is None:
                break
            self.assertNotIn(predicted.concept_id, mastered(before))
            value.observe(predicted, label)
            after = value.snapshot()
            self.assertLessEqual(mastered(before), mastered(after))
            for node in mastered(before):
                self.assertEqual(after['estimated_elo'][node], before['estimated_elo'][node])
            if label == 0:
                wrong_count += 1
                self.assertLess(after['estimated_elo'][predicted.concept_id], predicted.estimated_before)
            sequence = blocks(after['chapter_history'])
            self.assertEqual(len(sequence), len(set(sequence)))
        self.assertEqual(wrong_count, 2)
        self.assertEqual(mastered(value.snapshot()), set(nodes))
        self.assertEqual(blocks(value.snapshot()['chapter_history']), ('A', 'B'))
        self.assertEqual(value.metrics()['chapter_reentry'], 0)

    def test_foreign_parents_mastered_at_entry_allow_contiguous_completion(self):
        nodes = ('p', 'a1', 'a2', 'b')
        chapters = dict(p='P', a1='A', a2='A', b='B')
        value = make_controller(nodes, chapters, (('p', 'a1'), ('p', 'a2'), ('a1', 'a2')),
                                dict(p=1300., a1=1249., a2=1249., b=1249.))
        self.assertEqual(mastered(value.snapshot()), {'p'})
        for _ in range(3):
            predicted = value.predict_next()
            self.assertIsNotNone(predicted)
            value.observe(predicted, 1)
        self.assertEqual(value.snapshot()['chapter_history'], ('A', 'A', 'B'))
        self.assertEqual(value.snapshot()['estimated_elo']['p'], 1300.)
        self.assertEqual(mastered(value.snapshot()), set(nodes))
        self.assertEqual(value.metrics()['chapter_reentry'], 0)

    def test_acyclic_chapter_quotient_can_still_force_a_b_a(self):
        nodes = ('a1', 'b', 'a2')
        chapters = dict(a1='A', b='B', a2='A')
        edges = (('b', 'a2'),)
        quotient = {(chapters[parent], chapters[child]) for parent, child in edges}
        self.assertEqual(quotient, {('B', 'A')})
        rank = {'B': 0, 'A': 1}
        self.assertTrue(all(rank[parent] < rank[child] for parent, child in quotient))
        value = make_controller(nodes, chapters, edges, dict(a1=1248., b=1249., a2=1200.))
        self.assertEqual(value.ready_set(), ('a1', 'b'))
        first = value.predict_next()
        self.assertEqual(first.concept_id, 'a1')
        value.observe(first, 1)
        self.assertEqual(value.ready_set(), ('b',))
        second = value.predict_next()
        self.assertEqual(second.concept_id, 'b')
        value.observe(second, 1)
        self.assertEqual(value.ready_set(), ('a2',))
        third = value.predict_next()
        self.assertEqual(third.concept_id, 'a2')
        value.observe(third, 1)
        self.assertEqual(value.snapshot()['chapter_history'], ('A', 'B', 'A'))
        self.assertEqual((value.metrics()['chapter_switches'], value.metrics()['chapter_reentry']), (2, 1))

    def test_global_lowest_elo_toy_can_alternate_without_continuity(self):
        # Đối chứng selector cục bộ, không sửa hoặc bypass controller production.
        estimates = dict(a=1200., b=1201.)
        counts = dict.fromkeys(estimates, 0)
        global_history = []
        for _ in range(3):
            ready = [node for node in estimates if estimates[node] < MASTERY_ELO]
            node = min(ready, key=lambda item: (estimates[item], item))
            difficulty = min(DIFFICULTIES, key=lambda item: (abs(item-estimates[node]), item))
            probability = elo_probability(estimates[node], difficulty)
            estimates[node] += dynamic_k(counts[node])*(1-probability)
            counts[node] += 1
            global_history.append(node.upper())
        self.assertEqual(global_history, ['A', 'B', 'A'])
        value = make_controller(('a', 'b'), dict(a='A', b='B'), (), dict(a=1200., b=1201.))
        for _ in range(3):
            value.observe(value.predict_next(), 1)
        self.assertEqual(value.snapshot()['chapter_history'], ('A', 'A', 'A'))
        self.assertEqual(value.metrics()['chapter_reentry'], 0)


if __name__ == '__main__':
    unittest.main()
