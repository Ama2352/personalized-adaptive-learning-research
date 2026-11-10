"""Fixtures JSON, không tải tensor hoặc chứng nhận thực thi training."""
from copy import deepcopy
from dataclasses import replace
import unittest

from knowledge_tracing.research_selected_checkpoint import (
    AKT_ROLE, SAKT_ROLE, GKT_ROLE, validate_selected_checkpoint,
)
from knowledge_tracing.research_selection_io import FileRef
from test_research_selected_rows import H, claim


def fixture(candidate='A0', schema=1):
    selected = claim(candidate)
    identity = dict(schema_version=schema, fitted_research_model=False,
                    encoding_sha256=H, phase_sha256='c' * 64)
    metadata = dict(schema_version=schema, identity=identity, checkpoint_sha256=H, checkpoint_bytes=100)
    if candidate.startswith('A'):
        role, status = AKT_ROLE, 'COMPLETE_CGAKT_EPOCH_TRAINING_STATE'
        identity.update(neural_binding=dict(phase_scope='select_train80', encoding_fit_scope='select_train80',
            encoding_sha256=H, vocabulary_sha256=H, selection_freeze_sha256=None),
            profile=dict(purpose='selected_fit_candidate', external_system_freeze_sha256=None,
                initial_backbone_sha256=H, runtime_receipt_sha256=H,
                protocol21_sha256=selected.context.protocol21_sha256,
                protocol26_sha256=selected.context.recipe26_sha256,
                candidate_allocation_sha256=selected.context.allocation_sha256),
            condition=dict(variant=candidate, train80=dict(train_shard_sha256=H)))
        metadata.update(fitted_research_model=False, iterator_resume_supported=False,
            lifecycle_resume_supported=False, layout=[], producer_config={}, receipt=dict(completed_epochs=1),
            restore_scope='completed_epoch_boundary', state_representation=[])
    else:
        identity.update(phase_scope='select_train80', profile=dict(runtime_sha256=H,
            protocol_sha256=selected.context.protocol21_sha256))
        if candidate == 'SAKT':
            role, status = SAKT_ROLE, 'COMPLETE_SAKT_EPOCH_TRAINING_STATE'
            identity['vocabulary_sha256'] = H
            metadata.update(progress=dict(completed_epochs=1), model_state_sha256=H,
                restore_scope='completed_epoch_boundary', iterator_resume_supported=False, fitted_research_model=False)
        else:
            role, status = GKT_ROLE, 'COMPLETE_GKT_EPOCH_STATE'
            identity.update(model_spec=dict(vocabulary_sha256=H), graph=dict(train80_shard_sha256=H),
                            completed_epoch_spec=dict(epoch=1))
            identity['profile']['initial_model_sha256'] = H
            metadata.update(counters=dict(complete_train_epochs=1), model_sha256=H,
                            participation=[], owned_rng_sha256=H, module_modes=[])
    identity['role'] = metadata['role'] = role
    complete = dict(schema_version=schema, status=status, metadata_sha256=H, checkpoint_sha256=H)
    return dict(claim=selected, complete=complete, metadata=metadata, expected_identity=deepcopy(identity),
        complete_ref=FileRef('checkpoint/COMPLETE.json', H, 100),
        metadata_ref=FileRef('checkpoint/metadata.json', H, 100),
        checkpoint_ref=FileRef('checkpoint/state.pt', H, 100))


class CheckpointBindingTests(unittest.TestCase):
    def test_all_candidates_selected_epoch_and_separate_training_phase(self):
        for candidate in ('A0', 'A1_EXPERT', 'A1_LEARNED', 'A2_EXPERT', 'A2_LEARNED',
                          'A3_EXPERT', 'A3_LEARNED', 'SAKT', 'GKT'):
            data = fixture(candidate)
            self.assertNotEqual(data['metadata']['identity']['phase_sha256'], data['claim'].phase_sha256)
            self.assertIsNone(validate_selected_checkpoint(**data))

    def test_schema_two_is_akt_only_and_schema_types_exact(self):
        validate_selected_checkpoint(**fixture('A0', 2))
        for candidate, schema in (('SAKT', 2), ('GKT', 2), ('A0', True), ('A0', 3)):
            with self.subTest(candidate=candidate, schema=schema), self.assertRaises(ValueError):
                validate_selected_checkpoint(**fixture(candidate, schema))

    def test_reject_byte_link_mismatch(self):
        for name, field, value in (('complete', 'metadata_sha256', 'b' * 64),
                ('complete', 'checkpoint_sha256', 'b' * 64), ('metadata', 'checkpoint_bytes', True),
                ('metadata', 'checkpoint_bytes', 101), ('metadata', 'checkpoint_sha256', 'b' * 64)):
            data = fixture()
            data[name][field] = value
            with self.subTest(name=name, field=field), self.assertRaises(ValueError):
                validate_selected_checkpoint(**data)

    def test_reject_relocated_sibling_or_non_pinned_ref(self):
        for replacement in (FileRef('other/state.pt', H, 100), FileRef('checkpoint/not-state.pt', H, 100),
                            FileRef('checkpoint/state.pt', H, 101), {'sha256': H}):
            data = fixture()
            data['checkpoint_ref'] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                validate_selected_checkpoint(**data)

    def test_full_identity_and_selected_epoch_not_latest(self):
        for candidate, section, key in (('A0', 'receipt', 'completed_epochs'),
                ('SAKT', 'progress', 'completed_epochs'), ('GKT', 'counters', 'complete_train_epochs')):
            data = fixture(candidate)
            data['metadata'][section][key] = 2
            with self.assertRaises(ValueError):
                validate_selected_checkpoint(**data)
        data = fixture()
        data['expected_identity']['phase_sha256'] = 'b' * 64
        with self.assertRaises(ValueError):
            validate_selected_checkpoint(**data)

    def test_wrong_scope_binding_rejected_even_if_identity_pin_matches(self):
        for candidate in ('A0', 'SAKT', 'GKT'):
            data = fixture(candidate)
            identity = data['metadata']['identity']
            if candidate == 'A0':
                identity['neural_binding']['phase_scope'] = 'refit90'
            else:
                identity['phase_scope'] = 'refit90'
            data['expected_identity'] = deepcopy(identity)
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                validate_selected_checkpoint(**data)

    def test_unknown_fields_wrong_role_and_bool_epoch_rejected(self):
        for section, name, value in (('complete', 'status', 'COMPLETE_GKT_EPOCH_STATE'),
                ('complete', 'authority', True), ('metadata', 'extra', 0),
                ('metadata', 'role', GKT_ROLE)):
            data = fixture()
            data[section][name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_selected_checkpoint(**data)
        data = fixture()
        data['metadata']['receipt']['completed_epochs'] = True
        with self.assertRaises(ValueError):
            validate_selected_checkpoint(**data)


if __name__ == '__main__':
    unittest.main()
