"""Read-only artifact alignment/hash validation; never loads environment classes."""
from pathlib import Path
import csv,hashlib,json,sys
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.simulator_bridge import SimulatorBank,SimulatorItem
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import (ResearchSplitPlan,ResearchProvenance,ShardLimits,audit_research_shard)
PREP=Path(__file__).resolve().parent;NATIVE=PREP/'native01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
canonical=lambda value:json.loads(json.dumps(value,allow_nan=False))
run=read(NATIVE/'run.json');pins=read(PREP/'native01_expected_sources.json')
assert run['status']=='ACCEPTED_NATIVE12_REQUESTED_ROLE_SMOKE_NOT_RESEARCH_READY'
assert run['counts']=={'reservations':12,'native_attempts':12,'native_returns':12}
assert run['controller_seconds']<30 and run['actual_model_optimizer_final_calls']==0
assert sha(PREP/'run_native_smoke01.py')==run['driver_sha256']
assert sha(PREP/'native01_expected_sources.json')==run['expected_sources_sha256']
assert run['source_before']==pins==run['source_after']
assert all(sha(ROOT/p)==s for p,s in pins.items())
assert {p.name for p in NATIVE.iterdir()}==set(run['outputs_sha256'])|{'run.json'}
assert all(sha(NATIVE/name)==digest for name,digest in run['outputs_sha256'].items())
plan=ResearchSplitPlan('native-collector-smoke-only-20261108-01',42,10,1,pins['docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md'])
assert canonical(plan.manifest())==read(NATIVE/'plan.json')
csv_path=next(ROOT/p for p in pins if p.endswith('/question_bank.csv'))
with csv_path.open(encoding='utf-8-sig',newline='') as f:
 items=tuple(SimulatorItem(x['question_id'],x['concept_id'],float(x['elo_difficulty'])) for x in csv.DictReader(f))
roles=[];global_rows=[];all_learners=set()
for role,learners,events in [('train',8,8),('selection',1,2),('calibration',1,2)]:
 manifest=read(NATIVE/(role+'.manifest.json'));observables=read(NATIVE/(role+'.observables.json'))
 bank=SimulatorBank(manifest['domain']['environment_id'],items);assert bank.identity==manifest['domain']
 trajectories=tuple(ObservableTrajectory.from_payload(t) for t in observables)
 pv=dict(manifest['provenance']);pv['source_bindings']=tuple(tuple(p) for p in pv['source_bindings'])
 provenance=ResearchProvenance(**pv)
 limits=ShardLimits(8,2,8)
 audited=audit_research_shard(trajectories,plan=plan,bank=bank,role=role,provenance=provenance,
     expected_provenance_sha256=manifest['provenance_sha256'],limits=limits,reference_items=bank.item_ids)
 assert canonical(audited)==manifest['audit']
 assert audited['audit']['learners']==learners and audited['audit']['targets']==events
 assert not audited['reference_complete']
 sidecar=read(NATIVE/(role+'.oracle.json'))
 from knowledge_tracing.simulator_bridge import identity_hash
 assert identity_hash(sidecar)==manifest['oracle_sidecar_sha256']
 for t in trajectories:
  assert t.learner_id not in all_learners;all_learners.add(t.learner_id)
  details=sidecar['learners'][t.learner_id]['events']
  assert len(details)==len(t.observations)
  for o,event in zip(t.observations,details,strict=True):
   assert event['query']=={'item_id':o.query.item_id,'timestamp':o.query.timestamp,'source_row':o.query.source_row}
   assert event['oracle_result']['y']==o.correct
   global_rows.append(o.query.source_row)
 roles.append({'role':role,'learners':learners,'events':events,'missing_reference_items':len(audited['missing_reference_items']),
               'complete_reference_support':False,'provenance_sha256':provenance.identity,'observable_oracle_alignment':True})
ledger=[json.loads(line) for line in (NATIVE/'teacher_attempts.jsonl').read_text().splitlines()]
assert [row['reservation'] for row in ledger]==list(range(1,13))
assert [row['role'] for row in ledger]==['train']*8+['selection']*2+['calibration']*2
assert all(row['stage']=='before_native_interact' and row['elapsed_seconds']<30 for row in ledger)
assert len(global_rows)==len(set(global_rows))==12 and len(all_learners)==10
result={'status':'VERIFIED_NATIVE_SMOKE_ARTIFACTS_NO_RERUN','native_run_sha256':sha(NATIVE/'run.json'),
 'all11native_outputSHA':True,'all13current_sourceSHA':True,'driver_and_sourcepin_sha_match':True,
 'role_audit_recomputed_from_strict_observables_only':roles,'global12rowIDs_unique':True,
 'global12precall_reservations_verified':True,'final_events_read':False,'environment_model_rng_calls_in_verifier':0,
 'scope':'hash/schema/sidecar alignment only, not simulation replay or efficacy/calibration evidence'}
with (PREP/'native01_readonly_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
