"""ROOT-only dry/closure; metadata/SHA/copy, không rerun test/model/import context."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
DRY = PREP/'graph_context_pure03_dry.json'
RUN = 'cgakt-research-context-engineering-20261109-01'
HELPER = ROOT/'src/knowledge_tracing/evidence.py'
HELPER_SHA = '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
PRIOR = 'research_tracking/runs/cgakt-research-condition-engineering-20261109-01/manifest.json'
PRIOR_SHA = '1c99ba062ace6cd3629fcbd65da4f31ddc1d7786cb3eb48ca95d4cd4cd6cbebd'
SOURCE = '5a5ada91a78a5d7de2b4d5021dc3cf34e6c97de2e46931509b8f6faf5c56c4d5'
TEST = 'ac6bff7187ef37aa9b4455706992763681ccd9f433fd93965cf93d7ce7c9dd52'
GENERATED = {'README.md', 'execution.log', 'approved_dry_inventory.json', 'copy_inventory_before.json',
             'copy_inventory_after.json', 'frozen_acceptance.json', 'closure_review.json', 'raw_log_paths.txt'}
NOTE = '''# CG-AKT research context — dữ liệu, chưa model

Actual03=109PASS(66condition+43context),0FES; actual01/02 đều67PASS+39setup errors.
Hai lỗi gồm fixture source_row0 và source đọc field labels không tồn tại.
Source/test lịch sử, exact raw logs/XML/receipts và cached-import sửa classidentity
được giữ nguyên. Không relabel lịch sử66 hoặc106 thành109.

NumPy data-only,0neural/optimizer/teacher/actualcorpus/artifact. Handmade typed
phases không fitted research attestation. Reuse native research geometry/audit;
full population/OOV/effectivepast/causality/indexseals được kiểm trên fixture.
Main model/checkpoint/lifecycle chưa nghiệm thu; static hotpath7fullcachehashes/
trainbatch vẫn cần xử lý SAU bounded correctness, không benchmark/costclaim.

Tham chiếu bundle condition13 bằng exactmanifest, không duplicate toàn sourcecũ.
Closure chỉ kiểm output integrity/SHA; không currentGate/NN/RQ3 efficacy proof.
'''


def need(ok, message):
    if not ok:
        raise ValueError(message)


def physical(path):
    path = path.absolute()
    need(path.is_relative_to(ROOT) and ROOT.resolve() == ROOT.absolute(), 'physical workspace path')
    cursor = ROOT
    for part in ('', *path.relative_to(ROOT).parts):
        cursor = cursor/part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias')
    need(path.resolve() == path, 'resolved path mismatch')
    return path


def sha(path):
    path = physical(path)
    need(path.is_file() and path.stat().st_size <= 2*1024**2, 'small regular evidence file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    sha(path)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def check():
    dry = read(DRY)
    need(dry['run_id'] == RUN and sha(HELPER) == HELPER_SHA, 'run/helper pin')
    prior = read(ROOT/PRIOR)
    need(sha(ROOT/PRIOR) == PRIOR_SHA and prior['status'] == 'completed'
         and len(prior['outputs_sha256']) == 13, 'immutable condition13 reference')
    aliases, paths = set(), set()
    for row in dry['copies']:
        path = physical(ROOT/row['source']); name = row['copy']
        need(path.suffix not in ('.pt', '.pth', '.bin', '.zip', '.parquet')
             and name not in aliases and '/' not in name and '\\' not in name and row['source'] not in paths,
             'unique flat small copy allowlist')
        need(sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], 'copy source SHA/size drift')
        aliases.add(name); paths.add(row['source'])
    need(sha(ROOT/'src/knowledge_tracing/akt/research_graph_context.py') == SOURCE
         and sha(ROOT/'tests/akt/test_research_graph_context.py') == TEST, 'accepted context source/test pin')
    trials = []
    for number, count, errors in (('01', 106, 39), ('02', 106, 39), ('03', 109, 0)):
        folder = PREP/('graph-context-pure'+number)
        result = read(folder/'result.json')
        expected = dict(tests=count, failures=0, errors=errors, skipped=0)
        tree = ET.parse(folder/'junit.xml').getroot()
        actual = {key: sum(int(s.get(key, '0')) for s in tree.iter('testsuite')) for key in expected}
        need(actual == result['counts'] == expected and len(list(tree.iter('testcase'))) == count, 'raw JUnit exact counts')
        need(result['source_before'] == result['source_after'] and all(c['accepted'] for c in result['cold_import_canaries']),
             'historical tested source/canary binding')
        need(result['actual_neural_model_calls'] == result['actual_optimizer_calls'] == result['actual_teacher_calls'] == 0
             and result['actual_artifact_or_corpus_parsed'] is False, 'data-only scope')
        if number == '03':
            need(result['status'] == 'ACCEPTED_109_CONDITION_CONTEXT_CASES_NOT_MODEL' and result['returncode'] == 0
                 and result['error'] is None and 0 <= result['seconds'] < result['cap_seconds'] == 90, 'actual03 accepted budget')
            need(result['source_before']['src/knowledge_tracing/akt/research_graph_context.py'] == SOURCE
                 and result['source_before']['tests/akt/test_research_graph_context.py'] == TEST, 'actual03 source binding')
        else:
            need(result['status'] == 'REJECTED_KEEP_ALL', 'historical setup failures preserved')
        trials.append(dict(trial=number, counts=actual, passed=count-errors, status=result['status'],
                           stored_controller_seconds=result['seconds'], result_sha256=sha(folder/'result.json')))
    need(dry['generated_outputs'] == sorted(GENERATED) and not aliases & GENERATED
         and dry['expected_output_count'] == len(aliases)+len(GENERATED), 'exact generated order/count')
    return dry, trials


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-dry', action='store_true'); parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256'); parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'project venv only')
    need(args.check_dry != args.close, 'choose readonly check or reviewed closure')
    dry, trials = check()
    if args.check_dry:
        print(json.dumps(dict(status='DRY_VERIFIED_NOT_CLOSED', dry_sha256=sha(DRY),
                              copies=len(dry['copies']), expected_outputs=dry['expected_output_count']))); return
    need(sha(DRY) == args.expected_dry_sha256 and type(args.review_reference) is str
         and bool(args.review_reference.strip()), 'exact ROOT dry review required')
    need(not (ROOT/'research_tracking/runs'/RUN).exists(), 'new run only')
    before = [dict(row, sha256_before_copy=sha(ROOT/row['source'])) for row in dry['copies']]
    spec = importlib.util.spec_from_file_location('pinned_evidence', HELPER)
    evidence = importlib.util.module_from_spec(spec); spec.loader.exec_module(evidence)
    with evidence.record_evidence_run(ROOT, RUN, metadata=dict(kind='CGAKT_RESEARCH_CONTEXT_NUMPY_NOT_MODEL',
            trials=trials, prior_condition13_manifest_sha256=PRIOR_SHA),
            sources=[ROOT/r['source'] for r in dry['copies']]+[DRY], note=NOTE) as output:
        write(output/'approved_dry_inventory.json', dry)
        write(output/'copy_inventory_before.json', before)
        after = []
        for row in dry['copies']:
            source, target = ROOT/row['source'], output/row['copy']
            with target.open('xb') as stream:
                stream.write(source.read_bytes())
            need(sha(source) == sha(target) == row['sha256'], 'copy pre/post SHA mismatch')
            after.append(dict(row, sha256_after_copy=sha(target), source_sha256_after_copy=sha(source)))
        write(output/'copy_inventory_after.json', after)
        write(output/'frozen_acceptance.json', dict(trials=trials, current_source=SOURCE, current_test=TEST,
            scientific_fit=False, model_execution_in_bundle=False, static_hotpath_not_benchmarked=True))
        write(output/'closure_review.json', dict(reference=args.review_reference, dry_sha256=sha(DRY),
            scope='ROOT metadata admission; no test/model rerun or fitted/Gate promotion'))
        with (output/'raw_log_paths.txt').open('x', encoding='utf-8') as stream:
            stream.write('\n'.join(r['source'] for r in dry['copies'] if r['source'].endswith(('.log', '.xml'))) + '\n')
        need({p.name for p in output.iterdir() if p.name != 'manifest.json'} ==
             set(dry['generated_outputs']) | {r['copy'] for r in dry['copies']}, 'exact output population')
        need(all(sha(ROOT/r['source']) == r['sha256'] for r in dry['copies']), 'source drift after copies')
    directory = ROOT/'research_tracking/runs'/RUN
    verified = evidence.verify_evidence_bundle(directory)
    need(verified['artifacts'] == dry['expected_output_count'], 'final output count')
    print(json.dumps(dict(**verified, manifest_sha256=sha(directory/'manifest.json'), run_id=RUN)))


if __name__ == '__main__':
    main()
