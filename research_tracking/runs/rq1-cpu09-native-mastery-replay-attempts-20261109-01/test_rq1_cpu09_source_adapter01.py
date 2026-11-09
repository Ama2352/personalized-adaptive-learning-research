"""Năm canary stdlib trên nguồn dựng tay, không import project/model thật."""

import hashlib
import importlib.machinery
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import worker_rq1_cpu09_native_mastery03 as worker


MODULE_PATHS = {
    'knowledge_tracing': 'src/knowledge_tracing/__init__.py',
    'knowledge_tracing.akt': 'src/knowledge_tracing/akt/__init__.py',
    'knowledge_tracing.akt.resources': 'src/knowledge_tracing/akt/resources.py',
    'knowledge_tracing.gam_kt': 'src/knowledge_tracing/gam_kt/__init__.py',
    'knowledge_tracing.paper2_reference': 'src/knowledge_tracing/paper2_reference.py',
    'knowledge_tracing.gam_kt.simulator_pathways': 'src/knowledge_tracing/gam_kt/simulator_pathways.py',
}
MISSING = object()


class SourceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.saved_modules = {name: sys.modules.get(name, MISSING) for name in MODULE_PATHS}
        self.saved_attributes = []
        for name in MODULE_PATHS:
            parent, _, child = name.rpartition('.')
            if parent and parent in sys.modules:
                module = sys.modules[parent]
                self.saved_attributes.append((module, child, getattr(module, child, MISSING)))
        for name in reversed(MODULE_PATHS):
            sys.modules.pop(name, None)
        self.temp = tempfile.TemporaryDirectory(prefix='cpu09-source-adapter-', dir=worker.PREP)
        self.root = Path(self.temp.name).resolve()
        self.patcher = patch.object(worker, 'ROOT', self.root)
        self.patcher.start()
        self.records = []
        for name, relative in MODULE_PATHS.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if name == 'knowledge_tracing.akt.resources':
                source = ('from __future__ import annotations\n'
                          'from dataclasses import dataclass\n'
                          'import sys\n'
                          '@dataclass\n'
                          'class Marker:\n'
                          '    value: int = 37\n'
                          'MODULE_SEEN_DURING_EXEC = sys.modules[__name__]\n')
            else:
                source = 'FIXTURE_ONLY = True\n'
            path.write_text(source, encoding='utf-8')

    def tearDown(self):
        for name in reversed(MODULE_PATHS):
            sys.modules.pop(name, None)
        for name, module in self.saved_modules.items():
            if module is not MISSING:
                sys.modules[name] = module
        for module, child, value in self.saved_attributes:
            if value is MISSING:
                if hasattr(module, child):
                    delattr(module, child)
            else:
                setattr(module, child, value)
        self.patcher.stop()
        self.temp.cleanup()
        self.assertTrue(all(sys.modules.get(name, MISSING) is value for name, value in self.saved_modules.items()))
        self.assertTrue(all(getattr(module, child, MISSING) is value for module, child, value in self.saved_attributes))

    def pin(self, name):
        raw = (self.root / MODULE_PATHS[name]).read_bytes()
        return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def load(self, name):
        return worker.load_pinned_project_source(name, self.pin(name), self.records)

    def test_exact_source_body_real_metadata_registration_and_no_get_code(self):
        original_get_code = importlib.machinery.SourceFileLoader.get_code
        def guard_project_get_code(loader, name):
            if name in MODULE_PATHS:
                raise AssertionError('project PYC loader invoked')
            return original_get_code(loader, name)
        with patch.object(importlib.machinery.SourceFileLoader, 'get_code', new=guard_project_get_code):
            root = self.load('knowledge_tracing')
            akt = self.load('knowledge_tracing.akt')
            module = self.load('knowledge_tracing.akt.resources')
            gam = self.load('knowledge_tracing.gam_kt')
            reference = self.load('knowledge_tracing.paper2_reference')
            pathways = self.load('knowledge_tracing.gam_kt.simulator_pathways')
        self.assertIs(root.akt, akt)
        self.assertIs(akt.resources, module)
        self.assertIs(root.gam_kt, gam)
        self.assertIs(root.paper2_reference, reference)
        self.assertIs(gam.simulator_pathways, pathways)
        self.assertIs(module.MODULE_SEEN_DURING_EXEC, module)
        self.assertEqual(module.Marker().value, 37)
        self.assertEqual(module.Marker.__module__, 'knowledge_tracing.akt.resources')
        self.assertEqual(module.__package__, 'knowledge_tracing.akt')
        self.assertEqual(module.__file__, str(self.root / MODULE_PATHS[module.__name__]))
        self.assertEqual(module.__spec__.origin, module.__file__)
        self.assertIsNone(module.__cached__)
        self.assertEqual(list(root.__path__), [str(self.root / 'src/knowledge_tracing')])
        self.assertEqual(list(akt.__path__), [str(self.root / 'src/knowledge_tracing/akt')])
        self.assertEqual([r['execution'] for r in self.records], ['PINNED_SOURCE_BODY_RETURNED']*6)

    def test_bad_hash_refused_before_registration_or_body(self):
        bad = dict(self.pin('knowledge_tracing'), sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'source bytes'):
            worker.load_pinned_project_source('knowledge_tracing', bad, self.records)
        self.assertNotIn('knowledge_tracing', sys.modules)
        self.assertEqual(self.records, [])

    def test_preexisting_real_name_refused_before_any_source_read(self):
        pin = self.pin('knowledge_tracing')
        existing = types.ModuleType('knowledge_tracing')
        sys.modules['knowledge_tracing'] = existing
        with patch.object(worker, 'physical', side_effect=AssertionError('must reject before read')):
            with self.assertRaisesRegex(ValueError, 'fresh real project'):
                worker.load_pinned_project_source('knowledge_tracing', pin, self.records)
        self.assertIs(sys.modules['knowledge_tracing'], existing)
        self.assertEqual(self.records, [])

    def test_missing_parent_refused_without_child_registration(self):
        with self.assertRaisesRegex(ValueError, 'parent package'):
            self.load('knowledge_tracing.akt.resources')
        self.assertNotIn('knowledge_tracing.akt.resources', sys.modules)
        self.assertEqual(self.records, [])

    def test_wrong_parent_path_and_existing_child_attribute_refused(self):
        parent = self.load('knowledge_tracing')
        expected_path = list(parent.__path__)
        parent.__path__ = [str(self.root / 'wrong')]
        with self.assertRaisesRegex(ValueError, 'parent package'):
            self.load('knowledge_tracing.akt')
        parent.__path__ = expected_path
        marker = object()
        parent.akt = marker
        with self.assertRaisesRegex(ValueError, 'parent package'):
            self.load('knowledge_tracing.akt')
        self.assertIs(parent.akt, marker)
        self.assertNotIn('knowledge_tracing.akt', sys.modules)
        self.assertEqual(len(self.records), 1)


if __name__ == '__main__':
    unittest.main()
