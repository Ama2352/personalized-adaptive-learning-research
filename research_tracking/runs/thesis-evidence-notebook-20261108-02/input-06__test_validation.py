"""Kiểm guard/schema/rerender; không kernel hoặc sửa notebook trong tests."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest import mock
import test_integrity as race

ROOT=race.ROOT


class ValidationTests(unittest.TestCase):
    def test_verified_inventory_and_existing_pointer_and_html_guards(self):
        helpers=race.builder()
        verified=helpers['load_verified_evidence'](ROOT)
        self.assertEqual(tuple(verified[k] for k in ('verified_inputs','verified_claims','verified_pointers')),(28,14,104))
        self.assertEqual(helpers['json_pointer']({'a/b':[{'~':7}]},'/a~1b/0/~0'),7)
        self.assertNotIn('<script>',helpers['table'](['x'],[['<script>unsafe</script>']]))
        with self.assertRaises(ValueError):
            helpers['resolve_repository_file'](ROOT,'../outside.json')

    def test_single_payload_rejects_sha_and_byte_length_drift(self):
        helpers=race.builder()
        payload=b'{}'
        digest=hashlib.sha256(payload).hexdigest()
        path=mock.Mock()
        path.read_bytes.return_value=payload
        self.assertEqual(helpers['verified_bytes'](path,digest,expected_bytes=2),payload)
        path.read_bytes.assert_called_once_with()
        for expected,length in [('0'*64,2),(digest,3)]:
            with self.assertRaisesRegex(ValueError,'SHA/size'):
                helpers['verified_bytes'](path,expected,expected_bytes=length)

    def test_source_map_wrong_expected_sha_rejected(self):
        helpers=race.builder()
        helpers['MAP_SHA256']='0'*64
        with self.assertRaisesRegex(ValueError,'source-map drift'):
            helpers['load_verified_evidence'](ROOT)

    def test_seven_cells_rerender_identical_cached_outputs_and_subset_schema(self):
        helpers=race.builder()
        notebook=helpers['make_notebook'](ROOT)
        helpers['execute_report_cells'](notebook)
        old=json.loads((ROOT/'notebooks/thesis_evidence_report.ipynb').read_bytes())
        self.assertEqual([c.get('outputs') for c in notebook['cells']], [c.get('outputs') for c in old['cells']])
        self.assertEqual((notebook['nbformat'],notebook['nbformat_minor'],len(notebook['cells'])),(4,5,14))
        self.assertEqual(len({c['id'] for c in notebook['cells']}),14)
        self.assertEqual([c['execution_count'] for c in notebook['cells'] if c['cell_type']=='code'],list(range(1,8)))

    def test_v1_replacement_checks_all_seven_archive_outputs_without_writes(self):
        helpers=race.builder()
        target=ROOT/'notebooks/thesis_evidence_report.ipynb'
        payload,record=helpers['verify_v1_replacement'](ROOT,target,helpers['V1_NOTEBOOK_SHA256'])
        self.assertEqual(hashlib.sha256(payload).hexdigest(),helpers['V1_NOTEBOOK_SHA256'])
        self.assertEqual(len(record['verified_v1_outputs']),7)

    def test_replacement_rejects_other_sha_or_other_generated_path(self):
        helpers=race.builder()
        target=ROOT/'notebooks/thesis_evidence_report.ipynb'
        for candidate,digest in [(target,'0'*64),(target.with_name('other.ipynb'),helpers['V1_NOTEBOOK_SHA256'])]:
            with self.assertRaisesRegex(ValueError,'exact reviewed V1'):
                helpers['verify_v1_replacement'](ROOT,candidate,digest)

    def test_archive_corruption_stops_replacement_before_publication(self):
        helpers=race.builder()
        corrupt=ROOT/'research_tracking/runs/thesis-evidence-notebook-20261108-01/build01.log'
        original=Path.read_bytes
        def read(candidate,*args,**kwargs):
            return b'corrupted' if candidate==corrupt else original(candidate,*args,**kwargs)
        with mock.patch.object(Path,'read_bytes',read),self.assertRaisesRegex(ValueError,'V1 archive output mismatch'):
            helpers['verify_v1_replacement'](ROOT,ROOT/'notebooks/thesis_evidence_report.ipynb',helpers['V1_NOTEBOOK_SHA256'])

    def test_cli_required_replacement_flag_reaches_exact_guard(self):
        helpers=race.builder()
        captured=[]
        def stop(root,target,expected):
            captured.append((root,target,expected))
            raise ValueError('contract-stop-before-render-or-write')
        with mock.patch.dict(helpers,verify_v1_replacement=stop),self.assertRaisesRegex(ValueError,'contract-stop'):
            helpers['main'](['--replace-generated-sha256',helpers['V1_NOTEBOOK_SHA256']])
        self.assertEqual(captured,[(ROOT,ROOT/'notebooks/thesis_evidence_report.ipynb',helpers['V1_NOTEBOOK_SHA256'])])

    def test_notebook_rejects_builder_drift_before_exec(self):
        helpers=race.builder()
        notebook=helpers['make_notebook'](ROOT)
        cell=compile(''.join(notebook['cells'][1]['source']),'first-cell','exec')
        original=Path.read_bytes
        def read(candidate,*args,**kwargs):
            payload=original(candidate,*args,**kwargs)
            return payload+b'\n# changed' if candidate==race.SCRIPT else payload
        with (mock.patch.object(Path,'read_bytes',read),redirect_stdout(io.StringIO()),
              self.assertRaisesRegex(RuntimeError,'Builder đã thay đổi')):
            exec(cell,{})


def load_tests(loader,tests,pattern):
    tests.addTests(loader.loadTestsFromTestCase(race.IntegrityTests))
    return tests


if __name__=='__main__':
    unittest.main(verbosity=2)
