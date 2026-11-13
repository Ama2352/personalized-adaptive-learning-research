"""Spool/resume và child checkpoints, dùng fitter CPU thật trên dữ liệu giả."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from test_junyi_confidence import case
from knowledge_tracing.akt.research_junyi_confidence_run import (
    approved_recipe, finalize, fit_one_child, rows_for_child, run_identity, sha, spool_windows,
)
from knowledge_tracing.akt.research_junyi_confidence import iter_surrogate_rows
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.edge_confidence import EdgeRuntimeBinding


@pytest.fixture
def runtime():
    import numpy
    import sklearn
    root = Path(__file__).resolve().parents[2]
    return EdgeRuntimeBinding(sklearn.__version__, numpy.__version__, 'b'*64,
                              sha(root/'src/knowledge_tracing/edge_confidence.py'))


def records(case, child='C'):
    view, encoding, _ = case
    for number, user in enumerate(view.users):
        events = tuple(KTEvent(user, ('A','B',child)[rank%3], rank+1,
            number*1000+rank+1, (rank+number)%2, 0, 0) for rank in range(12))
        yield from iter_windows(LearnerEvents(user, 0, events), encoding.native, training=True)


def spool(case, runtime, path, seconds=30, child='C'):
    view, _, condition = case
    return spool_windows(path, windows=records(case, child),
        session=JunyiGraphPhaseSession(condition, view),
        identity=run_identity(condition, 'a'*64, runtime),
        expected_targets=len(view.users)*12, expected_records=len(view.users),
        max_seconds=seconds, commit_windows=1)


def test_spool_resume_matches_reference_without_duplicate_targets(case, runtime, tmp_path):
    with pytest.raises(TimeoutError, match='tranche'):
        spool(case, runtime, tmp_path, .000001)
    result = spool(case, runtime, tmp_path)
    assert result['targets'] == len(case[0].users)*12
    actual = tuple(rows_for_child(tmp_path/'rows.sqlite', 'C'))
    expected = tuple(row for row in iter_surrogate_rows(records(case),
        JunyiGraphPhaseSession(case[2], case[0]), max_targets=10000, max_windows=1000,
        max_seconds=30) if row.child_id=='C')
    assert actual == expected
    assert spool(case, runtime, tmp_path) == result


def test_child_fit_complete_binding_and_corruption_guard(case, runtime, tmp_path):
    spool(case, runtime, tmp_path)
    with pytest.raises(FileNotFoundError):
        finalize(tmp_path, condition=case[2], runtime=runtime)
    first = fit_one_child(tmp_path, condition=case[2], runtime=runtime, child='C', max_rows=10000, max_seconds=30)
    assert first == fit_one_child(tmp_path, condition=case[2], runtime=runtime, child='C', max_rows=10000, max_seconds=30)
    receipt = finalize(tmp_path, condition=case[2], runtime=runtime)
    assert receipt['edges']==3 and receipt['supported_edges']+receipt['unsupported_edges']==3
    assert finalize(tmp_path, condition=case[2], runtime=runtime)==receipt
    manifest=json.loads((tmp_path/'fit-manifest.json').read_text())
    assert manifest['all_train_targets_seen']==len(case[0].users)*12
    assert manifest['uses_oracle_labels'] is False
    folder=tmp_path/'children'/hashlib.sha256(b'C').hexdigest()
    marker=folder/'COMPLETE.json'
    marker.unlink()  # Mô phỏng gián đoạn ngay trước marker, giữ summary/OOF đã đóng.
    assert fit_one_child(tmp_path, condition=case[2], runtime=runtime, child='C', max_rows=10000, max_seconds=30)==first
    (folder/first['oof_path']).write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='thay đổi'):
        fit_one_child(tmp_path, condition=case[2], runtime=runtime, child='C', max_rows=10000, max_seconds=30)


def test_empty_child_preserves_unsupported_edges(case, runtime, tmp_path):
    spool(case, runtime, tmp_path, child='A')
    result=fit_one_child(tmp_path, condition=case[2], runtime=runtime, child='C', max_rows=10000, max_seconds=30)
    assert result['targets']==0
    assert all(row['reason']=='CHILD_HAS_NO_TRAIN80_TARGETS' for row in result['edges'])
    assert finalize(tmp_path, condition=case[2], runtime=runtime)['unsupported_edges']==3


def test_wrong_lineage_and_resource_cap_do_not_publish_complete(case, runtime, tmp_path):
    spool(case, runtime, tmp_path)
    with pytest.raises(MemoryError):
        fit_one_child(tmp_path, condition=case[2], runtime=runtime, child='C', max_rows=1, max_seconds=30)
    assert not list((tmp_path/'children').glob('*/COMPLETE.json'))
    with pytest.raises(ValueError, match='runtime'):
        fit_one_child(tmp_path, condition=case[2], runtime=replace(runtime,lock_sha256='c'*64),
            child='C', max_rows=10000, max_seconds=30)
    with (tmp_path/'rows.sqlite').open('ab') as stream:
        stream.write(b'changed')
    with pytest.raises(ValueError, match='thay đổi'):
        spool(case, runtime, tmp_path)
