"""Normal entry CSV→metrics SAKT/GKT, synthetic và không model/Torch."""
from dataclasses import asdict, fields, replace
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest
from test_research_selected_rows import claim as claim_fixture
from knowledge_tracing import research_admission as admission
from knowledge_tracing.research_baseline_evaluation import evaluate_cached_selected_baseline
from knowledge_tracing.research_population import SelectionPopulation
from knowledge_tracing.research_selection_io import FileReadLimits, FileRef, csv_fields
from knowledge_tracing.simulator_research_data import ResearchSplitPlan
from knowledge_tracing.gam_kt.evaluation import _metrics


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def cached(tmp_path):
    def build(candidate='SAKT', mutation=None):
        plan=ResearchSplitPlan('baseline-fixture',42,20,1,admission.PROTOCOL21)
        context=replace(claim_fixture(candidate).context,split_sha256=plan.identity)
        selected=plan.split_plan.assignments('selection')
        predicted=[];targets=[];normalized=[]
        for index,learner in enumerate(selected):
            for rank in range(5):
                reason=('oov_item' if mutation=='all_unsupported' or rank==2 else 'unsupported_history' if candidate=='GKT' and rank>2 else 'supported')
                key=admission.ModelNeutralKey(learner.learner_id,'item-'+str(rank),100+rank,index*10+rank+1,
                    rank,admission.HISTORY_SCHEME,digest(f'{learner.learner_id}-{rank}'.encode()),'selection')
                label=0 if mutation=='one_class' else rank%2
                probability=None if reason!='supported' else .8 if label else .1
                input_reason=reason if probability is None else 'cold_query_only' if rank in (0,3) else 'known_history'
                prediction=dict(**asdict(key),probability='' if probability is None else repr(probability),
                    support_reason=reason,input_support_reason=input_reason,phase_scope='raw_selection10',
                    phase_sha256='a'*64,encoding_sha256='a'*64)
                target=dict(**asdict(key),correct=label)
                predicted.append(prediction);targets.append(target)
                normalized.append(admission.RawSelectedRow(candidate,key,label,probability,reason,
                    'raw_selection10','a'*64,'a'*64))
        order=sorted(range(len(normalized)),key=lambda i:normalized[i].key)
        predicted=[predicted[i] for i in order];targets=[targets[i] for i in order];normalized=[normalized[i] for i in order]
        full=hashlib.sha256();labels=hashlib.sha256()
        for row in normalized:
            full.update(admission._canonical(row.key.values()))
            labels.update(admission._canonical((row.key.values(),row.correct)))
        expectation=admission.PopulationExpectation(context,len(normalized),full.hexdigest(),labels.hexdigest())
        population=SelectionPopulation(expectation,tuple(sorted((entry.learner_id,5) for entry in selected)),
            (sum(row.correct==0 for row in normalized),sum(row.correct==1 for row in normalized)),'a'*64,'a'*64,context.selection_role_sha256,0.)
        reasons={}
        for row in normalized:
            if row.probability is None:reasons[row.support_reason]=reasons.get(row.support_reason,0)+1
        supported=[row for row in normalized if row.probability is not None]
        metrics=_metrics(pd.DataFrame(dict(correct=[row.correct for row in supported],
                                           prediction=[row.probability for row in supported])))
        objective=('native_torch_bce_float32_exported_supported_mean_v1' if candidate=='SAKT'
                   else 'gkt29_raw_response_pooled_binary64_log_loss_v1')
        coverage=dict(full_targets=10,supported_targets=len(supported),unsupported_targets=sum(reasons.values()),
            unsupported_counts=reasons,population=dict(scheme=expectation.scheme,full_keys_sha256=full.hexdigest(),
                full_keys_labels_sha256=labels.hexdigest()),objective=objective,supported_metrics=metrics)
        if mutation=='label':targets[0]['correct']=1-int(targets[0]['correct'])
        if mutation=='phase':predicted[0]['phase_scope']='calibration_predict'
        if mutation=='oov':predicted[0].update(probability='',support_reason='supported')
        if mutation=='rank':
            predicted[0]['global_rank']=targets[0]['global_rank']=99
        if mutation=='coverage':coverage['supported_targets']+=1
        if mutation=='key':targets[0]['source_row']+=100
        def put(name,raw):
            path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            return FileRef(name,digest(raw),len(raw))
        refs={}
        for kind,rows in [('predictions',predicted),('targets',targets)]:
            buffer=io.StringIO(newline='');writer=csv.DictWriter(buffer,fieldnames=csv_fields(candidate,kind))
            writer.writeheader();writer.writerows(rows)
            refs[kind+'_ref']=put(candidate+'/'+kind+'.csv',buffer.getvalue().encode())
        refs['coverage_ref']=put(candidate+'/coverage.json',json.dumps(coverage).encode())
        claim=replace(claim_fixture(candidate),context=context,full_targets=10,supported_targets=len(supported),
            unsupported_counts=tuple(sorted(reasons.items())),epoch_objective_id=objective,
            raw_predictions=admission.ArtifactClaim(refs['predictions_ref'].sha256,refs['predictions_ref'].size_bytes),
            targets=admission.ArtifactClaim(refs['targets_ref'].sha256,refs['targets_ref'].size_bytes),
            coverage=admission.ArtifactClaim(refs['coverage_ref'].sha256,refs['coverage_ref'].size_bytes))
        refs['claim_ref']=put(candidate+'/claim.json',json.dumps(asdict(claim)).encode())
        limits=FileReadLimits(2**20,32*2**20,8,2,2**20,2**20,16384,32,256,4096,32,4096,60.)
        return dict(root=tmp_path,**refs,population=population,plan=plan,io_limits=limits),metrics
    return build


@pytest.mark.parametrize('candidate',['SAKT','GKT'])
def test_normal_cached_entry_preserves_nulls_population_and_common_metrics(cached,candidate):
    arguments,metrics=cached(candidate)
    result=evaluate_cached_selected_baseline(**arguments)
    assert result['supported_metrics']==metrics
    assert result['full_targets']==10
    assert result['supported_targets']==(8 if candidate=='SAKT' else 4)
    assert result['full_metrics'] is None and result['unsupported_counts']['oov_item']==2
    assert result['metric_contract']['ece_bins']==15
    assert not result['all_nine_candidates_admitted'] and not result['checkpoint_weights_loaded']


@pytest.mark.parametrize('mutation',['label','phase','oov','rank','coverage','key'])
def test_cached_entry_rejects_target_phase_coverage_mismatch(cached,mutation):
    arguments,_=cached('SAKT',mutation)
    with pytest.raises(ValueError):evaluate_cached_selected_baseline(**arguments)


def test_cached_entry_rejects_wrong_learner_split_and_changed_file(cached):
    arguments,_=cached()
    with pytest.raises(ValueError,match='plan'):
        evaluate_cached_selected_baseline(**dict(arguments,plan=ResearchSplitPlan('other',42,20,1,admission.PROTOCOL21)))
    path=arguments['root']/arguments['predictions_ref'].path
    path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError):evaluate_cached_selected_baseline(**arguments)


def test_reporting_metrics_match_bkt_math_including_ece_boundaries():
    from knowledge_tracing.bkt_baseline.metrics import _metrics as bkt_metrics
    frame=pd.DataFrame(dict(correct=[0,1,0,1,1,0],prediction=[0.,1.,1/15,14/15,.5,.49]))
    baseline=bkt_metrics(frame);actual=_metrics(frame)
    assert all(actual[name]==value for name,value in baseline.items())


def test_cli_request_entry_is_runnable_with_pinned_csv(cached):
    arguments,_=cached('GKT')
    root=arguments.pop('root')
    document=dict(kind='CACHED_SELECTED_BASELINE_METRICS_V1',
        **{name:asdict(arguments[name+'_ref']) for name in ('claim','predictions','targets','coverage')},
        population=asdict(arguments['population']),
        plan={field.name:getattr(arguments['plan'],field.name) for field in fields(arguments['plan']) if field.init},
        io_limits=asdict(arguments['io_limits']))
    request=root/'request.json';request.write_text(json.dumps(document))
    output=root/'research_tracking/runs/baseline-check/result.json';output.parent.mkdir(parents=True)
    script=Path(__file__).resolve().parents[2]/'scripts/evaluate_selected_baseline.py'
    spec=importlib.util.spec_from_file_location('evaluate_selected_baseline',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.run_request(root,request,digest(request.read_bytes()),output)
    assert result['candidate_id']=='GKT' and json.loads(output.read_text())['supported_targets']==4


def test_consumer_import_has_no_torch_side_effect():
    subprocess.run([sys.executable,'-B','-c',
        'import sys; import knowledge_tracing.research_baseline_evaluation; assert "torch" not in sys.modules'],
        capture_output=True,text=True,check=True)


@pytest.mark.parametrize('mode',['one_class','all_unsupported'])
def test_sparse_support_keeps_undefined_metrics_explicit(cached,mode):
    arguments,_=cached('SAKT',mode)
    result=evaluate_cached_selected_baseline(**arguments)
    assert result['supported_metrics']['auc'] is None
    if mode=='all_unsupported':
        assert result['supported_targets']==0 and result['coverage']==0
        assert result['supported_class_counts']==dict(negative=0,positive=0)
        assert result['full_metrics'] is None
    else:
        assert result['full_class_counts']==dict(negative=10,positive=0)
