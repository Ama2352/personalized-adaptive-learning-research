"""Một suite pure synthetic Windows;0native/model/collector/GPU/remote."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/research'))
import windows_owned_worker as helper

WORKER_TEXT='''import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/research'))
import windows_owned_worker as helper
gate=helper.worker_gate()
attempt=Path(os.environ['KLTN_WINDOWS_LAUNCH_MANIFEST']).parent
mode=sys.argv[1]
result={'mode':mode,'gate':gate,'forbidden': [n for n in helper.FORBIDDEN if n in sys.modules]}
if mode=='descendant':
 child=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(4)'],stdin=subprocess.DEVNULL,
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
  creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP)
 api=helper.Kernel();result['descendant']=api.token(int(child._handle))
 job=api.check(api.k.OpenJobObjectW(4,False,gate['job_name']))
 try:result['descendant_in_job']=api.contains(int(child._handle),job)
 finally:api.close(job)
if mode=='timeout':time.sleep(4)
with (attempt/'body.json').open('x',encoding='utf-8') as f:
 json.dump(result,f);f.flush();os.fsync(f.fileno())
print(json.dumps({'mode':mode,'native_model_calls':0}))
'''


class LauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker=PREP/'synthetic_worker.py'
        with cls.worker.open('x',encoding='utf-8') as handle:handle.write(WORKER_TEXT)
        cls.worker_sha=hashlib.sha256(cls.worker.read_bytes()).hexdigest()

    def test_ready_nonce_source_command_entry_and_token_negatives(self):
        token=dict(pid=999,created_filetime_100ns='123',create_time=1.,image=str(ROOT/'.venv/Scripts/python.exe'))
        manifest=dict(nonce='a'*64,entry=str(ROOT/'.venv/Scripts/python.exe'),worker_sha256='b'*64,
                      helper_sha256='c'*64,worker_args=['normal'])
        ready=dict(schema_version=1,nonce=manifest['nonce'],worker=token,parent_pid=99,
            entry=manifest['entry'],prefix=str(ROOT/'.venv'),worker_sha256='b'*64,helper_sha256='c'*64,
            argv_sha256=helper.digest(helper.canonical(['normal'])),forbidden_imports=[])
        helper.validate_ready(ready,manifest,token)
        for field,value in [('nonce','0'*64),('worker',{**token,'pid':998}),('prefix',str(ROOT)),
                            ('worker_sha256','d'*64),('helper_sha256','d'*64),('argv_sha256','d'*64),
                            ('forbidden_imports',['torch']),('schema_version',True)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                helper.validate_ready({**ready,field:value},manifest,token)

    def test_unknown_provisional_handle_closed_without_registration_or_termination(self):
        parent_token=dict(pid=10,create_time=1.,created_filetime_100ns='100',image='C:\\python.exe')
        child_token=dict(pid=11,create_time=2.,created_filetime_100ns='200',image='C:\\python.exe')
        parent=dict(handle=100,token=parent_token)
        snapshot=dict(pid=11,parent_pid=10,create_time=2.)
        api=SimpleNamespace(open=mock.Mock(return_value=200),close=mock.Mock(),
            token=mock.Mock(return_value={**child_token,'create_time':99.}),
            k=SimpleNamespace(TerminateProcess=mock.Mock()))
        registry={10:parent}
        with self.assertRaisesRegex(ValueError,'creation time changed'):
            helper.provisional_descendant(api,snapshot,parent,{helper.norm('C:\\python.exe')},mock.Mock())
        api.close.assert_called_once_with(200)
        api.k.TerminateProcess.assert_not_called()
        self.assertEqual(set(registry),{10})

    def test_provisional_ancestry_change_never_becomes_owned(self):
        token=dict(pid=11,create_time=2.,created_filetime_100ns='200',image='C:\\python.exe')
        parent=dict(handle=100,token=dict(pid=10,create_time=1.))
        api=SimpleNamespace(open=mock.Mock(return_value=200),token=mock.Mock(return_value=token),close=mock.Mock(),
                            k=SimpleNamespace(TerminateProcess=mock.Mock()))
        lookup=lambda pid:SimpleNamespace(create_time=lambda:2.,ppid=lambda:999)
        with self.assertRaisesRegex(ValueError,'ancestry changed'):
            helper.provisional_descendant(api,dict(pid=11,parent_pid=10,create_time=2.),parent,
                                          {helper.norm('C:\\python.exe')},lookup)
        api.close.assert_called_once_with(200);api.k.TerminateProcess.assert_not_called()

    def test_path_traversal_and_root_alias_rejected(self):
        for path in [ROOT/'artifacts/../dataset',ROOT.parent/'outside',Path('relative')]:
            with self.subTest(path=str(path)),self.assertRaises(ValueError):helper.safe(path)
        original=Path.is_symlink
        with mock.patch.object(Path,'is_symlink',lambda p:p==ROOT or original(p)),self.assertRaises(ValueError):
            helper.safe(ROOT/'artifacts')

    def test_source_drift_rejected_before_any_kernel_or_process_even_with120s_cap(self):
        target=PREP/'preflight-rejected'
        with mock.patch.object(helper,'Kernel',side_effect=AssertionError('no kernel')), \
             mock.patch.object(helper.subprocess,'Popen',side_effect=AssertionError('no process')):
            result=helper.run_owned(self.worker,['normal'],target,expected_worker_sha256='0'*64,
                approval_reference='PURE_SOURCE_NEGATIVE_NOT_AUTHORITY',max_seconds=120,
                cleanup_reserve_seconds=3,max_output_bytes=4096)
        self.assertFalse(result['accepted']);self.assertFalse(target.exists())
        self.assertIn('worker source SHA mismatch',result['errors'][0]['message'])

    def test_z_one_sequential_actual_windows_normal_descendant_timeout(self):
        # If first real Job launch is blocked, assertion stops all later real launches.
        def run(mode,cap,reserve):
            result=helper.run_owned(self.worker,[mode],PREP/('actual-'+mode),
                expected_worker_sha256=self.worker_sha,approval_reference='ROOT_REVIEWED_PURE_SYNTHETIC20_NO_NATIVE',
                max_seconds=cap,cleanup_reserve_seconds=reserve,max_output_bytes=16384)
            with (PREP/('receipt-'+mode+'.json')).open('x',encoding='utf-8') as handle:
                json.dump(result,handle,ensure_ascii=False,indent=2);handle.write('\n')
            return result
        normal=run('normal',5,2)
        self.assertTrue(normal['accepted'],normal)
        self.assertTrue(normal['actual_worker_in_job_before_GO'] and normal['GO_released'])
        self.assertTrue(normal['cleanup_accepted'] and normal['popen_handle_closed'])
        self.assertEqual(normal['job_active_after_cleanup'],0)
        marker=json.loads((PREP/'actual-normal/body.json').read_bytes())
        self.assertEqual(marker['forbidden'],[])
        descendant=run('descendant',5,2)
        self.assertTrue(descendant['accepted'],descendant)
        marker=json.loads((PREP/'actual-descendant/body.json').read_bytes())
        self.assertTrue(marker['descendant_in_job'])
        self.assertEqual(descendant['worker_returncode_before_cleanup'],0)
        self.assertGreater(descendant['job_active_before_cleanup'],0)
        self.assertEqual(descendant['job_active_after_cleanup'],0)
        timeout=run('timeout',2,1)
        self.assertFalse(timeout['accepted'])
        self.assertTrue(timeout['GO_released'] and timeout['cleanup_accepted'] and timeout['popen_handle_closed'])
        self.assertEqual(timeout['job_active_after_cleanup'],0)
        self.assertFalse((PREP/'actual-timeout/body.json').exists())
        self.assertTrue(any(e['type']=='TimeoutError' for e in timeout['errors']))


if __name__=='__main__':
    unittest.main(verbosity=2)
