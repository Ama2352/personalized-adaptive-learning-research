"""ROOT-only cached analysis: one global10s, existing owned helper, no source edits."""
import time
START,WALL=time.perf_counter(),time.time()
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
SOURCE=PREP/'analyze_fixed_controller_candidates01.py'
SOURCE_SHA='e6275c7a57a7fc35276fb6536b13ff111138d8bb0bf31c8243aa0d7bf6877fe1'
CONTRACT=PREP/'rq1_fixed_controller_candidates_contract_20261109.md'
CONTRACT_SHA='eddde48afb910685de5d5f9ab4650f381bf04a1cae832fdc97b9012153fe19d3'
HELPER=ROOT/'scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
CAP=10.
OUT=PREP/'fixed-controller-cached01-outer'
OWNED=PREP/'fixed-controller-cached01-owned'
INNER=PREP/'fixed-controller-candidates-attempt01'
GROUPS=['pooled']+[f'profile:{p}' for p in ('PG','PY','PYH')]+[f'seed:{s}' for s in (20000,20001,20002)]
GROUPS += [f'trajectory:{s}:{p}' for s in (20000,20001,20002) for p in ('PG','PY','PYH')]


def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START,time.time()-WALL)


def physical(path):
    path=path.absolute();need(path.is_relative_to(ROOT),'workspace only')
    cursor=ROOT
    for part in path.relative_to(ROOT).parts:
        cursor/=part;need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'source/output alias')
    need(path.resolve()==path,'canonical physical path');return path


def sha(path,cap=4*1024**2):
    path=physical(path);need(path.is_file() and path.stat().st_size<=cap,'bounded source/output')
    with path.open('rb') as stream:data=stream.read(cap+1)
    need(len(data)<=cap and len(data)==path.stat().st_size,'stable input/output bytes')
    return hashlib.sha256(data).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush()


def integer(value,n):
    return type(value) is int and value==n


def validate(pins):
    need({p.name for p in INNER.iterdir()}=={'summary.json','event_flags.json','validation.json','result.json'},'exact4 complete inner outputs')
    artifacts={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in INNER.iterdir()}
    need(sum(v['bytes'] for v in artifacts.values())<=8*1024**2,'total8MiB outputs')
    read=lambda n:json.loads((INNER/n).read_bytes())
    result=read('result.json');validation=read('validation.json');summary=read('summary.json');rows=read('event_flags.json')
    need(result['status']=='INNER_COMPLETE_PENDING_ROOT_OWNED_POSTWRITE_ACCEPTANCE' and
         type(result['worker_seconds']) in (int,float) and math.isfinite(result['worker_seconds']) and 0<=result['worker_seconds']<=7
         and result['cap_seconds']==7,'inner7s complete pending only')
    need(result['outputs_sha256']=={n:v['sha256'] for n,v in artifacts.items() if n!='result.json'},'inner data outputs SHA')
    for name,n in dict(paired_snapshots=1080,source_R_membership_exact=2160,source_CID_exact=2160,old_groups_reconciled=16,
        raw_rows_per_stream=3240,joint_cells=512,B_CID_cells=64,new_independent_N=0,native_model_simulator_calls=0).items():
        need(integer(validation[name],n),'exact validation count: '+name)
    need(validation['inputs_sha256']==pins and validation['source_sha256']==SOURCE_SHA and validation['contract_sha256']==CONTRACT_SHA
         and validation['observed_R_order_parity_claimed'] is False,'validation source/provenance/units')
    nodes=summary['node_order'];need(type(nodes) is list and len(nodes)==len(set(nodes))==28,'node-index mapping')
    need([g['group'] for g in summary['groups']]==GROUPS,'all16 ordered groups')
    for g in summary['groups']:
        n=1080 if g['group']=='pooled' else (120 if g['group'].startswith('trajectory:') else 360)
        need(integer(g['paired_snapshots'],n) and len(g['joint_MRCBcid'])==32 and len(g['B_CID_cells'])==4,'group coverage')
        need([c['signature'] for c in g['joint_MRCBcid']]==[f'{i:05b}' for i in range(32)]
             and all(type(c['count']) is int and c['count']>=0 for c in g['joint_MRCBcid'])
             and sum(c['count'] for c in g['joint_MRCBcid'])==n,'all32 zero-preserving joint cells')
        need([(c['B_changed'],c['CID_changed']) for c in g['B_CID_cells']]==[(b,a) for b in (False,True) for a in (False,True)]
             and all(type(c['B_changed']) is type(c['CID_changed']) is bool for c in g['B_CID_cells'])
             and all(type(c['count']) is int and c['count']>=0 for c in g['B_CID_cells'])
             and sum(c['count'] for c in g['B_CID_cells'])==n,'all4 B/CID cells')
    need(type(rows) is list and len(rows)==1080,'exact1080 emitted rows')
    keys=set();cid_checks=0
    for row in rows:
        key=(row['seed'],row['profile'],int(row['event_id']))
        need(type(row['event_id']) is str and str(key[2])==row['event_id'] and key not in keys,'unique canonical emitted key')
        keys.add(key)
        for name in ('M_changed','R_changed','C_changed','B_changed','CID_changed','full_preview_changed'):
            need(type(row[name]) is bool,'boolean event flags')
        for label,preview in (('full',row['full_preview']),('empty',row['empty_preview'])):
            arm=row[label]
            for stage in ('R','C','B'):
                ids=arm[stage];need(type(ids) is list and len(ids)==len(set(ids))
                    and all(type(i) is int and 0<=i<28 for i in ids),'source-reconstructed stage domain')
            selected=arm['selected_index'];native_key=arm['native_key']
            need(type(selected) is int and selected in arm['B'] and set(arm['B'])<=set(arm['C'])
                 and nodes[selected]==preview['concept'] and len(native_key)==4 and native_key[3]==preview['concept']
                 and type(native_key[0]) is float and math.isfinite(native_key[0]),'2160 emitted CID/key/preview identities')
            cid_checks+=1
        need(row['R_changed']==(set(row['full']['R'])!=set(row['empty']['R']))
             and row['C_changed']==(set(row['full']['C'])!=set(row['empty']['C']))
             and row['B_changed']==(set(row['full']['B'])!=set(row['empty']['B']))
             and row['CID_changed']==(row['full']['selected_index']!=row['empty']['selected_index']), 'event-stage flags reconcile')
    need(keys=={(s,p,t) for s in (20000,20001,20002) for p in ('PG','PY','PYH') for t in range(120)} and cid_checks==2160,
         'all1080 identities/2160 CID checks, no subset')
    return artifacts,validation


def main(approval):
    need(approval and approval.strip(),'explicit ROOT dispatch approval')
    need(not OUT.exists() and not OWNED.exists() and not INNER.exists(),'exclusive one attempt; no retry/overwrite')
    physical(OUT);physical(OWNED);physical(INNER);OUT.mkdir()
    errors=[];receipt=None;before={};after={};artifacts={};validation=None;self_sha=sha(Path(__file__).resolve())
    try:
        need(sha(SOURCE)==SOURCE_SHA and sha(CONTRACT)==CONTRACT_SHA and sha(HELPER)==HELPER_SHA,'source/contract/helper freeze')
        pure_path=PREP/'fixed-controller-pure14-capture01/final.json'
        pure=json.loads(pure_path.read_bytes())
        pure_sources={SOURCE.name:SOURCE_SHA,'test_fixed_controller_candidates01.py':
            '711b8eb9153553e5acd5db29715098df8805b87d28df86134b15b9299a3e1383',CONTRACT.name:CONTRACT_SHA}
        need(pure['status']=='ACCEPTED_14_PURE_CONTROLLER_RULE_FIXTURES' and pure['counts']==dict(tests=14,failures=0,errors=0,skipped=0)
             and pure['errors']==[] and pure['source_before']==pure['source_after']==pure['source_expected']==pure_sources
             and pure['controller_sha256']==sha(PREP/'run_fixed_controller_pure14_01.py')
             and pure['owned_receipt_sha256']==sha(PREP/'fixed-controller-pure14-owned01/receipt.json')
             and not pure_path.with_name('postwrite_rejection.json').exists(),'actual pure14 prerequisite/source/receipt binding')
        need(not any(n in sys.modules for n in ('knowledge_tracing','numpy','pandas','torch','sklearn','scipy')),'fresh stdlib-only root')
        spec=importlib.util.spec_from_file_location('reviewed_controller_definitions',SOURCE)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)  # Definitions only, pinned source.
        pins=module.PINS
        need(type(pins) is dict and len(pins)==15,'reviewed15 exact inputs')
        before={n:sha(ROOT/n) for n in pins};need(before==pins,'input SHA preflight')
        write(OUT/'before.json',dict(source_sha256=SOURCE_SHA,contract_sha256=CONTRACT_SHA,controller_sha256=self_sha,
            helper_sha256=HELPER_SHA,pure_final_sha256=sha(pure_path),inputs_sha256=before,
            cap_seconds=10,worker_cap_seconds=7,cleanup_reserve_seconds=2,approval_reference=approval))
        allowance=CAP-elapsed()-.4
        need(allowance>=9,'insufficient whole10s to allocate worker7+cleanup2; STOP before cached dispatch')
        sys.path.insert(0,str(ROOT/'scripts/research'))
        from windows_owned_worker import run_owned
        receipt=run_owned(SOURCE,['--source-sha256',SOURCE_SHA,'--contract-sha256',CONTRACT_SHA,
            '--output-name',INNER.name],OWNED,expected_worker_sha256=SOURCE_SHA,approval_reference=approval,
            max_seconds=allowance,cleanup_reserve_seconds=2,max_output_bytes=16384)
        write(OWNED/'receipt.json',receipt)
        need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup']==0
             and receipt['popen_handle_closed'] is True and receipt['actual_worker_in_job_before_GO'] is True
             and receipt['returncode']==0 and not receipt['errors'],'owned execution/cleanup')
        for name,pin in receipt['output_sha256'].items():
            need(name in ('stdout.log','stderr.log') and sha(OWNED/name)==pin,'original owned logs SHA')
        need(not (OWNED/'postwrite_rejection.json').exists(),'no late owned rejection')
        artifacts,validation=validate(pins)
        after={n:sha(ROOT/n) for n in pins}
        need(before==after and sha(SOURCE)==SOURCE_SHA and sha(CONTRACT)==CONTRACT_SHA
             and sha(HELPER)==HELPER_SHA and sha(Path(__file__).resolve())==self_sha,'all source/input postchecks')
        need(elapsed()<CAP,'whole10s includes validation/copy/hash, not only worker')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
    final=dict(status='ACCEPTED_CACHED_SOURCE_RECONSTRUCTED_CONTROLLER_CID' if not errors else 'REJECTED_KEEP_PARTIAL_CACHED_CONTROLLER',
        errors=errors,elapsed_before_receipt_seconds=elapsed(),cap_seconds=CAP,source_sha256=SOURCE_SHA,contract_sha256=CONTRACT_SHA,
        controller_sha256=self_sha,input_before=before,input_after=after,artifacts=artifacts,validation=validation,
        owned_receipt_sha256=sha(OWNED/'receipt.json') if (OWNED/'receipt.json').exists() else None,
        source_R_CID_checks=2160 if not errors else None,paired_snapshots=1080 if not errors else None,
        native_model_simulator_calls=0,new_independent_N=0,automatic_retry=False,
        scope='Source-reconstructed C/B/local CID keys, not directlylogged pools, not qid explanation/calibration/mediation/learning benefit')
    write(OUT/'final.json',final)
    ok=not errors and elapsed()<CAP
    if elapsed()>=CAP:
        write(OUT/'postwrite_rejection.json',dict(status='REJECTED_WHOLE10S_POSTWRITE',elapsed_seconds=elapsed()))
        ok=False
    print(json.dumps(dict(status=final['status'] if ok else 'REJECTED_KEEP_PARTIAL_CACHED_CONTROLLER',elapsed_seconds=elapsed(),cap_seconds=CAP)))
    raise SystemExit(0 if ok else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--approval-reference',required=True)
    main(parser.parse_args().approval_reference)
