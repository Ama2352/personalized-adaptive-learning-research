"""GRAPH12/13: manufactured typed records; no files, corpus, model or authority."""
from dataclasses import replace
import hashlib
import json
import math
import random
import unittest
from knowledge_tracing import research_admission as a

H='a'*64


def digest(value):return hashlib.sha256(value.encode()).hexdigest()


def wire(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n'


def limits(**changes):return replace(a.AdmissionLimits(8,32,16,288,10.),**changes)


def fixture(transform=None):
    context=a.MainSelectionContext('grade10_simulator',a.PROTOCOL21,a.RECIPE26,a.ALLOCATION,
        H,digest('bank'),digest('split'),digest('train'),digest('selection'))
    keys=tuple(a.ModelNeutralKey(name,'item',i,i,rank,a.HISTORY_SCHEME,digest('past'+str(i)),'selection')
               for i,(name,rank) in enumerate((('a',0),('a',1),('b',0),('c',0))))
    groups=[]
    for ordinal,key in enumerate(keys):
        rows=[]
        for c in a.REQUIRED_CANDIDATE_IDS:
            unsupported=(ordinal==1 and c=='A1_EXPERT') or (ordinal==3 and c=='A0') or (ordinal==2 and c in ('SAKT','GKT','A2_EXPERT'))
            row=a.RawSelectedRow(c,key,ordinal%2,None if unsupported else .5,
                'oov_item' if unsupported else 'supported','raw_selection10',digest('phase'+c),digest('encoding'+c))
            rows.append(row if transform is None else transform(ordinal,row))
        groups.append(tuple(rows))
    full_hash=hashlib.sha256();label_hash=hashlib.sha256()
    for group in groups:
        key_values=group[0].key.values();full_hash.update(wire(key_values));label_hash.update(wire((key_values,group[0].correct)))
    expectation=a.PopulationExpectation(context,4,full_hash.hexdigest(),label_hash.hexdigest())
    claims=[]
    for c in a.REQUIRED_CANDIDATE_IDS:
        column=[next(r for r in group if r.candidate_id==c) for group in groups]
        supported=sum(r.probability is not None for r in column);reasons={}
        for row in column:
            if row.probability is None:reasons[row.support_reason]=reasons.get(row.support_reason,0)+1
        graph=c not in ('A0','SAKT')
        artifact=a.ArtifactClaim(H,100)
        claims.append(a.SelectedCandidateClaim(candidate_id=c,context=context,terminal_kind=a.TERMINAL_KIND,
            status='SELECTED_ONLY_COMPLETE',weights_phase='selected_fit80',prediction_phase='raw_selection10',
            encoding_fit_scope='select_train80',selected_epoch=1,complete_fit_epochs=2,terminal=artifact,
            checkpoint=artifact,raw_predictions=artifact,targets=artifact,coverage=artifact,stage_journal_sha256=H,
            config_sha256=digest('config'+c),sources_sha256=H,runtime_sha256=H,phase_sha256=digest('phase'+c),
            encoding_sha256=digest('encoding'+c),vocabulary_sha256=H,initial_model_sha256=digest('initial'+c),
            initial_backbone_sha256=H if c.startswith('A') else None,
            graph_condition_sha256=digest('condition'+c) if graph else None,
            graph_train_role_sha256=context.train_role_sha256 if graph else None,
            estimator_graph='disabled' if not graph else ('learned' if c.endswith('_LEARNED') else 'expert'),
            epoch_objective_id='MANUFACTURED_NATIVE_EPOCH_OBJECTIVE_NOT_REPORTING_LL',full_targets=4,
            supported_targets=supported,unsupported_counts=tuple(sorted(reasons.items())),
            refit_started=False,calibration_used_for_selection=False))
    return expectation,tuple(claims),tuple(groups)


def registered(data=None,**changes):
    expected,claims,groups=fixture() if data is None else data
    acc=a.MainAdmissionAccumulator(expected,limits(**changes))
    for claim in reversed(claims):acc.add_candidate(claim)
    acc.seal_candidate_claims()
    return acc,groups


def completed():
    acc,groups=registered()
    for group in groups:acc.add_row_group(group)
    return acc,acc.finish()


class MainAdmissionTests(unittest.TestCase):
    def test_all_nine_full_common_counts_and_stats_not_authority(self):
        before=random.getstate();acc,result=completed()
        self.assertEqual(random.getstate(),before)
        self.assertEqual((result.full_targets,result.common_targets,result.row_checks),(4,2,36))
        self.assertEqual(tuple((r.learner_id,r.common_target_count) for r in result.common_statistics),(('a',1),('b',1)))
        for learner in result.common_statistics:
            self.assertEqual(len(learner.candidates),5)
            self.assertTrue(all(abs(c.loss_sum-math.log(2.))<=1e-12 for c in learner.candidates))
        self.assertEqual(result.common_population_coverage.zero_contribution_learner_ids,('c',))
        self.assertEqual([(c.learner_id,c.full_targets,c.common_targets) for c in result.learner_coverage],[('a',2,1),('b',1,1),('c',1,0)])
        self.assertEqual(dict(result.learner_coverage[1].supported_by_candidate)['SAKT'],0)
        coverage={r.candidate_id:r for r in result.candidate_coverage}
        self.assertEqual((coverage['A2_EXPERT'].full_targets,coverage['A2_EXPERT'].supported_targets,
            coverage['A2_EXPERT'].unsupported_counts),(4,3,(('oov_item',1),)))
        self.assertEqual(acc.stage,'STATISTICS_ONLY_COMPLETE')
        self.assertEqual(result.status,'NOT_FILE_ADMISSION_STATISTICS_ONLY')
        self.assertFalse(result.artifact_bytes_verified or result.nine_terminal_files_admitted or result.external_freeze_authority)
        with self.assertRaises(ValueError):acc.finish()

    def test_terminal_stage_role_lineage_and_required_comparators(self):
        expected,claims,_=fixture();claim=claims[0]
        mutations=({'terminal_kind':'COMPLETE_A0_RESEARCH_LIFECYCLE'},{'weights_phase':'fresh_refit90'},
            {'prediction_phase':'calibration_predict'},{'encoding_fit_scope':'refit_union90'},
            {'refit_started':True},{'calibration_used_for_selection':True},{'selected_epoch':3},
            {'initial_backbone_sha256':None},{'estimator_graph':'expert'})
        for change in mutations:
            with self.subTest(change=change),self.assertRaises(ValueError):replace(claim,**change)
        foreign=replace(claim,context=replace(expected.context,environment_id='junyi_development_outer_fold4'))
        acc=a.MainAdmissionAccumulator(expected,limits())
        with self.assertRaises(ValueError):acc.add_candidate(foreign)
        self.assertEqual(acc.stage,'FAILED')
        missing=a.MainAdmissionAccumulator(expected,limits())
        for c in claims[:-1]:missing.add_candidate(c)
        with self.assertRaises(ValueError):missing.seal_candidate_claims()  # GKT cannot silently disappear.
        self.assertEqual(missing.stage,'FAILED')

    def test_duplicate_candidates_or_rows_poison_no_partial_result(self):
        expected,claims,groups=fixture();acc=a.MainAdmissionAccumulator(expected,limits())
        acc.add_candidate(claims[0])
        with self.assertRaises(ValueError):acc.add_candidate(claims[0])
        self.assertEqual(acc.stage,'FAILED')
        acc,groups=registered();acc.add_row_group(groups[0])
        with self.assertRaises(ValueError):acc.add_row_group(groups[0])
        self.assertEqual(acc.stage,'FAILED')
        with self.assertRaises(ValueError):acc.finish()
        fresh,_=registered()
        with self.assertRaises(ValueError):fresh.add_row_group(groups[0][:-1])

    def test_model_neutral_join_checks_key_labels_and_private_phase_bindings(self):
        # Positive fixture has different phase/encoding hashes for all9 models.
        completed()
        for change in ({'correct':1},{'key':replace(fixture()[2][0][0].key,history_sha256=digest('foreign'))},
                       {'encoding_sha256':digest('wrong')},{'phase_sha256':digest('wrong')}):
            acc,groups=registered();bad=list(groups[0]);bad[1]=replace(bad[1],**change)
            with self.subTest(change=change),self.assertRaises(ValueError):acc.add_row_group(tuple(bad))
            self.assertEqual(acc.stage,'FAILED')
        row=fixture()[2][0][0]
        for change in ({'correct':True},{'probability':float('nan')},{'probability':1},
                       {'probability':None},{'phase_scope':'calibration_predict'}):
            with self.subTest(change=change),self.assertRaises(ValueError):replace(row,**change)

    def test_expected_full_universe_digest_rejects_shared_bad_or_missing_rows(self):
        acc,groups=registered()
        for group in groups[:-1]:acc.add_row_group(group)
        with self.assertRaises(ValueError):acc.finish()
        acc,groups=registered()
        for i,group in enumerate(groups):
            bad=tuple(replace(r,correct=1-r.correct) for r in group) if i==0 else group
            acc.add_row_group(bad)
        with self.assertRaisesRegex(ValueError,'full canonical'):acc.finish()
        acc,groups=registered();acc.add_row_group(groups[1])
        with self.assertRaises(ValueError):acc.add_row_group(groups[0])

    def test_empty_common_and_claim_coverage_mismatch_do_not_become_A0(self):
        def no_common(i,row):
            return replace(row,probability=None,support_reason='oov_item') if row.candidate_id=='A0' else row
        acc,groups=registered(fixture(no_common))
        for group in groups:acc.add_row_group(group)
        with self.assertRaisesRegex(ValueError,'EMPTY_COMMON_POPULATION'):acc.finish()
        expected,claims,groups=fixture();wrong=list(claims)
        wrong[0]=replace(wrong[0],supported_targets=4,unsupported_counts=())
        acc,groups=registered((expected,tuple(wrong),groups))
        for group in groups:acc.add_row_group(group)
        with self.assertRaisesRegex(ValueError,'coverage'):acc.finish()

    def test_backbone_claim_and_resource_preflight_are_fail_closed(self):
        expected,claims,groups=fixture();wrong=list(claims)
        wrong[1]=replace(wrong[1],initial_backbone_sha256=digest('different-init'))
        with self.assertRaisesRegex(ValueError,'backbone'):registered((expected,tuple(wrong),groups))
        for change in ({'max_rows':3},{'max_row_checks':35}):
            with self.subTest(change=change),self.assertRaises(ValueError):registered(**change)
        acc,groups=registered(max_rows_per_learner=1);acc.add_row_group(groups[0])
        with self.assertRaisesRegex(ValueError,'per-learner'):acc.add_row_group(groups[1])
        self.assertEqual(acc.stage,'FAILED')

    def test_late_clock_after_result_construction_rejects_no_complete(self):
        old=a._clock;a._clock=lambda:0.
        try:
            acc,groups=registered()
            for group in groups:acc.add_row_group(group)
            calls={'n':0}
            def deadline():
                calls['n']+=1
                return 2. if calls['n']>=3 else 0.
            a._clock=deadline
            acc.limits=replace(acc.limits,max_seconds=1.)
            with self.assertRaisesRegex(ValueError,'deadline'):acc.finish()
            self.assertEqual(acc.stage,'FAILED')
        finally:a._clock=old


if __name__=='__main__':unittest.main(verbosity=2)
