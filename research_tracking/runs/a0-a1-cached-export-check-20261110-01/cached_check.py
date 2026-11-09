"""Kiểm cache84 rows A0/A1 trong3s; stdlib-only, không Git/model/Torchload."""
import time
START=time.perf_counter()
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import threading

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
OUT=PREP/'a0-a1-cached-export-check01'
BASE=ROOT/'experiments/akt/results'
RUNS=('main-a0-graph29-continuous-engineering10x84-20261110-01','main-a1-expert-engineering10x84-20261110-01')
KEY=('learner_id','item_id','timestamp','source_row','global_rank','history_sha256','history_hash_scheme','origin_role')


def need(ok,message):
    if not ok:raise ValueError(message)


def main():
    need(Path(sys.prefix).resolve()==ROOT/'.venv' and not OUT.exists(),'new repository-venv cached check')
    blocked={'torch','numpy','pandas','scipy','sklearn','joblib','knowledge_tracing'}
    need(not blocked.intersection(sys.modules),'stdlib only')
    def audit(event,args):
        if event=='import' and str(args[0]).split('.')[0] in blocked:raise RuntimeError('no scientific imports')
        if event=='subprocess.Popen' or event.startswith('socket.') or event=='os.system':raise RuntimeError('no processes/network')
    sys.addaudithook(audit)
    timer=threading.Timer(max(.001,2.7-(time.perf_counter()-START)),lambda:__import__('os')._exit(124));timer.daemon=True;timer.start()
    paths=[]
    for run in RUNS:
        paths += [BASE/run/'selected-claim.json',ROOT/'experiments/akt/configs'/(run+'.json'),
            BASE/run/'selection/predictions.csv',BASE/run/'selection/targets.csv']
    need(len(paths)==8 and sum(p.stat().st_size for p in paths)<=2**20 and all(p.stat().st_size<=256*2**10 for p in paths),'eight small cached inputs')
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    records=[]
    for run in RUNS:
        claim=json.loads((BASE/run/'selected-claim.json').read_bytes())
        config=json.loads((ROOT/'experiments/akt/configs'/(run+'.json')).read_bytes())
        with (BASE/run/'selection/predictions.csv').open(newline='',encoding='utf-8') as f:pred=list(csv.DictReader(f))
        with (BASE/run/'selection/targets.csv').open(newline='',encoding='utf-8') as f:target=list(csv.DictReader(f))
        keys=lambda rows:[tuple(row[n] for n in KEY) for row in rows]
        need(len(pred)==len(target)==len(set(keys(pred)))==84 and keys(pred)==keys(target),'full84 unique K with exact target join')
        labels=[int(row['correct']) for row in target];need(set(labels)<={0,1},'binary target labels')
        probabilities=[float(row['probability']) for row in pred]
        need(all(math.isfinite(p) and 0<=p<=1 and struct.unpack('!f',struct.pack('!f',p))[0]==p for p in probabilities),'exact exported FP32 probabilities')
        need(all(row['support_reason']=='supported' and row['phase_scope']=='raw_selection10' and row['origin_role']=='selection' for row in pred),'raw full supported selection only')
        chronology=[(int(row['timestamp']),int(row['source_row']),int(row['global_rank'])) for row in target]
        need(chronology==sorted(chronology) and [rank for _,_,rank in chronology]==list(range(84)),'stored chronology/global ranks')
        records.append(dict(claim=claim,config=config,pred=pred,target=target,keys=keys(pred),labels=labels,p=probabilities,chronology=chronology))
    a,b=records
    need(a['keys']==b['keys'] and a['labels']==b['labels'] and a['chronology']==b['chronology'],'cross-model exact K/y/chronology')
    for name in ('context','sources_sha256','runtime_sha256','phase_sha256','encoding_sha256','vocabulary_sha256',
                 'initial_backbone_sha256','epoch_objective_id','weights_phase','prediction_phase','encoding_fit_scope'):
        need(a['claim'][name]==b['claim'][name],'matched semantic lineage '+name)
    need(a['claim']['candidate_id']=='A0' and b['claim']['candidate_id']=='A1_EXPERT'
         and a['claim']['graph_condition_sha256']is None and b['claim']['graph_condition_sha256']is not None,'declared treatment metadata')
    differences={n:dict(A0=a['config'].get(n),A1=b['config'].get(n)) for n in set(a['config'])|set(b['config']) if a['config'].get(n)!=b['config'].get(n)}
    need(set(differences)=={'run_id','output_dir','max_rss_bytes'},'only allowed operational config differences')
    for x,y in zip(a['pred'],b['pred']):
        for n in ('phase_sha256','encoding_sha256','window_id','history_available','history_used','context_reset'):
            need(x[n]==y[n],'same causal geometry '+n)
    delta=[abs(y-x) for x,y in zip(a['p'],b['p'])]
    changed=sum(struct.pack('!f',x)!=struct.pack('!f',y) for x,y in zip(a['p'],b['p']))
    after={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in before};need(before==after,'immutable input bytes')
    OUT.mkdir()
    result=dict(status='VERIFIED_84_CACHED_A0_A1_MATCHED_EXPORTS_ENGINEERING_ONLY',rows=84,learners=len({k[0] for k in a['keys']}),
        exact_K_y_chronology=True,causal_geometry_exact=True,changed_probability_FP32_bit_count=changed,
        maximum_absolute_probability_delta=max(delta),mean_absolute_probability_delta=math.fsum(delta)/84,
        matched_claim_fields=['context','sources','runtime','phase','encoding','vocabulary','initial_backbone','objective'],
        initial_backbone_sha256=a['claim']['initial_backbone_sha256'],config_operational_differences=differences,
        input_before=before,input_after=after,canonical_metrics_recomputed=False,
        metrics_skip_reason='Located canonical gam_kt.evaluation reporter imports NumPy/Pandas/sklearn; skipped per stdlib-only scope.',
        new_model_calls=0,new_independent_N=0,efficacy_claim=False,elapsed_seconds=time.perf_counter()-START,whole_cap_seconds=3)
    text=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    (OUT/'result.json').write_bytes(text.encode())
    (OUT/'stdout.log').write_bytes((json.dumps({k:result[k] for k in ('status','rows','changed_probability_FP32_bit_count','maximum_absolute_probability_delta','mean_absolute_probability_delta')})+'\n').encode())
    (OUT/'stderr.log').write_bytes(b'')
    need(time.perf_counter()-START<3.,'whole3s cached check')
    timer.cancel();timer.join(timeout=.05)
    print((OUT/'stdout.log').read_text(),end='')


if __name__=='__main__':main()
