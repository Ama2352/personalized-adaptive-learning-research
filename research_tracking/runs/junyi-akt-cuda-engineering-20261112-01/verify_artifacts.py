"""Đối chiếu độc lập archive Junyi với dữ liệu cohort local, không nạp Torch."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs
from knowledge_tracing.gam_kt.evaluation import _metrics
import pandas as pd

BUNDLE = Path(__file__).parent
RUN = 'modal-junyi-a0-epoch-20261112-02'
native = ROOT/'experiments/akt/results'/RUN
receipt = json.loads((native/'receipt.json').read_text())
assert receipt['status']=='ACTUAL_JUNYI_A0_CUDA_ONE_EPOCH_COMPLETE'
request = json.loads((BUNDLE/'gpu-request.json').read_text())
cohort = ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01'
roles = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
views, encoding, learners, _ = prepare_inputs(cohort, roles,
    cohort_sha256=request['cohort_sha256'], roles_sha256=request['roles_sha256'])
truth = {event.source_row:asdict(event) for learner in learners['selection'] for event in learner.events}
prefix = 'experiments/akt/results/'+RUN+'/'
with zipfile.ZipFile(native/'artifacts.zip') as saved:
    inventory = json.loads(saved.read('SHA256.json'))
    assert set(saved.namelist()) == set(inventory)|{'SHA256.json'}
    for name, entry in inventory.items():
        raw = saved.read(name)
        assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
    terminal = json.loads(saved.read(prefix+'engineering-terminal.json'))
    stats = json.loads(saved.read(prefix+'epoch01.json'))
    prediction_raw = saved.read(prefix+'selection-predictions.jsonl')
    records = [json.loads(row) for row in prediction_raw.splitlines()]
    assert len(records)==len(truth)==1530 and len({row['source_row'] for row in records})==1530
    for row in records:
        actual = truth[row['source_row']]
        assert all(row[key]==actual[key] for key in actual)
        assert row['checkpoint_id']==terminal['checkpoint_sha256']
        known = row['exercise'] in encoding.native.vocabulary.values
        assert (row['prediction'] is not None)==known
        assert row['prediction_kind']==('fitted' if known else 'unseen')
        assert row['is_fallback'] is False
        assert row['history_used']<=row['history_available']
    supported = [row for row in records if row['prediction'] is not None]
    metrics = _metrics(pd.DataFrame(supported))
    assert metrics==terminal['supported_metrics']
    assert len(supported)==1405 and stats['valid_targets']==11833 and stats['optimizer_steps']==79
    assert stats['complete'] is True and stats['parameter_update_steps']==79
    checkpoint = prefix+'checkpoints/epoch-001/'
    metadata = json.loads(saved.read(checkpoint+'metadata.json'))
    complete = json.loads(saved.read(checkpoint+'COMPLETE.json'))
    assert inventory[checkpoint+'state.pt']['sha256']==metadata['checkpoint_sha256']==complete['checkpoint_sha256']
    assert inventory[checkpoint+'metadata.json']['sha256']==complete['metadata_sha256']
    preflight = json.loads(saved.read('experiments/akt/results/'+RUN+'-operation/preflight.json'))
    for name in ('epoch01.json','engineering-terminal.json','training-events.jsonl'):
        (BUNDLE/name).write_bytes(saved.read(prefix+name))
result = dict(status='VERIFIED_JUNYI_A0_ONE_EPOCH_ENGINEERING',run_id=RUN,
    gpu=preflight['gpu_name'], train_targets=11833,optimizer_steps=79,
    selection_targets=1530,supported_targets=1405,oov_targets=125,
    exact_selection_truth_identity=True,metrics_recomputed_exact=True,
    fresh_checkpoint_reload=terminal['fresh_checkpoint_reload'],selected_epoch=None,
    checkpoint_sha256=terminal['checkpoint_sha256'],checkpoint_bytes=metadata['checkpoint_bytes'],
    encoding_identity=encoding.identity,train_epoch_wall_seconds=stats['resource']['wall_seconds'],
    complete_lifecycle_seconds=terminal['elapsed_seconds'],driver_seconds=receipt['elapsed_seconds'],
    metrics=metrics,full_junyi_benchmark=False,
    limits='Một epoch cohort kỹ thuật. Chưa chọn epoch/refit/calibration/outer-evaluation hoặc so sánh BKT/GAM.')
(BUNDLE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
