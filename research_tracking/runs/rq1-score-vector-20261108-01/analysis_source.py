"""Phân tích lại stored pilot: S là mastery_score nguồn, không latent mastery/p(correct)."""
import csv
from dataclasses import asdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('rq1_transitions',ROOT/'scripts/research/analyze_rq1_transitions.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle

deadline=time.monotonic()+30
directory=ROOT/module.FIXED
verified=verify_evidence_bundle(directory)
manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
legacy=json.loads((directory/'comparisons.json').read_text(encoding='utf-8'))
rows=module.read_gzip_json(directory/'traces.jsonl.gz',deadline)
index,flags=module.paired_flags(rows)
flag_index={(r['candidate'],r['cluster'],r['event_id']):r for r in flags}
events=[]
for candidate in module.CANDIDATES:
    for (cluster,event_id),left in index['graph_free'].items():
        right=index[candidate][cluster,event_id]
        seed,profile=cluster.split('-',1)
        changed=[c for c in left['mastery'] if left['mastery'][c]!=right['mastery'][c]]
        delta=[right['mastery'][c]-left['mastery'][c] for c in left['mastery']]
        base=flag_index[candidate,cluster,event_id]
        a,b,y=left['probability'],right['probability'],left['correct']
        if a is None or b is None: raise ValueError('this stored pilot requires paired supported predictions')
        a_clip,b_clip=(min(1-1e-15,max(1e-15,p)) for p in (a,b))
        loss=lambda p:-y*math.log(p)-(1-y)*math.log(1-p)
        events.append({'candidate':candidate,'cluster':cluster,'seed':int(seed),'profile':profile,'event_id':event_id,
            'p_changed':base['p_changed'],'s_changed':bool(changed),'m_changed':base['m_changed'],
            'r_changed':base['r_changed'],'a_changed':base['a_changed'],
            'changed_score_concepts':len(changed),'concepts':len(delta),
            'mean_absolute_score_delta':sum(abs(d) for d in delta)/len(delta),'max_absolute_score_delta':max(map(abs,delta)),
            'candidate_minus_reference_log_loss':loss(b_clip)-loss(a_clip),
            'candidate_minus_reference_brier':(b-y)**2-(a-y)**2,
            'source_changed_concepts':sorted(changed)})
        module.check_time(deadline)

def summarize(selected):
    n=len(selected)
    return {'paired_events':n,'concept_score_pairs':sum(e['concepts'] for e in selected),
        'p_changed_events':sum(e['p_changed'] for e in selected),
        's_changed_events':sum(e['s_changed'] for e in selected),
        'changed_score_concept_pairs':sum(e['changed_score_concepts'] for e in selected),
        'm_changed_events':sum(e['m_changed'] for e in selected),'r_changed_events':sum(e['r_changed'] for e in selected),
        'a_changed_events':sum(e['a_changed'] for e in selected),
        's_changed_m_same':sum(e['s_changed'] and not e['m_changed'] for e in selected),
        's_changed_a_same':sum(e['s_changed'] and not e['a_changed'] for e in selected),
        's_same_m_changed':sum(not e['s_changed'] and e['m_changed'] for e in selected),
        's_same_a_changed':sum(not e['s_changed'] and e['a_changed'] for e in selected),
        'p_same_a_changed':sum(not e['p_changed'] and e['a_changed'] for e in selected),
        'p_same_a_changed_s_changed':sum(not e['p_changed'] and e['a_changed'] and e['s_changed'] for e in selected),
        'mean_event_mean_absolute_score_delta':sum(e['mean_absolute_score_delta'] for e in selected)/n,
        'maximum_absolute_score_delta':max(e['max_absolute_score_delta'] for e in selected),
        'candidate_minus_reference_log_loss':sum(e['candidate_minus_reference_log_loss'] for e in selected)/n,
        'candidate_minus_reference_brier':sum(e['candidate_minus_reference_brier'] for e in selected)/n}

groups=[];checks=[]
for candidate in module.CANDIDATES:
    subset=[e for e in events if e['candidate']==candidate]
    groups.append({'candidate':candidate,'scope':'pooled',**summarize(subset)})
    for seed in manifest['seeds']:
        selected=[e for e in subset if e['seed']==seed]
        groups.append({'candidate':candidate,'scope':'seed_block','seed':seed,**summarize(selected)})
    for old in [r for r in legacy if r['candidate']==candidate]:
        selected=[e for e in subset if e['seed']==old['seed'] and e['profile']==old['profile']]
        current=summarize(selected)
        for field in ('candidate_minus_reference_log_loss','candidate_minus_reference_brier'):
            assert math.isclose(current[field],old[field],rel_tol=1e-12,abs_tol=1e-12),(candidate,old['seed'],old['profile'],field)
        checks.append({'candidate':candidate,'seed':old['seed'],'profile':old['profile'],'loss_brier_legacy_tolerance':1e-12})
        groups.append({'candidate':candidate,'scope':'seed_profile','seed':old['seed'],'profile':old['profile'],**current})

payload={'scope':'Post-hoc descriptive reanalysis of existing fixed-stream synthetic pilot; no model/simulator/data rerun',
    'semantics':{'P':'probability for current logged query only','S':'full source mastery_score concept vector, not calibrated probability/latent mastery',
                 'M':'source is_mastered boolean set','R':'source ready set','A':'concept action preview on copied policy; not served'},
    'groups':groups,'legacy_loss_brier_checks':checks,'seed_blocks':manifest['seeds'],
    'examples_p_same_action_changed':[e for e in events if not e['p_changed'] and e['a_changed']],
    'limitations':['Conditional cooccurrence, not nested funnel or causal mediation.',
        'Graph package contains edge-independent mechanisms; empty graph is not identical architecture to graph-free.',
        'No calibration of S against mastery truth; no choice of S04 threshold/reference, no confirmatory CI/p-value.',
        'Fixed stream lacks independent logged item/time fields; same-stream identity remains source-declared.']}
sources=[Path(__file__),ROOT/'scripts/research/analyze_rq1_transitions.py',ROOT/'src/knowledge_tracing/diagnostics.py',
         directory/'manifest.json',directory/'traces.jsonl.gz',directory/'comparisons.json']
with record_evidence_run(ROOT,'rq1-score-vector-20261108-01',metadata={
    'kind':'RQ1_SOURCE_SCORE_VECTOR_PILOT_REANALYSIS','evidence_role':'descriptive_existing_synthetic_pilot',
    'new_model_or_simulator_runs':0,'real_data_holdout_queries':0,'gpu_cloud_calls':0,'source_bundle_verified_outputs':verified['artifacts']},
    sources=sources,note='''# RQ1 — tách scalar P và vector S đã lưu\n\nChỉ phân tích lại pilot fixed-stream có sẵn; không thêm quan sát, không chạy mô hình/simulator. S là mastery_score nguồn, không ground-truth mastery hay xác suất đã hiệu chỉnh. M giữ boolean is_mastered thật; A chỉ concept preview. Không nested funnel/causal mediation, không chốt S04/S05.\n\nanalysis.json có pooled/seed/profile quantities và đối chiếu loss/Brier với18aggregates cũ; event_flags.csv giữ mẫu số và cases để trích dẫn. Reproduce helper từ repository root bằng .venv; run_id exclusive nên muốn chạy lại phải chọn ID mới trong bản sao nguồn, không ghi đè bundle này.\n''') as out:
    (out/'analysis.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'event_flags.csv').open('x',newline='',encoding='utf-8') as stream:
        fields=[k for k in events[0] if k!='source_changed_concepts']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        writer.writerows({k:r[k] for k in fields} for r in events)
    copies=[]
    for source,name in [(Path(__file__),'analysis_source.py'),(ROOT/'scripts/research/analyze_rq1_transitions.py','transition_helper.py')]:
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        (out/name).write_bytes(source.read_bytes())
        after=hashlib.sha256(source.read_bytes()).hexdigest();copied=hashlib.sha256((out/name).read_bytes()).hexdigest()
        assert before==after==copied
        copies.append({'source':source.relative_to(ROOT).as_posix(),'copy':name,'sha256_before':before,'sha256_after':after,'copied_sha256':copied})
    (out/'copy_inventory.json').write_text(json.dumps(copies,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verification':verify_evidence_bundle(out),'pooled':[g for g in groups if g['scope']=='pooled']},ensure_ascii=False))
