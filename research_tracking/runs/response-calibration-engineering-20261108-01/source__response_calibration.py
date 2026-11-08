"""Temperature response/reference V1; không hiệu chuẩn latent mastery.

Chỉ scalar T được fit trên partition calibration khai báo. Identity/role là
hợp đồng provenance hợp tác; không chứng minh predictor đã thực sự train/refit
đúng manifest hay không đọc label trước đó. Không đọc dataset/checkpoint.
"""
from dataclasses import asdict, dataclass
from collections import Counter
from pathlib import Path
import hashlib
import math
from numbers import Real

from .simulator_bridge import ItemQuery, ReferenceSet, SimulatorBank, identity_hash

CLIP = 1e-6
T_MIN, T_MAX = .05, 20.
TAU_REF = sum(1 / (1 + 10 ** ((d - 1250) / 400)) for d in (1050, 1200, 1350)) / 3
RECIPE = 'response-temperature-reference-v1'


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('nonempty identifier required')


def _sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('SHA256 required')


def implementation_identity():
    root = Path(__file__).resolve().parents[2]
    names = ('src/knowledge_tracing/response_calibration.py', 'src/knowledge_tracing/simulator_bridge.py',
             'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md')
    return identity_hash({name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names})


def _probability(value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('finite probability in [0,1] required')
    return float(value)


def _logit(p):
    p = min(1 - CLIP, max(CLIP, _probability(p)))
    return math.log(p) - math.log1p(-p)


def _sigmoid(z):
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


@dataclass(frozen=True)
class PredictionBinding:
    model_id: str
    checkpoint_sha256: str
    vocabulary_sha256: str
    split_sha256: str
    bank_sha256: str
    reference_sha256: str
    model_source_sha256: str
    domain_sha256: str

    def __post_init__(self):
        _text(self.model_id)
        for name, value in asdict(self).items():
            if name != 'model_id': _sha(value)


@dataclass(frozen=True)
class CalibrationPartition:
    split_sha256: str
    calibration_learners: tuple[str, ...]
    excluded_learners: tuple[str, ...]
    # None = manifest không khai báo seed families; nếu có phải đủ cả hai sides.
    learner_seed_families: tuple[tuple[str, str], ...] | None

    def __post_init__(self):
        _sha(self.split_sha256)
        for name in ('calibration_learners', 'excluded_learners'):
            values = tuple(getattr(self, name))
            for value in values: _text(value)
            if len(set(values)) != len(values): raise ValueError('duplicate learner')
            object.__setattr__(self, name, tuple(sorted(values)))
        a, b = set(self.calibration_learners), set(self.excluded_learners)
        if not a or not b or a & b: raise ValueError('calibration/excluded learner separation required')
        if self.learner_seed_families is not None:
            rows = tuple(tuple(row) for row in self.learner_seed_families)
            if any(len(row) != 2 for row in rows): raise ValueError('seed-family schema')
            mapping = dict(rows)
            if len(mapping) != len(rows) or set(mapping) != a | b: raise ValueError('complete seed-family manifest required')
            for family in mapping.values(): _text(family)
            if {mapping[u] for u in a} & {mapping[u] for u in b}: raise ValueError('seed-family leakage')
            object.__setattr__(self, 'learner_seed_families', tuple(sorted(rows)))

    @property
    def identity(self):
        return identity_hash(asdict(self))


@dataclass(frozen=True)
class CalibrationTarget:
    learner_id: str
    event_id: str
    item_id: str
    history_sha256: str
    correct: int
    probability: float | None
    support_reason: str
    role: str = 'calibration'

    def __post_init__(self):
        for value in (self.learner_id, self.event_id, self.item_id, self.support_reason): _text(value)
        _sha(self.history_sha256)
        if self.role != 'calibration' or type(self.correct) is not int or self.correct not in (0, 1):
            raise ValueError('only binary observed calibration labels allowed')
        if self.probability is None:
            if self.support_reason == 'supported': raise ValueError('missing probability needs unsupported reason')
        else:
            object.__setattr__(self, 'probability', _probability(self.probability))
            if self.support_reason != 'supported': raise ValueError('unsupported cannot carry probability')


@dataclass(frozen=True)
class TemperatureCalibration:
    binding: PredictionBinding
    partition_sha256: str
    targets_sha256: str
    implementation_sha256: str
    status: str
    temperature: float | None
    objective_evaluations: int
    total_targets: int
    supported_targets: int
    class_counts: tuple[int, int]
    unsupported_counts: tuple[tuple[str, int], ...]
    raw_log_loss: float | None
    calibrated_log_loss: float | None

    @property
    def identity(self):
        return identity_hash(self.to_payload())

    def to_payload(self):
        return {'recipe': RECIPE, 'clip': CLIP, 'temperature_bounds': [T_MIN, T_MAX], **asdict(self)}

    @classmethod
    def from_payload(cls, payload, *, binding):
        expected = set(cls.__dataclass_fields__) | {'recipe', 'clip', 'temperature_bounds'}
        if not isinstance(payload, dict) or set(payload) != expected: raise ValueError('calibrator payload schema')
        if payload['recipe'] != RECIPE or payload['clip'] != CLIP or payload['temperature_bounds'] != [T_MIN, T_MAX]:
            raise ValueError('calibrator recipe mismatch')
        values = {k: v for k, v in payload.items() if k in cls.__dataclass_fields__}
        values['binding'] = PredictionBinding(**values['binding'])
        values['class_counts'] = tuple(values['class_counts'])
        values['unsupported_counts'] = tuple(tuple(row) for row in values['unsupported_counts'])
        result = cls(**values)
        _validate_calibration(result, binding, require_fitted=False)
        return result


def _validate_calibration(result, binding, *, require_fitted=True):
    if type(result) is not TemperatureCalibration or type(binding) is not PredictionBinding or result.binding != binding:
        raise ValueError('checkpoint/vocab/split/bank/reference/model binding mismatch')
    for value in (result.partition_sha256, result.targets_sha256, result.implementation_sha256): _sha(value)
    if result.implementation_sha256 != implementation_identity(): raise ValueError('implementation/source drift')
    integers = (result.total_targets, result.supported_targets, result.objective_evaluations, *result.class_counts)
    if (len(result.class_counts) != 2 or any(type(x) is not int or x < 0 for x in integers)
            or result.supported_targets != sum(result.class_counts) or result.supported_targets > result.total_targets
            or not 0 <= result.objective_evaluations <= 200): raise ValueError('calibrator counts')
    reasons = dict(result.unsupported_counts)
    if (len(reasons) != len(result.unsupported_counts) or any(not isinstance(k, str) or not k or type(v) is not int or v < 1 for k, v in reasons.items())
            or sum(reasons.values()) != result.total_targets - result.supported_targets): raise ValueError('unsupported counts')
    if result.status == 'fitted_response_temperature':
        if (isinstance(result.temperature, bool) or not isinstance(result.temperature, Real)
                or not math.isfinite(result.temperature) or not T_MIN <= result.temperature <= T_MAX
                or min(result.class_counts) < 1 or result.objective_evaluations < 3): raise ValueError('invalid fitted temperature')
        if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) or v < 0
               for v in (result.raw_log_loss, result.calibrated_log_loss)): raise ValueError('invalid objective')
    elif result.status in ('unsupported_no_predictions', 'unsupported_two_class_labels_required'):
        if (result.temperature is not None or result.objective_evaluations != 0 or result.raw_log_loss is not None
                or result.calibrated_log_loss is not None or min(result.class_counts) > 0): raise ValueError('invalid unsupported calibration')
        if (result.status == 'unsupported_no_predictions') != (result.supported_targets == 0):
            raise ValueError('unsupported status/population mismatch')
        if require_fitted: raise ValueError('calibrated evaluation unsupported: ' + result.status)
    else:
        raise ValueError('unknown calibration status')


def fit_temperature(targets, *, binding: PredictionBinding, partition: CalibrationPartition,
                    expected_target_keys: tuple[tuple[str, str, str, str], ...], max_evaluations: int = 200):
    """Fit calibration only; expected keys=(learner,event,item,full prehistory SHA).

    Thiếu một row là lỗi coverage; row unsupported phải còn nguyên với null p.
    Caller phải cung cấp frozen-predictor receipt/split manifest đúng thực tế.
    """
    if type(binding) is not PredictionBinding or type(partition) is not CalibrationPartition or binding.split_sha256 != partition.split_sha256:
        raise ValueError('calibration partition/binding mismatch')
    if type(max_evaluations) is not int or not 4 <= max_evaluations <= 200: raise ValueError('objective evaluation budget 4..200')
    targets = tuple(targets)
    if any(type(row) is not CalibrationTarget for row in targets): raise ValueError('calibration target schema')
    keys = tuple((r.learner_id, r.event_id, r.item_id, r.history_sha256) for r in targets)
    expected = tuple(tuple(row) for row in expected_target_keys)
    if (len(set(keys)) != len(keys) or len({(r.learner_id, r.event_id) for r in targets}) != len(targets)
            or len(set(expected)) != len(expected) or set(keys) != set(expected)
            or {r.learner_id for r in targets} != set(partition.calibration_learners)):
        raise ValueError('missing/extra/duplicate calibration population or wrong-role learner')
    ordered = tuple(sorted(targets, key=lambda r: (r.learner_id, r.event_id, r.item_id, r.history_sha256)))
    supported = tuple(r for r in ordered if r.probability is not None)
    counts = tuple(sum(r.correct == y for r in supported) for y in (0, 1))
    unsupported = tuple(sorted(Counter(r.support_reason for r in ordered if r.probability is None).items()))
    common = dict(binding=binding, partition_sha256=partition.identity,
                  targets_sha256=identity_hash([asdict(row) for row in ordered]), implementation_sha256=implementation_identity(),
                  total_targets=len(ordered), supported_targets=len(supported), class_counts=counts, unsupported_counts=unsupported)
    if not supported or min(counts) == 0:
        return TemperatureCalibration(**common, status='unsupported_no_predictions' if not supported else 'unsupported_two_class_labels_required',
                                      temperature=None, objective_evaluations=0, raw_log_loss=None, calibrated_log_loss=None)
    logits = tuple((_logit(r.probability), r.correct) for r in supported)
    def loss(beta):
        # Stable softplus(z)-y*z; beta=1/T gives convex scalar response NLL.
        return math.fsum(max(beta*z, 0) - y*beta*z + math.log1p(math.exp(-abs(beta*z))) for z, y in logits) / len(logits)
    values = []
    def objective(beta):
        if len(values) >= max_evaluations: raise RuntimeError('objective evaluation budget exhausted')
        value = loss(beta)
        if not math.isfinite(value): raise ValueError('nonfinite calibration objective')
        values.append((value, beta)); return value
    a, b = 1 / T_MAX, 1 / T_MIN
    raw_loss = objective(1.)
    objective(a); objective(b)
    ratio = (math.sqrt(5) - 1) / 2
    c, d = b - ratio*(b-a), a + ratio*(b-a)
    # Evaluate at most200 including endpoints and raw T1; low budget is explicit.
    if len(values) < max_evaluations: fc = objective(c)
    if len(values) < max_evaluations: fd = objective(d)
    else: fd = None
    while len(values) < max_evaluations and b-a > 1e-12 and fd is not None:
        if fc <= fd:
            b, d, fd = d, c, fc; c = b-ratio*(b-a); fc = objective(c)
        else:
            a, c, fc = c, d, fd; d = a+ratio*(b-a); fd = objective(d)
    best_loss, beta = min(values, key=lambda pair: (pair[0], abs(pair[1]-1), pair[1]))
    return TemperatureCalibration(**common, status='fitted_response_temperature', temperature=1/beta,
                                  objective_evaluations=len(values), raw_log_loss=raw_loss, calibrated_log_loss=best_loss)


def calibrate_probability(probability, *, calibration, binding):
    _validate_calibration(calibration, binding)
    return _sigmoid(_logit(probability) / calibration.temperature)


def reference_bank_v1(bank: SimulatorBank):
    """Đúng84 actual item IDs,28concepts×1050/1200/1350; không tạo item1250."""
    if type(bank) is not SimulatorBank: raise ValueError('SimulatorBank required')
    concepts = {}
    for item in bank.items: concepts.setdefault(item.concept_id, []).append(item)
    if len(concepts) != 28 or any(len(items) != 3 or {r.difficulty for r in items} != {1050.,1200.,1350.} for items in concepts.values()):
        raise ValueError('V1 requires28concepts each with3 actual reference difficulties')
    return tuple(ReferenceSet(c, tuple((r.item_id, 1/3) for r in rows)) for c, rows in sorted(concepts.items()))


def reference_identity(references):
    return identity_hash([asdict(row) for row in references])


def score_reference_bank(session, *, calibration, binding, timestamp: int, source_row: int):
    """Counterfactual response probes từ cùng history; không observe/RNG/practice.

    S là mean calibrated reference correctness; criterion không làP(K), không
    chọn ready/action và không nhận latent theta hoặc labels reference.
    """
    _validate_calibration(calibration, binding)
    refs = reference_bank_v1(session.bank)
    if (binding.model_id != session.backend.model_id or binding.bank_sha256 != session.bank.identity['item_bank_sha256']
            or binding.domain_sha256 != identity_hash(session.bank.identity) or binding.reference_sha256 != reference_identity(refs)):
        raise ValueError('reference model/bank/domain binding mismatch')
    before = session.history_sha256
    queries = tuple(ItemQuery(item, timestamp, source_row) for ref in refs for item, _ in ref.item_weights)
    results = session.probe_many(queries)
    scores = {}; offset = 0
    for ref in refs:
        rows = results[offset:offset+3]; offset += 3
        raw = {item: row.probability for (item, _), row in zip(ref.item_weights, rows)}
        # Identity đã được kiểm một lần cho toàn probe; không hash source84lần.
        calibrated = {item: None if p is None else _sigmoid(_logit(p) / calibration.temperature) for item, p in raw.items()}
        missing = tuple(item for item, p in calibrated.items() if p is None)
        score = None if missing else math.fsum(calibrated.values()) / 3
        scores[ref.concept_id] = dict(score=score, reference_criterion=None if score is None else score >= TAU_REF,
            expected_items=3, supported_items=3-len(missing), missing_items=missing,
            unsupported_reasons={item: row.prediction_kind for (item, _), row in zip(ref.item_weights, rows) if row.probability is None},
            raw_probabilities=raw, calibrated_probabilities=calibrated)
    if session.history_sha256 != before: raise ValueError('reference probe modified learner history')
    return dict(recipe=RECIPE, history_sha256=before, reference_history_sha256=before,
                bank_identity=session.bank.identity, calibration_sha256=calibration.identity,
                reference_sha256=reference_identity(refs), tau_ref=TAU_REF, concepts=scores,
                item_calibrated_probabilities={item: p for row in scores.values() for item, p in row['calibrated_probabilities'].items()},
                semantics='mean calibrated reference response correctness; not latent mastery probability',
                supported_concepts=sum(row['score'] is not None for row in scores.values()), total_concepts=28)
