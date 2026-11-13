"""Kiểm guard trong producer thật, training/evaluation mock như fixture hiện có."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest
import torch

from test_junyi_selected_runner import harness, graph_condition
from knowledge_tracing.akt import research_junyi_data, research_junyi_selection as selected
from knowledge_tracing.akt import research_junyi_window_cache
from knowledge_tracing.akt.research_runner import _state_hash


@pytest.fixture
def matched(harness,tmp_path,monkeypatch):
    for path in (harness.inputs.paths.canonical_manifest,harness.inputs.paths.split_manifest):
        path.write_text('{}')
    encoding_file=tmp_path/'encoding.json'
    encoding_file.write_text('{}')
    receipt=tmp_path/'encoding-receipt.json'
    receipt.write_text('{}')
    cache=tmp_path/'cache'
    cache.mkdir()
    (cache/'manifest.json').write_text('{}')
    encoding_args=dict(encoding_file=encoding_file,expected_encoding_sha256=selected.file_sha(encoding_file),
        encoding_receipt=receipt,expected_encoding_receipt_sha256=selected.file_sha(receipt),
        train_window_cache=cache,expected_train_window_manifest_sha256=selected.file_sha(cache/'manifest.json'))
    monkeypatch.setattr(research_junyi_data,'load_prepared_junyi_encoding',lambda *args,**kwargs:harness.encoding)

    class CacheSession:
        def __init__(self,*args,**kwargs):
            pass

        def iter_windows(self):
            return iter(())

    monkeypatch.setattr(research_junyi_window_cache,'JunyiWindowCacheSession',CacheSession)
    torch.manual_seed(42)
    native=torch.nn.Module()
    native.linear=torch.nn.Linear(1,1,device='cpu')
    native.register_buffer('epoch_marker',torch.tensor(0,dtype=torch.int64,device='cpu'))
    initial=_state_hash(SimpleNamespace(native=native))
    reference=selected._comparison_candidate(harness.config,harness.profile,harness.inputs,
        harness.encoding,initial,encoding_file=encoding_file,encoding_receipt=receipt,
        train_window_cache=cache,graph_condition=None,candidate_id='A0')
    reference['selection_population_sha256']='b'*64
    reference_path=tmp_path/'comparison-reference.json'

    def write_reference(value=reference):
        reference_path.write_text(json.dumps(dict(status='PASS_A0_DATA_LINEAGE_CANDIDATES_PENDING',reference=value)))
        return reference_path

    write_reference()
    return SimpleNamespace(harness=harness,reference=reference,write_reference=write_reference,
        reference_path=reference_path,encoding_args=encoding_args,initial=initial)


def test_main_graph_requires_reference_before_model_or_train(harness):
    with pytest.raises(PermissionError,match='pinned A0 comparison'):
        harness.run(graph_condition=graph_condition(harness),purpose='main_selected')
    assert not harness.control['models'] and not harness.control['train_calls']


@pytest.mark.parametrize('graph',[False,True])
def test_matched_reference_is_bound_to_checkpoint_and_terminal(matched,graph):
    harness=matched.harness
    condition=graph_condition(harness) if graph else None
    terminal=harness.run(graph_condition=condition,comparison_reference=matched.reference_path,
        encoding_args=matched.encoding_args)
    assert terminal['comparison_population_matched'] is True
    pin=selected.file_sha(matched.reference_path)
    assert terminal['comparison_reference_sha256']==pin
    identity=json.loads((harness.config.output_dir/'run-manifest.json').read_text())
    assert identity['comparison_reference_sha256']==pin
    assert len(list(harness.config.output_dir.glob('comparison-admission-*.json')))==1


def test_changed_reference_pin_stops_before_model(matched):
    harness=matched.harness
    with pytest.raises(ValueError,match='reference changed'):
        harness.run(comparison_reference=matched.reference_path,reference_pin='0'*64,
            encoding_args=matched.encoding_args)
    assert not harness.control['models'] and not harness.control['train_calls']


def test_main_comparison_rechecks_data_files_before_model(matched,monkeypatch):
    harness=matched.harness
    calls=[]

    def reject_cache(cache,roles,**pins):
        calls.append((cache,roles,pins))
        raise ValueError('Changed canonical cache bytes')

    monkeypatch.setattr(selected,'load_full_selected_cache',reject_cache)
    with pytest.raises(ValueError,match='canonical cache'):
        harness.run(graph_condition=graph_condition(harness),purpose='main_selected',
            comparison_reference=matched.reference_path,encoding_args=matched.encoding_args)
    assert calls==[(harness.inputs.paths.canonical.parent,harness.inputs.paths.split_manifest,
        dict(expected_manifest_sha256=matched.reference['data_pins']['selected_manifest'],
             expected_roles_sha256=matched.reference['data_pins']['roles']))]
    assert not harness.control['models'] and not harness.control['train_calls']


@pytest.mark.parametrize('field,value',[
    ('initial_backbone_sha256','0'*64),('encoding_identity','0'*64),
    ('train_targets',5),('selection_targets',3),('roles_identity','0'*64)])
def test_mismatch_stops_before_first_optimizer_step(matched,field,value):
    reference=deepcopy(matched.reference)
    reference[field]=value
    matched.write_reference(reference)
    harness=matched.harness
    with pytest.raises(ValueError,match='Comparison mismatch'):
        harness.run(comparison_reference=matched.reference_path,encoding_args=matched.encoding_args)
    assert not harness.control['train_calls']
    assert not list(harness.config.output_dir.glob('comparison-admission-*.json'))


def test_population_mismatch_cannot_publish_selected_checkpoint(matched):
    reference=deepcopy(matched.reference)
    reference['selection_population_sha256']='c'*64
    matched.write_reference(reference)
    harness=matched.harness
    with pytest.raises(ValueError,match='target population'):
        harness.run(comparison_reference=matched.reference_path,encoding_args=matched.encoding_args)
    assert harness.control['train_calls']==[1]
    assert (harness.config.output_dir/'checkpoints/train-epoch-001/COMPLETE.json').exists()
    assert not (harness.config.output_dir/'checkpoints/epoch-001').exists()
    assert not (harness.config.output_dir/'COMPLETE.json').exists()


def test_reference_change_is_rejected_on_resume(matched):
    harness=matched.harness
    harness.control['fail_validation_epoch']=1
    with pytest.raises(RuntimeError,match='interruption'):
        harness.run(comparison_reference=matched.reference_path,encoding_args=matched.encoding_args)
    checkpoint=harness.config.output_dir/'checkpoints/train-epoch-001/state.pt'
    reference=deepcopy(matched.reference)
    reference['selection_population_sha256']='c'*64
    matched.write_reference(reference)
    with pytest.raises(ValueError,match='identical unfinished logical run'):
        harness.run(resume=checkpoint,comparison_reference=matched.reference_path,
            encoding_args=matched.encoding_args)
    assert harness.control['train_calls']==[1]
