"""Cache graph qua entrypoint adapter, không đổi prefix, batch hoặc Adam."""
from dataclasses import replace
import hashlib
import sqlite3

import numpy as np
import pytest
import torch

from test_junyi_graph_model import (setup, windows, adam, _assert_tree_equal,
    test_native_graph_checkpoint_resume_matches_continuous as base_resume)
from knowledge_tracing.akt import research_junyi_graph_cache as cache
from knowledge_tracing.akt.research_junyi_compact import build_compact_context
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession


def prepared(setup, tmp_path, monkeypatch, entries=None):
    monkeypatch.setattr(cache,'CACHE_ROOT',tmp_path/'cache')
    adapter=setup['adapter'](compact=True)
    entries=entries or windows(setup,setup['train'],training=True)
    path=cache.CACHE_ROOT/'train.sqlite'
    binding=dict(dataset_sha256='a'*64,window_manifest_sha256='b'*64)
    receipt=cache.build_graph_context_cache(path,iter(entries),adapter.phase,**binding,
        expected_windows=len(entries),expected_targets=sum(int(e.window.target_mask.sum()) for e in entries),
        max_seconds=60,max_rss_bytes=2*1024**3)
    reader=cache.GraphContextCache.open(path,receipt['cache_sha256'],adapter.phase,**binding)
    return adapter,entries,reader,receipt


def test_rebatch_and_shuffle_exact(setup,tmp_path,monkeypatch):
    entries=windows(setup,setup['train'],training=True,items=('A','C')*250,labels=(1,0)*250)
    adapter,entries,reader,_=prepared(setup,tmp_path,monkeypatch,entries)
    for group in (tuple(e.window for e in entries),tuple(e.window for e in reversed(entries)),
                  (entries[-1].window,)):
        assert reader.batch(group,adapter.phase)==build_compact_context(group,adapter.phase)


@pytest.mark.parametrize('alpha',[0.,.75])
def test_cached_training_predictions_and_optimizer_match(setup,tmp_path,monkeypatch,alpha):
    direct,entries,reader,_=prepared(setup,tmp_path,monkeypatch)
    cached=setup['adapter'](compact=True)
    cached.set_phase(cached.phase,context_cache=reader)
    with torch.no_grad():
        direct.native.alpha.fill_(alpha)
    cached.native.load_state_dict(direct.native.state_dict())
    optimizers=[adam(direct),adam(cached)]
    for _ in range(2):
        rng=torch.get_rng_state().clone()
        results=[]
        rng_after=[]
        for adapter,optimizer in zip((direct,cached),optimizers):
            torch.set_rng_state(rng)
            results.append(adapter.step(adapter.collate_training(entries),optimizer))
            rng_after.append(torch.get_rng_state().clone())
        assert {k:v for k,v in results[0].items() if not k.endswith('_seconds')}=={
            k:v for k,v in results[1].items() if not k.endswith('_seconds')}
        assert torch.equal(*rng_after)
        _assert_tree_equal(direct.native.state_dict(),cached.native.state_dict())
        _assert_tree_equal(optimizers[0].state_dict(),optimizers[1].state_dict())
        for first,second in zip(direct.native.parameters(),cached.native.parameters()):
            if first.grad is not None:
                assert torch.equal(first.grad,second.grad)
    group=tuple(e.window for e in entries)
    assert all(np.array_equal(a,b) for a,b in zip(direct.predict_windows(group),cached.predict_windows(group)))
    signature=cached.audit_context_boundary()
    assert signature['graph_context_cache']==reader.identity
    cached.set_phase(JunyiGraphPhaseSession(cached.condition,setup['selection']))
    assert cached.audit_context_boundary()['graph_context_cache'] is None


def test_prior_change_misses_and_current_labels_are_excluded(setup,tmp_path,monkeypatch):
    adapter,entries,reader,_=prepared(setup,tmp_path,monkeypatch)
    entry=entries[0]
    altered=replace(entry,targets=1-entry.targets)
    assert cache.window_key(entry.window)==cache.window_key(altered.window)
    prior=entry.window.inputs.prior_responses.copy()
    prior[-1]=1-prior[-1]
    changed=replace(entry.window,inputs=replace(entry.window.inputs,prior_responses=prior))
    with pytest.raises(ValueError,match='cache miss'):
        reader.batch((changed,),adapter.phase)


@pytest.mark.parametrize('kind',['sha','phase','graph','dataset','manifest','payload','replacement'])
def test_stale_or_corrupt_rejected(setup,tmp_path,monkeypatch,kind):
    adapter,entries,reader,receipt=prepared(setup,tmp_path,monkeypatch)
    phase=adapter.phase
    binding=dict(dataset_sha256='a'*64,window_manifest_sha256='b'*64)
    expected=receipt['cache_sha256']
    if kind=='sha': expected='0'*64
    if kind=='phase': phase=JunyiGraphPhaseSession(adapter.condition,setup['selection'])
    if kind=='graph': phase=JunyiGraphPhaseSession(setup['condition']((('B','C'),)),setup['train'])
    if kind=='dataset': binding['dataset_sha256']='c'*64
    if kind=='manifest': binding['window_manifest_sha256']='c'*64
    if kind in ('payload','replacement'):
        with sqlite3.connect(reader.path) as connection:
            connection.execute("UPDATE contexts SET digest=?",('0'*64,))
        if kind=='replacement':
            with pytest.raises(ValueError,match='file changed'):
                reader.batch((entries[0].window,),phase)
            return
        expected=hashlib.sha256(reader.path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        reopened=cache.GraphContextCache.open(reader.path,expected,phase,**binding)
        reopened.batch((entries[0].window,),phase)


@pytest.mark.parametrize('kind',['incomplete','duplicate','budget'])
def test_failed_build_never_publishes(setup,tmp_path,monkeypatch,kind):
    monkeypatch.setattr(cache,'CACHE_ROOT',tmp_path/'cache')
    adapter=setup['adapter'](compact=True)
    entries=windows(setup,setup['train'],training=True)
    path=cache.CACHE_ROOT/'bad.sqlite'
    if kind=='duplicate': entries=entries*2
    with pytest.raises((ValueError,sqlite3.IntegrityError)):
        cache.build_graph_context_cache(path,entries,adapter.phase,dataset_sha256='a'*64,
            window_manifest_sha256='b'*64,expected_windows=len(entries)+(kind=='incomplete'),
            expected_targets=sum(int(e.window.target_mask.sum()) for e in entries),
            max_seconds=1e-9 if kind=='budget' else 60,max_rss_bytes=2*1024**3)
    assert not path.exists()
    assert list(path.parent.glob('*.partial'))


@pytest.mark.parametrize('enabled',[True,False])
def test_cached_checkpoint_resume_matches_continuous(setup,tmp_path,monkeypatch,enabled):
    entries=windows(setup,setup['train'],training=True,labels=(1,0)*550,items=('A','C')*550)
    _,_,reader,_=prepared(setup,tmp_path,monkeypatch,entries)
    original=setup['adapter']
    def cached_adapter(**kwargs):
        adapter=original(compact=True,**kwargs)
        adapter.set_phase(adapter.phase,context_cache=reader)
        return adapter
    base_resume(dict(setup,adapter=cached_adapter),tmp_path,enabled)
