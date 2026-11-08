"""Close operational failure and UNKNOWN process probe, no science execution."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
RUN='rq1-history-availability-20261108-01';DEST=ROOT/'research_tracking/runs'/RUN
assert not DEST.exists()
FAIL=PREP/'availability-replay-attempt01';PROBE=PREP/'windows-launch-probe01'
failure=read(FAIL/'run.json');probe=read(PROBE/'probe-attempt01/probe.json')
assert sha(FAIL/'run.json')=='da6624953800bf52468aea4ed8b872ab2a6a50559096e0bda3d78515a0b20ba8'
assert sha(PROBE/'probe-attempt01/probe.json')=='1f2508c7f89b58c005efd91393b724c5ccb70efdf7d8a147a504e011e475b504'
assert failure['status']=='REJECTED_RETAIN_NO_RETRY_NO_PARTIAL_CLAIM' and failure['returncode']==1
assert probe['status']=='UNKNOWN_OR_REJECTED_RETAIN_PURE_PROBE' and probe['returncode']==0
assert probe['cleanup_accepted'] is False and probe['explicit_torch_native_collector_model_gpu_remote_calls']==0
assert failure['source_input_before_sha256']==failure['source_input_after_sha256']
assert probe['source_before_sha256']==probe['source_after_sha256']
assert all(sha(ROOT/n)==d for n,d in failure['source_input_after_sha256'].items())
assert all(sha(ROOT/n)==d for n,d in probe['source_after_sha256'].items())
assert all(sha(FAIL/n)==d for n,d in failure['outputs_sha256'].items())
assert set(p.name for p in FAIL.iterdir())=={'dispatch.json','outer_failure.log','run.json','stderr.log','stdout.log'}
assert not any((FAIL/n).exists() for n in ('worker_run.json','case_ledger.jsonl','endpoint_records.jsonl'))
assert probe['availability_cumulative_seconds_after']==failure['elapsed_seconds']+probe['elapsed_seconds']
assert probe['availability_cumulative_seconds_after']==0.845393699943088
mapping={}
def add(path,name):
 assert path.is_file() and not path.is_symlink() and name not in mapping
 mapping[name]=path
for name in ('dispatch.json','outer_failure.log','run.json','stderr.log','stdout.log'):add(FAIL/name,'attempt01__'+name)
for name in ('run_probe.py','child_probe.py','FINDINGS01.md'):add(PROBE/name,'probe__'+name)
for path in sorted((PROBE/'probe-attempt01').iterdir()):
 assert path.is_file() and path.stat().st_size<=65536
 add(path,'probe_attempt01__'+path.name)
for name in ('history_availability_worker.py','run_history_availability.py','history_availability_plan.json',
 'history_availability_proposed_cli.json','availability_source_preparation_receipt.json',
 'availability_attempt01_frozen.json','RQ1_CONTROLLED_HISTORY_REPLAY_DESIGN.md','pack_availability_failure01.py'):
 add(PREP/name,'source__'+name)
add(ROOT/'src/knowledge_tracing/evidence.py','evidence_helper.py')
before={name:{'source':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size}
 for name,path in mapping.items()}
raw_before={p.relative_to(ROOT).as_posix():sha(p) for p in [*FAIL.iterdir(),*(PROBE/'probe-attempt01').iterdir()]}
sources=set(mapping.values())|{ROOT/n for n in failure['source_input_after_sha256']}
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
note='''# RQ1 history availability — failure trước native và pure probe UNKNOWN

**Evidence verdict: FAILED_PRE_NATIVE_AND_METADATA_PROBE_UNKNOWN.**
Đây là archive vận hành, KHÔNG native replay PASS, model result, science sample
hoặc kết quả RQ. manifest.status=completed chỉ xác nhận archiver copy xong;
outcome.json giữ status thất bại/UNKNOWN của hai hoạt động nguyên gốc.

## Attempt01 thực tế

Outer0.3893691999837756s,RC1. Traceback workerline44 immediatePPIDassert trước
knowledge_tracing import48/NumPy62/pandas63/native loader64 và case loop.
Zero native constructor/predict/update/select/teacher/RNGdraw/optimizer calls
theo control flow/source/traceback; không suy từ missinglogs đơn thuần.
Không có worker_run/caseledger/endpoints. Raw5files và executedworker/outer/plan
giữ byte-identical,18source/inputSHA trước=sau. Không retry/repair/delete.

## Một pure process probe thực tế

0.4560244999593124s,childRC0 nhưng overallUNKNOWN/rejected. Live PID/ctime/exe
chain đo được outer25364→.venv redirector22140→actualPython36656; actual child
getppid22140 khác outerPID. sys.executable/sys.prefix vẫn project.venv.
Nguồn child chỉ stdlib/psutil; không import NumPy/pandas/Torch/knowledge_tracing.
Ownedconhost18612 còn ở instantaneous finalsnapshot, cleanup_accepted=false;
không kill và không gọi đây là persistentleak/cleanupPASS. Raw.exe thiếu drive
được giữ nguyên, không sửa thành đường dẫn đoán. Đây chỉ một launch được quan sát.

## Budget và boundary

Spent chung0.845393699943088/60s, remaining59.15460630005691s trước diagnostics
mới. Native call caps vẫn chưa dùng, không cấp60s mới hay tự dispatchrevision02.
Không xóa guard, không dùng global/base interpreter, không thay scientificcases.
Revision sau phải source-review ancestry+ownedJob membership trước GO và cleanup
ownedtree kể cảshimRC0. Findings là proposal, chưa chứng minh helper mới accepted.
Không scientific independent N; không model/teacher/world/data experiment.

## Truy vết

attempt01__* và probe_attempt01__* là raworiginalbytes; source__* là exactsources
đã chạy/plan/metadata/design. probe__FINDINGS01.md là note nhận định của reviewer,
không relabel rawprobe. copy_inventory.json ghi source→copy+SHA/size trước/sau;
source/input model files chưa execute chỉ có SHA trong original receipts/manifest,
không copy notebook/dataset/checkpoint hoặc privateRPC. Không sửa C13/C14/history
bins/full-empty bundles, rootindices/state/Git. Sau closure không sửa bundle.
'''
with record_evidence_run(ROOT,RUN,metadata={'kind':'OPERATIONAL_PRE_NATIVE_FAILURE_AND_PURE_PROCESS_METADATA_PROBE',
 'evidence_status':'FAILED_PRE_NATIVE_AND_METADATA_PROBE_UNKNOWN','native_replay_accepted':False,
 'archival_completion_is_not_scientific_acceptance':True,'new_independent_N':0,
 'native_model_teacher_world_rng_draw_optimizer_calls':0,
 'first_attempt_elapsed_seconds':failure['elapsed_seconds'],'probe_elapsed_seconds':probe['elapsed_seconds'],
 'availability_cumulative_seconds':probe['availability_cumulative_seconds_after'],
 'availability_original_cap_seconds':60,'probe_cleanup_accepted':False,'retry_performed':False},
 sources=sorted(sources),note=note) as out:
 for name,path in mapping.items():
  with (out/name).open('xb') as f:f.write(path.read_bytes())
  assert sha(out/name)==before[name]['sha256']
 after={name:sha(path) for name,path in mapping.items()}
 assert all(after[n]==i['sha256'] for n,i in before.items())
 assert all(sha(ROOT/n)==d for n,d in raw_before.items())
 outcome={'status':'FAILED_PRE_NATIVE_AND_METADATA_PROBE_UNKNOWN',
  'attempt01_status':failure['status'],'probe_status':probe['status'],
  'attempt01_receipt_sha256':sha(FAIL/'run.json'),'probe_receipt_sha256':sha(PROBE/'probe-attempt01/probe.json'),
  'prior_spent_seconds':failure['elapsed_seconds'],'probe_seconds':probe['elapsed_seconds'],
  'cumulative_seconds':probe['availability_cumulative_seconds_after'],'original_cap_seconds':60,
  'remaining_before_new_diagnostics_seconds':60-probe['availability_cumulative_seconds_after'],
  'native_model_calls':0,'scientific_sample_or_result':False,'retry_or_science_reexecution_during_archival':False}
 (out/'outcome.json').write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'copy_inventory.json').write_text(json.dumps({'source_inventory_before':before,'source_sha256_after':after,
  'copied_output_sha256':{n:sha(out/n) for n in mapping},'exact_copy_identity':True,
  'pre_post_source_identity':True,'raw_original_paths_sha256_before_and_after':raw_before,
  'source_bindings_may_include_unexecuted_model_source':'SHA only; native source imports not reached'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 extras=['README.md','execution.log','outcome.json','copy_inventory.json','check_ignore.json','stage-paths.txt','files-to-force-add.txt','manifest.json']
 paths=sorted(f'research_tracking/runs/{RUN}/{n}' for n in [*mapping,*extras])
 assert all(not any(c in n for c in '\t\r\n') for n in paths)
 check=subprocess.run(['git','check-ignore','--',*paths],cwd=ROOT,text=True,capture_output=True)
 assert check.returncode in (0,1),(check.returncode,check.stderr)
 ignored=check.stdout.splitlines();assert set(ignored)<=set(paths)
 (out/'check_ignore.json').write_text(json.dumps({'argv':['git','check-ignore','--',*paths],
  'returncode':check.returncode,'ignored_paths':ignored,'stdout':check.stdout,'stderr':check.stderr},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'stage-paths.txt').write_text(''.join(n+'\n' for n in paths),encoding='utf-8')
 (out/'files-to-force-add.txt').write_text(''.join(n+'\n' for n in ignored),encoding='utf-8')
verification=verify_evidence_bundle(DEST);manifest=read(DEST/'manifest.json')
assert set(p.name for p in DEST.iterdir())==set(manifest['outputs_sha256'])|{'manifest.json'}
assert all(sha(ROOT/n)==d for n,d in manifest['sources_sha256'].items())
assert all(sha(ROOT/n)==d for n,d in raw_before.items())
whitespace={}
for n in manifest['outputs_sha256']:
 bad=[i for i,line in enumerate((DEST/n).read_text(encoding='utf-8').splitlines(),1) if line.endswith((' ','\t'))]
 if bad:whitespace[n]=bad
result={**verification,'evidence_status':'FAILED_PRE_NATIVE_AND_METADATA_PROBE_UNKNOWN',
 'manifest_sha256':sha(DEST/'manifest.json'),'copies':len(mapping),'source_bindings':len(manifest['sources_sha256']),
 'all_raw_and_source_copy_prepost_sha_exact':True,'raw_original_files':len(raw_before),
 'ignored_paths':ignored,'raw_whitespace_paths_lines':whitespace,
 'bundle_bytes':sum(p.stat().st_size for p in DEST.iterdir()),'new_native_model_or_process_probe_execution':False}
with (PREP/'availability_failure01_closure_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
