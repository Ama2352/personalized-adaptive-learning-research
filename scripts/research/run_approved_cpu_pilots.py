"""Pilot CPU được user chấp thuận, giữ caps và bằng chứng riêng mỗi run."""

import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import threading
import time

import duckdb
import numpy as np
import pandas as pd

from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
from knowledge_tracing.experimental_controls import FactorialOutcome, paired_mechanism_contrasts
from knowledge_tracing.paper2_reference import ROOT, load_reference
from knowledge_tracing.gam_kt.simulator_pathways import build_pathway_policy
from knowledge_tracing.gam_kt.simulator_mechanisms import build_mechanism_environment
from knowledge_tracing.gam_kt.practice_order import summarize_practice_order
from knowledge_tracing.akt.data import read_development_assignments
from knowledge_tracing.akt.runner import _data_paths
from knowledge_tracing.akt.splits import make_inner_split


def write(directory, name, payload):
    (directory/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def factorial(run_id):
    reference = load_reference()
    scope = reference['environment']
    classes = {False: build_mechanism_environment(reference, prerequisite_strength=0),
               True: build_mechanism_environment(reference, prerequisite_strength=.55)}
    paths = [ROOT/'scripts/research/run_approved_cpu_pilots.py', ROOT/'src/knowledge_tracing/evidence.py',
             ROOT/'src/knowledge_tracing/experimental_controls.py',ROOT/'src/knowledge_tracing/paper2_reference.py',
             ROOT/'src/knowledge_tracing/gam_kt/simulator_pathways.py',
             ROOT/'src/knowledge_tracing/gam_kt/simulator_mechanisms.py',
             ROOT/reference['provenance']['notebook']]
    paths += [ROOT/path for path in reference['provenance']['inputs']]
    metadata = {'kind':'approved_cpu_factorial_pilot','rq':['RQ1','RQ2'],
                'authorization':'User approved CPU09/CPU10 pilot limits in chat2026-11-07',
                'seeds':list(range(21000,21010)),'profiles':list(scope['PERSONAS']),
                'steps':120,'cells':4,'max_events':14400,'max_seconds':120,
                'edge_treatment':'S=P=on versus S=P=off, L=off in both',
                'mechanism_strength':[0,.55],'environment_controller_graph':'historical advanced, fixed'}
    note = '''# Pilot factorial ability/prerequisite mechanism

Được user chấp thuận tối đa10seed/profile×120steps,4cells. Treatment bật parent signal/adaptation, local pathway tắt trong cả treatment/control. G_env và G_controller giữ graph lịch sử. Lambda0/.55 là variant simulator riêng đã kiểm parity ở.55.

outcomes.json lưu4cells cùng latent/random identity mỗi seed/profile. contrasts.json tính (on-off)|lambda.55 − (on-off)|lambda0. traces.jsonl.gz lưu actual served actions và outcomes. Cùng base_theta và step-indexed uniforms, labels có thể khác khi actions khác.

Đây là interaction contrast conditional trên simulator và thiết kế này, chưa là time-DiD hoặc causal benefit trên Junyi. Initial abilities nguồn có graph correlation. Pilot không có final significance testing, không dùng seed này làm untouched final. Source_provenance.json và manifest ghi nguồn/hash/caps.
'''
    started = time.perf_counter()
    with record_evidence_run(ROOT,run_id,metadata=metadata,sources=paths,note=note) as directory:
        rows=[]
        with gzip.open(directory/'traces.jsonl.gz','wt',encoding='utf-8') as trace:
            for seed in metadata['seeds']:
                for profile in scope['PERSONAS']:
                    base=scope['persona_base_abilities'](profile,seed)
                    uniforms=np.random.default_rng(seed).random((120,2))
                    latent_id=hashlib.sha256(json.dumps(base,sort_keys=True).encode()).hexdigest()
                    random_id=hashlib.sha256(uniforms.tobytes()).hexdigest()
                    for mechanism in (False,True):
                        for graph_on in (False,True):
                            environment=classes[mechanism](base)
                            policy=build_pathway_policy(reference,signal=graph_on,parent_adaptation=graph_on,local_adaptation=False)
                            timestamp=pd.Timestamp('2026-01-01',tz='UTC')
                            for step in range(120):
                                if time.perf_counter()-started >120:
                                    raise TimeoutError('factorial pilot wall cap exceeded')
                                timestamp+=pd.Timedelta(hours=72 if step>0 and step%len(base)==0 else 6)
                                cid,qid,difficulty=policy.select()
                                probability=policy.predict(cid,qid,difficulty,timestamp)
                                result=environment.interact(cid,difficulty,timestamp,*uniforms[step])
                                trace.write(json.dumps({'seed':seed,'profile':profile,'graph_on':graph_on,
                                    'mechanism_on':mechanism,'step':step,'concept':cid,'question':qid,
                                    'prediction':probability,**result},ensure_ascii=False)+'\n')
                                policy.update(cid,qid,difficulty,timestamp,result['y'],probability)
                            final=environment.snapshot(timestamp)
                            outcome=float(np.mean([final[c]-base[c] for c in base]))
                            rows.append(FactorialOutcome(seed,profile,graph_on,mechanism,latent_id,random_id,outcome))
        contrasts=paired_mechanism_contrasts(rows)
        write(directory,'outcomes.json',[asdict(row) for row in rows])
        write(directory,'contrasts.json',contrasts)
        write(directory,'source_provenance.json',reference['provenance'])
        write(directory,'summary.json',{profile:{'paired_seeds':10,
            'mean_interaction':float(np.mean([row['interaction_contrast'] for row in contrasts if row['profile']==profile]))}
            for profile in scope['PERSONAS']})
    return directory


def junyi_order(run_id):
    paths=_data_paths()
    assignments=read_development_assignments(paths)
    split=make_inner_split(assignments,outer_fold=0)
    cohort=sorted(split.inner_train_users,key=lambda user:hashlib.sha256(f'order-pilot-v1|{user}'.encode()).hexdigest())[:32]
    selected=assignments[assignments.user_id.isin(cohort)].copy()
    catalog=ROOT/'dataset/junyi_Exercise_table.csv'
    frame=pd.read_csv(catalog).fillna('')
    edges=sorted({(parent.strip(),str(row['name'])) for row in frame.to_dict('records')
                  for parent in str(row['prerequisites']).split(',') if parent.strip()})
    sources=[ROOT/'scripts/research/run_approved_cpu_pilots.py',ROOT/'src/knowledge_tracing/evidence.py',
             ROOT/'src/knowledge_tracing/gam_kt/practice_order.py',catalog,paths.assignments,
             paths.canonical_manifest,paths.split_manifest]
    metadata={'kind':'approved_cpu_junyi_order_pilot','rq':['RQ2'],'authorization':'User approved CPU09/CPU10 limits2026-11-07',
              'outer_fold':0,'scope':'inner-train learners only','max_learners':32,'max_events_per_learner':120,
              'max_seconds':120,'cohort_sha256':hashlib.sha256(json.dumps(sorted(cohort)).encode()).hexdigest(),
              'graph_source':'catalog prerequisites, comma-delimited parent→exercise','uses_correct_labels':False,
              'duckdb_memory':'512MB','duckdb_threads':2}
    note='''# Pilot Junyi first-exposure order

Tối đa32learner inner-train của outer-fold0,120events/learner, hash-selected cohort. Chỉ đọc user/exercise/time_done/source_row, không dùng correctness labels hoặc Holdout. Metadata graph từ prerequisites của exercise catalog, không dùng relationship_annotation_testing.

order_summary.json chứa co-observation và hướng first exposure trên prefix. reverse_summary.json là sensitivity đảo cạnh, không là graph chất lượng kém đã được xác nhận. Metadata audit ghi endpoint coverage/self loops. Chưa là graph predictive comparison hoặc instructional causal effect. Prefix censoring và cohort nhỏ hạn chế diễn giải, không suy full Junyi population. Không xuất raw learner IDs.
'''
    with record_evidence_run(ROOT,run_id,metadata=metadata,sources=sources,note=note) as directory:
        con=duckdb.connect(config={'memory_limit':'512MB','threads':'2','temp_directory':''})
        timer=threading.Timer(120,con.interrupt)
        timer.daemon=True
        try:
            con.register('selected_inner_train',selected)
            pattern=str(paths.canonical/'**/*.parquet')
            timer.start()
            data=con.execute("SELECT c.user_id,c.exercise,c.time_done,c.source_row,u.fold,'development' AS partition "
                "FROM read_parquet(?,hive_partitioning=true) c JOIN selected_inner_train u ON c.user_id=u.user_id "
                "QUALIFY row_number() OVER (PARTITION BY c.user_id ORDER BY c.time_done,c.source_row)<=120 "
                "ORDER BY c.user_id,c.time_done,c.source_row",[pattern]).df()
        finally:
            timer.cancel()
            con.close()
        self_edges=[edge for edge in edges if edge[0]==edge[1]]
        usable=[edge for edge in edges if edge[0]!=edge[1]]
        rows=data.to_dict('records')
        write(directory,'order_summary.json',summarize_practice_order(rows,usable,allowed_users=set(cohort),outer_fold=0))
        write(directory,'reverse_summary.json',summarize_practice_order(rows,[(b,a) for a,b in usable],allowed_users=set(cohort),outer_fold=0))
        names=set(frame.name.astype(str))
        write(directory,'catalog_audit.json',{'catalog_exercises':len(names),'edges':len(edges),
            'self_edges':self_edges,'missing_parent_endpoints':sorted({a for a,b in edges if a not in names}),
            'actual_learners':len(cohort),'actual_events':len(rows)})
    return directory


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=('factorial','junyi-order'))
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    path=factorial(args.run_id) if args.mode=='factorial' else junyi_order(args.run_id)
    print(json.dumps({'run':str(path.relative_to(ROOT)),**verify_evidence_bundle(path)},ensure_ascii=False))
