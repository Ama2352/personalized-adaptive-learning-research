"""Một H100/model outer, CPU chuẩn bị và sao lưu tách khỏi container."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import warnings

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')
sys.path[:0]=[str(ROOT/'scripts/akt')]

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def save(path,payload):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(payload,stream,ensure_ascii=False,indent=2)
        stream.write('\n')

def main(variant):
    import modal
    from modal_junyi_outer import create_outer_gpu_app
    accepted=json.loads((B/'MODAL_STAGING_ACCEPTANCE01.json').read_text())
    assert accepted['status']=='ALL_REMOTE_INPUT_BYTES_SHA256_VERIFIED'
    request_path=B/('REQUEST_'+variant+'_GPU01.json')
    request=json.loads(request_path.read_text())
    relative='requests/'+request['run_id']+'-'+variant.lower()+'-outer01.json'
    physical='/__modal/volumes/vo-dv1975utRQbmagCjA0brSe'
    entry=dict(path=physical+'/'+relative,sha256=sha(request_path))
    assert any(x['path']==entry['path'] and x['sha256']==entry['sha256'] for x in accepted['files'])
    ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json'
    ledger=json.loads(ledger_path.read_text())
    allocation='outer-'+variant.lower()+'-gpu-20261117-01'
    if not any(x['id']==allocation for x in ledger['new_allocations']):
        ledger['new_allocations'].append(dict(id=allocation,status='USER_APPROVED_OUTER_EVALUATION',
            reserved_upper_usd=.75,actual_cost_usd=None,gpu=True,evidence=str(request_path.relative_to(ROOT))))
        assert ledger['historical_usage_reserved_upper_usd']+sum(x['reserved_upper_usd'] for x in ledger['new_allocations'])+ledger['safety_and_final_inference_reserve_usd']<=30
        ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    auth=dict(workspace='honguyenminhsang2016',stage='gpu',allocation_id=allocation,
        reserved_usd=.75,request_sha256=entry['sha256'])
    save(B/(variant+'_GPU_AUTHORIZATION01.json'),auth)
    image=modal.Image.from_id('im-ifzJuCpP1yGdoDMSVIVgZz')
    packet=ROOT/'artifacts/akt/local-calibration/20261117/outer-source-guard-release/source'
    guard=packet/'src/knowledge_tracing/akt/research_junyi_window_cache.py'
    image=image.add_local_file(str(guard),'/opt/kltn/src/knowledge_tracing/akt/research_junyi_window_cache.py',copy=False)
    plan=json.loads((ROOT/'research_tracking/runs/junyi-outer-gpu-preparation-20261117-01/STAGING_PLAN01.json').read_text())
    for item in plan['scripts'].values():
        assert sha(item['local_path'])==item['sha256']
        image=image.add_local_file(item['local_path'],item['remote_image_path'],copy=False)
    volume=modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')
    app,predict=create_outer_gpu_app(image,volume)
    with modal.enable_output(),app.run(environment_name='main'):
        print(variant,'H100_OUTER_START_MAX300S_NO_RETRY',flush=True)
        result=predict.remote(entry,sha(ROOT/'scripts/akt/outer_gpu_worker.py'),auth,'run01')
        save(B/(variant+'_GPU_RESULT01.json'),result)
        assert result['status']=='OUTER_GPU_OPERATION_COMPLETE'
        assert result['result']['counts']['targets']==4137050
        assert result['result']['counts']['oov_targets']==144
        print(variant,'OUTER_NUMERIC_COMPLETE_GPU_RELEASE',flush=True)
    print('APP_STOPPED',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',required=True,choices=('A0','A1','A2','A3'))
    main(parser.parse_args().variant)
