"""ONE reviewed native smoke, no research cohort/model: max12 teacher attempts.

Prepare only until root authorizes this exact driver/source pin/CLI. All failures
are terminal retained receipts. No automatic retry or final-event collection.
"""
from pathlib import Path
import argparse,hashlib,json,os,sys,time
START=time.perf_counter();ROOT=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==ROOT/'.venv'
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',OMP_NUM_THREADS='2',
                  MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import knowledge_tracing.simulator_research_collection as collector
from knowledge_tracing.simulator_research_data import ResearchSplitPlan

PREP=Path(__file__).resolve().parent;OUT=PREP/'native01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser(description='One native12-event smoke, not research fitting')
parser.add_argument('--driver-sha256',required=True)
parser.add_argument('--expected-sources-sha256',required=True)
parser.add_argument('--approval-reference',required=True)
args=parser.parse_args()
assert sha(Path(__file__))==args.driver_sha256
PINFILE=PREP/'native01_expected_sources.json'
assert sha(PINFILE)==args.expected_sources_sha256 and args.approval_reference.strip()
expected=json.loads(PINFILE.read_bytes());assert len(expected)==13
assert not OUT.exists();OUT.mkdir(exist_ok=False)
limits=collector.ResearchCollectionLimits(8,2,8,30.,512*1024**2,1024**3)
plan=ResearchSplitPlan('native-collector-smoke-only-20261108-01',42,10,1,expected[collector.PROTOCOL_PATH])
counts={'reservations':0,'native_attempts':0,'native_returns':0}
role_context={'role':None};results=[];error=None;original_loader=collector.load_reference
before_rng=np.random.get_state();source_before={}
def guard():
    collector._guard(START,limits)
def load_counted_reference():
    reference=original_loader()
    native_class=reference['environment']['LatentStudentEnvironment']
    class CountedEnvironment(native_class):
        def interact(self,*call_args,**call_kwargs):
            guard()
            if counts['reservations']>=12:
                raise RuntimeError('global12-attempt smoke budget exhausted before native call')
            counts['reservations']+=1
            entry={'reservation':counts['reservations'],'role':role_context['role'],
                   'stage':'before_native_interact','elapsed_seconds':time.perf_counter()-START}
            with (OUT/'teacher_attempts.jsonl').open('a',encoding='utf-8') as log:
                log.write(json.dumps(entry,separators=(',',':'))+'\n');log.flush();os.fsync(log.fileno())
            guard()
            counts['native_attempts']+=1
            value=native_class.interact(self,*call_args,**call_kwargs)
            counts['native_returns']+=1
            return value
    return {**reference,'environment':{**reference['environment'],'LatentStudentEnvironment':CountedEnvironment}}
def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
try:
    guard()
    source_before=collector.source_inventory()
    assert source_before==expected and 'torch' not in sys.modules
    collector.load_reference=load_counted_reference
    write('plan.json',plan.manifest())  # Final IDs are metadata only.
    for role,event_count in (('train',1),('selection',2),('calibration',2)):
        role_context['role']=role;guard()
        profiles={a.learner_id:'PG' for a in plan.split_plan.assignments(role)}
        recipe=collector.ResearchCollectionRecipe('uniform_items',event_count,1767225600,21600)
        result=collector.collect_research_role(plan,role=role,profiles=profiles,recipe=recipe,
                                               limits=limits,expected_sources=expected)
        guard()
        assert result.manifest['completed_events']==len(profiles)*event_count
        assert not result.manifest['audit']['reference_complete']  # Deliberately too small for research support.
        assert result.manifest['sources_before']==expected==result.manifest['sources_after']
        write(role+'.observables.json',[t.payload() for t in result.trajectories])
        write(role+'.oracle.json',result.oracle_sidecar)
        write(role+'.manifest.json',result.manifest)
        results.append({'role':role,'events':result.manifest['completed_events'],
                        'learners':len(profiles),'provenance_sha256':result.provenance.identity,
                        'role_manifest_sha256':sha(OUT/(role+'.manifest.json')),
                        'reference_complete':False})
    assert counts=={'reservations':12,'native_attempts':12,'native_returns':12}
    rows=[o['query']['source_row'] for role in ('train','selection','calibration')
          for t in json.loads((OUT/(role+'.observables.json')).read_bytes()) for o in t['observations']]
    assert len(rows)==len(set(rows))==12
    after_rng=np.random.get_state()
    assert before_rng[0]==after_rng[0] and np.array_equal(before_rng[1],after_rng[1]) and before_rng[2:]==after_rng[2:]
    assert collector.source_inventory()==expected and 'torch' not in sys.modules
    guard()
except Exception as exc:
    error={'type':type(exc).__name__,'message':str(exc)}
    if isinstance(exc,collector.ResearchCollectionFailure):error['collector_receipt']=exc.receipt
finally:
    collector.load_reference=original_loader
try:
    source_after=collector.source_inventory()
    if source_after!=expected:
        raise ValueError('source changed during native smoke')
    output_hashes={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}
    guard()  # Postcheck after source/output hashing, not merely after native calls.
except Exception as exc:
    source_after=locals().get('source_after',{})
    output_hashes=locals().get('output_hashes',{})
    error=error or {'type':type(exc).__name__,'message':str(exc)}
elapsed=time.perf_counter()-START
ok=error is None and elapsed<30 and counts['native_attempts']==12 and len(results)==3
receipt={'status':'ACCEPTED_NATIVE12_REQUESTED_ROLE_SMOKE_NOT_RESEARCH_READY' if ok else 'REJECTED_RETAIN_NO_RETRY',
 'approval_reference':args.approval_reference,'driver_sha256':args.driver_sha256,
 'expected_sources_sha256':args.expected_sources_sha256,'source_before':source_before,
 'source_after':source_after,'counts':counts,'role_results':results,'error':error,
 'controller_seconds':elapsed,'cumulative_native_smoke_cap_seconds':30,'actual_model_optimizer_final_calls':0,
 'research_corpus_ready':False,'support_limit':'84reference coverage missing by construction',
 'instrumentation':'private subclass counts/reserves before original interact; returns original value; no extra env/RNG calls',
 'resource_scope':'cooperative global+per-role guards; no hardkill or peak-allocation attestation',
 'outputs_sha256':output_hashes}
write('run.json',receipt)
print(json.dumps(receipt,ensure_ascii=False,indent=2));sys.exit(0 if ok else 1)
