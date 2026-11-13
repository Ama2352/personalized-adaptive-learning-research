"""Đo CPU projector thử nghiệm, không thay production hoặc phát hành cache."""
from dataclasses import asdict, dataclass, fields, is_dataclass
import hashlib
import json
from pathlib import Path
import platform
import time

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
SOURCE_SHA = '3a3a45634ba7ea84520472f57c1828b28a705b9d2a8a10f8476510cf682507e5'
ATOMIC = frozenset((str, int, float, bool, type(None)))


@dataclass(frozen=True)
class Parent:
    parent: str
    support: int
    confidence: float
    mean_observed_correctness: float | None


@dataclass(frozen=True)
class Audit:
    target_fitted: bool
    parents: tuple
    observed_rows: tuple
    effective_start: int
    condition_sha256: str
    encoding_sha256: str


@dataclass(frozen=True)
class Evidence:
    learner_id: str
    source_row: int
    global_rank: int
    window_id: str
    local_position: int
    audit: Audit


def project(value):
    kind = type(value)
    if kind in ATOMIC:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: project(getattr(value, field.name)) for field in fields(value)}
    if kind is tuple:
        if all(type(item) in ATOMIC for item in value):
            return value
        return tuple(project(item) for item in value)
    if kind is list:
        return [project(item) for item in value]
    if kind is dict:
        return {project(key): project(item) for key, item in value.items()}
    raise TypeError('Prototype chỉ hỗ trợ primitive, dataclass và exact tuple/list/dict')


def evidence_hash(rows, projector):
    payload = tuple(tuple(None if item is None else projector(item) for item in row) for row in rows)
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def fixture(dense):
    return tuple(tuple(Evidence(str(row), row*200+rank, rank, 'win'+str(row), rank,
        Audit(True, (Parent('A', 1, 1., .5), Parent('B', 1, 1., 1.)),
            tuple(range(rank if dense else rank % 5)), 0, 'a'*64, 'b'*64))
        for rank in range(100, 200)) for row in range(128))


def main():
    started = time.perf_counter()
    source = ROOT/'src/knowledge_tracing/akt/research_graph_model.py'
    source_bytes = source.read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == SOURCE_SHA
    snapshot = BUNDLE/'research_graph_model_source2.py'
    if snapshot.exists():
        assert snapshot.read_bytes() == source_bytes
    else:
        snapshot.write_bytes(source_bytes)
    # Chỉ self-check phạm vi primitive; chưa nghiệm thu payload tùy biến.
    primitive = Audit(True, (), (0, 1), 0, 'Tiếng Việt', {'none':None, 'float':-0., 'list':[True, 1, .25]})
    assert evidence_hash(((None, primitive),), project) == evidence_hash(((None, primitive),), asdict)
    before = evidence_hash(((primitive,),), project)
    object.__setattr__(primitive, 'effective_start', 1)
    assert evidence_hash(((primitive,),), project) != before
    result = dict(status='PROTOTYPE_BENCHMARK_ONLY_NOT_ADOPTED', python=platform.python_version(),
        production_source_sha256=SOURCE_SHA, production_changed=False, gpu_used=False,
        modal_spent_usd=0, fixtures=[])
    for dense in (False, True):
        rows = fixture(dense)
        measurements = []
        for projector in (asdict, project, asdict, project):
            assert time.perf_counter()-started < 10
            at = time.perf_counter()
            digest = evidence_hash(rows, projector)
            measurements.append(dict(method=projector.__name__, seconds=time.perf_counter()-at, sha256=digest))
        assert len({row['sha256'] for row in measurements}) == 1
        legacy = sum(row['seconds'] for row in measurements if row['method']=='asdict')/2
        candidate = sum(row['seconds'] for row in measurements if row['method']=='project')/2
        result['fixtures'].append(dict(kind='dense_observed_rows_100_199' if dense else 'sparse_observed_rows_0_4',
            rows=128, targets_per_row=100, parents_per_target=2, measurements=measurements,
            legacy_mean_seconds=legacy, candidate_mean_seconds=candidate, speedup=legacy/candidate,
            saved_seconds_per_100_training_batches_at_four_hashes=400*(legacy-candidate)))
    assert source.read_bytes() == source_bytes
    result['elapsed_seconds'] = time.perf_counter()-started
    result['limits_vi'] = ('Fixture tự tạo bằng stdlib, chưa đo payload Junyi thực hoặc runtime Modal. '
        'SHA khớp trong fixture đã kiểm, chưa chứng minh mọi payload hỗ trợ. '
        'Hiệu quả sparse thấp, giữ nguyên source2 và không tạo source3/migration từ benchmark này.')
    output = BUNDLE/'evidence-projector-benchmark.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
