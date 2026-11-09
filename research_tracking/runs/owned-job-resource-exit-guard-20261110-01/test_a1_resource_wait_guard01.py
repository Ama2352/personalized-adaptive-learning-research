"""Canaries thuần stdlib cho helper thật, không WinAPI/process/model."""
from collections import deque
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE=Path(__file__).with_name('check_a1_expert_engineering03.py')
spec=importlib.util.spec_from_file_location('a1_wait_guard_definitions',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
TICKS=134387324892686944
CREATED=(TICKS-116444736000000000)/10000000


class Fixture:
    def __init__(self, waits=(258,), failure=None, member=True, wrong_pid=False, wrong_time=False, exit_code=0):
        self.waits=deque(waits);self.last=waits[-1];self.wait_calls=0;self.member_calls=0
        self.failure=failure;self.member=member;self.exit_code=exit_code
        self.error=PermissionError('synthetic access denied');self.error.winerror=5
        self.api=SimpleNamespace(check=self.check,contains=self.contains,k=SimpleNamespace(
            GetProcessId=lambda h:124 if wrong_pid else 123,GetProcessTimes=self.times,
            WaitForSingleObject=self.wait,GetExitCodeProcess=self.exit))
        child=SimpleNamespace(create_time=lambda:self.value('psutil_creation',CREATED+int(wrong_time)),
            memory_info=lambda:self.value('rss',SimpleNamespace(rss=4096)))
        self.psutil=SimpleNamespace(Process=lambda pid:child,AccessDenied=type('FakeAccessDenied',(Exception,),{}),
            NoSuchProcess=type('FakeNoSuchProcess',(Exception,),{}))

    def value(self, phase, result):
        if self.failure==phase:raise self.error
        return result

    def contains(self,*unused):
        self.member_calls+=1
        return self.value('membership',self.member)

    def times(self,handle,creation,*unused):
        self.value('creation_identity',None)
        creation._obj.dwLowDateTime=TICKS&0xffffffff;creation._obj.dwHighDateTime=TICKS>>32
        return 1

    def wait(self,*unused):
        self.wait_calls+=1
        return self.waits.popleft() if self.waits else self.last

    def exit(self,handle,code):
        code._obj.value=self.exit_code;return 1

    def check(self,value):
        if not value:raise PermissionError('synthetic failed native wait/query')
        return value

    def sample(self):
        return module.sample_opened_resource_member(self.api,1,2,123,self.psutil)


class ResourceWaitGuardCanaries(unittest.TestCase):
    def test_live_success(self):
        f=Fixture();self.assertEqual(f.sample()['rss_bytes'],4096);self.assertEqual(f.member_calls,1)

    def test_exited_precheck_omits_rss_and_membership(self):
        f=Fixture((0,));row=f.sample();self.assertEqual(row['kind'],'exited');self.assertEqual(f.member_calls,0)

    def test_live_denied_rethrows_same_error(self):
        for phase in ('membership','creation_identity','psutil_creation','rss'):
            with self.subTest(phase=phase):
                f=Fixture((258,258),failure=phase)
                with self.assertRaises(PermissionError) as caught:f.sample()
                self.assertIs(caught.exception,f.error)

    def test_verified_exit_denied_logged(self):
        for phase in ('membership','creation_identity','psutil_creation','rss'):
            with self.subTest(phase=phase):
                f=Fixture((258,0),failure=phase);row=f.sample()
                self.assertEqual((row['kind'],row['wait'],row['phase']),('exited',0,phase))
                self.assertEqual(row['error']['winerror'],5);self.assertIn('synthetic access denied',row['error']['traceback'])

    def test_failed_and_unknown_wait_reject(self):
        for value,kind in ((0xffffffff,PermissionError),(17,ValueError)):
            with self.subTest(value=value):
                with self.assertRaises(kind):Fixture((value,)).sample()

    def test_denied_unknown_wait_keeps_original_error(self):
        for value in (0xffffffff,17):
            with self.subTest(value=value):
                f=Fixture((258,value),failure='membership')
                with self.assertRaises(PermissionError) as caught:f.sample()
                self.assertIs(caught.exception,f.error);self.assertIsNotNone(caught.exception.__cause__)

    def test_pid_and_creation_mismatch_never_masked(self):
        f=Fixture((0,),wrong_pid=True)
        with self.assertRaisesRegex(ValueError,'PID mismatch'):f.sample()
        self.assertEqual(f.wait_calls,0)
        f=Fixture((258,0),wrong_time=True)
        with self.assertRaisesRegex(ValueError,'creation identity'):f.sample()
        self.assertEqual(f.wait_calls,1)

    def test_false_membership_requires_verified_exit(self):
        with self.assertRaisesRegex(ValueError,'not in owned Job'):Fixture((258,258),member=False).sample()
        row=Fixture((258,0),member=False).sample();self.assertEqual(row['phase'],'membership_false')

    def test_signaled_exit259_is_not_live_timeout(self):
        row=Fixture((0,),exit_code=259).sample();self.assertEqual(row['exit_code'],259)


if __name__=='__main__':unittest.main()
