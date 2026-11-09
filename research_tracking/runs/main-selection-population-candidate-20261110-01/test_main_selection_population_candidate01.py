"""Fixtures manufactured chỉ kiểm helper quần thể, không actual corpus/audit proof."""
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from knowledge_tracing import research_admission as admission
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, identity_hash
from knowledge_tracing.simulator_corpus_reader import PublicRoleData
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import ResearchProvenance

PATH = Path(__file__).with_name('main_selection_population_candidate01.py')
SPEC = importlib.util.spec_from_file_location('main_selection_population_candidate01', PATH)
candidate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = candidate
SPEC.loader.exec_module(candidate)


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def fixture(observations=None, role='selection'):
    observations = observations or (Observation(ItemQuery('z', 100, 1), 0), Observation(ItemQuery('a', 200, 2), 1))
    provenance = ResearchProvenance(role, digest('research'), digest('split'), digest('domain'), digest('graph'),
        (('collector', digest('collector')), ('environment', digest('env'))), digest('recipe'),
        'cyclic-observable', 'unix_seconds_utc', 'UTC', False)
    trajectory = ObservableTrajectory('learner', digest('split'), digest('domain'), 'cyclic-observable', observations)
    shard = identity_hash([trajectory.payload()])
    context = admission.MainSelectionContext('grade10_simulator', admission.PROTOCOL21, admission.RECIPE26,
        admission.ALLOCATION, digest('domain'), digest('bank-file'), digest('research'), digest('train'), shard)
    audit = dict(role=role, research_plan_sha256=context.split_sha256, provenance_sha256=provenance.identity,
        audit=dict(role=role, shard_sha256=shard, domain_sha256=context.domain_sha256,
                   plan_sha256=provenance.split_plan_sha256, learners=1, targets=len(observations)))
    audit['receipt_sha256'] = identity_hash(audit)
    counts = tuple(sum(o.correct == label for o in observations) for label in (0, 1))
    value = PublicRoleData(role, provenance, (trajectory,), json.dumps({'provenance_sha256': provenance.identity}),
                           json.dumps(audit), counts)
    return value, context


def calculate(role, context, **changes):
    limits = replace(candidate.PopulationLimits(4, 16, 8, 65536, 3.), **changes)
    return candidate.prepare_selection_population(role, context, expected_provenance_sha256=role.provenance.identity,
        expected_audit_receipt_sha256=role.audit['receipt_sha256'], limits=limits)


class PopulationTests(unittest.TestCase):
    def test_chronology_prefix_then_canonical_K_hash_known_answer(self):
        role, context = fixture()
        before = asdict(role)
        first = role.trajectories[0].observations[0]
        prefix0 = identity_hash(dict(scheme=admission.HISTORY_SCHEME, domain_sha256=context.domain_sha256, learner_id='learner'))
        prefix1 = identity_hash(dict(scheme=admission.HISTORY_SCHEME, previous_sha256=prefix0, observation=asdict(first)))
        # Item 'a' sorts before 'z', although it is chronologically second.
        keys = (admission.ModelNeutralKey('learner', 'a', 200, 2, 1, admission.HISTORY_SCHEME, prefix1, 'selection'),
                admission.ModelNeutralKey('learner', 'z', 100, 1, 0, admission.HISTORY_SCHEME, prefix0, 'selection'))
        expected_keys = hashlib.sha256(b''.join(admission._canonical(k.values()) for k in keys)).hexdigest()
        expected_labels = hashlib.sha256(b''.join(admission._canonical((k.values(), y)) for k, y in zip(keys, (1, 0)))).hexdigest()
        result = calculate(role, context)
        self.assertEqual((result.expectation.full_keys_sha256, result.expectation.full_keys_labels_sha256), (expected_keys, expected_labels))
        self.assertEqual((result.expectation.full_targets, result.class_counts, result.learner_target_counts), (2, (1, 1), (('learner', 2),)))
        self.assertEqual(asdict(role), before)
        self.assertFalse(result.file_admission_performed or result.external_freeze_authority or result.refit_authorized)

    def test_mutated_labels_rejected_against_trusted_shard_receipt(self):
        role, context = fixture()
        old = role.trajectories[0]
        changed = replace(old, observations=(replace(old.observations[0], correct=1), old.observations[1]))
        mutated = replace(role, trajectories=(changed,), class_counts=(0, 2))
        with self.assertRaisesRegex(ValueError, 'shard/label mutation'):
            calculate(mutated, context)

    def test_duplicate_rows_and_learners_rejected(self):
        duplicate = (Observation(ItemQuery('z', 100, 1), 0), Observation(ItemQuery('a', 200, 1), 1))
        role, context = fixture(duplicate)
        with self.assertRaisesRegex(ValueError, 'Duplicate source row'):
            calculate(role, context)
        role, context = fixture()
        duplicate_role = replace(role, trajectories=role.trajectories * 2)
        with self.assertRaises(ValueError):
            calculate(duplicate_role, context)

    def test_nonselection_and_empty_population_rejected(self):
        for name in ('train', 'calibration', 'final'):
            role, context = fixture(role=name)
            with self.subTest(role=name), self.assertRaisesRegex(ValueError, 'selection role only'):
                calculate(role, context)
        role, context = fixture()
        with self.assertRaises(ValueError):
            calculate(replace(role, trajectories=()), context)

    def test_count_caps_and_bad_binary_value_rejected(self):
        role, context = fixture()
        for limits in (dict(max_rows=1), dict(max_rows_per_learner=1)):
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                calculate(role, context, **limits)
        bad_observation = Observation(ItemQuery('z', 100, 1), 0)
        object.__setattr__(bad_observation, 'correct', True)
        bad = replace(role.trajectories[0], observations=(bad_observation, role.trajectories[0].observations[1]))
        with self.assertRaisesRegex(ValueError, 'Binary observable target'):
            calculate(replace(role, trajectories=(bad,)), context)

    def test_single_class_not_new_eligibility_rule_and_context_mismatch(self):
        role, context = fixture((Observation(ItemQuery('a', 100, 1), 0),))
        self.assertEqual(calculate(role, context).class_counts, (1, 0))
        with self.assertRaisesRegex(ValueError, 'binding'):
            calculate(role, replace(context, domain_sha256=digest('other-domain')))


if __name__ == '__main__':
    unittest.main()
