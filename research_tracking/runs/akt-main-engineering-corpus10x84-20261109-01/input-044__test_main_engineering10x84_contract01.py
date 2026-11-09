"""Chín pure contract fixtures; không tạo corpus, import native hoặc cấp grant."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('engineering10x84_contract_worker',P/'collect_main_engineering10x84_01.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)


def manufactured_request():
    return dict(schema_version=1,purpose='GENUINE_10X84_ENGINEERING_CORPUS_NOT_RESEARCH_ALLOCATION',
        approval_reference='MANUFACTURED_CONTRACT_FIXTURE_NOT_DISPATCH',plan_recipe=deepcopy(worker.PLAN),
        collection_recipe=deepcopy(worker.RECIPE),profile='PG',generated_roles=list(worker.ROLES),
        limits=deepcopy(worker.LIMITS),collection_sources={name:'a'*64 for name in worker.COLLECTION_SOURCES},
        extra_sources={name:'b'*64 for name in worker.EXTRA_SOURCES},runtime_report=worker.RUNTIME,
        runtime_sha256=worker.RUNTIME_SHA,gate_index=worker.INDEX,gate_index_sha256=worker.INDEX_SHA)


class EngineeringContract(unittest.TestCase):
    def test_exact_metadata_consistency_is_not_execution_authority(self):
        request=manufactured_request()
        self.assertIs(worker.validate_contract(request),request)
        self.assertNotIn('authorized',request)
        self.assertEqual(sum(worker.EVENTS.values()),840)

    def test_reject_final_other_corpus_profiles_or_policy(self):
        changes=[('generated_roles',['train','selection','calibration','final']),('profile','PYH')]
        for field,value in changes:
            with self.subTest(field=field),self.assertRaises(ValueError):
                request=manufactured_request();request[field]=value;worker.validate_contract(request)
        for field,value in [('namespace','grade10-development-lifecycle01-20261108'),('development_learners',60),('final_learners',0)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                request=manufactured_request();request['plan_recipe'][field]=value;worker.validate_contract(request)
        with self.assertRaises(ValueError):
            request=manufactured_request();request['collection_recipe']['policy']='uniform_items';worker.validate_contract(request)

    def test_exact_source_allowlist_and_digest_shape(self):
        for mode in ('missing','extra','uppercase','null'):
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                request=manufactured_request();sources=request['collection_sources'];name=next(iter(sources))
                if mode=='missing':del sources[name]
                elif mode=='extra':sources['dataset/unapproved.csv']='a'*64
                elif mode=='uppercase':sources[name]='A'*64
                else:sources[name]=None
                worker.validate_contract(request)

    def test_budget_bool_nan_and_changed_reservation_inputs_rejected(self):
        for section,field,value in [('limits','worker_seconds',float('nan')),('limits','max_rss_bytes',True),
                                    ('limits','worker_seconds',61.),('collection_recipe','events_per_learner',85),
                                    ('plan_recipe','root_seed',True)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                request=manufactured_request();request[section][field]=value;worker.validate_contract(request)

    def test_runtime_and_index_are_exact_inputs_not_claimed_pass_booleans(self):
        for field,value in [('runtime_sha256','c'*64),('gate_index','artifacts/akt/preflight/gate2-current.json'),
                            ('schema_version',True),('verified',True)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                request=manufactured_request();request[field]=value;worker.validate_contract(request)

    def test_hardkill_accounting_retains_unknown_active_work(self):
        result=worker.failure_accounting({'train':672},'selection')
        self.assertIsNone(result['actual_attempts'])
        self.assertEqual((result['actual_attempts_lower_bound'],result['actual_attempts_upper_bound']),(672,840))
        self.assertEqual(result['active_actual'],'UNKNOWN')
        self.assertFalse(result['automatic_retry'])

    def test_genuine_failure_receipt_can_add_known_partial_calls(self):
        result=worker.failure_accounting({'train':672},'selection',dict(interact_attempts=7,interact_returns=6))
        self.assertEqual(result['actual_attempts'],679)
        self.assertEqual(result['reserved_teacher_attempts'],840)

    def test_failure_counters_reject_reset_overflow_and_completed_overlap(self):
        for receipt in (dict(interact_attempts=True,interact_returns=0),dict(interact_attempts=85,interact_returns=1),
                        dict(interact_attempts=2,interact_returns=3)):
            with self.subTest(receipt=receipt),self.assertRaises(ValueError):
                worker.failure_accounting({'train':672},'selection',receipt)
        with self.assertRaises(ValueError):worker.failure_accounting({'train':671},'selection')
        with self.assertRaises(ValueError):worker.failure_accounting({'train':672},'train')

    def test_cycle_algebra_and_final_metadata_only_not_native_execution(self):
        for offset in (0,1,83):
            self.assertEqual(set((offset+rank)%84 for rank in range(84)),set(range(84)))
        self.assertEqual(worker.PLAN['final_learners'],1)
        self.assertNotIn('final',worker.ROLES)


if __name__=='__main__':
    unittest.main(verbosity=2)
