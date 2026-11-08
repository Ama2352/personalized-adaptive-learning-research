"""Replay duy nhất fixed-profile AST gốc, control/observer, exact parity hoặc STOP."""
import ast
from collections import Counter,deque
import copy
from dataclasses import asdict,is_dataclass
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from knowledge_tracing.diagnostics import DecisionTrace,compare_decision_traces
from knowledge_tracing.paper2_reference import load_reference
from observer import Context,PolicyObserver,canonical,exact,row_sha

ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
PREP=Path(__file__).resolve().parent
OUTPUT=Path(sys.argv[1]).resolve();assert OUTPUT.is_relative_to(PREP) and OUTPUT!=PREP
OUTPUT.mkdir(exist_ok=False)
HISTORICAL=ROOT/'research_tracking/runs/cpu-rq12-20261107-03'
EXPECTED_RUNNER='402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45'
START=time.perf_counter();DEADLINE=START+float(os.environ['RQ1_REMAINING_SECONDS'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def check():
    if time.perf_counter()>DEADLINE:raise TimeoutError('cumulative120s engineering budget')


def state_data(value):
    if isinstance(value,np.ndarray):return {'array_shape':list(value.shape),'dtype':str(value.dtype),'bytes_sha256':hashlib.sha256(value.tobytes()).hexdigest()}
    if isinstance(value,np.generic):return state_data(value.item())
    if isinstance(value,pd.Timestamp):return {'timestamp_iso':value.isoformat(),'timestamp_ns':int(value.value)}
    if isinstance(value,float):return {'float_hex':value.hex()}
    if isinstance(value,dict):return {str(k):state_data(v) for k,v in value.items()}
    if isinstance(value,deque):return {'deque_maxlen':value.maxlen,'items':[state_data(v) for v in value]}
    if isinstance(value,(list,tuple)):return [state_data(v) for v in value]
    if is_dataclass(value):return state_data(vars(value))
    if value is None or type(value) in (str,int,bool):return value
    raise TypeError('unknown native state field '+str(type(value)))


def fingerprint(value):return row_sha(state_data(value))
def unwrap(value):return value._delegate if isinstance(value,PolicyObserver) else value


class TraceSink:
    def __init__(self,stream,expected,*,observed):
        self.stream=stream;self.expected=expected;self.observed=observed;self.context=None;self.keys=set();self.counts=Counter()
    def write(self,text):
        value=json.loads(text);key=(value['variant'],value['learner_id'],value['event_id'])
        self.stream.write(text)
        if key in self.keys or key not in self.expected:raise ValueError('duplicate/unexpected legacy key '+str(key))
        if not exact(value,self.expected[key]):
            mismatch={'key':key,'actual':value,'historical':self.expected[key]}
            (OUTPUT/'historical_parity_failure.json').write_text(json.dumps(mismatch,ensure_ascii=False,indent=2),encoding='utf-8')
            raise ValueError('HISTORICAL_EXACT_PARITY_FAILED; STOP '+str(key))
        self.keys.add(key);self.counts[value['variant']]+=1
        if self.observed:self.context.legacy(value)


def graph_identity(scope):
    graph=scope['graph'];nodes=list(scope['nodes'])
    edges=sorted((parent,child) for parent in graph.nodes for child in graph.successors(parent))
    return {'nodes':nodes,'edges':edges,'sha256':row_sha({'nodes':nodes,'edges':edges})}


def replay(code,expected,expected_comparisons,provenance,*,observed):
    label='observed' if observed else 'control';reference=load_reference();empty=load_reference(estimator_edges=[])
    assert exact(reference['provenance'],provenance) and exact(empty['provenance'],provenance)
    policy_class=reference['estimator']['GAMKTPolicy'];empty_class=empty['estimator']['GAMKTPolicy']
    comparisons=[];summaries=[];headers=[];capture_rows=0
    with gzip.open(OUTPUT/(label+'_legacy.jsonl.gz'),'wt',encoding='utf-8') as stream,gzip.open(OUTPUT/(label+'_query_sidecar.jsonl.gz'),'wt',encoding='utf-8') as metadata:
        sink=TraceSink(stream,expected,observed=observed)
        for seed in (20000,20001,20002):
            for profile in reference['environment']['PERSONAS']:
                check();context=Context(seed,profile,metadata);sink.context=context;initial={}
                def factory(cls,variant):
                    def construct(flag):
                        native=cls(flag);initial[variant]=fingerprint(vars(native))
                        return PolicyObserver(native,variant,context) if observed else native
                    return construct
                model_scope=dict(reference['estimator'])
                def regular_factory(flag):return factory(policy_class,'graph_package' if flag else 'graph_free')(flag)
                model_scope['GAMKTPolicy']=regular_factory
                empty_scope={**empty,'estimator':dict(empty['estimator'])}
                empty_scope['estimator']['GAMKTPolicy']=factory(empty_class,'empty_graph_package')
                scope={'np':np,'pd':pd,'copy':copy,'json':json,'DecisionTrace':DecisionTrace,'asdict':asdict,
                       'compare_decision_traces':compare_decision_traces,'env_scope':reference['environment'],
                       'model_scope':model_scope,'empty':empty_scope,'seed':seed,'profile':profile,'steps':120,
                       'traces':sink,'comparisons':comparisons}
                exec(code,scope)
                policies=scope['policies']
                update_counts={name:sum(s.attempts for s in unwrap(policy).states.values()) for name,policy in policies.items()}
                assert update_counts=={name:120 for name in policies}
                summaries.append({'seed':seed,'profile':profile,'initial_policy_sha256':initial,
                    'native_update_counts':update_counts,
                    'final_policy_sha256':{name:fingerprint(vars(unwrap(policy))) for name,policy in policies.items()},
                    'environment_sha256':fingerprint(vars(scope['environment'])),
                    'uniforms_sha256':fingerprint(scope['uniforms']),
                    'rng_state_sha256':fingerprint(scope['rng'].bit_generator.state)})
                headers.append({'seed':seed,'profile':profile,'initial_policy_state_sha256':initial,
                    'parameter_flags':{'graph_free':False,'graph_package':True,'empty_graph_package':True},
                    'native_class_definition_sha256':provenance['definitions']['GAMKTPolicy']['sha256'],
                    'native_selector_definition_sha256':provenance['definitions']['CoverageAwareSelectorMixin']['sha256'],
                    'environment_graph':graph_identity(reference['environment']),'controller_graph':graph_identity(reference['controller']),
                    'estimator_graph':graph_identity(reference['estimator']),'empty_estimator_graph':graph_identity(empty['estimator'])})
                if observed:
                    assert not context.pending and context.started==context.completed=={name:120 for name in policies}
                    by_event={}
                    for row in context.rows:
                        query=(row['query'],row['correct'])
                        if row['event_id'] in by_event:assert exact(query,by_event[row['event_id']]), 'shared query/label mismatch'
                        else:by_event[row['event_id']]=query
                    assert len(by_event)==120;capture_rows+=len(context.rows)
                check()
        assert sink.keys==set(expected) and sink.counts=={'graph_free':1080,'graph_package':1080,'empty_graph_package':1080}
        assert exact(comparisons,expected_comparisons), 'historical comparison exact parity failed'
    return {'pass':label,'legacy_rows':len(sink.keys),'comparisons':len(comparisons),'query_captures':capture_rows,
            'profile_state_rng_fingerprints':summaries,'policy_headers':headers}


def main():
    manifest=json.loads((HISTORICAL/'manifest.json').read_text());provenance=json.loads((HISTORICAL/'source_provenance.json').read_text())
    assert all(sha(HISTORICAL/name)==h for name,h in manifest['outputs_sha256'].items())
    assert all(sha(ROOT/name)==h for name,h in provenance['inputs'].items())
    assert sha(ROOT/provenance['notebook'])==provenance['notebook_sha256']
    before={name:sha(ROOT/name) for name in ['src/knowledge_tracing/paper2_reference.py','src/knowledge_tracing/diagnostics.py',provenance['notebook'],*provenance['inputs']]}
    assert before['src/knowledge_tracing/paper2_reference.py']=='a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1'
    assert before['src/knowledge_tracing/diagnostics.py']=='651da44e7f8e2ce94fc5733f8a962d6fb1a5776d08c8224fb86aab879ac24d95'
    historical=subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'show','e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a:scripts/research/run_cpu_diagnostics.py'],cwd=ROOT)
    assert hashlib.sha256(historical).hexdigest()==EXPECTED_RUNNER
    with (OUTPUT/'historical_runner.py').open('xb') as out:out.write(historical)
    tree=ast.parse(historical);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    profile_loop=next(n for n in ast.walk(function) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='profile')
    block=ast.Module(body=profile_loop.body,type_ignores=[])
    code=compile(block,str(OUTPUT/'historical_runner.py'),'exec')
    expected={}
    with gzip.open(HISTORICAL/'traces.jsonl.gz','rt',encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line);key=(row['variant'],row['learner_id'],row['event_id']);assert key not in expected;expected[key]=row
    assert len(expected)==3240
    expected_comparisons=json.loads((HISTORICAL/'comparisons.json').read_text())
    assert len(expected_comparisons)==18
    control=replay(code,expected,expected_comparisons,provenance,observed=False)
    observed=replay(code,expected,expected_comparisons,provenance,observed=True)
    assert exact(control['profile_state_rng_fingerprints'],observed['profile_state_rng_fingerprints'])
    assert exact(control['policy_headers'],observed['policy_headers'])
    assert observed['query_captures']==3240
    assert all(sha(ROOT/name)==h for name,h in before.items())
    assert all(sha(HISTORICAL/name)==h for name,h in manifest['outputs_sha256'].items())
    check()
    result={'status':'PASS_EXACT_LEGACY_PARITY_NEW_OBSERVATIONS_ONLY','control':control,'observed':observed,
        'reference_runner_sha256':EXPECTED_RUNNER,'source_input_sha256_before_after':before,
        'historical_trace_sha256':manifest['outputs_sha256']['traces.jsonl.gz'],'logical_event_keys':1080,
        'variant_rows':3240,'actual_query_and_preview_tuples':3240,'native_prediction_calls_total':6480,
        'native_update_calls_total':6480,'native_environment_interactions_total':2160,'optimizer_steps':0,
        'new_independent_N':0,'preview_is_served':False,'historical_metadata_backfilled':False,
        'new_graph_generation':False,'elapsed_seconds':time.perf_counter()-START}
    with (OUTPUT/'parity.json').open('x',encoding='utf-8') as out:json.dump(result,out,ensure_ascii=False,indent=2);out.write('\n')
    print(json.dumps({key:value for key,value in result.items() if key not in ('control','observed','source_input_sha256_before_after')},ensure_ascii=False))


if __name__=='__main__':main()
