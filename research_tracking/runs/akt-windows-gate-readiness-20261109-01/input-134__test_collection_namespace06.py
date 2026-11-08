"""Kiểm biên namespace thuần Python; không Kernel, Torch hoặc collection."""
from pathlib import Path
import importlib.util
import unittest

path = Path(__file__).with_name('gate_collection_worker06.py')
spec = importlib.util.spec_from_file_location('collection_namespace06_checks',path)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class NamespaceAdmission(unittest.TestCase):
    def fixture(self):
        result = {}
        for name in ('scripts','scripts.akt','scripts.research'):
            paths = [str(worker.ROOT/Path(*name.split('.')))]
            if name == 'scripts':
                paths.append(str(worker.ROOT/'.venv/Lib/site-packages/win32/scripts'))
            result[name] = dict(file=None,origin=None,namespace_paths=paths,spec_search_paths=list(paths))
        return result

    def reject(self,packages):
        with self.assertRaises(ValueError):
            worker.validate_scripts_namespace(packages)

    def test_verified_parent_namespace_with_exact_project_children(self):
        worker.validate_scripts_namespace(self.fixture())

    def test_foreign_project_child_is_rejected(self):
        value = self.fixture()
        value['scripts.akt']['namespace_paths'].append(str(worker.ROOT/'.venv/Lib/site-packages/win32/scripts/akt'))
        self.reject(value)

    def test_foreign_parent_namespace_is_rejected(self):
        value = self.fixture()
        for key in ('namespace_paths','spec_search_paths'):
            value['scripts'][key].append(str(worker.ROOT/'artifacts/scripts'))
        self.reject(value)

    def test_project_root_must_precede_installed_namespace(self):
        value = self.fixture()
        for key in ('namespace_paths','spec_search_paths'):
            value['scripts'][key].reverse()
        self.reject(value)

    def test_shadowing_package_file_is_rejected(self):
        value = self.fixture()
        value['scripts.akt']['file'] = str(worker.ROOT/'artifacts/scripts/akt/__init__.py')
        self.reject(value)

    def test_missing_project_child_is_rejected(self):
        value = self.fixture()
        del value['scripts.research']
        self.reject(value)


if __name__ == '__main__':
    unittest.main()
