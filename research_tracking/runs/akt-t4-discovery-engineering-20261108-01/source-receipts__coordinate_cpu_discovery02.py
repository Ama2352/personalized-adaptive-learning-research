"""Chuẩn bị/nhận RPC metadata; không tự gửi lệnh hoặc cấp GPU."""
import hashlib
import json
from pathlib import Path
import sys

work=Path(__file__).resolve().parent
root=work.parents[4]
private=root/'artifacts/akt/private/colab-bridge/session-a67c8207b6224b9398ad00cfa0876435'
requests=root/'artifacts/akt/colab/requests'
sha=lambda b:hashlib.sha256(b).hexdigest()
def snapshot(name):
    with (work/name).open('x',encoding='utf-8') as stream:
        json.dump([p.name for p in private.glob('result-*.json')],stream)
def new_rpc(name):
    old=set(json.loads((work/name).read_bytes()))
    found=[p for p in private.glob('result-*.json') if p.name not in old]
    assert len(found)==1, 'Wait actual RPC completion; never repeat remote operation'
    raw=found[0].read_bytes(); obj=json.loads(raw)
    assert obj.get('is_error') is False
    return obj.get('structured_content') or obj['data'],sha(raw)
mode=sys.argv[1]
if mode=='prepare-add':
    path=work/'request-add-cpu-discovery02.json';raw=path.read_bytes()
    assert sha(raw)=='d33db0ccdb6ea659a06883ba5a2ba7074d46ce914b6ccd983ae29d1e21c65cb6'
    target=requests/'gpu09-add-cpu-readonly-discovery02.json'
    before=dict(source=str(path.relative_to(root)),destination=str(target.relative_to(root)),bytes=len(raw),sha256_before=sha(raw))
    with (work/'request02-copy-before.json').open('x',encoding='utf-8') as stream:json.dump(before,stream)
    with target.open('xb') as stream:stream.write(raw)
    assert sha(target.read_bytes())==sha(path.read_bytes())==before['sha256_before']
    with (work/'request02-copy-after.json').open('x',encoding='utf-8') as stream:json.dump({**before,'sha256_after':sha(target.read_bytes())},stream)
    snapshot('rpc02-before-add.json')
    print('EXACT_REQUEST_COPIED_WITH_PRE_POST_SHA')
elif mode=='prepare-run':
    data,_=new_rpc('rpc02-before-add.json')
    assert set(data)=={'newCellId'}
    with (requests/'gpu09-run-cpu-readonly-discovery02.json').open('x',encoding='utf-8') as stream:
        json.dump({'cellId':data['newCellId']},stream)
    snapshot('rpc02-before-run.json')
    print('RUN_REQUEST_FROM_ACTUAL_CELL_RECEIPT')
elif mode=='receive':
    data,rpcsha=new_rpc('rpc02-before-run.json')
    outputs=data['outputs']
    assert not any(row.get('output_type')=='error' for row in outputs)
    text=''.join(''.join(row['text']) if isinstance(row['text'],list) else row['text']
        for row in outputs if row.get('output_type')=='stream' and row.get('name')=='stdout')
    assert len(text.encode())<=48000
    launch=json.loads(text)
    with (work/'actual-cpu-discovery02-launcher.json').open('x',encoding='utf-8') as stream:
        stream.write(text)
    if 'inline_result_text' not in launch:
        print(json.dumps({'status':'RETRIEVAL_REQUIRED_NOT_ACCEPTED','launcher_status':launch['status']}))
        raise SystemExit(2)
    raw=launch['inline_result_text'].encode()
    assert sha(raw)==launch['result_sha256'] and len(raw)==launch['result_bytes']
    actual=json.loads(raw)
    with (work/'actual-cpu-discovery02-result.json').open('xb') as stream:stream.write(raw)
    accepted=(launch['status']=='COMPLETED_CPU_DISCOVERY_ONLY_NOT_GPU_READY'
        and launch['cleanup_accepted'] is True and launch['child_returncode']==0
        and launch['project_source_snapshot_sha256_before']==launch['project_source_snapshot_sha256_after']
        and actual.get('child',{}).get('cleanup_accepted') is True
        and actual['status']=='WARM_CANDIDATE_REQUIRES_AUDIT')
    receipt=dict(status='VERIFIED_ACTUAL_WARM_CPU_DISCOVERY_NOT_GPU_READY' if accepted else 'STOP_RETAIN_EVIDENCE_NOT_ACCEPTED',
        raw_rpc_sha256=rpcsha,result_sha256=sha(raw),actual_status=actual['status'],
        launcher_cleanup=launch['cleanup_accepted'],native_target_cleanup=actual.get('child',{}).get('cleanup_accepted'),
        source_files=launch['project_source_file_count'],launcher_seconds=launch['launcher_seconds'],
        model_gpu_install_calls=0,scope='Actual read-only CPU environment evidence; no normal-site import audit/CUDA readiness/authorization.')
    with (work/'actual-cpu-discovery02-acceptance.json').open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2)
    print(json.dumps(receipt))
else:
    raise ValueError('unknown operation')
