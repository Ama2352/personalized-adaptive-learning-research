"""Dry inventory/explicitly approved archive only; never execute model/tests/analysis."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import math
import xml.etree.ElementTree as ET

PREP = Path(__file__).resolve().parent
ROOT = PREP.parents[3]
RUN_ID = 'rq1-closed-loop-reconstruction-20261108-02'
REPORT = ROOT / 'research_tracking/reports/rq1_closed_loop_reconstruction_20261108.md'
OLD = ROOT / 'research_tracking/runs/cpu-closedloop-20261107-01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    original = read(PREP / 'closed-loop-model-attempt01/run.json')
    accepted = read(PREP / 'closed-loop-fast-model-attempt01/run.json')
    parity = read(PREP / 'closed-loop-fast-model-attempt01/parity.json')
    raw_review = read(PREP / 'parent-closed-loop-fast-review02.json')
    rank_review = read(PREP / 'parent-ranking-review.json')
    if original['status'] != 'REJECTED_CUMULATIVE_RESOURCE_BOUND' or (PREP / 'closed-loop-model-attempt01/parity.json').exists():
        raise ValueError('original failure must remain rejected/no parity')
    if accepted['status'] != 'PASS_CURRENT_SOURCE_RECONSTRUCTION_EXACT_STORED_LEGACY_PARITY':
        raise ValueError('accepted raw reconstruction missing')
    if accepted['controller_seconds_including_spy'] > 300 or accepted['overall_seconds_including_prior_failure_and_diagnostic'] > 430:
        raise ValueError('resource bounds')
    if raw_review['status'] != 'PASS_PARENT_RAW_RECONSTRUCTION_REVIEW_NO_NEW_METRICS':
        raise ValueError('actual parent raw review required')
    if rank_review['status'] != 'PASS_PARENT_INDEPENDENT_RAW_RANKING_AND_DESCRIPTIVE_REVIEW':
        raise ValueError('actual parent source-key review required')
    for label, count in [('closed-loop-spy-attempt01', 17), ('closed-loop-fast-spy-attempt01', 10)]:
        receipt = read(PREP / label / 'run.json')
        if receipt['counts'] != dict(tests=count, failures=0, errors=0, skipped=0):
            raise ValueError('separate spy counts')
    descriptive = read(PREP / 'closed_loop_descriptive_controller_receipt.json')
    posthoc = read(PREP / 'closed_loop_ranking_posthoc_controller_receipt.json')
    if (descriptive['status'] != 'PASS_DESCRIPTIVE_ONLY_NO_MODEL'
            or descriptive['purefixture_counts'] != dict(tests=12, failures=0, errors=0, skipped=0)
            or descriptive['controller_elapsed_seconds'] > 30):
        raise ValueError('descriptive receipt')
    if (posthoc['status'] != 'PASS_POSTHOC_CANDIDATE_REVIEW_PENDING'
            or posthoc['purefixture_counts'] != dict(tests=5, failures=0, errors=0, skipped=0)
            or posthoc['controller_elapsed_seconds_including_purefixtures'] > 15):
        raise ValueError('posthoc generation receipt; generated pending label must remain historical')
    for folder, count in [('closed-loop-spy-attempt01', 17), ('closed-loop-fast-spy-attempt01', 10),
                          ('closed-loop-analysis-spy-attempt01', 12), ('closed-loop-ranking-spy-attempt01', 5)]:
        suites = list(ET.parse(PREP / folder / 'pytest.xml').getroot().iter('testsuite'))
        actual = {k: sum(int(s.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
        if actual != dict(tests=count, failures=0, errors=0, skipped=0):
            raise ValueError('separate actual JUnit count mismatch: ' + folder)
    for name in ('closed_loop_fast_source_inventory.json', 'closed_loop_descriptive_source_inventory.json',
                 'closed_loop_ranking_posthoc_source_inventory.json'):
        for rel, digest in read(PREP / name)['files_sha256'].items():
            if sha(ROOT / rel) != digest:
                raise ValueError('frozen source/input drift: ' + rel)
    for name in ('closed_loop_model_attempt01_frozen.json', 'closed_loop_fast_model_attempt01_frozen.json'):
        folder = 'closed-loop-model-attempt01' if name == 'closed_loop_model_attempt01_frozen.json' else 'closed-loop-fast-model-attempt01'
        for rel, item in read(PREP / name)['actual_raw_files'].items():
            if sha(PREP / folder / rel) != item['sha256']:
                raise ValueError('raw preservation')
    historical = read(OLD / 'manifest.json')
    for rel, digest in historical['outputs_sha256'].items():
        if sha(OLD / rel) != digest:
            raise ValueError('historical8 drift')
    if ([v['legacy_rows'] for v in parity['passes']] != [3240, 3240]
            or [v['outcome_rows'] for v in parity['passes']] != [27, 27]
            or parity['passes'][0]['native_state_fingerprints'] != parity['passes'][1]['native_state_fingerprints']
            or parity['passes'][0]['uniform_fingerprints'] != parity['passes'][1]['uniform_fingerprints']):
        raise ValueError('stored parity receipt consistency')
    prior_archive = ROOT / 'research_tracking/runs/rq1-closed-loop-reconstruction-20261108-01'
    if sha(prior_archive / 'manifest.json') != '07dd5de2d4b9577a25e5be3e70f9ab56527ad885c688ea883a1595ee8bb76928':
        raise ValueError('failed archive manifest changed')
    prior = read(prior_archive / 'manifest.json')
    if prior['status'] != 'failed' or len(prior['outputs_sha256']) != 116:
        raise ValueError('prior failed archive identity')
    for name, digest in prior['outputs_sha256'].items():
        if sha(prior_archive / name) != digest:
            raise ValueError('prior failed archive output changed')
    return {'prior_failed_archive_manifest_sha256': sha(prior_archive / 'manifest.json'),
            'prior_failed_archive_outputs_verified': 116, 'prior_archive_failure_role': 'OPERATIONAL_GIT_IGNORE_OPTION_BUG_NOT_NATIVE_FAILURE', 'kind': 'CURRENT_SOURCE_CLOSED_LOOP_RECONSTRUCTION_WITH_DESCRIPTIVE_AND_POSTHOC_LOCAL_EXPLANATION',
            'original_a585_whole_source_recovered': False, 'new_independent_N': 0, 'optimizer_steps': 0,
            'original_failure_seconds': original['controller_seconds_including_spy'],
            'accepted_revision_seconds_including_conservative5spy': accepted['controller_seconds_including_spy'],
            'overall_seconds_including_prior_failure_and_diagnostic': accepted['overall_seconds_including_prior_failure_and_diagnostic'],
            'revision_cap_seconds': 300, 'overall_cap_seconds': 430,
            'test_groups_separate_not_broad_suite': {'original_spies': 17, 'fast_spies': 10, 'descriptive_fixtures': 12, 'posthoc_fixtures': 5},
            'legacy_rows_exact_each_pass': 3240, 'outcome_rows_exact_each_pass': 27,
            'final_state_pairs': 27, 'uniform_pairs': 9, 'observed_metadata_rows': 3240,
            'posthoc_role': 'EXPLORATORY_SOURCE_LOCAL_CID_EXPLANATION_PARENT_REVIEWED_NOT_CONFIRMATORY',
            'parent_raw_review_sha256': sha(PREP / 'parent-closed-loop-fast-review02.json'),
            'parent_ranking_review_sha256': sha(PREP / 'parent-ranking-review.json'),
            'archive_model_test_analysis_RNG_calls': 0}


def selection():
    names = [
        'CLOSED_LOOP_OBSERVABILITY_CONTRACT.md', 'CLOSED_LOOP_OBSERVABILITY_CONTRACT.sources.json',
        'closed_loop_observer.py', 'run_closed_loop_reconstruction.py', 'test_closed_loop_observer.py',
        'closed_loop_source_inventory.json', 'closed_loop_spy_receipt.json', 'closed_loop_proposed_command.ps1.txt',
        'CLOSED_LOOP_IMPLEMENTATION_FREEZE.md', 'closed_loop_model_attempt01_frozen.json',
        'closed_loop_observer_fast.py', 'run_closed_loop_reconstruction_fast.py', 'test_closed_loop_observer_fast.py',
        'benchmark_closed_loop_callbacks_fast.py', 'closed_loop_fast_source_inventory.json',
        'closed_loop_fast_budget_ledger.json', 'closed_loop_fast_spy_receipt.json',
        'closed_loop_fast_proposed_command.ps1.txt', 'CLOSED_LOOP_FAST_IMPLEMENTATION_FREEZE.md',
        'closed_loop_fast_model_attempt01_frozen.json', 'parent-closed-loop-fast-review02.json',
        'parent_closed_loop_fast_review.py', 'analyze_closed_loop_descriptive.py', 'test_closed_loop_descriptive.py',
        'CLOSED_LOOP_DESCRIPTIVE_ANALYSIS_PLAN.json', 'closed_loop_descriptive_source_inventory.json',
        'closed_loop_descriptive_controller_receipt.json', 'analyze_closed_loop_ranking_posthoc.py',
        'test_closed_loop_ranking_posthoc.py', 'CLOSED_LOOP_RANKING_POSTHOC_PLAN.json',
        'closed_loop_ranking_posthoc_source_inventory.json', 'closed_loop_ranking_posthoc_controller_receipt.json',
        'parent-ranking-review.json', 'parent_ranking_review.py', 'closed_loop_native_source_snapshot.json',
        'closed_loop_archive_failure_diagnostic01.json', 'closed_loop_git_ignore_argv_test01.json']
    pairs = [(PREP / name, 'prep__' + name) for name in names]
    folders = [('closed-loop-spy-attempt01', 'spy_original'), ('closed-loop-fast-spy-attempt01', 'spy_fast'),
               ('closed-loop-analysis-spy-attempt01', 'spy_descriptive'), ('closed-loop-ranking-spy-attempt01', 'spy_posthoc'),
               ('closed-loop-model-attempt01', 'failed120'), ('closed-loop-fast-model-attempt01', 'accepted_fast'),
               ('closed-loop-descriptive-analysis01', 'descriptive'), ('closed-loop-ranking-posthoc01', 'posthoc')]
    for folder, alias in folders:
        for path in sorted((PREP / folder).iterdir()):
            if path.is_file():
                if path.suffix not in {'.py', '.json', '.log', '.xml', '.gz', '.md', '.csv'}:
                    raise ValueError('unselected top-level artifact: ' + str(path))
                pairs.append((path, alias + '__' + path.name))
    for name in ('manifest.json', 'source_provenance.json', 'closed_loop_outcomes.json', 'traces.jsonl.gz', 'README.md'):
        pairs.append((OLD / name, 'historical__' + name))
    pairs += [(REPORT, 'rq1_closed_loop_reconstruction_20261108.md'),
              (Path(__file__).resolve(), 'pack_closed_loop_reconstruction_v2.py'),
              (ROOT / 'src/knowledge_tracing/evidence.py', 'evidence_helper.py'),
              (ROOT / 'src/knowledge_tracing/paper2_reference.py', 'paper2_reference.py'),
              (ROOT / 'scripts/research/run_cpu_diagnostics.py', 'current_candidate_runner.py')]
    prior_archive = ROOT / 'research_tracking/runs/rq1-closed-loop-reconstruction-20261108-01'
    pairs += [(PREP / 'pack_closed_loop_reconstruction.py', 'operational_failed01__original_packager.py'),
              (prior_archive / 'rq1_closed_loop_reconstruction_20261108.md', 'operational_failed01__approved_report54a.md'),
              (prior_archive / 'manifest.json', 'operational_failed01__manifest.json'),
              (prior_archive / 'execution.log', 'operational_failed01__execution.log'),
              (prior_archive / 'closure_review.json', 'operational_failed01__closure_review.json')]
    provenance = read(OLD / 'source_provenance.json')
    for rel, digest in provenance['inputs'].items():
        path = ROOT / rel
        if sha(path) != digest:
            raise ValueError('simulator source input drift')
        pairs.append((path, 'simulator_input__' + path.name))
    if len({alias for _, alias in pairs}) != len(pairs):
        raise ValueError('duplicate flat output aliases')
    for path, alias in pairs:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT) or not path.is_file():
            raise ValueError('unsafe source path')
        if path.stat().st_size > 2 * 1024 * 1024 or any(v in alias.lower() for v in ('base64', 'private', '.pt', '.parquet', '.zip')):
            raise ValueError('out-of-scope payload')
    if sum(path.stat().st_size for path, _ in pairs) > 6 * 1024 * 1024:
        raise ValueError('small evidence bundle byte cap')
    return pairs


def inventory():
    acceptance = validate()
    pairs = selection()
    sources = {path for path, _ in pairs}
    for name in ('closed_loop_fast_source_inventory.json', 'closed_loop_descriptive_source_inventory.json',
                 'closed_loop_ranking_posthoc_source_inventory.json'):
        sources |= {ROOT / rel for rel in read(PREP / name)['files_sha256']}
    sources |= {OLD / name for name in read(OLD / 'manifest.json')['outputs_sha256']}
    prior_archive = ROOT / 'research_tracking/runs/rq1-closed-loop-reconstruction-20261108-01'
    sources |= {prior_archive / name for name in read(prior_archive / 'manifest.json')['outputs_sha256']}
    return {'role': 'DRY_INVENTORY_ONLY_NO_BUNDLE_CREATED', 'run_id': RUN_ID, 'report_sha256': sha(REPORT),
            'acceptance': acceptance, 'copy_pairs': [{'source': path.relative_to(ROOT).as_posix(), 'copy': alias,
                'bytes': path.stat().st_size, 'sha256_before_copy': sha(path)} for path, alias in pairs],
            'selected_bytes': sum(p.stat().st_size for p, _ in pairs),
            'sources_sha256': {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(sources)},
            'close_adds_byte_exact_approved_dry_inventory_copy': True,
            'expected_generated_outputs': ['README.md', 'execution.log', 'copy_inventory_before.json', 'copy_inventory.json',
                'frozen_acceptance.json', 'historical8_preservation.json', 'closure_review.json',
                'git_ignore_check.json', 'force_add_paths.txt'],
            'excluded': ['pytest tmp directories', 'whole notebooks/ZIPs', 'checkpoint/Parquet', 'base64 payloads/private RPC',
                         'realdata/Holdout', 'unrelated fixed-stream/RQ1 bundles'],
            'model_test_analysis_rng_calls': 0}


class GitIgnoreQueryError(ValueError):
    def __init__(self, receipt):
        super().__init__('Git ignore query rejected; actual stderr/argv persisted')
        self.receipt = receipt


def query_ignored(paths, timeout=5.0):
    if (not paths or len(set(paths)) != len(paths)
            or any(not isinstance(p, str) or any(c in p for c in ('\t', '\n', '\r')) for p in paths)):
        raise ValueError('explicit unique paths without tabs/LF/CR required')
    command = ['git', '-c', 'safe.directory=' + str(ROOT), '-c', 'core.quotePath=false',
               'check-ignore', '--no-index', '--verbose', '--', *paths]
    start = time.perf_counter()
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=timeout)
        receipt = {'argv': command, 'returncode': result.returncode,
                   'stdout': result.stdout.decode('utf-8', errors='replace'),
                   'stderr': result.stderr.decode('utf-8', errors='replace'),
                   'elapsed_seconds': time.perf_counter() - start, 'timeout_seconds': timeout}
    except subprocess.TimeoutExpired as error:
        receipt = {'argv': command, 'returncode': None, 'failure': 'TimeoutExpired',
                   'stdout': (error.stdout or b'').decode('utf-8', errors='replace'),
                   'stderr': (error.stderr or b'').decode('utf-8', errors='replace'),
                   'elapsed_seconds': time.perf_counter() - start, 'timeout_seconds': timeout}
        raise GitIgnoreQueryError(receipt) from error
    if (result.returncode not in (0, 1) or not math.isfinite(receipt['elapsed_seconds'])
            or receipt['elapsed_seconds'] > timeout):
        raise GitIgnoreQueryError(receipt)
    ignored = {}
    for line in receipt['stdout'].splitlines():
        if '\t' not in line:
            raise GitIgnoreQueryError({**receipt, 'parse_error': 'verbose tab delimiter missing'})
        rule, path = line.rsplit('\t', 1)
        if not rule or path not in paths or path in ignored:
            raise GitIgnoreQueryError({**receipt, 'parse_error': 'unexpected/duplicate path or empty rule'})
        ignored[path] = {'verbose_rule': rule}
    return ignored, receipt


def close(args, dry):
    if (not args.approved_report_sha256 or args.approved_report_sha256 != sha(REPORT)
            or not args.approved_inventory_sha256 or args.approved_inventory_sha256 != sha(args.inventory_output)
            or not args.approval_reference):
        raise ValueError('exact report/inventory SHA and actual parent closure approval required')
    if read(args.inventory_output) != dry:
        raise ValueError('dry inventory changed or source selection drift')
    if Path(sys.prefix).resolve() != ROOT / '.venv':
        raise ValueError('project venv only')
    count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
    os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'
    os.environ[f'GIT_CONFIG_VALUE_{count}'] = str(ROOT)
    os.environ['GIT_CONFIG_COUNT'] = str(count + 1)
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    pairs = [(ROOT / row['source'], row['copy']) for row in dry['copy_pairs']]
    pairs.append((args.inventory_output, 'approved_dry_inventory.json'))
    before = [{'source': p.relative_to(ROOT).as_posix(), 'copy': alias,
               'bytes': p.stat().st_size, 'sha256_before_copy': sha(p)} for p, alias in pairs]
    sources = sorted({ROOT / name for name in dry['sources_sha256']} | {args.inventory_output})
    historical_before = {name: sha(OLD / name) for name in read(OLD / 'manifest.json')['outputs_sha256']}
    note = ('# RQ1 closed-loop — current-source reconstruction, không exact historical source\n\n'
        'Giữ timeout120.029706s và fastPASS revision183.8694935s/overall304.0824027s. '
        '17original/10fast/12descriptive/5posthoc tests là4nhóm khác nhau, không broad model efficacy suite. '
        'Hai passes exact3240legacy+27outcome mỗi pass;27state/9uniform pairs;newN0/0optimizer. '
        'Descriptive all27trajectories/all18comparisons; ranking là explicitPOSTHOC source-local CID explanation đã parentreview, '
        'không qid/difficulty, causal mediation, edge-only hoặc learning benefit. Served-itemP tínhsau select; '
        'Bscore đã log đủlocalranking nhưng calibratedmastery/S04/fullSglobal còn mở. Originala585MISSING. '
        'Partial gzip failure giữ nguyên, không repair. Source/code/CSV là simulator inputs; không realdata/Holdout, '
        'checkpoint/Parquet/privateRPC/base64 hoặc notebookexecution. Archive chỉ copy/hash, không model/tests/analysis.\n\n'
        'Canonical public report: [báo cáo](../../reports/rq1_closed_loop_reconstruction_20261108.md). Report snapshot giữ original canonical-relative links; đọc public report qua link này. copy_inventory.json map exact sources→aliases. '
        'Archive -01 FAILED116 do Git option bug giữ immutable; đây không native model failure. '
        'Candidate JSON pendinglabel giữ generated-state lịch sử; actual parent-ranking-review và closure_review ghi review đến sau.\n')
    with record_evidence_run(ROOT, RUN_ID, metadata={**dry['acceptance'],
            'closure_approval_reference': args.approval_reference,
            'approved_report_sha256': args.approved_report_sha256,
            'approved_dry_inventory_sha256': args.approved_inventory_sha256}, sources=sources, note=note) as directory:
        for source, alias in pairs:
            shutil.copyfile(source, directory / alias)
        after = []
        for row in before:
            copied = sha(directory / row['copy'])
            if copied != row['sha256_before_copy'] or copied != sha(ROOT / row['source']):
                raise ValueError('pre/post copy identity changed')
            after.append({**row, 'sha256_after_copy': copied, 'exact_match': True})
        def write(name, value):
            (directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        historical_after = {name: sha(OLD / name) for name in historical_before}
        if historical_after != historical_before:
            raise ValueError('historical source artifacts changed during copy')
        write('copy_inventory_before.json', before)
        write('copy_inventory.json', after)
        write('frozen_acceptance.json', dry['acceptance'])
        write('historical8_preservation.json', {'before': historical_before, 'after': historical_after, 'all8unchanged': True})
        write('closure_review.json', {'approval_reference': args.approval_reference,
            'approved_report_sha256': args.approved_report_sha256,
            'approved_dry_inventory_sha256': args.approved_inventory_sha256,
            'parent_raw_review_sha256': sha(PREP / 'parent-closed-loop-fast-review02.json'),
            'parent_ranking_review_sha256': sha(PREP / 'parent-ranking-review.json'),
            'posthoc_role': dry['acceptance']['posthoc_role'], 'methodology_adoption': False})
        expected_names = {alias for _, alias in pairs} | set(dry['expected_generated_outputs'])
        paths = sorted((directory / name).relative_to(ROOT).as_posix() for name in expected_names | {'manifest.json'})
        ignored = {}
        query_receipts = []
        for offset in range(0, len(paths), 32):
            part = paths[offset:offset+32]
            try:
                batch_ignored, query_receipt = query_ignored(part)
            except GitIgnoreQueryError as error:
                write('git_check_ignore_failure.json', error.receipt)
                raise
            ignored.update(batch_ignored)
            query_receipts.append(query_receipt)
        checks = [{'path': path, 'ignored': path in ignored, 'rule': ignored.get(path)} for path in paths]
        write('git_ignore_check.json', {'paths': checks, 'argv_queries': query_receipts, 'model_calls': 0})
        (directory / 'force_add_paths.txt').write_text(''.join(path+'\n' for path in paths if path in ignored), encoding='utf-8')
    verified = verify_evidence_bundle(directory)
    if {p.name for p in directory.iterdir()} != expected_names | {'manifest.json'}:
        raise ValueError('unexpected closed bundle files')
    print(json.dumps({**verified, 'copy_pairs': len(pairs), 'manifest_sha256': sha(directory / 'manifest.json'),
                      'force_add_paths': [path for path in paths if path in ignored]}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['dry', 'close'])
    parser.add_argument('--inventory-output', type=Path, required=True)
    parser.add_argument('--approved-report-sha256')
    parser.add_argument('--approved-inventory-sha256')
    parser.add_argument('--approval-reference')
    args = parser.parse_args()
    args.inventory_output = args.inventory_output.resolve()
    if args.inventory_output.parent != PREP or args.inventory_output.is_symlink():
        raise ValueError('exclusive direct prep inventory path')
    dry = inventory()
    if args.mode == 'dry':
        with args.inventory_output.open('x', encoding='utf-8') as stream:
            json.dump(dry, stream, ensure_ascii=False, indent=2);stream.write('\n')
        print(json.dumps({'status': 'DRY_ONLY_NO_BUNDLE_CREATED', 'report_sha256': sha(REPORT),
            'inventory_sha256': sha(args.inventory_output), 'copy_pairs_excluding_dry_self': len(dry['copy_pairs']),
            'selected_bytes': dry['selected_bytes'], 'source_count': len(dry['sources_sha256']),
            'expected_closed_output_count': len(dry['copy_pairs']) + 1 + len(dry['expected_generated_outputs'])}, ensure_ascii=False))
    else:
        close(args, dry)


if __name__ == '__main__':
    main()
