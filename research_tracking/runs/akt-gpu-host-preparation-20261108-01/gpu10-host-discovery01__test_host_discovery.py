"""Pure/synthetic producer+receiver contracts; no real RPC/GPU receipt produced."""
import ast,copy,contextlib,hashlib,importlib.util,io,json,tempfile,unittest
from pathlib import Path
W=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('generic_discovery_tests',W/'host_discovery.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
PROFILE_RAW=(d.OLD/'discovery_profile01.json').read_bytes();SOURCE=(d.OLD/'discovery02.py').read_bytes()
PROFILE=json.loads(PROFILE_RAW)
BASE=json.loads((d.OLD/'actual-cpu-discovery02-result.json').read_bytes())

class HostDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.actual=copy.deepcopy(BASE);self.actual['approval_reference']='SYNTHETIC_GPU_HOST_ONLY_NO_ACTUAL_HARDWARE'
        self.actual['host_signals']={'COLAB_GPU':'1','TPU_present':False,'nvidia_device_entry_names':['nvidia0']}
        self.attempt='gpu-host-synthetic01';self.cmd=d.discovery_argv(self.attempt,self.actual['approval_reference'])
        snapshot={'state':'EXACT','file_count':165,'digest':d.digest(json.dumps(d.expected_map(PROFILE),sort_keys=True).encode())}
        self.launch={'phase':d.PHASE,'attempt_id':self.attempt,'source_sha256':d.SOURCE_SHA,'profile_sha256':d.PROFILE_SHA,
                     'command':self.cmd,'child_returncode':0,'cleanup_accepted':True,'error':None,'launcher_seconds':.2,
                     'root_snapshot_before':copy.deepcopy(snapshot),'root_snapshot_after':copy.deepcopy(snapshot),
                     'project_source_file_count':165,'project_source_snapshot_sha256_before':snapshot['digest'],
                     'project_source_snapshot_sha256_after':snapshot['digest'],
                     'result_path':d.STAGING_TEXT+'/'+self.attempt+'/result.json','model_gpu_install_calls':0}
    def rpc(self,inline=True):
        raw=json.dumps(self.actual,ensure_ascii=False,indent=2).encode()
        launch=copy.deepcopy(self.launch);launch['result_bytes']=len(raw);launch['result_sha256']=d.digest(raw)
        launch['status'],_=d.classify_result(launch,self.actual,PROFILE)
        if inline:launch['inline_result_text']=raw.decode()
        text=json.dumps(launch,ensure_ascii=False)+'\n'
        self.assertLessEqual(len(text.encode()),48000)
        rpc=json.dumps({'is_error':False,'structured_content':{'outputs':[{'output_type':'stream','name':'stdout','text':[text]}]}}).encode()
        return rpc,raw,launch
    def test_ROOT_absent_snapshot_and_cold_without_target_no_writes(self):
        with tempfile.TemporaryDirectory(dir=W/'trial01') as td:
            root=Path(td)/'absent';self.assertTrue(root.resolve().is_relative_to(W.resolve()))
            self.assertEqual(d.project_snapshot(root,{'never/read': 'a'*64}),{'state':'ABSENT','file_count':0,'digest':None});self.assertFalse(root.exists())
        self.actual.update(status='COLD_ROOT_ABSENT',source_sha256={},target_probe=None,child=None)
        for key in ('root_snapshot_before','root_snapshot_after'):self.launch[key]={'state':'ABSENT','file_count':0,'digest':None}
        self.launch['project_source_file_count']=0
        rpc,_,_=self.rpc();_,_,receipt=d.derive_receipt(rpc,PROFILE,'SYNTHETIC_REVIEW_ONLY')
        self.assertEqual(receipt['status'],'COLD_DISCOVERY_NOT_GPU_READY_NO_INSTALL_AUTHORITY')
        self.assertIsNone(receipt['native_target_cleanup']);self.assertFalse(receipt['install_authority'])
    def test_warm_needs_generic_identity_bothclean165_and_indication(self):
        rpc,raw,launch=self.rpc();l,b,receipt=d.derive_receipt(rpc,PROFILE,'SYNTHETIC_REVIEW_ONLY')
        self.assertEqual(b,raw);self.assertEqual(receipt['launcher_sha256'],d.digest(l))
        self.assertEqual(receipt['raw_rpc_sha256'],d.digest(rpc));self.assertEqual(receipt['result_sha256'],d.digest(raw))
        self.assertEqual(receipt['status'],'VERIFIED_ACTUAL_WARM_GPU_HOST_DISCOVERY_NOT_GPU_READY')
        self.assertEqual(receipt['origin_kind'],'LOCAL_DERIVED_RECEIPT_FROM_VERIFIED_RPC')
    def test_CPU_or_missing_nativecleanup_and_164_sources_stop(self):
        for case in ('cpu','nativecleanup','launchercleanup','164','TPU','boolclock'):
            with self.subTest(case=case):
                olda,oldl=copy.deepcopy(self.actual),copy.deepcopy(self.launch)
                if case=='cpu':self.actual['host_signals']=copy.deepcopy(BASE['host_signals'])
                if case=='nativecleanup':self.actual['child']['cleanup_accepted']=None
                if case=='launchercleanup':self.launch['cleanup_accepted']=False
                if case=='164':self.launch['root_snapshot_after']['file_count']=164
                if case=='TPU':self.actual['host_signals']['TPU_present']=True
                if case=='boolclock':self.launch['launcher_seconds']=False
                self.assertEqual(d.classify_result(self.launch,self.actual,PROFILE)[0],'STOP_RETAIN_PARTIAL_NO_RERUN')
                self.actual,self.launch=olda,oldl
    def test_changed_profile_source_ABI_and_attempt_labels_stop(self):
        for case in ('source','profile','abi','cpu-attempt','late'):
            with self.subTest(case=case):
                olda,oldl=copy.deepcopy(self.actual),copy.deepcopy(self.launch)
                if case=='source':self.actual['controller_source_sha256_after']='f'*64
                if case=='profile':self.launch['profile_sha256']='f'*64
                if case=='abi':self.actual['host_abi']['gil_disabled']=False
                if case=='cpu-attempt':self.launch['attempt_id']='cpu-readonly02'
                if case=='late':self.launch['launcher_seconds']=30.01
                self.assertEqual(d.classify_result(self.launch,self.actual,PROFILE)[0],'STOP_RETAIN_PARTIAL_NO_RERUN')
                self.actual,self.launch=olda,oldl
    def test_cold_venv_absent_is_not_bootstrap_or_install_authority(self):
        self.actual.update(status='COLD_VENV_ABSENT',target_probe=None,child=None)
        rpc,_,_=self.rpc();_,_,receipt=d.derive_receipt(rpc,PROFILE,'SYNTHETIC')
        self.assertEqual(receipt['status'],'COLD_DISCOVERY_NOT_GPU_READY_NO_INSTALL_AUTHORITY')
        self.assertEqual(receipt['actual_status'],'COLD_VENV_ABSENT')
    def test_payload_SHA_and_external_retrieval_exact_bytes(self):
        rpc,raw,_=self.rpc(inline=False);_,missing,receipt=d.derive_receipt(rpc,PROFILE,'SYNTHETIC')
        self.assertIsNone(missing);self.assertEqual(receipt['status'],'RETRIEVAL_REQUIRED_NOT_ACCEPTED')
        _,b,receipt=d.derive_receipt(rpc,PROFILE,'SYNTHETIC',raw);self.assertEqual(b,raw)
        self.assertTrue(receipt['status'].startswith('VERIFIED_ACTUAL_WARM'))
        with self.assertRaises(ValueError):d.derive_receipt(rpc,PROFILE,'SYNTHETIC',raw+b' ')
    def test_actualRPC_error_and_output_cap_reject(self):
        with self.assertRaises(ValueError):d.decode_rpc(b'x'*(256*1024+1))
        for value in ({'is_error':True},{'is_error':False,'data':{'outputs':[{'output_type':'error'}]}},
                      {'is_error':False,'data':{'outputs':[{'output_type':'stream','name':'stdout','text':'x'*48001}]}}):
            with self.subTest(),self.assertRaises(ValueError):d.decode_rpc(json.dumps(value).encode())
    def test_rendered_cell_AST_exact_source02_CLI_and_root_absence_path(self):
        code,command=d.render_cell(SOURCE,PROFILE_RAW,self.attempt,self.actual['approval_reference']);ast.parse(code)
        self.assertEqual(command,self.cmd);self.assertLess(len(json.dumps({'cellIndex':0,'language':'python','code':code}).encode()),48000)
        spec=importlib.util.spec_from_file_location('old_parser_definitions_only',d.OLD/'discovery02.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        parsed=m._parser().parse_args(command[5:]);self.assertEqual(parsed.attempt_id,self.attempt)
        self.assertNotIn('assert os.name==\'posix\' and PROJECT.is_dir()',code)
        self.assertIn('before=project_snapshot(PROJECT,expected_map(profile))',code)
        self.assertNotIn('is_available(',code)
    def test_required_and_operation_specific_CLI_flags(self):
        base=['--operation','prepare','--mode',d.PHASE,'--attempt-id',self.attempt,'--approval-reference',self.actual['approval_reference']]
        d.validate_options(d.parser().parse_args(base))
        receive=['--operation','receive','--mode',d.PHASE,'--attempt-id',self.attempt,'--rpc-json','/actual/rpc.json','--receipt-id','gpu-host-receipt01','--parent-review-reference','SYNTHETIC']
        d.validate_options(d.parser().parse_args(receive))
        for key in ('--operation','--mode','--attempt-id'):
            missing=base.copy();i=missing.index(key);del missing[i:i+2]
            with self.subTest(key=key),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):d.parser().parse_args(missing)
        for flag in ('--rpc-json','--parent-review-reference','--receipt-id'):
            missing=receive.copy();i=missing.index(flag);del missing[i:i+2]
            with self.subTest(flag=flag),self.assertRaises(ValueError):d.validate_options(d.parser().parse_args(missing))
        with self.assertRaises(ValueError):d.validate_options(d.parser().parse_args(base[:-2]))

if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HostDiscoveryTests))
    print(json.dumps({'methods':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'actualRPC_target_GPU_hardware_model_install_calls':0,'scope':'Synthetic in-memory metadata only; no fake fresh GPU result/receipt saved.'}))
    raise SystemExit(0 if r.wasSuccessful() else 1)
