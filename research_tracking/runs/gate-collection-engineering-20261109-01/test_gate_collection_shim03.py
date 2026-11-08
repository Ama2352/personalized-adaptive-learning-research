"""Pure identity predicates only; không Kernel/Job/Popen/collection/native call."""
import copy
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).with_name('gate_collection_worker03.py')
spec = importlib.util.spec_from_file_location('gate_collection_shim03_pure', SOURCE)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)  # Definitions only; main/worker_gate not called.


class NativeShimPredicates(unittest.TestCase):
    def fixture(self):
        entry = str(worker.ROOT/'.venv/Scripts/python.exe')
        observed = dict(expected_shim_entry=entry, shim_pid=20, shim_ppid=10,
            shim_create_time=2., shim_exe=entry[2:],
            owner=dict(os_parent_pid=20,
                parent_owner=dict(pid=10, create_time=1., created_filetime_100ns='100'),
                worker=dict(pid=30, create_time=3., created_filetime_100ns='300')))
        token = dict(pid=20, image=entry, create_time=2., created_filetime_100ns='200')
        return observed, token, copy.deepcopy(token)

    def accepted(self, observed, before, after, in_job=True):
        return all(worker.validate_native_shim(observed, before, after, in_job).values())

    def test_full_native_identity_accepts_missing_drive_psutil_diagnostic(self):
        observed, before, after = self.fixture()
        self.assertFalse(Path(observed['shim_exe']).drive)
        self.assertTrue(self.accepted(observed, before, after))

    def test_wrong_native_drive_rejected(self):
        observed, before, after = self.fixture()
        other = 'E:' if Path(before['image']).drive.upper() != 'E:' else 'F:'
        before['image'] = after['image'] = other+before['image'][2:]
        self.assertFalse(self.accepted(observed, before, after))

    def test_wrong_native_path_rejected(self):
        observed, before, after = self.fixture()
        before['image'] = after['image'] = str(worker.ROOT/'venv/Scripts/python.exe')
        self.assertFalse(self.accepted(observed, before, after))

    def test_wrong_native_pid_rejected(self):
        observed, before, after = self.fixture()
        before['pid'] = after['pid'] = 21
        self.assertFalse(self.accepted(observed, before, after))

    def test_native_ctime_changed_rejected(self):
        observed, before, after = self.fixture()
        after['created_filetime_100ns'] = '201'
        self.assertFalse(self.accepted(observed, before, after))

    def test_native_ctime_outside_parent_worker_bounds_rejected(self):
        observed, before, after = self.fixture()
        before['created_filetime_100ns'] = after['created_filetime_100ns'] = '99'
        self.assertFalse(self.accepted(observed, before, after))

    def test_not_exact_owned_job_rejected(self):
        observed, before, after = self.fixture()
        self.assertFalse(self.accepted(observed, before, after, False))

    def test_original_ppid_and_time_order_still_required(self):
        observed, before, after = self.fixture()
        observed['shim_ppid'] = 11
        self.assertFalse(self.accepted(observed, before, after))
        observed['shim_ppid'] = 10
        observed['shim_create_time'] = 4.
        self.assertFalse(self.accepted(observed, before, after))


if __name__ == '__main__':
    unittest.main()
