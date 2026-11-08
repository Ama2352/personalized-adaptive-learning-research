"""GRAPH18 pure manufactured claims: no files/model/selector/freeze authority."""
from dataclasses import replace
import builtins
from pathlib import Path
import unittest

from knowledge_tracing import research_admission as admission
from knowledge_tracing.akt import research_main_stage as stage

H = 'a'*64
G = 'b'*64


def fixture(candidate='A3_EXPERT', environment='grade10_simulator'):
    context = admission.MainSelectionContext(environment, admission.PROTOCOL21, admission.RECIPE26,
        admission.ALLOCATION, H, H, H, H, G)
    graph = candidate not in ('A0','SAKT')
    spec = stage.MainSelectedStageSpec(candidate, context, stage.PROTOCOL22, stage.ACCOUNTING23,
        H, H, H, H if graph else None, context.train_role_sha256 if graph else None)
    artifact = admission.ArtifactClaim(H, 100)
    claim = admission.SelectedCandidateClaim(candidate_id=candidate, context=context,
        terminal_kind=admission.TERMINAL_KIND, status='SELECTED_ONLY_COMPLETE',
        weights_phase='selected_fit80', prediction_phase='raw_selection10', encoding_fit_scope='select_train80',
        selected_epoch=1, complete_fit_epochs=2, terminal=artifact, checkpoint=artifact,
        raw_predictions=artifact, targets=artifact, coverage=artifact, stage_journal_sha256=H,
        config_sha256=H, sources_sha256=H, runtime_sha256=H, phase_sha256=H, encoding_sha256=H,
        vocabulary_sha256=H, initial_model_sha256=H,
        initial_backbone_sha256=H if candidate.startswith('A') else None,
        graph_condition_sha256=H if graph else None,
        graph_train_role_sha256=context.train_role_sha256 if graph else None,
        estimator_graph='disabled' if not graph else 'learned' if candidate.endswith('_LEARNED') else 'expert',
        epoch_objective_id='MANUFACTURED_NATIVE_OBJECTIVE_NOT_REPORTING_LOSS',
        full_targets=4, supported_targets=3, unsupported_counts=(('oov_item',1),),
        refit_started=False, calibration_used_for_selection=False)
    return spec,claim


def ready(candidate='A3_EXPERT'):
    spec,claim=fixture(candidate)
    return stage.prepare_main_selected_stage(spec),claim


class MainSelectedStageTests(unittest.TestCase):
    def test_all_nine_exact_bindings_and_both_environments(self):
        expected = (('A0','A0','disabled'),('A1_EXPERT','A1','expert'),('A1_LEARNED','A1','learned'),
            ('A2_EXPERT','A2','expert'),('A2_LEARNED','A2','learned'),('A3_EXPERT','A3','expert'),
            ('A3_LEARNED','A3','learned'),('SAKT','SAKT','disabled'),('GKT','GKT','expert'))
        self.assertEqual(tuple(row[0] for row in expected), admission.REQUIRED_CANDIDATE_IDS)
        for env in ('grade10_simulator','junyi_development_outer_fold4'):
            for candidate,variant,graph in expected:
                with self.subTest(environment=env,candidate=candidate):
                    spec,claim=fixture(candidate,env)
                    current=stage.prepare_main_selected_stage(spec)
                    self.assertEqual((spec.candidate_variant,spec.estimator_graph),(variant,graph))
                    fit=current.begin_selected_fit()
                    self.assertEqual(fit.phase_inputs(),('select_train80',(('train',spec.context.train_role_sha256),)))
                    self.assertEqual(fit.epoch_validation_inputs(),('raw_selection10',(('selection',spec.context.selection_role_sha256),)))
                    self.assertEqual(fit.phase,'selected_fit80')  # Every epoch may validate before final best export.
                    raw=fit.begin_raw_best_selection()
                    self.assertEqual(raw.phase_inputs(),('raw_selection10',(('selection',spec.context.selection_role_sha256),)))
                    done=raw.finish_selected(claim)
                    self.assertIs(done.terminal_claim,claim)
                    self.assertEqual(done.phase,'SELECTED_ONLY_COMPLETE')
                    self.assertEqual(done.status,'NO_EXECUTION_AUTHORITY')
                    self.assertFalse(done.artifact_bytes_verified or done.external_freeze_authority)
                    with self.assertRaises(ValueError): done.phase_inputs()
                    self.assertEqual(current.phase,'READY')  # Immutable, not an anti-fork token.

    def test_phase_order_and_no_terminal_reentry(self):
        current,claim=ready()
        for operation in (current.begin_raw_best_selection,lambda:current.finish_selected(claim),current.phase_inputs):
            with self.assertRaises(ValueError): operation()
        with self.assertRaises(ValueError): current.epoch_validation_inputs()
        fit=current.begin_selected_fit()
        with self.assertRaises(ValueError): fit.finish_selected(claim)
        raw=fit.begin_raw_best_selection()
        with self.assertRaises(ValueError): raw.epoch_validation_inputs()
        with self.assertRaises(ValueError): raw.begin_selected_fit()
        done=raw.finish_selected(claim)
        with self.assertRaises(ValueError): done.epoch_validation_inputs()
        for operation in (done.begin_selected_fit,done.begin_raw_best_selection,lambda:done.finish_selected(claim)):
            with self.assertRaises(ValueError): operation()

    def test_protocol_and_allocation_id_drift_rejected(self):
        spec,_=fixture()
        for change in ({'protocol22_sha256':G},{'accounting23_sha256':G},{'config_sha256':True},
                       {'sources_sha256':'A'*64},{'candidate_id':'A3_OFF_AS_A0'}):
            with self.subTest(change=change),self.assertRaises(ValueError): replace(spec,**change)
        for change in ({'protocol21_sha256':G},{'recipe26_sha256':G},{'allocation_sha256':G}):
            with self.subTest(change=change),self.assertRaises(ValueError): replace(spec.context,**change)

    def test_graph_train80_and_graph_disabled_baselines(self):
        spec,_=fixture()
        with self.assertRaises(ValueError): replace(spec,graph_train_role_sha256=spec.context.selection_role_sha256)
        with self.assertRaises(ValueError): replace(spec,graph_condition_sha256=None)
        for candidate in ('A0','SAKT'):
            spec,_=fixture(candidate)
            with self.assertRaises(ValueError): replace(spec,graph_condition_sha256=H)
            with self.assertRaises(ValueError): replace(spec,graph_train_role_sha256=H)

    def test_claim_candidate_context_config_runtime_sources_graph_must_match(self):
        current,claim=ready();raw=current.begin_selected_fit().begin_raw_best_selection()
        for field in ('config_sha256','runtime_sha256','sources_sha256','graph_condition_sha256'):
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'binding'):
                raw.finish_selected(replace(claim,**{field:G}))
        foreign=replace(claim,context=replace(claim.context,environment_id='junyi_development_outer_fold4'))
        with self.assertRaisesRegex(ValueError,'binding'): raw.finish_selected(foreign)
        _,other=fixture('A3_LEARNED')
        with self.assertRaisesRegex(ValueError,'binding'): raw.finish_selected(other)
        self.assertEqual(raw.phase,'raw_best_selection10')

    def test_pilot_refit_calibrated_and_incomplete_claims_do_not_promote(self):
        _,claim=ready()
        for change in ({'terminal_kind':'COMPLETE_A0_RESEARCH_LIFECYCLE'}, {'refit_started':True},
                       {'prediction_phase':'calibration_predict'}, {'encoding_fit_scope':'refit_union90'},
                       {'calibration_used_for_selection':True}, {'selected_epoch':3}):
            with self.subTest(change=change),self.assertRaises(ValueError): replace(claim,**change)

    def test_mutated_existing_claim_revalidated_before_terminal(self):
        current,claim=ready();raw=current.begin_selected_fit().begin_raw_best_selection()
        object.__setattr__(claim,'refit_started',True)
        with self.assertRaises(ValueError): raw.finish_selected(claim)

    def test_stage_seal_detects_valid_looking_spec_and_phase_tamper(self):
        for kind in ('spec','phase','seal'):
            with self.subTest(kind=kind):
                current,_=ready()
                if kind=='spec': object.__setattr__(current,'spec',replace(current.spec,config_sha256=G))
                elif kind=='phase': object.__setattr__(current,'phase','selected_fit80')
                else: object.__setattr__(current,'content_sha256',G)
                with self.assertRaisesRegex(ValueError,'drift'): current.assert_integrity()

    def test_terminal_claim_mutation_cannot_reuse_old_state_identity(self):
        current,claim=ready();done=current.begin_selected_fit().begin_raw_best_selection().finish_selected(claim)
        object.__setattr__(claim,'encoding_sha256',G)  # Still syntactically valid; seal must catch.
        with self.assertRaisesRegex(ValueError,'drift'): _=done.identity

    def test_no_actual_freeze_verifier_means_refit_always_unavailable(self):
        current,claim=ready();done=current.begin_selected_fit().begin_raw_best_selection().finish_selected(claim)
        for payload in (None,True,False,H, {'status':'VERIFIED','all_nine_files_verified':True,'sha256':H}, claim):
            with self.subTest(payload=type(payload).__name__):
                for head in (current,done):
                    with self.assertRaisesRegex(stage.ExternalFreezeVerifierUnavailable,stage.REFIT_UNAVAILABLE):
                        head.request_refit_after_external_freeze(payload)

    def test_fake_verified_object_or_callback_is_not_invoked(self):
        class Trap:
            @property
            def verified(self): raise AssertionError('no caller-declared verifier access')
            def __bool__(self): raise AssertionError('no caller truth-value authority')
            def __call__(self): raise AssertionError('no verifier callback execution')
        current,_=ready()
        with self.assertRaises(stage.ExternalFreezeVerifierUnavailable): current.request_refit_after_external_freeze(Trap())

    def test_calibration_not_a_selected_only_transition(self):
        current,claim=ready();fit=current.begin_selected_fit();raw=fit.begin_raw_best_selection();done=raw.finish_selected(claim)
        for head in (current,fit,raw,done):
            with self.assertRaisesRegex(ValueError,'excludes calibration'): head.request_calibration()
            self.assertFalse(hasattr(head,'execution_grant') or hasattr(head,'winner') or hasattr(head,'model'))

    def test_no_file_or_model_callback_for_pure_state_path(self):
        current,claim=ready();calls=[]
        def denied(*args,**kwargs):
            calls.append('file');raise AssertionError('no semantic file access from metadata contract')
        old_open,old_read=builtins.open,Path.read_bytes
        try:
            builtins.open=denied;Path.read_bytes=denied
            done=current.begin_selected_fit().begin_raw_best_selection().finish_selected(claim)
            self.assertEqual(done.status,stage.STATUS)
            self.assertEqual(len(done.identity),64)
            with self.assertRaises(stage.ExternalFreezeVerifierUnavailable): done.request_refit_after_external_freeze(H)
        finally:
            builtins.open=old_open;Path.read_bytes=old_read
        self.assertEqual(calls,[])

    def test_direct_constructor_and_fake_terminal_shape_rejected(self):
        with self.assertRaises(TypeError): stage.MainSelectedStage()
        with self.assertRaises(ValueError): stage.prepare_main_selected_stage({'status':'APPROVED'})
        current,claim=ready();raw=current.begin_selected_fit().begin_raw_best_selection()
        with self.assertRaises(ValueError): raw.finish_selected(dict(claim=claim,verified=True))


if __name__ == '__main__': unittest.main()
