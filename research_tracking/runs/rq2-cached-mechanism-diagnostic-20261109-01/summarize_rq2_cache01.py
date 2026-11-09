"""Tổng hợp mô tả từ phân tích cache đã nhận; không model/mô phỏng/inference."""
from pathlib import Path
import hashlib
import json
import statistics

P=Path(__file__).resolve().parent
ROOT=P.parents[3]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    outer=P/'rq2-cached-mechanism-native02-outer/final.json'
    assert sha(outer)=='ad5170d4cd312b126b78f4fc96b01a4f1809962a7cee820010e2ab86a44d757c'
    accepted=json.loads(outer.read_bytes())
    assert accepted['status']=='ACCEPTED_CACHED_RQ2_SECONDARY_ANALYSIS' and not accepted['errors']
    base=P/'rq2-cache-mechanism-attempt01'
    data={n:json.loads((base/n).read_bytes()) for n in ('arm_exposures.json','paired_trajectories.json','joined_contrasts.json')}
    for n in data:
        assert sha(base/n)==accepted['artifacts'][n]['sha256']
    arms=data['arm_exposures.json']; pairs=data['paired_trajectories.json']; joins=data['joined_contrasts.json']
    assert (len(arms),len(pairs),len(joins))==(120,120,30)
    totals=[]; divergence=[]; effects=[]
    for profile in ('PG','PY','PYH'):
        for g in (False,True):
            for m in (False,True):
                selected=[r for r in arms if (r['profile'],r['graph_on'],r['mechanism_on'])==(profile,g,m)]
                assert len(selected)==10 and sum(r['events'] for r in selected)==1200
                totals.append(dict(profile=profile,graph_on=g,mechanism_on=m,seed_blocks=10,events=1200,
                    true_deficit_events=sum(r['positive_true_deficit_events'] for r in selected),
                    root_events=sum(r['root_events'] for r in selected),
                    mean_true_deficit=sum(r['mean_true_deficit']*r['events'] for r in selected)/1200))
        for axis in ('mechanism','policy'):
            selected=[r for r in pairs if r['profile']==profile and r['axis']==axis]
            assert len(selected)==20
            q=[r['first_query_difference_step'] for r in selected if r['first_query_difference_step'] is not None]
            y=[r['first_label_difference_step'] for r in selected if r['first_label_difference_step'] is not None]
            divergence.append(dict(profile=profile,axis=axis,paired_trajectories=20,
                query_divergent_pairs=len(q),label_divergent_pairs=len(y),
                zero_observable_prefix_pairs=sum(r['common_observable_prefix_steps']==0 for r in selected),
                query_first_divergence_if_present=dict(min=min(q),median=statistics.median(q),max=max(q)) if q else None,
                label_first_divergence_if_present=dict(min=min(y),median=statistics.median(y),max=max(y)) if y else None,
                query_difference_events=sum(r['different_query_steps'] for r in selected),
                label_difference_events=sum(r['different_label_steps'] for r in selected),
                common_observable_prefix_total=sum(r['common_observable_prefix_steps'] for r in selected)))
        selected=[r for r in joins if r['profile']==profile]
        values=[r['interaction_contrast'] for r in selected]
        effects.append(dict(profile=profile,seeds=10,mean_interaction=sum(values)/10,
            positive=sum(v>1e-12 for v in values),negative=sum(v < -1e-12 for v in values),
            zero=sum(abs(v)<=1e-12 for v in values),min=min(values),max=max(values),
            mean_graph_effect_mechanism_on=sum(r['graph_effect_mechanism_on'] for r in selected)/10,
            mean_graph_effect_mechanism_off=sum(r['graph_effect_mechanism_off'] for r in selected)/10))
    out=P/'rq2_cached_secondary_synthesis01.json'
    payload=dict(kind='DESCRIPTIVE_SECONDARY_CACHED_ANALYSIS_NOT_CONFIRMATORY',
        accepted_outer_sha256=sha(outer),source_sha256=sha(Path(__file__)),
        input_sha256={n:sha(base/n) for n in data},arm_exposures=totals,
        divergence=divergence,interaction=effects,worlds=120,events=14400,
        independent_seed_clusters_reused=10,new_independent_seed_families=0,
        model_calls=0,world_transitions=0,
        caveat_vi='Các cặp dùng lại20trajectories/profile/axis từ10seedblocks, không20learners độc lập. Firstdivergence là chỉ số0-based. Sau diverge không chung query/history; không causal mediation/dose–response/ability isolation/time-DiD. Không pvalue/CI.')
    with out.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    assert all(sha(base/n)==h for n,h in payload['input_sha256'].items())
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
