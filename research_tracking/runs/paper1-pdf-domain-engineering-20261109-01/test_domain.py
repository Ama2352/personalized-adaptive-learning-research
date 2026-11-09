"""Fixture domain tự tạo, không đọc CSV nghiên cứu hoặc chạy simulator.

Hash fixture chỉ chứng minh bytes khai báo trong test. Không gắn historical
PDF identity hoặc canonical candidate identity cho các concept c00..c27.
"""

import csv
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from knowledge_tracing.paper1_pdf import domain


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='paper1-pdf-domain-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.directory = self.root/domain.INPUT_DIRECTORY
        self.directory.mkdir(parents=True)
        self.nodes = tuple(f'c{i:02d}' for i in range(28))
        self.chapters = {node: ('A' if i < 9 else 'B' if i < 17 else 'C')
                         for i, node in enumerate(self.nodes)}
        baseline = [(self.nodes[i], self.nodes[i+1]) for i in range(27)
                    if self.chapters[self.nodes[i]] == self.chapters[self.nodes[i+1]]]
        advanced = baseline + [('c00', 'c02'), ('c09', 'c11'), ('c17', 'c19'),
                               ('c08', 'c09'), ('c16', 'c17'), ('c07', 'c18')]
        self.rows = {
            'nodes.csv': [(node,) for node in self.nodes],
            'question_bank.csv': [(f'{node}-{level}', node, str(level)) for node in self.nodes
                                  for level in (1050, 1200, 1350)],
            'concept_to_chapter_map.csv': list(self.chapters.items()) +
                                        [(f'extra{i:02d}', 'A') for i in range(8)],
            'edges_baseline.csv': baseline,
            'edges.csv': advanced,
        }
        for name in self.rows:
            self.write_rows(name)
        root_patch = patch.object(domain, 'ROOT', self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        self.pin_patch = patch.object(domain, 'INPUT_SHA256', self.pins())
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)

    def write_rows(self, name):
        stream = io.StringIO(newline='')
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(domain.HEADERS[name])
        writer.writerows(self.rows[name])
        (self.directory/name).write_bytes(stream.getvalue().encode('utf-8'))

    def pins(self):
        return tuple((name, hashlib.sha256((self.directory/name).read_bytes()).hexdigest())
                     for name, _ in domain.PROSPECTIVE_INPUT_SHA256)

    def repin(self):
        domain.INPUT_SHA256 = self.pins()

    def changed_rows_rejected(self, name):
        self.write_rows(name)
        self.repin()
        with self.assertRaises(ValueError):
            domain.load_prospective_paper2_domain()

    def test_complete_domain_and_explicit_source_scope(self):
        result = domain.load_prospective_paper2_domain()
        self.assertEqual((len(result.nodes), len(result.bank.items)), (28, 84))
        self.assertEqual((len(result.baseline_edges), len(result.advanced_edges)), (25, 31))
        self.assertEqual(dict(result.chapters), self.chapters)
        self.assertEqual(result.excluded_chapter_entries, tuple((f'extra{i:02d}', 'A') for i in range(8)))
        self.assertEqual(len(result.files), 5)
        metadata = result.metadata()
        self.assertTrue(metadata['source_bytes_verified'])
        for key in ('canonical_candidate_pins', 'historical_pdf_input_identity_claimed',
                    'b0_policy_implemented', 'full_matrix_implemented', 'execution_authority'):
            self.assertFalse(metadata[key], key)
        self.assertEqual(result.identity, domain.load_prospective_paper2_domain().identity)

    def test_lexicographic_topology_is_per_graph(self):
        result = domain.load_prospective_paper2_domain()
        for edges, order in ((result.baseline_edges, result.baseline_traversal_order),
                             (result.advanced_edges, result.advanced_traversal_order)):
            remaining = set(self.nodes)
            prefix = []
            for chosen in order:
                eligible = [node for node in remaining if all(parent in prefix
                            for parent, child in edges if child == node)]
                self.assertEqual(chosen, min(eligible))
                prefix.append(chosen)
                remaining.remove(chosen)
        self.assertEqual(domain._lexicographic_order(('z', 'a', 'm'), (('z', 'a'),)), ('m', 'z', 'a'))

    def test_metadata_is_detached(self):
        result = domain.load_prospective_paper2_domain()
        identity = result.identity
        metadata = result.metadata()
        metadata['bank_identity']['environment_id'] = 'changed'
        metadata['chapters'] = ()
        self.assertEqual(result.identity, identity)

    def test_sha_rejection_precedes_csv_parser(self):
        path = self.directory/'nodes.csv'
        path.write_bytes(path.read_bytes()+b'bad')
        with patch.object(domain, '_rows', side_effect=AssertionError('parser must not run')):
            with self.assertRaisesRegex(ValueError, 'SHA'):
                domain.load_prospective_paper2_domain()

    def test_input_drift_during_build_rejected(self):
        original = domain._lexicographic_order
        def mutate_after_validation(nodes, edges):
            path = self.directory/'nodes.csv'
            path.write_bytes(path.read_bytes()+b'\n')
            return original(nodes, edges)
        with patch.object(domain, '_lexicographic_order', side_effect=mutate_after_validation):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                domain.load_prospective_paper2_domain()

    def test_pin_inventory_rejected(self):
        pins = self.pins()
        variants = (pins[:-1], pins + (pins[0],),
                    (('unknown.csv', pins[0][1]),)+pins[1:],
                    ((pins[0][0], 'A'*64),)+pins[1:],
                    ((pins[0][0], '0'*65),)+pins[1:])
        for invalid in variants:
            with self.subTest(pins=invalid), patch.object(domain, 'INPUT_SHA256', invalid):
                with self.assertRaises(ValueError):
                    domain.load_prospective_paper2_domain()

    def test_missing_file_rejected(self):
        (self.directory/'nodes.csv').unlink()
        with self.assertRaises(ValueError):
            domain.load_prospective_paper2_domain()

    def test_per_file_and_total_caps(self):
        for attribute in ('MAX_FILE_BYTES', 'MAX_TOTAL_BYTES'):
            with self.subTest(cap=attribute), patch.object(domain, attribute, 8):
                with self.assertRaises(ValueError):
                    domain.load_prospective_paper2_domain()

    def test_symlink_and_junction_ancestors_rejected_without_read(self):
        target = self.root/'paper2'
        for attribute in ('is_symlink', 'is_junction'):
            original = getattr(Path, attribute, lambda self: False)
            def is_alias(path):
                return path == target or original(path)
            with self.subTest(alias=attribute), patch.object(Path, attribute, is_alias, create=True):
                with self.assertRaisesRegex(ValueError, 'alias'):
                    domain._physical_file('nodes.csv')

    def test_wrong_header_rejected(self):
        path = self.directory/'nodes.csv'
        path.write_bytes(path.read_bytes().replace(b'concept_id', b'concept', 1))
        self.repin()
        with self.assertRaisesRegex(ValueError, 'header'):
            domain.load_prospective_paper2_domain()

    def test_invalid_csv_encoding_and_fields(self):
        path = self.directory/'nodes.csv'
        for raw in (b'concept_id\n\xff\n', b'concept_id\nc00\x00\n', b'concept_id\nc00,x\n',
                    b'concept_id\n c00\n', b'concept_id\n"unfinished\n'):
            with self.subTest(raw=raw):
                path.write_bytes(raw)
                self.repin()
                with self.assertRaises(ValueError):
                    domain.load_prospective_paper2_domain()

    def test_duplicate_or_missing_nodes_rejected(self):
        original = list(self.rows['nodes.csv'])
        for rows in (original[:-1], original[:-1]+[original[0]], original+[('extra',)]):
            with self.subTest(rows=rows):
                self.rows['nodes.csv'] = rows
                self.changed_rows_rejected('nodes.csv')

    def test_duplicate_or_missing_items_rejected(self):
        original = list(self.rows['question_bank.csv'])
        for rows in (original[:-1], original[:-1]+[original[0]]):
            with self.subTest(rows=rows):
                self.rows['question_bank.csv'] = rows
                self.changed_rows_rejected('question_bank.csv')

    def test_foreign_item_concept_rejected(self):
        item, _, level = self.rows['question_bank.csv'][0]
        self.rows['question_bank.csv'][0] = (item, 'outside', level)
        self.changed_rows_rejected('question_bank.csv')

    def test_difficulty_contract_rejected(self):
        original = self.rows['question_bank.csv'][0]
        for value in ('nan', 'inf', 'not-number', '1100', '1200'):
            with self.subTest(difficulty=value):
                self.rows['question_bank.csv'][0] = (*original[:2], value)
                self.changed_rows_rejected('question_bank.csv')

    def test_missing_or_duplicate_chapter_rejected(self):
        original = list(self.rows['concept_to_chapter_map.csv'])
        for rows in (original[1:], original+[original[0]]):
            with self.subTest(rows=rows):
                self.rows['concept_to_chapter_map.csv'] = rows
                self.changed_rows_rejected('concept_to_chapter_map.csv')

    def test_four_domain_chapters_rejected(self):
        self.rows['concept_to_chapter_map.csv'][0] = ('c00', 'D')
        self.changed_rows_rejected('concept_to_chapter_map.csv')

    def test_duplicate_graph_edge_rejected(self):
        self.rows['edges.csv'][-1] = self.rows['edges.csv'][0]
        self.changed_rows_rejected('edges.csv')

    def test_unknown_graph_endpoint_rejected(self):
        self.rows['edges.csv'][-1] = ('c07', 'outside')
        self.changed_rows_rejected('edges.csv')

    def test_graph_cycle_rejected(self):
        self.rows['edges.csv'][-1] = ('c02', 'c00')
        self.changed_rows_rejected('edges.csv')

    def test_baseline_must_be_subset(self):
        self.rows['edges_baseline.csv'][0] = ('c00', 'c03')
        self.changed_rows_rejected('edges_baseline.csv')

    def test_baseline_cross_chapter_rejected(self):
        previous = self.rows['edges_baseline.csv'][0]
        self.rows['edges_baseline.csv'][0] = ('c00', 'c09')
        self.rows['edges.csv'][self.rows['edges.csv'].index(previous)] = ('c00', 'c09')
        self.write_rows('edges.csv')
        self.changed_rows_rejected('edges_baseline.csv')

    def test_added_intra_cross_balance_rejected(self):
        self.rows['edges.csv'][-1] = ('c18', 'c20')
        self.changed_rows_rejected('edges.csv')

    def test_graph_row_counts_rejected(self):
        for name in ('edges_baseline.csv', 'edges.csv'):
            with self.subTest(graph=name):
                original = self.rows[name]
                self.rows[name] = original[:-1]
                self.changed_rows_rejected(name)
                self.rows[name] = original
                self.write_rows(name)


if __name__ == '__main__':
    unittest.main()
