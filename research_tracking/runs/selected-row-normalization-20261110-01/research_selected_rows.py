"""Chuẩn hóa khai báo và dòng CSV selected-only của ba producer.

Hàm thuần, không đọc file, tải model hoặc cấp quyền chọn/refit. Caller vẫn phải
kiểm bytes, metadata, toàn bộ quần thể và đủ chín candidate bằng lớp admission.
Giữ nguyên xác suất binary64 sau khi đọc chuỗi CSV, không điền giá trị OOV.
"""
from dataclasses import fields
import re

from .research_admission import (
    ArtifactClaim, MainSelectionContext, RawSelectedRow, SelectedCandidateClaim,
)
from .research_selection_io import GEOMETRY_FIELDS, PHASE_FIELDS, _key, csv_fields, need


def _exact_fields(value, names):
    need(type(value) is dict and set(value) == set(names), 'Exact object fields required')


def decode_selected_claim(document):
    """Giải mã khai báo JSON, chưa xác minh artifact hoặc operation receipt."""
    _exact_fields(document, (field.name for field in fields(SelectedCandidateClaim)))
    values = dict(document)
    context = values['context']
    _exact_fields(context, (field.name for field in fields(MainSelectionContext)))
    values['context'] = MainSelectionContext(**context)
    for name in ('terminal', 'checkpoint', 'raw_predictions', 'targets', 'coverage'):
        artifact = values[name]
        _exact_fields(artifact, ('sha256', 'size_bytes'))
        values[name] = ArtifactClaim(**artifact)
    reasons = values['unsupported_counts']
    need(type(reasons) is list and len(reasons) <= 128, 'Bounded JSON reason pairs required')
    need(all(type(pair) is list and len(pair) == 2 for pair in reasons), 'JSON reason/count pairs required')
    values['unsupported_counts'] = tuple(tuple(pair) for pair in reasons)
    return SelectedCandidateClaim(**values)


def _unsigned(text):
    need(re.fullmatch(r'0|[1-9][0-9]{0,18}', text) is not None, 'Canonical bounded integer required')
    value = int(text)
    need(value < 2**63, 'Integer outside key range')
    return value


def normalize_selected_row(prediction, target, claim):
    """Join một cặp dòng theo đầy đủ khóa và binding của đúng producer.

    Không chứng minh coverage bằng một dòng. Accumulator kiểm lại số lượng,
    duplicate, nhãn và population hash sau khi caller đã kiểm metadata/file.
    """
    need(type(claim) is SelectedCandidateClaim, 'Typed selected claim required')
    claim.validate()
    candidate = claim.candidate_id
    for row, kind in ((prediction, 'predictions'), (target, 'targets')):
        _exact_fields(row, csv_fields(candidate, kind))
        need(all(type(value) is str and len(value) <= 4096 for value in row.values()),
             'Bounded raw CSV strings required')
        for name in ('timestamp', 'source_row', 'global_rank'):
            _unsigned(row[name])
    key = _key(prediction)
    need(key == _key(target), 'Prediction/target full key mismatch')
    phase = ('raw_selection10', claim.phase_sha256, claim.encoding_sha256)
    need(tuple(prediction[name] for name in PHASE_FIELDS) == phase, 'Prediction phase/encoding mismatch')
    is_akt = candidate.startswith('A')
    if is_akt:
        need(tuple(target[name] for name in PHASE_FIELDS) == phase, 'Target phase/encoding mismatch')
    need(target['correct'] in ('0', '1'), 'Exact binary CSV label required')
    text = prediction['probability']
    need(text == text.strip(), 'Probability whitespace forbidden')
    probability = None if text == '' else float(text)
    reason = prediction['support_reason']
    if probability is None:
        need(reason in dict(claim.unsupported_counts), 'Undeclared unsupported reason')
    if is_akt:
        if probability is None:
            need(reason == 'oov_item' and all(prediction[name] == '' for name in GEOMETRY_FIELDS),
                 'AKT OOV must have empty geometry')
        else:
            window = prediction['window_id']
            need(re.fullmatch('[0-9a-f]{64}', window) is not None, 'AKT window SHA256 required')
            available = _unsigned(prediction['history_available'])
            used = _unsigned(prediction['history_used'])
            need(used <= available and prediction['context_reset'] in ('True', 'False'),
                 'AKT history geometry mismatch')
    else:
        input_reason = prediction['input_support_reason']
        unsupported = ('oov_item', 'cold_unsupported') if candidate == 'SAKT' else ('oov_item', 'unsupported_history')
        if probability is None:
            need(reason == input_reason and input_reason in unsupported, 'Baseline unsupported reason mismatch')
        else:
            need(input_reason in ('known_history', 'cold_query_only'), 'Baseline supported input reason mismatch')
    return RawSelectedRow(candidate, key, int(target['correct']), probability, reason,
                          *phase)
