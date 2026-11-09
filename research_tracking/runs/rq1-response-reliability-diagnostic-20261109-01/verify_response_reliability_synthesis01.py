"""Đối chiếu JSON tổng hợp đã tạo với các bins được nghiệm thu."""
import hashlib
import json
import math
from pathlib import Path

PREP = Path(__file__).resolve().parent
OUTER = PREP / 'rq1-response-reliability-native01-outer/final.json'
RELIABILITY = PREP / 'rq1-response-reliability-attempt01/reliability.json'
SYNTHESIS = PREP / 'rq1_response_reliability_synthesis01.json'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def derive_summary(source, source_sha256, outer_sha256):
    rows = []
    for group in source['groups']:
        if group['level'] == 'world':
            continue
        row = {name: group[name] for name in (
            'level', 'profile', 'graph_on', 'mechanism_on', 'rows',
            'ordinary_ece15', 'oracle_response_ece15')}
        count = group['rows']
        fields = (
            ('mean_prediction', 'mean_prediction'),
            ('mean_observed_correct', 'mean_correct'),
            ('mean_true_response_probability', 'mean_oracle_probability'),
        )
        for destination, field in fields:
            row[destination] = math.fsum(
                item['rows'] * item[field]
                for item in group['bins'] if item['rows']) / count
        row['mean_model_bias'] = row['mean_prediction'] - row['mean_true_response_probability']
        row['mean_response_residual'] = row['mean_true_response_probability'] - row['mean_observed_correct']
        rows.append(row)
    return dict(kind='DESCRIPTIVE_RESPONSE_CALIBRATION_SYNTHESIS',
                source_sha256=source_sha256, accepted_outer_sha256=outer_sha256,
                groups=rows, model_calls=0, new_worlds=0, new_seed_families=0)

def main():
    accepted = json.loads(OUTER.read_bytes())
    if (digest(OUTER) != 'e68aae35eca99c111107d2748a62baeb1a78bf5e4b5952bb777befe980ae6ca8'
            or accepted['status'] != 'ACCEPTED_CACHED_RQ1_RESPONSE_RELIABILITY'):
        raise ValueError('actual accepted analysis required')
    source_sha256 = digest(RELIABILITY)
    if source_sha256 != accepted['artifacts']['reliability.json']['sha256']:
        raise ValueError('accepted bin table changed')
    actual = json.loads(SYNTHESIS.read_bytes())
    expected = derive_summary(json.loads(RELIABILITY.read_bytes()), source_sha256, digest(OUTER))
    if actual != expected or len(actual['groups']) != 16:
        raise ValueError('existing derived JSON differs from accepted bins')
    result = dict(status='VERIFIED_EXISTING_SYNTHESIS_FROM_ACCEPTED_BINS',
                  recipe_sha256=digest(Path(__file__)), synthesis_sha256=digest(SYNTHESIS),
                  reliability_input_sha256=source_sha256, groups=16,
                  model_calls=0, new_worlds=0,
                  provenance_vi='Recipe được lưu sau phép tổng hợp ban đầu, đã đối chiếu toàn bộ16nhóm đúng JSON hiện có.')
    destination = PREP / 'rq1_response_reliability_synthesis_verification01.json'
    with destination.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
