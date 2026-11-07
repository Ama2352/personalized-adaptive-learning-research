"""Nhận ZIP tổng hợp qua MCP, kiểm chunks/ZIP/output SHA trước ghi artifacts."""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
import zipfile

root=Path.cwd()
private=root/'artifacts/akt/private/colab-bridge/session-1990f93a9bc34123b21dd07aa93c1207'
chunks={};inventory=[]
for p in private.glob('result-*.json'):
    if p.stat().st_size<50000:continue
    raw_bytes=p.read_bytes()
    if b'SYNTHETIC_ARTIFACT_CHUNK03' not in raw_bytes:continue
    value=json.loads(raw_bytes)
    outputs=(value.get('structured_content') or {}).get('outputs',[])
    assert not value['is_error'] and not any(o.get('output_type')=='error' for o in outputs)
    raw=''.join(''.join(o.get('text',[])) for o in outputs if o.get('output_type')=='stream')
    try:content=json.loads(raw)
    except json.JSONDecodeError:content=json.loads(json.loads('"'+raw+'"'))
    if content.get('status')!='SYNTHETIC_ARTIFACT_CHUNK03':continue
    index=content['index']
    assert index not in chunks and content['count']==144
    assert content['archive_sha256']=='64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188'
    data=base64.b64decode(content['base64'],validate=True)
    assert len(data)==content['bytes'] and hashlib.sha256(data).hexdigest()==content['sha256']
    chunks[index]=data
    inventory.append({'index':index,'bytes':len(data),'chunk_sha256':content['sha256'],
                      'receipt':str(p.relative_to(root)),'receipt_sha256':hashlib.sha256(raw_bytes).hexdigest()})
if len(chunks)!=144:
    print(json.dumps({'status':'TRANSFER_IN_PROGRESS','verified_chunks':len(chunks),'expected':144}))
    raise SystemExit(0)
assert sorted(chunks)==list(range(144))
data=b''.join(chunks[index] for index in range(144))
assert len(data)==28657701
digest=hashlib.sha256(data).hexdigest()
assert digest=='64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188'
target=root/'artifacts/akt/colab/actual-cuda-synthetic-20261107-01.zip'
if target.exists():assert target.read_bytes()==data
else:
    with target.open('xb') as stream:stream.write(data)
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    manifest=json.loads(archive.read('RESULT_MANIFEST.json'))
    assert manifest['bundle_sha256']=='ddb35b8eb39906eea6ca6d1ad629d849d398ce4111ee95f3eca64ed9d369155b'
    assert manifest['cpu_portability_pass'] and manifest['cuda_lifecycle_pass']
    assert set(archive.namelist())==set(manifest['files'])|{'RESULT_MANIFEST.json'}
    assert len(archive.namelist())<200 and sum(i.file_size for i in archive.infolist())<100*1024*1024
    for name,expected in manifest['files'].items():
        path=PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name
        assert hashlib.sha256(archive.read(name)).hexdigest()==expected
    suites=ET.fromstring(archive.read('cpu-tests.xml'))
    cases=list(suites.iter('testcase'))
    assert len(cases)==505 and not any(list(suites.iter(t)) for t in ('failure','error','skipped'))
    lifecycle=json.loads(archive.read('synthetic-run/report.json'))
    recovery=json.loads(archive.read('synthetic-recovery/report.json'))
    assert lifecycle['status']=='passed_synthetic' and lifecycle['device']=='cuda'
    assert lifecycle['cuda_lifecycle'] and lifecycle['gate4_pass'] is False
    assert lifecycle['step']['valid_targets']==400 and lifecycle['step']['parameter_updated']
    assert lifecycle['export']['prediction_rows']==400 and lifecycle['export']['status']=='complete'
    assert recovery['status']=='passed_synthetic_recovery' and recovery['device']=='cuda'
    assert recovery['gate4_pass'] is False and recovery['cuda_mid_epoch_resume_verified']
    assert recovery['optimizer_updates_total_all_processes']==10
    assert recovery['training_targets_per_logical_branch']==17 and recovery['updates_per_complete_branch']==5
    for key in ('optimized_row_ledger_exact','rng_exact','sampler_exact','interrupted_source_immutable'):
        assert recovery[key]
    output=root/'experiments/akt/results/colab-actual-cuda-20261107-01'
    output.mkdir(parents=True,exist_ok=False)
    for name in archive.namelist():
        path=output/name
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(archive.read(name))
    for name,expected in manifest['files'].items():assert hashlib.sha256((output/name).read_bytes()).hexdigest()==expected
report={'status':'VERIFIED_ACTUAL_COLAB_CUDA_SYNTHETIC','zip':str(target.relative_to(root)),
        'zip_bytes':len(data),'zip_sha256':digest,'output_directory':str(output.relative_to(root)),
        'output_files':len(manifest['files']),'cpu_tests':505,'cpu_failures':0,'cpu_errors':0,'cpu_skips':0,
        'lifecycle':{k:lifecycle[k] for k in ('status','gpu_name','training_seconds','peak_vram_bytes','gate4_pass')},
        'recovery':{k:recovery[k] for k in ('status','elapsed_seconds','cuda_mid_epoch_resume_verified','max_state_abs_delta','max_prediction_abs_delta','gate4_pass')},
        'chunks':sorted(inventory,key=lambda x:x['index']),
        'scope':'Bounded synthetic CUDA lifecycle/controlled optimizer-boundary recovery only; no full training, realdata, Modal, hard-kill/preemption or RQ efficacy'}
with (root/'artifacts/akt/colab/actual-cuda-verification-20261107.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='chunks'},ensure_ascii=False))
