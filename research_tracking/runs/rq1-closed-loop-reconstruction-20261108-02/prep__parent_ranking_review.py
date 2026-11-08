"""Kiểm độc lập ranking/prefix từ raw metadata, không gọi policy hoặc RNG."""
from collections import Counter,defaultdict
import csv,gzip,hashlib,json
from pathlib import Path
root=Path.cwd();p=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
candidate=p/'closed-loop-ranking-posthoc01/ranking_candidate.json'
assert sha(candidate)=='119d75da6bdf97f58fea2ff265a5590c956308d24eabf9cf6d194a7f627a0e77'
c=json.loads(candidate.read_bytes());a=json.loads((p/'closed-loop-descriptive-analysis01/analysis.json').read_bytes())
inventory=json.loads((p/'closed_loop_ranking_posthoc_source_inventory.json').read_bytes())
for path,h in inventory['files_sha256'].items():assert sha(root/path)==h
with gzip.open(p/'closed-loop-fast-model-attempt01/observed_metadata.jsonl.gz','rt',encoding='utf-8') as f:rows=[json.loads(line) for line in f]
with (root/inventory['chapter_map_path']).open(encoding='utf-8-sig',newline='') as f:chapters={r['concept_id']:r['chapter'] for r in csv.DictReader(f)}
groups=defaultdict(list)
for row in rows:groups[(row['seed'],row['profile'],row['variant'])].append(row)
assert len(groups)==27 and len(rows)==3240
ranks={}
for group,items in groups.items():
    visits=Counter();previous=None
    for t,r in enumerate(items):
        assert r['step']==t
        scores={v['concept']:v['score'] for v in r['mastery_score_calls']}
        assert len(scores)==len(r['mastery_score_calls'])==len(r['balanced_candidates'])
        assert set(scores)==set(r['balanced_candidates'])
        keys={cid:(score,int(chapters[cid]!=previous),visits[cid],cid) for cid,score in scores.items()}
        assert min(keys,key=keys.get)==r['served_tuple']['concept']
        ranks[(*group,t)]=keys
        visits[r['served_tuple']['concept']]+=1;previous=chapters[r['served_tuple']['concept']]
    result=next(v for v in a['trajectories'] if (v['seed'],v['profile'],v['variant'])==group)
    assert result['R_to_C_setdiff']==sum(set(v['ready_set'])!=set(v['eligible_candidates']) for v in items)
    assert result['C_to_B_setdiff']==sum(set(v['eligible_candidates'])!=set(v['balanced_candidates']) for v in items)
    assert result['selected_outside_R']==sum(v['served_tuple']['concept'] not in v['ready_set'] for v in items)
    assert result['selected_M_true']==sum(v['mastered_decisions'][v['served_tuple']['concept']] for v in items)
counts=Counter()
for comp in c['comparisons']:
    s,profile,variant=comp['seed'],comp['profile'],comp['candidate']
    left=groups[(s,profile,'graph_free')];right=groups[(s,profile,variant)]
    breaking=None
    for t,(l,r) in enumerate(zip(left,right)):
        same=(l['served_tuple']==r['served_tuple'] and l['query']['timestamp_ns']==r['query']['timestamp_ns'] and l['correct']==r['correct'])
        if not same:breaking=t;break
    if breaking is None:
        assert comp['negative_case'] is True;counts[(variant,'negative')]+=1;continue
    assert comp['first_prefix_break']['step']==breaking
    l,r=left[breaking],right[breaking]
    lk,rk=ranks[(s,profile,'graph_free',breaking)],ranks[(s,profile,variant,breaking)]
    same_sets=(l['mastered_decisions']==r['mastered_decisions'] and all(set(l[k])==set(r[k]) for k in ['ready_set','eligible_candidates','balanced_candidates']))
    if same_sets:
        assert set(lk)==set(rk) and all(lk[k][1:]==rk[k][1:] for k in lk)
        assert any(lk[k][0]!=rk[k][0] for k in lk)
        assert min(lk,key=lk.get)!=min(rk,key=rk.get)
        assert comp['first_prefix_break']['classification']=='SAME_B_TIES_NATIVE_B_SCORE_RANKING_EXPLAINS_CONCEPT_CHOICE'
        counts[(variant,'same_membership_score_choice')]+=1
    else:
        assert comp['first_prefix_break']['classification']=='B_MEMBERSHIP_DIFF_SCORE_ONLY_EXPLANATION_NOT_CLAIMED'
        counts[(variant,'membership_diff')]+=1
assert counts=={('graph_package','same_membership_score_choice'):8,('graph_package','membership_diff'):1,('empty_graph_package','same_membership_score_choice'):2,('empty_graph_package','negative'):7}
report=dict(status='PASS_PARENT_INDEPENDENT_RAW_RANKING_AND_DESCRIPTIVE_REVIEW',raw_rank_keys_verified=3240,trajectory_groups=27,comparisons=18,
    full_same_membership_score_choices=8,full_membership_change=1,empty_same_membership_score_choices=2,empty_negative_cases=7,
    model_policy_rng_calls=0,new_independent_N=0,scope='Giải thích CID theo key nguồn trên dữ liệu tái dựng; post-hoc, không giải thích choose_question/difficulty, causal mediation hoặc hiệu quả học tập. P served-item được tính sau select; không là biến gây ra same-step selection.')
with (p/'parent-ranking-review.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False))
