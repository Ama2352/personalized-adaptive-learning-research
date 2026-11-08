"""GRAPH04 actual happy1+partial1 updates; chạy dưới external global4step cap."""
from dataclasses import replace
import csv
import json
import uuid

import pytest
import torch

from knowledge_tracing.akt import simulator_engineering as engineering
from knowledge_tracing.akt.config import PROJECT_ROOT
from knowledge_tracing.akt.simulator_data import fit_simulator_encoding
from test_graph_training import observables, setup


def inputs(label):
    config,train,selection,encoding=observables()
    run='grapheng-20261108-'+label+'-'+uuid.uuid4().hex[:8]
    config=replace(config,run_id=run,output_dir=PROJECT_ROOT/'artifacts/akt/synthetic'/run,max_epochs=1)
    budget=engineering.SyntheticEngineeringBudget('Root bounded GRAPH04 engineering; actual<=4steps/60s alltrials',
        train.identity,selection.identity,True)
    return config,train,selection,encoding,budget


@pytest.fixture(scope='module')
def graph_completed():
    cfg,train,selection,encoding,budget=inputs('complete')
    previous_threads=torch.get_num_threads()
    with torch.device('meta'):
        result=engineering.run_graph_engineering_epoch(cfg,train=train,selection=selection,budget=budget,setup=setup())
        assert torch.empty(1).device.type=='meta'
    assert torch.get_num_threads()==previous_threads
    return cfg,train,selection,encoding,result


def test_actual_a3_epoch_updates_all_parts_and_publishes_only_complete(graph_completed):
    cfg,train,selection,encoding,result=graph_completed
    assert result.optimizer_steps==1 and result.train_targets==8 and result.weight_role=='engineering_only'
    assert result.reload_max_abs_delta==0
    assert result.selection_coverage==dict(expected_rows=4,known_rows=3,unseen_rows=1,
        engineering_mean_log_loss=result.selection_coverage['engineering_mean_log_loss'])
    assert (cfg.output_dir/'COMPLETE').read_text().strip()=='complete_graph_engineering_only'
    assert not (cfg.output_dir/'failure.json').exists()
    events=[json.loads(line) for line in (cfg.output_dir/'optimizer_events.jsonl').read_text().splitlines()]
    assert [e['event'] for e in events]==['optimizer_started','optimizer_body_returned','graph_batch_completed']
    changed=events[-1]['changed_parameters']
    assert all(any(name.startswith(prefix) for name in changed) for prefix in
        ('native.','message_module.','gate_module.')) and 'readout' in changed
    identity=json.loads((cfg.output_dir/'invocation.json').read_text())
    assert identity['purpose']==engineering.GRAPH_PURPOSE and identity['selection_policy']=='only_complete_epoch'
    assert identity['resume_supported'] is False and 'training_domain' not in identity


def test_graph_csv_coverage_truth_sidecar_and_reload_telemetry(graph_completed):
    cfg,train,selection,encoding,result=graph_completed
    rows=json.loads((cfg.output_dir/'selection.json').read_text())['predictions']
    with (cfg.output_dir/'selection.csv').open(newline='',encoding='utf-8') as f:csvrows=list(csv.DictReader(f))
    with (cfg.output_dir/'selection_targets.csv').open(newline='',encoding='utf-8') as f:truth=list(csv.DictReader(f))
    key=lambda row:(row['learner_id'],int(row['source_row']),int(row['global_rank']))
    assert len(rows)==len(csvrows)==len(truth)==4
    assert [key(r) for r in rows]==[key(r) for r in csvrows]==[key(r) for r in truth]
    assert all('correct' not in row for row in rows) and all(row['role']=='selection' for row in truth)
    expected={(t.learner_id,o.query.source_row,i):o.correct for t in selection.trajectories for i,o in enumerate(t.observations)}
    assert {key(r):int(r['correct']) for r in truth}==expected
    missing=[row for row in rows if row['probability'] is None]
    assert len(missing)==1 and missing[0]['global_rank']==1
    fields=('base_probability','graph_applied','gate_value','confidence_mass','normalizer','graph_residual','window_id','effective_start')
    assert all(missing[0][f] is None for f in fields)
    assert any(row['graph_applied'] is True for row in rows)
    assert all(float(c['probability'])==row['probability'] for c,row in zip(csvrows,rows,strict=True) if row['probability'] is not None)


def test_partial_graph_epoch_retains_step_events_but_no_checkpoint_or_complete():
    cfg,train,selection,encoding,budget=inputs('partial')
    cfg=replace(cfg,batch_size=1,max_steps=1)
    with pytest.raises(engineering.IncompleteEngineeringEpoch):
        engineering.run_graph_engineering_epoch(cfg,train=train,selection=selection,budget=budget,setup=setup())
    stats=json.loads((cfg.output_dir/'training.json').read_text())
    assert stats['optimizer_steps']==1 and stats['valid_targets']==4 and stats['complete'] is False
    events=[json.loads(line) for line in (cfg.output_dir/'optimizer_events.jsonl').read_text().splitlines()]
    assert [e['event'] for e in events]==['optimizer_started','optimizer_body_returned','graph_batch_completed']
    assert (cfg.output_dir/'failure.json').exists()
    failure=json.loads((cfg.output_dir/'failure.json').read_text())
    assert failure['graph_optimizer_start_reservations']==failure['graph_optimizer_body_returns']==1
    assert len(failure['graph_local_step_events'])==3 and failure['optimizer_rollback_performed'] is False
    assert all(not (cfg.output_dir/p).exists() for p in ('epoch1.pt','COMPLETE','result.json','selection.csv'))


def test_confidence_recipe_drift_rejected_before_deserialization_or_constructor(graph_completed,monkeypatch):
    cfg,train,selection,encoding,result=graph_completed
    original=setup();changed=replace(original,confidence=replace(original.confidence,provenance_sha256='a'*64))
    expected=json.loads((cfg.output_dir/'invocation.json').read_text())
    monkeypatch.setattr(torch,'load',lambda *a,**k:pytest.fail('deserialized before confidence recipe check'))
    with pytest.raises(ValueError,match='before deserialization'):
        engineering.load_graph_engineering_checkpoint(cfg.output_dir/'does-not-exist.pt',cfg,encoding,
            train=train,selection=selection,setup=changed,expected_sha256=result.checkpoint_sha256,expected_identity=expected)


def test_base_loader_does_not_promote_graph_artifact(graph_completed):
    cfg,train,selection,encoding,result=graph_completed
    expected=json.loads((cfg.output_dir/'invocation.json').read_text())
    with pytest.raises(ValueError,match='scope'):
        engineering.load_engineering_checkpoint(cfg.output_dir/'epoch1.pt',cfg,encoding,
            expected_sha256=result.checkpoint_sha256,expected_identity=expected)


def test_optimizer_config_drift_rejected_before_checkpoint_read(graph_completed,monkeypatch):
    cfg,train,selection,encoding,result=graph_completed
    expected=json.loads((cfg.output_dir/'invocation.json').read_text())
    monkeypatch.setattr(torch,'load',lambda *a,**k:pytest.fail('deserialized before full config check'))
    with pytest.raises(ValueError,match='scope'):
        engineering.load_graph_engineering_checkpoint(cfg.output_dir/'does-not-exist.pt',replace(cfg,lr=cfg.lr*2),encoding,
            train=train,selection=selection,setup=setup(),expected_sha256=result.checkpoint_sha256,expected_identity=expected)
