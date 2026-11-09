"""ROOT-only four stdlib canaries of actual AST predicate; no open sink/child/NN."""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

WORKER=Path(__file__).with_name('check_colab_contract_inventory02.py')
if len(sys.argv)!=2:raise ValueError('ROOT-reviewed worker SHA argument required')
raw=WORKER.read_bytes()
if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise ValueError('worker bytes changed')
functions=[node for node in ast.parse(raw,filename=str(WORKER)).body
           if isinstance(node,ast.FunctionDef) and node.name=='allow_metadata_devnull']
if len(functions)!=1:raise ValueError('exact one reviewed predicate')
namespace={'os':os}
exec(compile(ast.Module(body=functions,type_ignores=[]),str(WORKER),'exec'),namespace)
allow=namespace['allow_metadata_devnull']


class NullSinkGuardTests(unittest.TestCase):
    def check(self,path=None,mode=None,flags=None,phase='windows_metadata',count=0):
        return allow(os.devnull if path is None else path,mode,os.O_RDWR if flags is None else flags,
                     phase=phase,allowed_count=count)

    def test_exact_os_open_and_noninherit_bits_only(self):
        self.assertTrue(self.check())
        harmless=getattr(os,'O_NOINHERIT',0)|getattr(os,'O_CLOEXEC',0)
        self.assertTrue(self.check(flags=os.O_RDWR|harmless))

    def test_no_normalization_alias_bytes_or_source_path(self):
        for path in (os.devnull.upper(),str(Path(os.devnull).absolute()),os.fsencode(os.devnull),
                     'nul.txt','source.py','./'+os.devnull):
            with self.subTest(path=repr(path)):
                self.assertFalse(self.check(path=path))

    def test_access_mode_creation_truncation_append_unknown_flags_denied(self):
        for flags in (0,os.O_WRONLY,True,os.O_RDWR|os.O_CREAT,os.O_RDWR|os.O_TRUNC,
                      os.O_RDWR|os.O_APPEND,os.O_RDWR|(1<<29)):
            with self.subTest(flags=flags):self.assertFalse(self.check(flags=flags))
        for mode in ('w','a','r+b','r+'):
            with self.subTest(mode=mode):self.assertFalse(self.check(mode=mode))

    def test_phase_and_bounded_count_not_reusable_later(self):
        self.assertTrue(self.check(count=2))
        for count in (-1,3,True):
            with self.subTest(count=count):self.assertFalse(self.check(count=count))
        for phase in ('inventory_tests_no_subprocess','windows_metadata_later',''):
            with self.subTest(phase=phase):self.assertFalse(self.check(phase=phase))


suite=unittest.defaultTestLoader.loadTestsFromTestCase(NullSinkGuardTests)
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps(dict(kind='FOUR_STDLIB_AST_NULL_SINK_GUARD_CASES_NOT_NATIVE',tests=result.testsRun,
    failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),worker_sha256=sys.argv[1])))
raise SystemExit(0 if result.wasSuccessful() and result.testsRun==4 else 1)
