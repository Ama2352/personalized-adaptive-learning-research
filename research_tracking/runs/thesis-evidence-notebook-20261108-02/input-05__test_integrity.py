"""Canary payload race: mock thay read thứhai, không đổi artifact lịch sử."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[4]
SCRIPT=ROOT/'scripts/research/build_thesis_evidence_notebook.py'

def builder():
    namespace={'__name__':'integrity_test_builder','__file__':str(SCRIPT)}
    payload=SCRIPT.read_bytes()
    exec(compile(payload,str(SCRIPT),'exec'),namespace)
    return namespace


class IntegrityTests(unittest.TestCase):
    def assert_single_payload_json(self,relative,cache_key=None):
        helpers=builder()
        path=ROOT/relative
        actual=path.read_bytes()
        changed=json.loads(actual)
        changed['__unverified_race__']=True
        text_reads=[];byte_reads=[]
        original_text=Path.read_text;original_bytes=Path.read_bytes
        def read_text(candidate,*args,**kwargs):
            if candidate==path:
                text_reads.append(str(candidate))
                return json.dumps(changed)
            return original_text(candidate,*args,**kwargs)
        def read_bytes(candidate,*args,**kwargs):
            if candidate==path:
                byte_reads.append(str(candidate))
                return actual
            return original_bytes(candidate,*args,**kwargs)
        with mock.patch.object(Path,'read_text',read_text),mock.patch.object(Path,'read_bytes',read_bytes):
            verified=helpers['load_verified_evidence'](ROOT)
        value=verified['cache'][cache_key] if cache_key else verified['source_map']
        self.assertNotIn('__unverified_race__',value)
        self.assertEqual(text_reads,[])
        self.assertEqual(len(byte_reads),1)

    def test_source_map_uses_hashed_payload(self):
        self.assert_single_payload_json(builder()['MAP_PATH'])

    def test_cached_input_uses_hashed_payload(self):
        name='research_tracking/runs/cpu-rq1-transitions-20261108-01/analysis.json'
        self.assert_single_payload_json(name,name)

    def test_notebook_executes_exact_verified_builder_payload(self):
        helpers=builder()
        notebook=helpers['make_notebook'](ROOT)
        cell=compile(''.join(notebook['cells'][1]['source']),'first-notebook-cell','exec')
        expected=SCRIPT.read_bytes()
        original_compile=compile
        compiled=[]
        def check_compile(source,filename,*args,**kwargs):
            if str(filename)==str(SCRIPT):
                self.assertIsInstance(source,bytes)
                self.assertEqual(source,expected)
                compiled.append(hashlib.sha256(source).hexdigest())
            return original_compile(source,filename,*args,**kwargs)
        namespace={}
        with (mock.patch('runpy.run_path',side_effect=AssertionError('unverified second builder read')),
                mock.patch('builtins.compile',check_compile),redirect_stdout(io.StringIO())):
            exec(cell,namespace)
        self.assertEqual(len(compiled),1)
        self.assertEqual(namespace['verified']['verified_inputs'],28)


if __name__=='__main__':
    unittest.main(verbosity=2)
