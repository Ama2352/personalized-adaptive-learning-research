"""Pure metadata/AST mocks only: không main, filesystem delta, Git/Popen/model."""
import ast
import base64
import copy
import hashlib
import json
import math
from pathlib import Path,PurePosixPath
import re
import unittest

BASE=Path(__file__).parent


def pure_functions(filename,names):
    tree=ast.parse((BASE/filename).read_bytes());namespace={'copy':copy,'math':math,'PurePosixPath':PurePosixPath,
        'sha':lambda raw:hashlib.sha256(raw).hexdigest()}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for name in node.targets:
                if isinstance(name,ast.Name):
                    try:namespace[name.id]=ast.literal_eval(node.value)
                    except (ValueError,TypeError):
                        if isinstance(node.value,ast.Dict) and all(isinstance(v,(ast.Constant,ast.Name)) for v in node.value.values):
                            namespace[name.id]={ast.literal_eval(k):(namespace[v.id] if isinstance(v,ast.Name) else ast.literal_eval(v))
                                                for k,v in zip(node.value.keys,node.value.values)}
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(functions)==len(names)
    exec(compile(ast.Module(body=functions,type_ignores=[]),filename,'exec'),namespace)
    return namespace,tree


D,DT=pure_functions('apply_source_delta01.py',{'validate_manifest','verify_loader_receipt','loader_relative_path'})
G,GT=pure_functions('linux_cpu_gate24_driver01.py',{'validate_materialization_lineage','validate_delta_result','validate_loader_remediation','validate_reused_runtime','loader_relative_path'})
BASE_RECEIPT=json.loads((BASE/'received/materialization-receipt.json').read_text())
LOADER_PATH='upstream-loader-transfer03/result.json';LOADER_RECEIPT_SHA='a'*64;MATERIAL_SHA='b'*64


def loader():
    return {'status':'MATERIALIZED_TRANSFERRED_PINNED_LOADER_SOURCE_ONLY','source_sha256':D['LOADER_SOURCE_SHA'],
        'source_origin':'LOCAL_PINNED_GIT_BLOB_TRANSFER','cleanup':{'accepted':True},
        'audit':{'source_origin':'LOCAL_PINNED_GIT_BLOB_TRANSFER','source_before_after':{'files':G['LF_SOURCE_FILES']},
                 'loader':{'path':'load_data.py','sha256':D['LOADER_SHA'],'git_blob_id':D['LOADER_BLOB'],'bytes':6428}}}


def material():
    manifest=D['validate_manifest'](BASE_RECEIPT,base64.b64decode(D['PAYLOAD_B64']))
    return {'status':'MATERIALIZED_SOURCE_DELTA_ONLY_NO_EXECUTION','base_materialization_receipt_sha256':G['BASE_MATERIALIZATION_SHA'],
        'base_archive_sha256':BASE_RECEIPT['archive_sha256'],'base_archive_contains_delta':False,'new_archive_created':False,
        'manifest':manifest,'source_sha256_after':{name:entry['sha256'] for name,entry in manifest['files'].items()},
        'delta':{'target':G['TEST_PATH'],'old_sha256':G['OLD_TEST_SHA'],'new_sha256':G['NEW_TEST_SHA'],
                 'controller_source_sha256':G['DELTA_SOURCE_SHA'],'loader_remediation_sha256':LOADER_RECEIPT_SHA,'loader_remediation_path':LOADER_PATH}}


class MetadataTests(unittest.TestCase):
    def test_all_static_SHA_pins64_and_real_reviewed_sources_match(self):
        for namespace in (D,G):
            for name,value in namespace.items():
                if name.endswith('_SHA') and isinstance(value,str):self.assertRegex(value,r'^[a-f0-9]{64}$')
        for value in G['PRESERVED'].values():self.assertRegex(value,r'^[a-f0-9]{64}$')
        self.assertEqual(hashlib.sha256((BASE/'apply_source_delta01.py').read_bytes()).hexdigest(),G['DELTA_SOURCE_SHA'])
        self.assertEqual(hashlib.sha256((BASE/'materialize_upstream_loader04.py').read_bytes()).hexdigest(),D['LOADER_SOURCE_SHA'])

    def test_delta_manifest_exactly_one_test_without_mutating_base(self):
        before=copy.deepcopy(BASE_RECEIPT);m=material();new=m['manifest']['files'];old=before['manifest']['files']
        self.assertEqual([name for name in old if old[name]!=new[name]],[G['TEST_PATH']]);self.assertEqual(BASE_RECEIPT,before)
        G['validate_materialization_lineage'](m,BASE_RECEIPT,LOADER_RECEIPT_SHA,LOADER_PATH)
        with self.assertRaises(ValueError):D['validate_manifest'](BASE_RECEIPT,b'wrong')

    def test_lineage_rejects_phantom_zip_extra_change_wrong_loader(self):
        for case in ('zip','source','loader','path'):
            m=material()
            if case=='zip':m['base_archive_contains_delta']=True
            elif case=='source':m['manifest']['files']['src/knowledge_tracing/akt/graph_prototype.py']['sha256']='c'*64
            elif case=='loader':m['delta']['loader_remediation_sha256']='d'*64
            else:m['delta']['loader_remediation_path']='upstream-loader-transfer02/result.json'
            with self.assertRaises(ValueError):G['validate_materialization_lineage'](m,BASE_RECEIPT,LOADER_RECEIPT_SHA,LOADER_PATH)

    def test_loader_acceptance_required_and_failed_old_source_rejects(self):
        for validate in (D['verify_loader_receipt'],G['validate_loader_remediation']):
            validate(loader())
            for case in ('status','cleanup','source'):
                r=loader()
                if case=='status':r['status']='FAILED_TRANSFERRED_LOADER_RETAIN_PARTIAL'
                elif case=='cleanup':r['cleanup']['accepted']=False
                else:r['source_sha256']='9489a25d14aab2f5ecd9173b128378db358c11950daa5aefcfd8615d2aabbda1'
                with self.assertRaises(ValueError):validate(r)

    def test_loader_path_is_explicit_POSIX_not_hardcoded_stage02(self):
        for validate in (D['loader_relative_path'],G['loader_relative_path']):
            self.assertEqual(validate(LOADER_PATH),LOADER_PATH)
            for bad in ('/content/result.json','../result.json','upstream-loader-transfer03\\result.json','upstream-loader-transfer03/../result.json','C:/result.json'):
                with self.assertRaises(ValueError):validate(bad)

    def test_actual_prior_runtime02_reused_as105a_not_new_driver(self):
        prior=json.loads((BASE/'received-linux-runtime02/linux-cpu-validation-runtime-20261108-02/result.json').read_text())
        runtime=json.loads((BASE/'received-linux-runtime02/artifacts/akt/runtime/linux-cpu-20261108-02.json').read_text())
        G['validate_reused_runtime'](prior,runtime,BASE_RECEIPT,prior['upstream_audit_sha256'])
        wrong=copy.deepcopy(prior);wrong['driver_source_sha256']='f'*64
        with self.assertRaises(ValueError):G['validate_reused_runtime'](wrong,runtime,BASE_RECEIPT,prior['upstream_audit_sha256'])

    def test_delta_elapsed_bool_or_partial_never_accepted(self):
        accepted={'status':'ACCEPTED_TEST_ONLY_SOURCE_DELTA_NO_EXECUTION','source_sha256':G['DELTA_SOURCE_SHA'],
            'new_materialization_sha256':MATERIAL_SHA,'changed_paths':[G['TEST_PATH']],'other160files_unchanged':True,
            'inventory_file_count':161,'old_backup_sha256':G['OLD_TEST_SHA'],'new_target_sha256':G['NEW_TEST_SHA'],
            'elapsed_seconds':1.,'elapsed_wall_seconds':1.}
        G['validate_delta_result'](accepted,material(),MATERIAL_SHA)
        for field,value in [('status','FAILED_SOURCE_DELTA_RETAIN_PARTIAL'),('elapsed_seconds',True),('elapsed_wall_seconds',31.)]:
            bad={**accepted,field:value}
            with self.assertRaises(ValueError):G['validate_delta_result'](bad,material(),MATERIAL_SHA)

    def test_gate_native_scope_cleanup_and_git_environment_unchanged(self):
        old=ast.parse((BASE/'linux_cpu_validation_driver02.py').read_bytes())
        def fn(tree,name):return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
        for name in ('cleanup','isolated_git_environment'):
            self.assertEqual(ast.dump(fn(old,name)),ast.dump(fn(GT,name)))
        source=(BASE/'linux_cpu_gate24_driver01.py').read_text()
        self.assertIn("{'passed':771,'failed':0,'errors':0,'skipped':0}",source)
        self.assertIn("'--timeout-seconds','600'",source)
        self.assertNotIn("'scripts/akt/check_runtime.py'",source)
        self.assertNotIn("'--deselect'",source)


if __name__=='__main__':unittest.main(verbosity=2)
