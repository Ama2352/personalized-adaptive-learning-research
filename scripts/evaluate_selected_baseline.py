"""Tính metrics từ cached selected CSV SAKT/GKT, không tạo model."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def run_request(root, request_path, expected_sha256, output):
    from knowledge_tracing.research_admission import MainSelectionContext, PopulationExpectation
    from knowledge_tracing.research_population import SelectionPopulation
    from knowledge_tracing.research_baseline_evaluation import evaluate_cached_selected_baseline
    from knowledge_tracing.research_selection_io import FileRef, FileReadLimits, need
    from knowledge_tracing.simulator_research_data import ResearchSplitPlan
    root = Path(root).resolve(strict=True)
    request_path = Path(request_path).resolve(strict=True)
    need(request_path.is_relative_to(root) and request_path.stat().st_size <= 2*1024**2,
         'Small owned request required')
    raw = request_path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected_sha256, 'Pinned metrics request required')
    request = json.loads(raw)
    need(set(request) == {'kind', 'claim', 'predictions', 'targets', 'coverage', 'population', 'plan', 'io_limits'}
         and request['kind'] == 'CACHED_SELECTED_BASELINE_METRICS_V1', 'Exact metrics request schema required')
    document = dict(request['population'])
    expectation = dict(document.pop('expectation'))
    expectation['context'] = MainSelectionContext(**expectation['context'])
    document['expectation'] = PopulationExpectation(**expectation)
    document['learner_target_counts'] = tuple(tuple(pair) for pair in document['learner_target_counts'])
    document['class_counts'] = tuple(document['class_counts'])
    result = evaluate_cached_selected_baseline(root,
        **{name+'_ref': FileRef(**request[name]) for name in ('claim', 'predictions', 'targets', 'coverage')},
        population=SelectionPopulation(**document), plan=ResearchSplitPlan(**request['plan']),
        io_limits=FileReadLimits(**request['io_limits']))
    output = Path(output).absolute()
    base = root/'research_tracking/runs'
    need(output.is_relative_to(base) and len(output.relative_to(base).parts) == 2
         and output.suffix == '.json' and not output.exists()
         and output.parent.is_dir() and output.resolve() == output,
         'New JSON output in one existing research run required')
    body = (json.dumps(dict(result, request_sha256=expected_sha256), ensure_ascii=False,
                       sort_keys=True, allow_nan=False)+'\n').encode()
    need(len(body) <= 2*1024**2, 'Small metric report output cap')
    with output.open('xb') as stream:
        stream.write(body)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if Path(sys.prefix).resolve() != (ROOT/'.venv').resolve():
        raise ValueError('Repository .venv required')
    result = run_request(ROOT, args.request, args.request_sha256, args.output)
    print(json.dumps(dict(status=result['status'], candidate=result['candidate_id'],
                          full_targets=result['full_targets'], supported_targets=result['supported_targets'])))


if __name__ == '__main__':
    main()
