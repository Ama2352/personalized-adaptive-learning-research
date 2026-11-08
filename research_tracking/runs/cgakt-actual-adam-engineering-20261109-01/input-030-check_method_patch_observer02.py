"""ROOT chạy stdlib regression riêng;0Torch/import/process/native/model."""
import json
import unittest

from method_patch_observer02 import MethodPatches


def family():
    class Parent:
        def step(self): return 'baseline'
    class Child(Parent):
        pass
    return Parent, Child


class RestoreObserverTests(unittest.TestCase):
    def test_legacy_per_entry_guard_reproduces_false_failure(self):
        Parent, Child = family(); baseline = Parent.step
        records = []
        def old_patch(obj, name, value):
            records.append((obj, name, getattr(obj, name), name in vars(obj)))
            setattr(obj, name, value)
        old_patch(Parent, 'step', lambda self: 'counted parent')
        old_patch(Child, 'step', lambda self: 'denied child')
        Parent.step = lambda self: 'optimizer profile rewrap'
        verdict = True
        for obj, name, original, own in reversed(records):
            if own: setattr(obj, name, original)
            else: delattr(obj, name)
            verdict = verdict and getattr(obj, name) is original and (name in vars(obj)) == own
        self.assertFalse(verdict)
        self.assertIs(Parent.step, baseline)
        self.assertIs(Child.step, baseline)
        self.assertNotIn('step', vars(Child))

    def test_precaptured_inheritance_final_two_pass_matches_real_baseline(self):
        Parent, Child = family(); baseline = Parent.step
        observer = MethodPatches(); observer.capture_many(((Parent,'step'),(Child,'step')))
        observer.patch(Parent, 'step', lambda self: 'counted parent')
        observer.patch(Child, 'step', lambda self: 'denied child')
        Parent.step = lambda self: 'optimizer profile rewrap'
        report = observer.restore()
        self.assertTrue(report['accepted']); self.assertEqual(report['patched_targets'], 2)
        self.assertTrue(all(row['restored'] for row in report['final_checks']))
        self.assertIs(Parent.step, baseline); self.assertIs(Child.step, baseline)
        self.assertNotIn('step', vars(Child))

    def test_owned_child_override_preserved_instead_of_deleted(self):
        Parent, Child = family()
        def owned(self): return 'owned child baseline'
        Child.step = owned
        observer = MethodPatches(); observer.capture_many(((Parent,'step'),(Child,'step')))
        observer.patch(Parent,'step',lambda self: 'parent wrapper')
        observer.patch(Child,'step',lambda self: 'child wrapper')
        self.assertTrue(observer.restore()['accepted'])
        self.assertIs(vars(Child)['step'], owned)

    def test_late_inherited_capture_rejected_before_child_mutation(self):
        Parent, Child = family(); observer = MethodPatches()
        observer.patch(Parent,'step',lambda self: 'temporary parent')
        with self.assertRaisesRegex(RuntimeError, 'inherited baseline'):
            observer.patch(Child,'step',lambda self: 'not admitted')
        self.assertNotIn('step',vars(Child))
        self.assertTrue(observer.restore()['accepted'])

    def test_restore_error_does_not_skip_other_final_checks(self):
        blocked = []
        class Meta(type):
            def __setattr__(self, name, value):
                if blocked and name == 'step': raise RuntimeError('simulated read-only restoration')
                return super().__setattr__(name,value)
        class Parent(metaclass=Meta):
            def step(self): return 'baseline'
        class Child(Parent): pass
        observer=MethodPatches(); observer.capture_many(((Parent,'step'),(Child,'step')))
        observer.patch(Parent,'step',lambda self:'wrapped')
        observer.patch(Child,'step',lambda self:'denied')
        blocked.append(True)
        report=observer.restore()
        self.assertFalse(report['accepted']); self.assertEqual(len(report['restore_errors']),1)
        self.assertEqual(len(report['final_checks']),2)
        self.assertTrue(all(row['restored'] is False for row in report['final_checks']))


if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(RestoreObserverTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps(dict(kind='STDLIB_OBSERVER_ONLY_NOT_NATIVE', tests=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))))
    raise SystemExit(0 if result.wasSuccessful() else 1)
