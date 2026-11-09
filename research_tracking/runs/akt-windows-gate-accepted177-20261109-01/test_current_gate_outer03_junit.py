"""Sáu fixtures cho fullouter03; không chạy Gate/test bodies/NN.

Chạy bởi ROOT sau review. Chỉ bộ đọc bytes được thay bằng payload trong RAM;
parser JUnit thật và kiểm exact identity trong outer03 giữ nguyên. Mapper identity
của fixture không chứng nhận mapping pytest thực, vốn được source-pin riêng.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
from types import SimpleNamespace
import unittest

PREP = Path(__file__).resolve().parent
ROOT = PREP.parents[3]
OUTER = PREP/'windows_current_gate_outer03.py'
OUTER_SHA = '4722088dadf1dc3e45203bb29c242e22d5d54bd66b4141f46b2ab8df28f64f3e'
NATIVE = ROOT/'scripts/akt/refresh_gate2.py'
NATIVE_SHA = '8689c5b4737f4eae00459f4a3bc85c22206f58974274304fa4411e36f9acc055'
PACKET = PREP/'windows_current_gate_packet04.ROOT.json'
PACKET_SHA = '85069ac16a591d022a85de661dcefaa2d8ed1b32e80f335ea129cd6bbc7bcb70'
XML_SHA = {
    'stdlib': '7dc25665255fdcc8286be9050f84d279aa6ccec6f498addb9d3acade400046e1',
    'no-torch': '9cc2456b8d7ade9a17991b916ef6aa0e66590a84fc2cba076dcbd81a4081b454',
    'remaining': 'effa078619fda455681ec490d7f9ef92bb6baccac87e068870898ec18d033a71',
}


def bounded_bytes(path, cap):
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    if len(raw) > cap:
        raise ValueError('bounded fixture input')
    return raw


def reference(ref):
    name = ref['path']
    if Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('relative pinned evidence only')
    path = ROOT/name
    if not path.is_relative_to(PREP):
        raise ValueError('existing preparation evidence only')
    raw = bounded_bytes(path,8*1024**2)
    if hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('historical reference changed')
    return path,json.loads(raw)


def load(path, expected, name):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('reviewed source changed')
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PhysicalJUnitItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outer = load(OUTER,OUTER_SHA,'fixture_fullouter03')
        cls.native = load(NATIVE,NATIVE_SHA,'fixture_native_junit')
        if any(name in sys.modules for name in ('torch','numpy')):
            raise AssertionError('stdlib fixture must not import Torch/NumPy')

    def parse(self, xml):
        payload = xml.encode('utf-8')
        original = getattr(self.outer,'bounded',None)
        def bytes_in_memory(path, cap):
            if len(payload) > cap:
                raise ValueError('bounded fixture payload')
            return payload
        self.outer.bounded = bytes_in_memory
        try:
            nodes = ['a','b']
            utility = SimpleNamespace(mangle_test_address=lambda value: ['fixture',value],
                                      bin_xml_escape=lambda value: value)
            pinned = [dict(classname='fixture',name=name) for name in nodes]
            return self.outer.read_junit(PREP/'not_read_fixture.xml',nodes,utility,pinned,self.native)
        finally:
            if original is None:
                del self.outer.bounded
            else:
                self.outer.bounded = original

    def test_actual_three_immutable_old_shards_exact_ids(self):
        from _pytest import junitxml as utility
        import xml.etree.ElementTree as ET
        self.assertEqual(Path(utility.__file__).resolve(),self.outer.JUNIT.resolve())
        self.assertEqual(hashlib.sha256(self.outer.JUNIT.read_bytes()).hexdigest(),self.outer.JUNIT_SHA)
        raw = bounded_bytes(PACKET,2*1024**2)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),PACKET_SHA)
        packet = json.loads(raw)
        final_path,final = reference(packet['collection_result'])
        self.assertEqual(final['status'],'ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS')
        physical,declared = 0,0
        unchanged = {PACKET:PACKET_SHA,final_path:packet['collection_result']['sha256']}
        original = getattr(self.outer,'bounded',None)
        self.outer.bounded = bounded_bytes
        try:
            for stage in final['stages']:
                name = stage['group']
                child_path,child = reference(dict(path=stage['child_result_relative'],
                                                sha256=stage['child_result_sha256']))
                unchanged[child_path] = stage['child_result_sha256']
                path = ROOT/'artifacts/akt/preflight'/f'gate2-tests-win-current-gate-20261109-04-{name}.xml'
                xml = bounded_bytes(path,32*1024**2)
                self.assertEqual(hashlib.sha256(xml).hexdigest(),XML_SHA[name])
                unchanged[path] = XML_SHA[name]
                result = self.outer.read_junit(path,child['nodeids'],utility,
                                              packet['expected_JUnit_ids'][name],self.native)
                self.assertEqual(result['counts']['tests'],packet['expected_native_counts'][name])
                physical += result['counts']['tests']
                declared += sum(int(suite.get('tests')) for suite in ET.fromstring(xml).iter('testsuite'))
            self.assertEqual(physical,1726)
            self.assertEqual(declared,1791)
            for path,digest in unchanged.items():
                self.assertEqual(hashlib.sha256(bounded_bytes(path,8*1024**2)).hexdigest(),digest)
            self.assertFalse(any(name in sys.modules for name in ('torch','numpy')))
            print(json.dumps(dict(kind='HISTORICAL_XML_PARSER_CHECK_NOT_GATE_ACCEPTANCE',
                                  physical_items=physical,raw_tests_attributes=declared,
                                  old_gate04_remains_rejected=True)))
        finally:
            if original is None:
                del self.outer.bounded
            else:
                self.outer.bounded = original

    def test_successful_subtests_surplus_counts_physical_items(self):
        result = self.parse('<testsuites><testsuite tests="67" failures="0" errors="0" skipped="0">'
                            '<testcase classname="fixture" name="a"/>'
                            '<testcase classname="fixture" name="b"/></testsuite></testsuites>')
        self.assertEqual(result['counts'],dict(tests=2,failures=0,errors=0,skipped=0))
        self.assertEqual(result['identities'],[('fixture','a'),('fixture','b')])

    def test_hidden_failure_rejected_despite_zero_count_attributes(self):
        for tag in ('failure','error','skipped'):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.parse('<testsuite tests="67" failures="0" errors="0" skipped="0">'
                           '<testcase classname="fixture" name="a"><'+tag+'/></testcase>'
                           '<testcase classname="fixture" name="b"/></testsuite>')

    def test_missing_case_rejected_despite_declared_surplus(self):
        with self.assertRaises(ValueError):
            self.parse('<testsuite tests="67" failures="0" errors="0" skipped="0">'
                       '<testcase classname="fixture" name="a"/></testsuite>')

    def test_duplicate_case_rejected(self):
        with self.assertRaises(ValueError):
            self.parse('<testsuite tests="67" failures="0" errors="0" skipped="0">'
                       '<testcase classname="fixture" name="a"/>'
                       '<testcase classname="fixture" name="a"/></testsuite>')

    def test_tampered_count_attributes_rejected(self):
        for tests in ('1','-1','1.0','true',''):
            with self.subTest(tests=tests),self.assertRaises(ValueError):
                self.parse('<testsuite tests="'+tests+'" failures="0" errors="0" skipped="0">'
                           '<testcase classname="fixture" name="a"/>'
                           '<testcase classname="fixture" name="b"/></testsuite>')


if __name__ == '__main__':
    unittest.main(verbosity=2)
