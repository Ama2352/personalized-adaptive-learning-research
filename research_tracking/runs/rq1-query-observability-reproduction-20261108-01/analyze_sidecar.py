"""Phân tích read-only stored reproduction; không RNG/model/paper rerun/CI."""
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path

from observer import exact

BASE=Path(__file__).resolve().parent
ATTEMPT=BASE/'attempt01';DATA=ATTEMPT/'replay'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def load(path):
    result={}
    with gzip.open(path,'rt',encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line);key=(row['variant'],row['learner_id'],row['event_id'])
            assert key not in result;result[key]=row
    assert len(result)==3240
    return result


def main():
    inputs=[DATA/'observed_query_sidecar.jsonl.gz',DATA/'observed_legacy.jsonl.gz',DATA/'control_legacy.jsonl.gz',DATA/'parity.json',ATTEMPT/'run.json',Path(__file__),BASE/'observer.py']
    before={str(p.relative_to(BASE)):sha(p) for p in inputs}
    run=json.loads((ATTEMPT/'run.json').read_text());parity=json.loads((DATA/'parity.json').read_text())
    assert run['status']=='PASS' and run['controller_elapsed_seconds']<=120 and run['optimizer_steps']==0
    assert parity['status']=='PASS_EXACT_LEGACY_PARITY_NEW_OBSERVATIONS_ONLY'
    sidecar=load(inputs[0]);legacy=load(inputs[1]);control=load(inputs[2]);assert set(sidecar)==set(legacy)==set(control)
    for key,row in sidecar.items():
        assert row['preview_is_served'] is False and row['preview_timestamp_argument'] is None
        assert row['update_pairing_verified'] is True and row['preview']['concept']==legacy[key]['action']
        assert exact(legacy[key],control[key]) and exact(row['probability'],legacy[key]['probability']) and row['correct']==legacy[key]['correct']
    logical=sorted({(learner,event) for variant,learner,event in sidecar},key=lambda k:(k[0],int(k[1])))
    assert len(logical)==1080;variants=('graph_free','graph_package','empty_graph_package')
    for learner,event in logical:
        reference=sidecar[('graph_free',learner,event)]
        for variant in variants:
            candidate=sidecar[(variant,learner,event)]
            assert exact(candidate['query'],reference['query']) and candidate['correct']==reference['correct']
    counters={};flags=[];examples={}
    for learner,event in logical:
        reference=sidecar[('graph_free',learner,event)]
        for variant in variants[1:]:
            candidate=sidecar[(variant,learner,event)]
            same_p=exact(reference['probability'],candidate['probability'])
            concept=reference['preview']['concept']!=candidate['preview']['concept']
            question=reference['preview']['question']!=candidate['preview']['question']
            difficulty=not exact(reference['preview']['difficulty'],candidate['preview']['difficulty'])
            full=not exact(reference['preview'],candidate['preview'])
            assert full==(concept or question or difficulty)
            values={'pairs':1,'P_same':int(same_p),'P_changed':int(not same_p),'concept_changed':int(concept),
                'question_changed':int(question),'difficulty_changed':int(difficulty),'full_tuple_changed':int(full),
                'same_concept_full_tuple_changed':int(full and not concept),
                'same_P_full_tuple_changed':int(same_p and full),'same_P_concept_changed':int(same_p and concept),
                'same_P_question_changed':int(same_p and question),'same_P_difficulty_changed':int(same_p and difficulty),
                'changed_P_full_tuple_unchanged':int(not same_p and not full)}
            for group in ('pooled',candidate['profile'],learner):
                counters.setdefault((variant,group),Counter()).update(values)
            row={'candidate':variant,'seed':candidate['seed'],'profile':candidate['profile'],'learner_id':learner,'event_id':event,
                'P_same':int(same_p),'A_concept_changed':int(concept),'A_question_changed':int(question),
                'A_difficulty_changed':int(difficulty),'A_full_tuple_changed':int(full),
                'reference_probability':reference['probability'],'candidate_probability':candidate['probability']}
            for prefix,value in [('reference',reference),('candidate',candidate)]:
                row.update({prefix+'_preview_'+name:field for name,field in value['preview'].items()})
            flags.append(row)
            for name,condition in [('same_concept_different_full',full and not concept),('same_P_different_full',same_p and full)]:
                if condition:examples.setdefault(variant+':'+name,row)
    assert counters[('graph_package','pooled')]['concept_changed']==22
    assert counters[('empty_graph_package','pooled')]['concept_changed']==0
    cross_profile={}
    for left,right in [('PG','PY'),('PG','PYH'),('PY','PYH')]:
        matched=0
        for seed in (20000,20001,20002):
            for step in range(120):
                a=sidecar[('graph_free',f'{seed}-{left}',str(step))]['query']
                b=sidecar[('graph_free',f'{seed}-{right}',str(step))]['query']
                assert exact(a,b);matched+=1
        cross_profile[left+'__'+right]={'query_pairs':360,'exact_same_query_tuples':matched}
    assert len(flags)==2160 and all(sha(p)==before[str(p.relative_to(BASE))] for p in inputs)
    output={'status':'PASS_STORED_OBSERVABILITY_ANALYSIS_NO_MODEL_RERUN','input_sha256_before_after':before,
        'logical_event_pairs_per_comparison':1080,'variant_rows':3240,'shared_query_label_checks':1080,
        'current_query_tuple_identical_all_three_variants':True,'comparison_rows':len(flags),
        'counts':[{'candidate':variant,'group':group,**dict(count)} for (variant,group),count in sorted(counters.items())],
        'cross_profile_query_identity':cross_profile,'deterministic_first_examples':examples,
        'float_comparison':'exact binary64 parsed values; no tolerance','new_independent_N':0,
        'scope':'same3seed families/same3profiles reproduction metadata only; preview not served; no causal/calibration/CI or historical backfill',
        'model_rng_optimizer_network_calls':0}
    with (ATTEMPT/'sidecar_analysis.json').open('x',encoding='utf-8') as stream:json.dump(output,stream,ensure_ascii=False,indent=2);stream.write('\n')
    with (ATTEMPT/'sidecar_event_flags.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(flags[0]));writer.writeheader();writer.writerows(flags)
    print(json.dumps({'status':output['status'],'counts':[row for row in output['counts'] if row['group'] in ('pooled','PG','PY','PYH')],
        'analysis_sha256':sha(ATTEMPT/'sidecar_analysis.json'),'flags_sha256':sha(ATTEMPT/'sidecar_event_flags.csv')},ensure_ascii=False))


if __name__=='__main__':main()
