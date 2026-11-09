"""Root bounded cached diagnostic, không chạy model, không retry."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
WORKER_SHA = '52ee0f409ad6752a3413e18565e31b95908dec57574739a8f76fe5aa01121b43'
CONTRACT_SHA = '5ba4d9da4fd98aeac4dd9ead2250b7f8252cb83c076e52cc6fa4242eb94b510a'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
OUTPUT = WORK/'reference-mixture-cached-attempt01'
OUTER = WORK/'reference-mixture-cached-outer01'
OWNED = WORK/'reference-mixture-cached-owned01'

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    need(path.is_file() and not path.is_symlink() and path.stat().st_size <= 4*1024**2, 'bounded file')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    sha(path)
    return json.loads(path.read_bytes())

if __name__ == '__main__':
    start = time.perf_counter()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv')
    worker = WORK/'analyze_rq1_reference_mixture01.py'
    contract = WORK/'rq1_reference_mixture_contract01.json'
    helper_path = ROOT/'scripts/research/windows_owned_worker.py'
    need(sha(worker)==WORKER_SHA and sha(contract)==CONTRACT_SHA and sha(helper_path)==HELPER_SHA, 'reviewed sources')
    pure = read(WORK/'reference-mixture-pure02/result.json')
    need(pure['status']=='ACCEPTED_REFERENCE_MIXTURE_PURE' and pure['tests']==8 and pure['returncode']==0
         and pure['source_before']==pure['source_after'], 'actual pure8 before cached work')
    for name,pin in pure['source_before'].items():
        need(sha(ROOT/name)==pin, 'current pure inputs')
    need(not OUTPUT.exists() and not OUTER.exists() and not OWNED.exists(), 'exclusive output names')
    OUTER.mkdir()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    import windows_owned_worker as helper
    import psutil
    need(psutil.virtual_memory().available>=512*1024**2, 'bounded cache needs512MiB free')
    before_environment = {name:os.environ.get(name) for name in ('COLUMNS','LINES')}
    receipt = None
    failure = None
    outputs = {}
    try:
        os.environ.update(COLUMNS='80',LINES='24')
        receipt = helper.run_owned(worker, ['--source-sha256',WORKER_SHA,'--contract-sha256',CONTRACT_SHA,
            '--outer-sha256','81cf9dd9df724338d6c8d57e01be16b5d2120d27b9730c186b5eb539803e4594',
            '--output-name',OUTPUT.name], OWNED, expected_worker_sha256=WORKER_SHA,
            approval_reference='ROOT_REFERENCE_MIXTURE_CACHED_REVIEW01',max_seconds=8,
            cleanup_reserve_seconds=2,max_output_bytes=65536)
        need(receipt['accepted'] and receipt['returncode']==0 and receipt['worker_returncode_before_cleanup']==0
             and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0
             and receipt['errors']==receipt['cleanup_errors']==[] and receipt['popen_handle_closed'], 'owned clean exit/Job0')
        need({f.name for f in OUTPUT.iterdir()}=={'summary.json','joined_rows.jsonl','validation.json','result.json'}, 'exact four outputs')
        outputs={f.name:dict(sha256=sha(f),bytes=f.stat().st_size) for f in OUTPUT.iterdir()}
        need(sum(v['bytes'] for v in outputs.values())<=4*1024**2, 'all output bytes')
        result=read(OUTPUT/'result.json'); validation=read(OUTPUT/'validation.json'); summary=read(OUTPUT/'summary.json')
        need(result['status']=='ACCEPTED_CACHED_REFERENCE_MIXTURE_RESPONSE_DIAGNOSTIC_ONLY'
             and result['outputs_sha256']=={k:v['sha256'] for k,v in outputs.items() if k!='result.json'}
             and result['source_sha256']==WORKER_SHA and result['contract_sha256']==CONTRACT_SHA
             and result['source_input_before']==result['source_input_after'], 'actual output and input identity')
        for name,pin in result['source_input_after'].items():
            need(sha(ROOT/name)==pin, 'actual post-input hash')
        need(validation['all2160arm_rows'] and validation['all1080query_y_pairs'] and validation['all18CRC']
             and summary['arm_rows']==2160 and summary['unique_query_responses']==1080
             and summary['independent_new_N']==0 and len(summary['groups'])==32
             and sum(len(g['bins']) for g in summary['groups'])==480, 'actual population and completeness')
        lines=(OUTPUT/'joined_rows.jsonl').read_bytes().splitlines()
        need(len(lines)==2160 and all(lines), 'actual2160 output rows')
        need(sha(worker)==WORKER_SHA and sha(contract)==CONTRACT_SHA and sha(helper_path)==HELPER_SHA, 'sources after operation')
        need(time.perf_counter()-start<10, 'whole10seconds including readback')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error))
    finally:
        for name,value in before_environment.items():
            if value is None:
                os.environ.pop(name,None)
            else:
                os.environ[name]=value
    restored=all(os.environ.get(name)==value for name,value in before_environment.items())
    final=dict(status='ACCEPTED_CACHED_REFERENCE_MIXTURE' if failure is None and restored else 'REJECTED',
               error=failure,receipt=receipt,outputs=outputs,elapsed_seconds=time.perf_counter()-start,
               whole_cap_seconds=10,owned_cap_seconds=8,cleanup_reserve_seconds=2,
               environment_restored=restored,automatic_retry=False)
    with (OUTER/'final.json').open('x',encoding='utf-8') as stream:
        json.dump(final,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    postwrite_elapsed = time.perf_counter()-start
    if postwrite_elapsed >= 10:
        rejection = dict(status='REJECTED_AFTER_FINAL_WRITE', elapsed_seconds=postwrite_elapsed, whole_cap_seconds=10)
        with (OUTER/'postwrite-rejection.json').open('x',encoding='utf-8') as stream:
            json.dump(rejection,stream);stream.flush();os.fsync(stream.fileno())
        final['status']='REJECTED'
        failure=dict(type='TimeoutError',message='whole10 exceeded including final receipt write')
    print(json.dumps(dict(status=final['status'],error=failure,elapsed_seconds=postwrite_elapsed),ensure_ascii=False))
    raise SystemExit(0 if final['status']=='ACCEPTED_CACHED_REFERENCE_MIXTURE' else 1)
