"""Virtual-only cleanup calls + immediate-finally structure, không Popen thật."""
import ast
import copy
from pathlib import Path
import types
import unittest

SOURCE=Path(__file__).parent/'post_install_audit01.py'
TREE=ast.parse(SOURCE.read_bytes())
MAIN=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='main')
FUNCTION=next(n for n in MAIN.body if isinstance(n,ast.FunctionDef) and n.name=='cleanup_once')
class BoundGlobals(ast.NodeTransformer):
    def visit_Nonlocal(self,node):return ast.Global(names=node.names)
FUNCTION=BoundGlobals().visit(copy.deepcopy(FUNCTION))
class Timeout(Exception):pass
class Proc:
    pid=991
    def wait(self,timeout):return 0
    def poll(self):return 0


class CleanupTests(unittest.TestCase):
    def make(self,process=None,kill=None):
        calls=[]
        if kill is None:kill=lambda pgid,sig:calls.append((pgid,sig.name))
        ns={'process':Proc() if process is None else process,'cleanup_attempted':False,'cleanup_ok':False,
            'cleanup':[],'result':{},'os':types.SimpleNamespace(getpgrp=lambda:777,killpg=kill),
            'signal':types.SimpleNamespace(SIGTERM=types.SimpleNamespace(name='SIGTERM'),SIGKILL=types.SimpleNamespace(name='SIGKILL')),
            'subprocess':types.SimpleNamespace(TimeoutExpired=Timeout)}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(FUNCTION)],type_ignores=[])),str(SOURCE),'exec'),ns)
        return ns,calls
    def test_once_only(self):
        ns,calls=self.make();ns['cleanup_once']();ns['cleanup_once']()
        self.assertEqual(len(calls),2);self.assertTrue(ns['cleanup_ok']);self.assertEqual(ns['result']['child_returncode'],0)
    def test_signal_error_blocks_and_no_resignal(self):
        calls=[]
        def denied(*args):calls.append(args);raise PermissionError('synthetic')
        ns,_=self.make(kill=denied);ns['cleanup_once']();ns['cleanup_once']()
        self.assertFalse(ns['cleanup_ok']);self.assertEqual(len(calls),2)
    def test_absent_group_is_clean(self):
        def absent(*args):raise ProcessLookupError()
        ns,_=self.make(kill=absent);ns['cleanup_once']();self.assertTrue(ns['cleanup_ok'])
    def test_own_group_refused(self):
        process=Proc();process.pid=777;ns,calls=self.make(process);ns['cleanup_once']()
        self.assertFalse(ns['cleanup_ok']);self.assertEqual(calls,[])
    def test_reap_timeout_blocks(self):
        class Stuck(Proc):
            def wait(self,timeout):raise Timeout()
        ns,_=self.make(Stuck());ns['cleanup_once']();self.assertFalse(ns['cleanup_ok'])
    def test_no_process_no_signal(self):
        ns,calls=self.make();ns['process']=None;ns['cleanup_once']()
        self.assertFalse(ns['cleanup_attempted']);self.assertFalse(ns['cleanup_ok']);self.assertEqual(calls,[])
    def test_immediate_child_finally_and_outer_fallback(self):
        tries=[n for n in ast.walk(MAIN) if isinstance(n,ast.Try) and any(isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name) and x.value.func.id=='cleanup_once' for x in n.finalbody)]
        self.assertEqual(len(tries),2)
        child=next(n for n in tries if len(n.finalbody)==1)
        self.assertTrue(any(isinstance(n,ast.While) for n in child.body))
        final_accept=next(n for n in ast.walk(MAIN) if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp) and ast.unparse(n.test)=='candidate and cleanup_ok and resource_ok')
        self.assertTrue(final_accept.body)


if __name__=='__main__':unittest.main(verbosity=2)
