"""Fixtures file IO nhỏ, không model/corpus/actual selection hoặc authority."""
from dataclasses import replace
import csv
import hashlib
import io
from pathlib import Path
import tempfile
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from knowledge_tracing import research_selection_io as m
H = 'a' * 64


def limits(**changes):
    return replace(m.FileReadLimits(65536, 1048576, 64, 1, 32768, 65536, 4096,
        32, 128, 4096, 32, 2048, 5.), **changes)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='selection_io_')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def put(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return m.FileRef(name, hashlib.sha256(data).hexdigest(), len(data))

    def csv(self, candidate='A0', kind='predictions', rows=None, fields=None, name='input.csv'):
        fields = fields or m.csv_fields(candidate, kind)
        base = dict(learner_id='learner', item_id='q,quoted', timestamp='100', source_row='1', global_rank='0',
            history_hash_scheme='observable-prefix-chain-v1', history_sha256=H, origin_role='selection',
            phase_scope='raw_selection10', phase_sha256=H, encoding_sha256=H, window_id='window',
            history_available='0', history_used='0', context_reset='False', probability='',
            support_reason='oov_item', input_support_reason='oov_item', correct='1')
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows([base] if rows is None else [dict(base, **row) for row in rows])
        return self.put(name, stream.getvalue().encode())

    def test_json_zero_file_and_final_hash_readback(self):
        ref = self.put('metadata.json', b'{"ok":true,"n":1}')
        empty = self.put('stderr.log', b'')
        with m.BoundedArtifactReader(self.root, limits()) as reader:
            self.assertEqual(reader.read_json(ref), {'ok': True, 'n': 1})
            self.assertEqual(reader.verify_file(empty), empty)
            proof = reader.verify_unchanged()
            self.assertEqual((proof['files'], reader.open_files), (2, 0))
            self.assertFalse(proof['external_freeze_authority'])
        self.assertTrue(reader.closed)

    def test_scoped_cursor_preserves_rows_and_closes_handle(self):
        ref = self.csv(rows=[{}, {'source_row': '2', 'global_rank': '1'}])
        with m.BoundedArtifactReader(self.root, limits()) as reader:
            index = reader.index_csv(ref, candidate_id='A0', kind='predictions')
            expected = [index.row(key) for key in index.keys]
            with index.open_rows() as cursor:
                self.assertEqual(reader.open_files, 1)
                self.assertEqual([cursor.row(key) for key in index.keys], expected)
                self.assertEqual(reader.open_files, 1)
            self.assertEqual(reader.open_files, 0)
            self.assertTrue(reader.verify_unchanged()['source_and_input_hashes_rechecked'])
            with self.assertRaisesRegex(ValueError, 'Active owned'):
                cursor.row(index.keys[0])
            self.assertTrue(reader.failed)

    def test_cursor_tampering_and_handle_limit_fail_closed(self):
        ref = self.csv()
        with m.BoundedArtifactReader(self.root, limits()) as reader:
            index = reader.index_csv(ref, candidate_id='A0', kind='predictions')
            with self.assertRaises(ValueError):
                with index.open_rows():
                    path = self.root / ref.path
                    path.write_bytes(path.read_bytes().replace(b'oov_item', b'bad_item'))
            self.assertTrue(reader.failed)
            self.assertEqual(reader.open_files, 0)
        ref = self.csv(name='fresh.csv')
        with m.BoundedArtifactReader(self.root, limits()) as reader:
            index = reader.index_csv(ref, candidate_id='A0', kind='predictions')
            with self.assertRaises(ValueError):
                with index.open_rows():
                    with index.open_rows():
                        self.fail('Second open handle must be rejected')
            self.assertTrue(reader.failed)
            self.assertEqual(reader.open_files, 0)

    def test_bad_paths_protected_names_and_ancestor_alias(self):
        for path in ('../x', '/x', 'x\\y', './x', 'a//b', '.', 'C:/x'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                m.FileRef(path, H, 0)
        ref = self.put('dataset/forbidden.json', b'{}')
        with self.assertRaisesRegex(ValueError, 'Protected'):
            m.BoundedArtifactReader(self.root, limits()).read_json(ref)
        ref = self.put('safe.json', b'{}')
        with patch.object(Path, 'is_symlink', return_value=True), self.assertRaises(ValueError):
            m.BoundedArtifactReader(self.root, limits()).read_json(ref)

    def test_unique_finite_json_and_failed_reader(self):
        for data in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}', b'[]'):
            ref = self.put('bad.json', data)
            reader = m.BoundedArtifactReader(self.root, limits())
            with self.subTest(data=data), self.assertRaises(ValueError):
                reader.read_json(ref)
            self.assertTrue(reader.failed)
            self.assertEqual(reader.open_files, 0)
            with self.assertRaises(ValueError):
                reader.verify_file(ref)

    def test_ctime_checked_within_each_api(self):
        ref = self.put('ctime.json', b'{"value":1}')
        actual_fstat = os.fstat

        def shifted(fd, shift):
            value = actual_fstat(fd)
            return SimpleNamespace(st_dev=value.st_dev, st_ino=value.st_ino,
                st_size=value.st_size, st_mtime_ns=value.st_mtime_ns,
                st_ctime_ns=value.st_ctime_ns + shift)

        # Stable cross-API ctime difference is accepted, all content checks run.
        reader = m.BoundedArtifactReader(self.root, limits())
        with patch('os.fstat', side_effect=lambda fd: shifted(fd, 1000)):
            self.assertEqual(reader.read_json(ref), {'value': 1})
            self.assertEqual(reader.verify_unchanged()['files'], 1)
        self.assertEqual(reader.open_files, 0)

        # A change within the same handle API still poisons the operation.
        calls = []
        def changing(fd):
            calls.append(fd)
            return shifted(fd, len(calls))
        reader = m.BoundedArtifactReader(self.root, limits())
        with patch('os.fstat', side_effect=changing), self.assertRaisesRegex(ValueError, 'changed during read'):
            reader.read_json(ref)
        self.assertTrue(reader.failed)
        self.assertEqual(reader.open_files, 0)

    def test_all_nine_producer_headers_and_null_wire_strings(self):
        for candidate in m.REQUIRED_CANDIDATE_IDS:
            for kind in ('predictions', 'targets'):
                ref = self.csv(candidate, kind, name=candidate + '-' + kind + '.csv')
                with m.BoundedArtifactReader(self.root, limits()) as reader:
                    index = reader.index_csv(ref, candidate_id=candidate, kind=kind)
                    row = index.row(index.keys[0])
                    self.assertEqual(row['item_id'], 'q,quoted')
                    self.assertEqual(row['probability'] if kind == 'predictions' else row['correct'], '' if kind == 'predictions' else '1')
                    self.assertEqual(reader.open_files, 0)
                    self.assertEqual(reader.verify_unchanged()['index_entries'], 1)

    def test_duplicates_extra_headers_and_foreign_role_rejected(self):
        for ref in (self.csv(rows=[{}, {}], name='duplicate.csv'),
                    self.csv(fields=(*m.csv_fields('A0', 'predictions'), 'calibrated_probability'), name='extra.csv'),
                    self.csv(fields=(*m.csv_fields('A0', 'predictions'), 'probability'), name='duplicate-header.csv'),
                    self.csv(rows=[dict(origin_role='train')], name='foreign-role.csv')):
            with self.subTest(path=ref.path), self.assertRaises(ValueError):
                m.BoundedArtifactReader(self.root, limits()).index_csv(ref, candidate_id='A0', kind='predictions')

    def test_multiline_control_and_oversize_fields_rejected(self):
        for value in ('quoted\nnewline', 'control\tchar', 'x' * 2049):
            ref = self.csv(rows=[dict(item_id=value)])
            with self.subTest(value=value[:20]), self.assertRaises((ValueError, csv.Error)):
                m.BoundedArtifactReader(self.root, limits()).index_csv(ref, candidate_id='A0', kind='predictions')

    def test_sha_size_byte_and_index_limits_fail_before_acceptance(self):
        ref = self.put('metadata.json', b'{"x":1}')
        for changed in (replace(ref, sha256=H), replace(ref, size_bytes=ref.size_bytes + 1)):
            with self.subTest(ref=changed), self.assertRaises(ValueError):
                m.BoundedArtifactReader(self.root, limits()).read_json(changed)
        reader = m.BoundedArtifactReader(self.root, limits())
        reader.bytes_read = reader.limits.max_total_read_bytes
        with self.assertRaisesRegex(ValueError, 'before IO'):
            reader.read_json(ref)
        self.assertEqual(reader.open_files, 0)
        ref = self.csv(rows=[{}, dict(timestamp='200', source_row='2', global_rank='1')])
        with self.assertRaises(ValueError):
            m.BoundedArtifactReader(self.root, limits(max_csv_rows=1)).index_csv(ref, candidate_id='A0', kind='predictions')
        reader = m.BoundedArtifactReader(self.root, limits(max_index_entries=32))
        reader.index_entries = 32
        with self.assertRaises(ValueError):
            reader.index_csv(ref, candidate_id='A0', kind='predictions')

    def test_index_order_is_statistical_and_postread_tampering_rejected(self):
        ref = self.csv(rows=[dict(item_id='z'), dict(item_id='a', timestamp='200', source_row='2', global_rank='1')])
        reader = m.BoundedArtifactReader(self.root, limits())
        index = reader.index_csv(ref, candidate_id='A0', kind='predictions')
        self.assertEqual([key.item_id for key in index.keys], ['a', 'z'])
        self.assertEqual([row['global_rank'] for row in index.rows()], ['1', '0'])
        path = self.root / ref.path
        path.write_bytes(path.read_bytes().replace(b'oov_item', b'bad_item'))
        with self.assertRaises(ValueError):
            reader.verify_unchanged()
        self.assertEqual(reader.open_files, 0)

    def test_deadline_and_closed_reader_reject(self):
        ref = self.put('metadata.json', b'{}')
        with patch.object(m, '_now', return_value=100.):
            reader = m.BoundedArtifactReader(self.root, limits())
        with patch.object(m, '_now', return_value=106.), self.assertRaises(ValueError):
            reader.read_json(ref)
        reader = m.BoundedArtifactReader(self.root, limits())
        reader.close()
        with self.assertRaises(ValueError):
            reader.read_json(ref)


if __name__ == '__main__':
    unittest.main()
