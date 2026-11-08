"""Kiểm metadata/hashes actual discovery đã nhận; không gọi probe lại."""
import hashlib,json,re
from pathlib import Path
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
p=load(W/'discovery_profile01.json');r=load(W/'actual-cpu-discovery02-result.json');launch=load(W/'actual-cpu-discovery02-launcher.json');accept=load(W/'actual-cpu-discovery02-acceptance.json')
assert sha(W/'actual-cpu-discovery02-result.json')==launch['result_sha256']==accept['result_sha256']=='b0032f9d556d0ca3655d4bafa6d010d30feca05e1d4d6c02ac8148757d8c4ec9'
assert r['status']=='WARM_CANDIDATE_REQUIRES_AUDIT' and launch['status']=='COMPLETED_CPU_DISCOVERY_ONLY_NOT_GPU_READY'
expected={**p['source_files'],**{'artifacts/akt/dependencies/upstream/'+k:v for k,v in p['upstream_files'].items()},p['lock_relative']:p['lock_sha256']}
assert len(p['source_files'])==161 and len(expected)==165 and r['source_sha256']==expected
semantic=hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()
assert launch['project_source_snapshot_sha256_before']==launch['project_source_snapshot_sha256_after']==semantic
assert r['controller_source_sha256_before']==r['controller_source_sha256_after']==sha(W/'discovery02.py')
assert r['profile_file_sha256_before']==r['profile_file_sha256_after']==sha(W/'discovery_profile01.json')
assert r['child']['returncode']==launch['child_returncode']==0
assert r['child']['cleanup_accepted'] is True and launch['cleanup_accepted'] is True
assert 0<=r['elapsed_seconds']<=30 and 0<=launch['launcher_seconds']<=30
q=r['target_probe'];assert q['abi']==r['host_abi']==p['expected_host']
assert q['no_site']==q['isolated']==1 and q['prefix']==q['base_prefix']=='/usr'
assert q['purelib']=='/content/KLTN_GPU08_20261108_01/.venv/lib/python3.13/site-packages'
assert q['cuda_visible_devices']==q['nvidia_visible_devices']=='' and q['heavy_modules_imported']==[]
versions={re.sub('[-_.]+','-',row['name']).lower():row['version'] for row in q['distributions']}
assert len(q['distributions'])==len(versions)==44 and versions==p['package_versions']
assert sum(n.startswith('nvidia-') for n in versions)==14
assert q['origins']['pip'] is None and len([v for v in q['origins'].values() if v is not None])==8
assert r['gpu_queries']==r['model_imports']==r['installs']==0
first=load(W/'actual-cpu-discovery01-acceptance.json');assert first['status']=='STOP_RETAIN_EVIDENCE_NOT_ACCEPTED' and first['native_target_cleanup'] is None
logs=load(W/'actual-cpu-discovery01-existing-logs.json')['files']
for row in logs.values():assert hashlib.sha256(row['text'].encode()).hexdigest()==row['sha256'] and len(row['text'].encode())==row['bytes']
assert 'local/lib/python3.13/dist-packages' in logs['cpu-readonly01/target.stderr']['text']
record={'status':'INDEPENDENT_ACTUAL_READONLY_CPU_DISCOVERY_VERIFIED_NOT_GPU_READY','result_sha256':sha(W/'actual-cpu-discovery02-result.json'),'launcher_sha256':sha(W/'actual-cpu-discovery02-launcher.json'),'profile_sha256':sha(W/'discovery_profile01.json'),'source02_sha256':sha(W/'discovery02.py'),'source161_plus_upstream4_and_lock_dedup_count':165,'source_pre_post_snapshot_sha256':semantic,'actual44versions14nvidia_verified':True,'no_site_prefix_recorded_not_normal_venv_prefix':'/usr','launcher_and_native_cleanup_accepted':True,'source_seconds':r['elapsed_seconds'],'launcher_seconds':launch['launcher_seconds'],'module_imports_GPU_install_calls':0,'entrypoint_origin_fingerprints':8,'metadata_record_fingerprints':44,'failure01_raw_log_text_SHA_and_bytes_verified':True,'failure01_inner_cleanup_unknown_retained':True,'limits':'Metadata/source/origin fingerprints may serve as pre-switch baseline; not full RECORD origins/installed-site byte attestation, normal startup/import audit, target wheel tags or CUDA/hardware/worker readiness.'}
(W/'actual02-independent-verification.json').open('x',encoding='utf-8').write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record))
