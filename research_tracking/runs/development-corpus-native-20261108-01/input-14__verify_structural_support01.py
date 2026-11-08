"""Kiểm độc lập public corpus/support; không oracle, không fit hoặc tune."""
import hashlib
import json
from collections import Counter
from pathlib import Path

root=Path.cwd();prep=Path(__file__).resolve().parent
load=lambda path:json.loads(path.read_bytes())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
run=load(prep/'run.json');worker=load(prep/'native01/worker_result.json');owned=load(prep/'owned_launch_receipt.json')
assert run['status']=='ACCEPTED_FIRST_DEVELOPMENT_CORPUS_NOT_MODEL_FITTED' and run['error'] is None
assert run['cumulative_seconds']<120 and run['actual_interact_attempts']==run['actual_interact_returns']==12600
assert owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed']
base=root/'artifacts/simulator/corpora/grade10-development-lifecycle01-20261108'
before={row['path']:row['sha256'] for row in run['artifacts']}
assert len(before)==17
for name,digest in before.items():assert sha(root/name)==digest
bank=load(base/'bank.json');items={row['item_id']:row['concept_id'] for row in bank['items']}
assert len(items)==84 and len(set(items.values()))==28
done=load(base/'DONE.json');assert len(done['files_sha256'])==9
for name,digest in done['files_sha256'].items():assert sha(base/name)==digest
train_item_learners=Counter();train_concept_learners=Counter();train_lagged=Counter();train_coobserved=Counter()
roles={};all_ids=set();all_rows=set()
for role,n in [('train',48),('selection',6),('calibration',6)]:
    rows=[json.loads(line) for line in (base/(role+'.jsonl')).read_bytes().splitlines()]
    assert len(rows)==n and sum(len(row['observations']) for row in rows)==n*210
    coverage=set();labels=Counter()
    for row in rows:
        assert row['learner_id'] not in all_ids;all_ids.add(row['learner_id'])
        assert len(row['observations'])==210
        seen_items=set();seen_concepts=set();lagged=set()
        for rank,obs in enumerate(row['observations'],1):
            query=obs['query'];item=query['item_id'];concept=items[item]
            assert query['timestamp']==1767225600+rank*21600
            assert query['source_row'] not in all_rows;all_rows.add(query['source_row'])
            assert type(obs['correct']) is int and obs['correct'] in (0,1)
            labels[obs['correct']]+=1;coverage.add(item)
            lagged.update((parent,concept) for parent in seen_concepts if parent!=concept)
            seen_items.add(item);seen_concepts.add(concept)
        if role=='train':
            train_item_learners.update(seen_items);train_concept_learners.update(seen_concepts);train_lagged.update(lagged)
            train_coobserved.update((a,b) for a in seen_concepts for b in seen_concepts if a!=b)
    assert set(items)==coverage
    roles[role]=dict(learners=n,events=n*210,covered_items=len(coverage),class_counts=dict(labels),two_classes=min(labels.values())>0 and len(labels)==2)
    assert [labels[0],labels[1]]==worker['class_counts'][role]
for name,digest in before.items():assert sha(root/name)==digest
assert len(all_ids)==60 and len(all_rows)==12600
concepts=sorted(set(items.values()))
pair_rows=[dict(parent=a,child=b,coobserved_learners=train_coobserved[(a,b)],
                prior_parent_before_child_learners=train_lagged[(a,b)]) for a in concepts for b in concepts if a!=b]
result=dict(status='PASS_PUBLIC_POPULATION_AND_STRUCTURAL_SUPPORT_NOT_MODEL_FIT',roles=roles,
 total_distinct_source_rows=len(all_rows),files_before_after_unchanged=True,files_sha256=before,
 train_item_learner_support=dict(sorted(train_item_learners.items())),
 train_concept_learner_support=dict(sorted(train_concept_learners.items())),ordered_pair_support=pair_rows,
 minimum_item_learner_support=min(train_item_learners.values()),
 minimum_concept_learner_support=min(train_concept_learners.values()),
 minimum_lagged_pair_learner_support=min(row['prior_parent_before_child_learners'] for row in pair_rows),
 pairs_with_lagged_support_at_least20=sum(row['prior_parent_before_child_learners']>=20 for row in pair_rows),
 scope_vi='Chỉ structural opportunity trên train; nhãn được parse và audit binary/class counts, không dùng chọn seed/cấu hình/edge. Không confidence estimate, OOF eligibility hoặc causal benefit.',
 oracle_opened=False,final_events=0,model_or_teacher_calls=0)
with (prep/'structural_support01.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('files_sha256','ordered_pair_support','train_item_learner_support','train_concept_learner_support')},ensure_ascii=False))
