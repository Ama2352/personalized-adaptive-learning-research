"""Archive actual Colab artifacts; không model/GPU/runtime execution."""
import ast,base64,csv,hashlib,io,json,os,re,sys,zipfile
from pathlib import Path,PurePosixPath
import xml.etree.ElementTree as ET
ROOT=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
RUN='colab-cuda-synthetic-20261107-01'
C='artifacts/akt/colab/';L='artifacts/akt/local-tests/';E='experiments/akt/results/colab-actual-cuda-20261107-01/'
Z=C+'actual-cuda-synthetic-20261107-01.zip'
ZS='64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188'
BS='ddb35b8eb39906eea6ca6d1ad629d849d398ce4111ee95f3eca64ed9d369155b'
HISTORICAL_HEAD='e7dcf6b63a92bb532663eec40948b835f5b7155f'
RR='artifacts/akt/private/colab-bridge/session-1990f93a9bc34123b21dd07aa93c1207/result-03aa18b6c7e24e0ea65a021041b7f6e9.json'
def h(data):return hashlib.sha256(data).hexdigest()
def sha(p):return h(p.read_bytes())
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def transcript(raw):
 out=raw['structured_content']['outputs']
 assert not raw.get('is_error',False) and not any(o.get('output_type')=='error' for o in out)
 return ''.join(''.join(o.get('text',[])) if isinstance(o.get('text',[]),list) else o.get('text','') for o in out if o.get('output_type')=='stream')
def safe_raw(name):
 text=(ROOT/name).read_text(encoding='utf-8')
 assert 'SYNTHETIC_ARTIFACT_CHUNK03' not in text and '"base64"' not in text
 assert not re.search(r'(?i)(authorization\s*[:=]\s*[\"\x27]?(?:bearer|basic)|sk-proj-|ghp_|BEGIN [A-Z ]*PRIVATE KEY)',text)
 return json.loads(text)
proof=load(C+'actual-cuda-verification-20261107.json');data=(ROOT/Z).read_bytes()
assert proof['status']=='VERIFIED_ACTUAL_COLAB_CUDA_SYNTHETIC'
assert len(data)==proof['zip_bytes']==28657701 and h(data)==proof['zip_sha256']==ZS
manifest=load(E+'RESULT_MANIFEST.json')
assert len(manifest['files'])==proof['output_files']==44 and manifest['bundle_sha256']==BS
assert manifest['cpu_portability_pass'] and manifest['cuda_lifecycle_pass']
outputs=[]
with zipfile.ZipFile(io.BytesIO(data)) as z:
 assert set(z.namelist())=={*manifest['files'],'RESULT_MANIFEST.json'}
 assert json.loads(z.read('RESULT_MANIFEST.json'))==manifest
 assert len(z.infolist())<200 and sum(i.file_size for i in z.infolist())<100*1024*1024
 for name,expected in manifest['files'].items():
  p=PurePosixPath(name)
  assert not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name
  local=ROOT/E/name
  assert local.resolve().is_relative_to((ROOT/E).resolve()) and not local.is_symlink()
  assert sha(local)==expected==h(z.read(name)),name
  outputs.append({'original_path':(Path(E)/name).as_posix(),'manifest_key':name,'bytes':local.stat().st_size,'sha256':expected,'small_copy':local.suffix in {'.json','.txt','.log','.xml','.csv'}})
assert {p.relative_to(ROOT/E).as_posix() for p in (ROOT/E).rglob('*') if p.is_file()}=={*manifest['files'],'RESULT_MANIFEST.json'}
chunks=proof['chunks'];assert len(chunks)==144 and [r['index'] for r in chunks]==list(range(144))
offset=0
for r in chunks:
 chunk=data[offset:offset+r['bytes']]
 assert len(chunk)==r['bytes'] and h(chunk)==r['chunk_sha256']
 assert sha(ROOT/r['receipt'])==r['receipt_sha256'];offset+=len(chunk)
assert offset==len(data)
cpu=load(E+'cpu-acceptance.json')
assert cpu['status']=='PASS' and cpu['counts']=={'tests':505,'failures':0,'errors':0,'skipped':0}
xml=ET.parse(ROOT/(E+'cpu-tests.xml')).getroot()
assert len(list(xml.iter('testcase')))==505 and not any(list(xml.iter(t)) for t in ('failure','error','skipped'))
assert '505 passed, 2 deselected in 117.23s' in (ROOT/(E+'cpu-tests.log')).read_text(encoding='utf-8')
life=load(E+'synthetic-run/report.json');rec=load(E+'synthetic-recovery/report.json')
assert life['status']=='passed_synthetic' and life['device']=='cuda' and life['gpu_name']=='Tesla T4' and not life['gate4_pass']
assert life['step']['valid_targets']==400 and life['step']['parameter_updated'] and life['export']['prediction_rows']==400
assert life['export']['status']=='complete' and life['peak_vram_bytes']==187200000
assert abs(life['training_seconds']-.916326332999688)<1e-12
assert rec['status']=='passed_synthetic_recovery' and rec['device']=='cuda' and rec['gpu_name']=='Tesla T4' and not rec['gate4_pass']
assert rec['cuda_mid_epoch_resume_verified'] and rec['training_targets_per_logical_branch']==17
assert rec['updates_per_complete_branch']==5 and rec['optimizer_updates_total_all_processes']==10
assert rec['floating_atol']==rec['floating_rtol']==1e-5
assert rec['max_state_abs_delta']==rec['max_prediction_abs_delta']==0
assert abs(rec['elapsed_seconds']-28.94393326799991)<1e-12
for key in ('optimized_row_ledger_exact','rng_exact','sampler_exact','interrupted_source_immutable'):assert rec[key]
phases={p:load(E+'synthetic-recovery/'+p+'/phase.json') for p in ('continuous','interrupted','resumed')}
assert [r['committed_steps'] for r in phases.values()]==[5,2,5]
assert [len(r['optimized_rows_this_process']) for r in phases.values()]==[17,7,10]
assert len({r['pid'] for r in phases.values()})==3
assert phases['continuous']['optimized_rows_this_process']==phases['interrupted']['optimized_rows_this_process']+phases['resumed']['optimized_rows_this_process']
nbsha=sha(ROOT/'notebooks/akt_colab_synthetic.ipynb')
assert nbsha=='e75004d19a500ad562d7e7a11656158fae4cb74c8fc74c8fd389214e566616a7'
nb=load('notebooks/akt_colab_synthetic.ipynb');code=[c for c in nb['cells'] if c['cell_type']=='code']
assert all(not c.get('outputs') and c.get('execution_count') is None for c in code)
boot=next(''.join(c['source']) for c in code if c['id']=='akt-bootstrap')
assign={n.targets[0].id:n.value for n in ast.parse(boot).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
sz=base64.b64decode(ast.literal_eval(assign['BUNDLE_BASE64']),validate=True);assert h(sz)==BS
bundle=load(E+'BUNDLE_MANIFEST.json');assert len(bundle['files'])==139
sourcechecks=[]
with zipfile.ZipFile(io.BytesIO(sz)) as z:
 assert json.loads(z.read('BUNDLE_MANIFEST.json'))==bundle
 for name,expected in bundle['files'].items():
  payload=z.read(name);assert h(payload)==expected
  local=ROOT/name;actual=sha(local);transform=bundle.get('notebook_copy_transforms',{}).get(name)
  if transform:
   assert actual==transform['original_sha256'],name
   assert [c.get('source') for c in json.loads(local.read_text(encoding='utf-8'))['cells']]==[c.get('source') for c in json.loads(payload)['cells']],name
  else:assert actual==expected,(name,actual,expected)
  sourcechecks.append({'path':name,'local_sha256':actual,'embedded_sha256':expected,'declared_notebook_transform':transform,'verified':True})
head=(ROOT/'.git/HEAD').read_text().strip()
if head.startswith('ref: '):head=(ROOT/'.git'/head[5:]).read_text().strip()
pairs=[(r['original_path'],'result__'+r['manifest_key'].replace('/','__')) for r in outputs if r['small_copy']]
pairs += [(E+'RESULT_MANIFEST.json','RESULT_MANIFEST_original.json'),(C+'actual-cuda-verification-20261107.json','receive_verification_144chunks.json'),('notebooks/akt_colab_synthetic.ipynb','akt_colab_synthetic_v12_snapshot.ipynb'),(L+'prepare_colab_v12.py','prepare_colab_v12.py'),(L+'prepare_colab_chunk_request.py','prepare_colab_chunk_request.py'),(L+'receive_colab_chunks03.py','receive_colab_chunks03.py'),(L+'prepare_colab_release03.py','prepare_colab_release03.py'),(C+'requests/add-runtime-release03.json','runtime_release03_request.json'),(RR,'runtime_release03_raw_receipt.json'),('scripts/akt/synthetic_device_probe.py','synthetic_device_probe_source.py'),('scripts/akt/synthetic_recovery_probe.py','synthetic_recovery_probe_source.py'),('src/knowledge_tracing/evidence.py','evidence_helper_source.py'),('research_tracking/reports/colab_cuda_acceptance_20261107.md','parent_colab_cuda_acceptance_report.md'),('research_tracking/reports/colab_cuda_adversarial_review_20261107.md','parent_colab_cuda_adversarial_review.md')]
stages=[]
for phase in ('bootstrap','setup','cpu','lifecycle','recovery','export'):
 name=C+'mcp-stage-'+phase+'03.json';r=load(name)
 assert r['status']=='PASS_CELL_OUTPUT' and r['phase']==phase and sha(ROOT/r['response_file'])==r['response_sha256']
 assert transcript(safe_raw(r['response_file']))==r['transcript'],phase
 pairs += [(name,'mcp_stage_'+phase+'03.json'),(r['response_file'],'mcp_stage_'+phase+'03_raw_response.json')]
 stages.append({'phase':phase,'receipt_sha256':sha(ROOT/name),'raw_response_sha256':r['response_sha256'],'transcript_exact':True})
release=transcript(safe_raw(RR))
assert 'KLTN_RUNTIME_RELEASE_REQUEST' in release and 'KLTN_RUNTIME_RELEASE_ACCEPTED' in release
request=load(C+'requests/add-runtime-release03.json')
assert 'runtime.unassign()' in request['code'] and 'nvidia-smi' in request['code']
inv=[{'source':s,'archived_as':d,'sha256_before_copy':sha(ROOT/s)} for s,d in pairs]
heavy=[r for r in outputs if not r['small_copy']]
assert sum(r['original_path'].endswith('.pt') for r in heavy)==13
assert sum(r['original_path'].endswith('.parquet') for r in heavy)==2
heavy.append({'original_path':Z,'bytes':len(data),'sha256':ZS,'small_copy':False,'role':'Verified transportZIP, keep original'})
import duckdb
parquets=[ROOT/E/'synthetic-run/predictions'/s['path'] for s in life['export']['shards']]
con=duckdb.connect()
try:
 cur=con.execute('SELECT * FROM read_parquet(?) ORDER BY source_row',[[str(p) for p in parquets]])
 columns=[d[0] for d in cur.description];rows=cur.fetchall()
finally:con.close()
assert len(rows)==400 and len({r[columns.index('source_row')] for r in rows})==400
text=os.environ.get('KLTN_CUDA_FINAL_PACK_SOURCE')
if text is None:text=Path(__file__).read_text(encoding='utf-8')
metadata={'kind':'ACTUAL_COLAB_T4_BOUNDED_SYNTHETIC_CUDA_LIFECYCLE_RECOVERY','schema_version':1,'actual_cpu':{'passed':505,'failures':0,'errors':0,'skips':0,'pytest_seconds':117.23,'explicit_deselections':cpu['explicit_deselections']},'actual_lifecycle':{'gpu':'Tesla T4','targets':400,'optimizer_steps':1,'training_seconds':life['training_seconds'],'peak_vram_bytes':187200000,'gate4_pass':False},'actual_recovery':{'targets_per_branch':17,'continuous_updates':5,'interrupted_updates':2,'resumed_updates':3,'total_updates_all_processes':10,'three_fresh_processes':True,'elapsed_seconds':rec['elapsed_seconds'],'max_state_abs_delta':0.,'max_prediction_abs_delta':0.,'floating_atol':1e-5,'floating_rtol':1e-5,'gate4_pass':False},'transfer':{'zip_sha256':ZS,'zip_bytes':len(data),'outputs_verified':44,'chunks_verified':144,'receipt_sha_verified':144,'base64_chunk_receipts_copied':0},'historical_source_git_head_reference':HISTORICAL_HEAD,'archive_git_head_at_preflight':head,'source_identity_vi':'Execution kitv12 bind historicalGit e7 cộng workingfiles verified bằng139SHA. ArchiveHEADe25 tách riêng; khôngcleanGit/HEADalone sourceidentity claim.','notebook_sha256':nbsha,'source_bundle_sha256':BS,'new_workload':{'model_training_steps':0,'gpu_cloud_calls':0,'dataset_queries':0,'synthetic_prediction_rows_read':400},'limits_vi':['Gate4false; khôngfulltrain/realdata/Junyi/Test/RQefficacy.','KhôngModal/Volume/hardkill/preemption/durabilityproof; same-runtime optimizerboundary recovery.','Khôngmove/copy.pt/Parquet/28MBZIPvàobundle; CSVderived400syntheticrows.','ReleaseAPIaccepted từreturnmarker; frontenddisconnect/cloudVMtermination chưaindependentlyverified.'],'pack_source_sha256':h(text.encode())}
note='''# Actual Colab T4 synthetic lifecycle và recovery — 07/11/2026

Chỉ archive actual artifacts đã chạy, không thêm model/GPU/cloud run hoặc sửa notebook. ZIP SHA64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188,28657701bytes; tự verify44RESULT_MANIFEST outputs trong ZIP/local,144chunk SHA và144response SHA. receive_verification_144chunks.json giữ hash/path metadata; không copy144Base64 receipts hoặc private auth. Giữ6stage03receipts/raw responses exact bytes.

Actual Linux/Colab CPU505pass0fail/error/skip117.23s với2explicit deselections(nativeCPUimport/frozenassignmentsrealdata); portable/software suite, không main realdataGate2. Actual TeslaT4 lifecycle400targets,1optimizer step0.916326333s,peakVRAM187200000bytes,export400predictions. Gate4false.

ActualT4 recovery17targets/branch,continuous5updates so với interrupt2+resume3;3fresh processes,total10updates28.943933268s. Target ledger/RNG/sampler/source immutability exact,max state/prediction absdelta0 với atol=rtol1e-5. Controlled optimizer boundary trong same runtime, không hardkill/preemption/runtime replacement/ModalVolume/durability proof. Không fulltraining/realdata/Holdout/RQefficacy.

Source execution identity là historical GitHEAD e7dcf6b63a92bb532663eec40948b835f5b7155f cộng working-file changes verify139source SHA, không cleanGit/HEADalone claim. Archive HEAD hiện e25 là commit sau execution, ghi riêng trong metadata/helper manifest. Exact local notebookv12 SHA e75004d1... và embedded sourcebundle ddb35b8e... khớp returned manifest. Ba Paper notebooks chỉ strip outputs/metadata trong bundle copies; kiểm original SHA và cell source equality, không sửa historical notebooks.

Small JSON/log/XML/TXT copy theo inventory. synthetic_predictions.csv là derived400unique rows đọc2verified synthetic Parquet, không original CSV từ Colab. .pt/Parquet/28MB ZIP giữ vị trí gốc; large_file_inventory.json giữ locations/sizes/SHA, không unpickle checkpoints. archive_copy_inventory.json có SHA trước/sau copy và manifest hash mọi output.

Guarded release03 kiểm đúng workspace/ZIP/144chunks và GPU worker trước unassign; raw receipt có KLTN_RUNTIME_RELEASE_ACCEPTED. Official [google.colab.runtime.unassign](https://raw.githubusercontent.com/googlecolab/colabtools/main/google/colab/runtime.py) lines13–35 raises nếu HTTPstatus khác200 rồi request frontend disconnect. HTTP200 APIacceptance là suy ra có điều kiện từ return và reference code, không rawHTTPstatus capture/independent cloudlist/frontenddisconnect verification. Không gọi release thêm hoặc đụng runtime khác.

Một archive preflight guard trước bundle creation đã fail vì HEAD vừa đổi e7→e25. Đây là archive metadata guard, không GPU failure; không có output/source-file snapshot riêng cho invocation lỗi. Không regenerate ZIP/notebook/results; sửa cách phân biệt execution-source historical HEAD với archive HEAD rồi kiểm lại all artifact/source hashes. Lỗi tool launcher trước đó cũng không thực thi Python/GPU. Parent acceptance/adversarial reports được snapshot nguyên bytes.

Không sửa bundle sau closure. force_add_paths.txt liệt kê logs cần force-add; không sửa Git/.gitattributes/index/state/docs. Manifest có private-path/SHA references không có nghĩa cần commit private files. Parent review/commit riêng.
'''
source_paths=list(dict.fromkeys([s for s,d in pairs]+[r['original_path'] for r in heavy]+[r['receipt'] for r in chunks]+[r['path'] for r in sourcechecks]))
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=[ROOT/p for p in source_paths],note=note) as directory:
 (directory/'pack_evidence.py').write_bytes(text.encode('utf-8'))
 for r in inv:
  source=ROOT/r['source'];assert sha(source)==r['sha256_before_copy']
  target=directory/r['archived_as'];target.write_bytes(source.read_bytes())
  r['sha256_after_copy']=sha(target);r['exact_match']=r['sha256_after_copy']==r['sha256_before_copy'];assert r['exact_match']
 def put(name,value):(directory/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 put('archive_copy_inventory.json',inv);put('original_output_inventory.json',outputs);put('large_file_inventory.json',heavy)
 put('source_inventory_git_e7_working_files.json',{'historical_source_head_reference':HISTORICAL_HEAD,'archive_head_at_preflight':head,'git_clean_not_asserted':True,'notebook_sha256':nbsha,'embedded_bundle_sha256':BS,'files':sourcechecks})
 with (directory/'synthetic_predictions.csv').open('x',encoding='utf-8',newline='') as f:
  writer=csv.writer(f,lineterminator='\n');writer.writerow(columns);writer.writerows(rows)
 put('synthetic_prediction_csv_derivation.json',{'rows':400,'unique_source_rows':400,'columns':columns,'ordering':'source_row ascending','inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in parquets],'csv_sha256':sha(directory/'synthetic_predictions.csv'),'scope_vi':'Chỉ derived synthetic prediction artifacts, không dataset query/model inference.'})
 put('runtime_release_evidence.json',{'raw_receipt_sha256':sha(ROOT/RR),'transcript':release,'guarded_current_runtime':True,'api_return_accepted':True,'http200_inferred_not_raw_status_captured':True,'official_source_url':'https://raw.githubusercontent.com/googlecolab/colabtools/main/google/colab/runtime.py','official_source_lines':'13-35','official_source_checked_during_archive':True,'frontend_disconnect_independently_verified':False,'cloud_vm_termination_independently_verified':False,'new_runtime_actions_during_archive':0})
 put('archive_preflight_history.json',{'scope':'Archive preflight only, not GPU/model failure','failed_guard':'Historical e7 HEAD was incorrectly required to equal current archive HEAD after parent commit e25','failed_invocation_created_bundle':False,'failed_invocation_source_or_log_file_snapshot_available':False,'tool_traceback_location':'<cuda-evidence-pack> line84, AssertionError','resolution':'Separate historical sourcekit identity from current archive HEAD; reverify44outputs/139source hashes; no artifact regenerated','prior_launcher_issue':'MSIX packaged pwsh launcher failed before code execution; explicit native shell invocation works'})
 put('archive_validation.json',{'zip_sha_exact':ZS,'original_outputs_sha_exact':44,'chunk_sha_exact':144,'response_sha_exact':144,'stage_receipts':stages,'small_pre_post_copy_exact':len(inv),'pt_original_count':13,'parquet_original_count':2,'csv_derived_rows':400,'source_files_verified':139,'new_model_gpu_execution':False})
 force=[f'research_tracking/runs/{RUN}/'+n for n in ['execution.log']+[d for s,d in pairs if d.endswith('.log')]]
 (directory/'force_add_paths.txt').write_text('\n'.join(force)+'\n',encoding='utf-8')
verified=verify_evidence_bundle(directory)
closed=load('research_tracking/runs/'+RUN+'/manifest.json')
assert {p.name for p in directory.iterdir()}=={'manifest.json',*closed['outputs_sha256']}
assert all(sha(directory/n)==expected for n,expected in closed['outputs_sha256'].items())
print(json.dumps({'run':directory.relative_to(ROOT).as_posix(),'integrity':verified,'copied_small_files':len(inv),'exact_output_sha_count':len(closed['outputs_sha256']),'verified_original_outputs':44,'verified_chunks_and_receipts':144,'verified_source_files':139,'csv_rows':400,'heavy_original_files_retained':len(heavy),'runtime_release_archived':True,'manifest_sha256':sha(directory/'manifest.json'),'force_add_paths':force},ensure_ascii=False,indent=2))
