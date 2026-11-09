"""Kiểm độc lập từ gzip/ON, giữ first-visit như phân tích mô tả bổ sung."""
import time
START = time.perf_counter()
import csv
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PHASE = PREP / 'observer03-truth-cached02'
OUTER = PREP / 'observer03-truth-cached02-owned/final.json'
KEY = (21000, 'PG', False, False)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(OUTER) == '32042e63144f36cec7acff18e30b62657fe528a4bbf137de608227cf0a25cebe'
assert read(OUTER)['status'] == 'ACCEPTED_OBSERVER03_CACHED120_LATENT_WITNESS'
source = ROOT / 'research_tracking/runs/cpu-factorial-20261107-01/traces.jsonl.gz'
assert sha(source) == '2a136fbf627cfa59170deec54c10ae562c2f8214eb00970ce41b96c43d065dcc'
on_path = ROOT / 'research_tracking/runs/rq1-cpu09-observer-readiness-20261109-01/03__on.json'
assert sha(on_path) == 'a8b9c6479127d1f96dc84ac97f237242c8f25327c3d9dbe32cf40147481ad737'
on = read(on_path)
assert on['key'] == list(KEY) and len(on['readouts']) == 120
bank_path = ROOT / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/question_bank.csv'
assert sha(bank_path) == 'fb5924ac0d19049ef1a5be23352592e30dfa3a4bde3e3fa07f10979fe0887e4d'
with bank_path.open(encoding='utf-8-sig', newline='') as stream:
    bank = {row['question_id']: (row['concept_id'], float(row['elo_difficulty']))
            for row in csv.DictReader(stream)}
selected = []
total_rows = total_bytes = 0
with gzip.open(source, 'rb') as stream:
    for raw in stream:
        total_rows += 1
        total_bytes += len(raw)
        assert len(raw) <= 8192 and total_rows <= 14400 and total_bytes <= 8*1024**2
        if total_rows % 128 == 0:
            assert time.perf_counter() - START < 5
        row = json.loads(raw)
        if tuple(row[name] for name in ('seed', 'profile', 'graph_on', 'mechanism_on')) == KEY:
            assert type(row['graph_on']) is type(row['mechanism_on']) is bool
            selected.append(row)
assert total_rows == 14400 and len(selected) == 120
joined = read(PHASE / 'joined120.json')
summary = read(PHASE / 'summary.json')
assert len(joined) == 120
matrix = {key: 0 for key in ('00', '01', '10', '11')}
theta_matrix = dict(matrix)
suppression = dict(latent_false=0, latent_true=0)
first_visits = {}
current = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
for step, (native, stored, emitted) in enumerate(zip(on['readouts'], selected, joined)):
    assert native['step'] == stored['step'] == emitted['step'] == step
    current += dt.timedelta(hours=72 if step and step % 28 == 0 else 6)
    assert native['timestamp'] == current.isoformat() == emitted['timestamp']
    concept, difficulty = bank[stored['question']]
    assert native['selected'] == [concept, stored['question'], difficulty]
    assert struct.pack('>d', native['prediction']) == struct.pack('>d', stored['prediction'])
    estimated_positive = native['theta_est'] >= 1250.0
    precision_eligible = native['pi_task_stored'] <= .55
    native_positive = estimated_positive and precision_eligible
    latent_positive = stored['theta_before'] >= 1250.0
    assert native['native_M'] is native_positive and native['theta_gate'] is estimated_positive
    assert emitted['native_M'] is native_positive and emitted['simulator_latent_criterion'] is latent_positive
    assert emitted['simulator_theta_before'] == stored['theta_before']
    matrix[str(int(native_positive))+str(int(latent_positive))] += 1
    theta_matrix[str(int(estimated_positive))+str(int(latent_positive))] += 1
    if estimated_positive and not precision_eligible:
        suppression['latent_true' if latent_positive else 'latent_false'] += 1
    first_visits.setdefault(concept, dict(concept=concept, step=step,
        simulator_theta_before=stored['theta_before'], theta_est=native['theta_est'],
        already_latent_positive=latent_positive))
assert matrix == summary['native_M_by_latent']
assert theta_matrix == summary['theta_gate_by_latent']
assert suppression == summary['uncertainty_suppression_by_latent']
elapsed = time.perf_counter() - START
assert elapsed < 5
result = dict(status='INDEPENDENT_RAW_JOIN_AND_COUNTS_VERIFIED', joined_rows=120,
    cache_rows=total_rows, source_sha256=sha(source), accepted_outer_sha256=sha(OUTER),
    native_M_by_latent=matrix, theta_gate_by_latent=theta_matrix,
    uncertainty_suppression_by_latent=suppression,
    first_visit_analysis=dict(kind='POSTHOC_SOURCE_MECHANISM_CHECK_NOT_NEW_CONFIRMATION',
        observed_concepts=len(first_visits), latent_positive_first_visits=sum(
            row['already_latent_positive'] for row in first_visits.values()), rows=list(first_visits.values()),
        limitation='Chỉ các concept được phục vụ. Suy luận base cần giả thiết teacher cập nhật concept-local và theta_at>=base.'),
    elapsed_seconds=elapsed, new_model_world_RNG_calls=0, new_independent_N=0)
with (PREP / 'observer03_truth120_independent_crosscheck01.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status=result['status'], matrix=matrix, observed_concepts=len(first_visits),
                     positive_first_visits=result['first_visit_analysis']['latent_positive_first_visits'],
                     elapsed_seconds=elapsed)))
