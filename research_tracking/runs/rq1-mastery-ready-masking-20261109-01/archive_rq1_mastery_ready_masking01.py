"""ROOT inventory/closure cho cached masking đã nghiệm thu, không phân tích lại."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
REL = PREP.relative_to(ROOT).as_posix() + '/'
RUN_ID = 'rq1-mastery-ready-masking-20261109-01'
REPORT = ROOT / 'research_tracking/reports/rq1_mastery_ready_masking_20261109.md'
DRY = PREP / 'rq1_mastery_ready_masking_archive_dry01.json'
PURE = PREP / 'rq1-mask-pure09-attempt01'
INNER = PREP / 'rq1-mastery-ready-masking-attempt01'
PURE_OUTER = PREP / 'rq1-mask-pure09-outer01'
CACHED_OUTER = PREP / 'rq1-mask-cached-outer01'
BEFORE = PREP / 'masking-independent-recount-before02'
PURE_SHA = 'd16a773976c4a77de6a56e3543716b89b5ec0ed2fb2778e3f610a7bb214c0472'
CACHED_SHA = 'f6581b082c784bb97ec53b3e3c8f09ed71718ac2331e51f962e0e61c4bafc59a'
OLD_VERIFIER_SHA = '997f402ea30a9b2f587fe7c19acc114c121e47fa1133ca1681aa0e5995e9ccd0'
PINS = {
    'scripts/research/analyze_rq1_mastery_ready_masking.py': '33e5fddf96e3559575538de71dcc424b9f72accb2ba6b3eb2cc66c1c55a8d6a9',
    'tests/shared_kt/test_rq1_mastery_ready_masking.py': '2d30113ac7433a88fef0c4daadc27fa9c5389ac775dc54686fd813aeaee6559a',
    REL + 'check_rq1_masking_pure09_01.py': '02422f008e68d8df0324e74a4887111bb25ec106ee48125a2e21c9002ea863b5',
    REL + 'run_rq1_masking01.py': 'a3eec6da5872cf2e3f35911e2bf21d95d01affad4682540287a84aaefe00071e',
    REL + 'rq1_masking_allocation01.json': '22ce49c25095b8130a93af110dc1d40c6a6c9f185653d44a023f5bdcf3c2460e',
    REL + 'RQ1_MASTERY_READY_MASKING_SPEC01.md': '24d229ed64f6709cecf8f625bd8e7f925bb9ba99edd0a4b6ccd73907b4d53031',
    REL + 'ROOT_RQ1_MASKING_REVIEW01.md': 'dfc1bcf3110e53d86e7d264324c5db8f9a4d76e87ec2373c41c91cae1d5af05e',
    REL + 'verify_masking_from_native_snapshots02.py': '883bf62cda23cafa1b4004f7024063b3212274acb911401dc699a615f2fa6c33',
    REL + 'masking_independent_native_recount02.json': 'e06912cddd278db9c1929517b2c03d9cf5f3c921d46386222f54491f090d23d9',
    REL + 'prepare_masking_recount02.py': '9dd16a4fa066eb157ad79f11ba2aed393e47d4571245759a1f581b3cb69bdd4c',
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json',
             'scope.json', 'timing_scope.json', 'closure_review.json', 'reviewed_dry.json', 'raw_log_paths.txt')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical workspace file')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no aliases')
    need(path.is_file() and path.stat().st_size <= 4 * 1024**2, 'small bounded regular source/input')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable input bytes')
    return hashlib.sha256(raw).hexdigest()


def read(path):
    sha(path)
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def owned(terminal, directory):
    receipt = terminal['receipt']
    need(receipt == read(directory / 'receipt.json') and receipt['accepted'] is True
         and receipt['returncode'] == receipt['worker_returncode_before_cleanup'] == 0
         and receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup'] == 0
         and receipt['popen_handle_closed'] is True and receipt['actual_worker_in_job_before_GO'] is True
         and receipt['errors'] == receipt['cleanup_errors'] == [], 'actual owned success and Job0')
    for name, pin in receipt['output_sha256'].items():
        need(name in ('stdout.log', 'stderr.log') and sha(directory / name) == pin, 'actual raw child log identity')


def gather(report_sha):
    need(re.fullmatch('[a-f0-9]{64}', report_sha) and sha(REPORT) == report_sha, 'ROOT reviewed exact report')
    for name, pin in PINS.items():
        need(sha(ROOT / name) == pin, 'frozen source/review/recount pin')
    need(sha(PURE_OUTER / 'final.json') == PURE_SHA and sha(CACHED_OUTER / 'final.json') == CACHED_SHA,
         'actual pure/cached outer pins before parse')
    pure, final = read(PURE_OUTER / 'final.json'), read(CACHED_OUTER / 'final.json')
    packet = read(PREP / 'rq1_masking_allocation01.json')
    for record, status, phase, whole in ((pure, 'ACCEPTED_MASKING_PURE_9_FIXTURES', 'pure', 20),
                                      (final, 'ACCEPTED_CACHED_MASTERY_READY_MASKING', 'cached', 12)):
        need(record['status'] == status and record['phase'] == phase and record['errors'] == []
             and record['caps'] == packet['caps'][phase] and record['elapsed_before_final_seconds'] < whole
             and record['source_before'] == record['source_after'] == packet['sources']
             and record['environment_restored'] is True and record['automatic_retry'] is False
             and record['native_model_calls'] == 0 and not any(record['cold_after'].values()), 'accepted source/cold/phase/resource scope')
    need(final['prerequisite_pure_final_sha256'] == PURE_SHA, 'cached actual pure9 prerequisite')
    owned(pure, PREP / 'rq1-mask-pure09-owned01')
    owned(final, PREP / 'rq1-mask-cached-owned01')
    need(not any((folder / name).exists() for folder in (PURE, PURE_OUTER, INNER, CACHED_OUTER)
                 for name in ('postwrite-rejection.json', 'failure.json', 'failure.log')), 'no partial/late rejection')
    for terminal, folder, names in ((pure, PURE, {'result.json', 'unittest.log'}),
                                  (final, INNER, {'summary.json', 'event_flags.json', 'validation.json', 'result.json'})):
        need({p.name for p in folder.iterdir()} == names and set(terminal['outputs']) == names, 'exact terminal outputs')
        for name, record in terminal['outputs'].items():
            need(sha(folder / name) == record['sha256'] and (folder / name).stat().st_size == record['bytes'], 'actual output SHA/size')
    test = read(PURE / 'result.json')
    need(test['counts'] == dict(tests=9, failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)
         and test['collected_ids'] == test['started_ids'] == test['completed_ids'] == packet['physical_test_ids']
         and len(set(test['completed_ids'])) == 9 and test['source_before'] == test['source_after']
         and not any(test['cold_before'].values()) and not any(test['cold_after'].values())
         and not any(test['audit_attempts'].values()), 'nine actual physical pure tests')
    need(sha(PURE / 'unittest.log') == test['log_sha256'], 'actual unittest raw log')
    summary, validation, result = (read(INNER / name) for name in ('summary.json', 'validation.json', 'result.json'))
    need(result['status'] == 'INNER_COMPLETE_PENDING_ROOT_OWNED_POSTWRITE_ACCEPTANCE'
         and result['outputs'] == {name: item for name, item in final['outputs'].items() if name != 'result.json'}
         and result['worker_cap_seconds'] == 7 and result['worker_seconds'] < 7, 'actual inner result / outer inventory')
    need(validation['source_input_before'] == validation['source_input_after'] == final['input_before'] == final['input_after']
         and len(final['input_after']) == 38 and validation['paired_keys'] == 1080
         and validation['arm_states'] == validation['exact_R_C_B_CID_keys'] == 2160
         and validation['closed_gzip_streams'] == 18 and validation['concept_pairs'] == 30240
         and validation['groups'] == 16 and validation['native_model_simulator_calls'] == validation['oracle_reads'] == 0,
         'all38 source/input and full admission')
    need(len(summary['groups']) == 16 and len(read(INNER / 'event_flags.json')) == 1080
         and summary['new_independent_N'] == 0
         and all(len(g['concept_IAF_cells']) == 8 and len(g['parent_exposure_A_I_F_cells']) == 16
                 and len(g['R_branch_pairs']) == 9 for g in summary['groups']), 'all groups and zero cells retained')
    pooled = summary['groups'][0]
    need(pooled['group'] == 'pooled' and pooled['M_changed_events'] == 90
         and pooled['R_changed_events'] == 60 and pooled['M_changed_R_same_events'] == 30
         and pooled['changed_mastery_parent_opportunities'] == 148
         and {c['signature']: c['count'] for c in pooled['concept_IAF_cells']} ==
             {'000': 30026, '001': 0, '010': 44, '011': 80, '100': 90, '101': 0, '110': 0, '111': 0}, 'reviewed descriptive partitions')
    independent = read(PREP / 'masking_independent_native_recount02.json')
    expected_proof_inputs = dict(final['input_after'])
    for name in ('check_rq1_masking_pure09_01.py', 'run_rq1_masking01.py'):
        expected_proof_inputs[REL + name] = PINS[REL + name]
    need(independent['status'] == 'INDEPENDENT_NATIVE_SNAPSHOT_PREDICATE_RECOUNT_PASS'
         and independent['inputs'] == 40 and independent['input_sha256'] == expected_proof_inputs
         and independent['gzip_crc_streams'] == 18 and independent['native_states'] == 2160
         and independent['paired_events'] == 1080 and independent['paired_concepts'] == 30240
         and independent['own_changed_concept_blocked_by_prerequisites'] == 90
         and independent['changed_parent_opportunities'] == 148
         and independent['source_before_after_equal'] is True and independent['scientific_modules_absent'] is True
         and independent['elapsed_seconds'] < independent['cap_seconds'] == 15,
         'independent raw-source recount admission')
    need(independent['event_reason_counts'] == dict(no_direct_child_and_own_prerequisites_blocked=18,
         child_mastered_without_exposure=8, child_mastered_and_exposure=4)
         and independent['nonexclusive_predicate_counts'] == dict(child_mastered_both=12, exposure_exception=4, both=4)
         and len(independent['event_reasons']) == 30 and all(r['profile'] == 'PG' for r in independent['event_reasons']),
         'overlap preserved, no exposure-only attribution')
    inventory01, failure01 = read(BEFORE / 'inventory-before.json'), read(BEFORE / 'failure-note.json')
    need(inventory01['sha256'] == failure01['source_sha256'] == sha(BEFORE / 'verify_masking_from_native_snapshots01.py')
         == sha(PREP / 'verify_masking_from_native_snapshots01.py') == OLD_VERIFIER_SHA
         and inventory01['bytes'] == (BEFORE / 'verify_masking_from_native_snapshots01.py').stat().st_size
         and failure01['kind'] == 'ROOT_INDEPENDENT_VERIFIER_EXPECTATION_FAILURE'
         and failure01['observed_from'] == 'Root tool output, no separate raw subprocess log was captured'
         and failure01['scientific_analyzer_changed'] is False and failure01['cached_analyzer_verdict'] == 'ACCEPTED',
         'preserved verifier01 expectation failure, no fabricated subprocess log')
    paths = {}

    def add(alias, path):
        sha(path)
        need(alias not in paths and Path(alias).name == alias and not any(c in alias for c in '\t\r\n')
             and path.suffix.lower() in ('.py', '.md', '.json', '.log'), 'unique flat small text copy only, no gzip')
        paths[alias] = path

    for name in PINS:
        add(Path(name).name, ROOT / name)
    add('report_snapshot.md', REPORT)
    add(Path(__file__).name, Path(__file__).resolve())
    need({p.name for p in BEFORE.iterdir()} == {'verify_masking_from_native_snapshots01.py', 'inventory-before.json', 'failure-note.json'},
         'exact preserved before02 context')
    for path in sorted(BEFORE.iterdir()):
        add('recount_before02__' + path.name, path)
    directories = (('pure', PURE), ('pure_outer', PURE_OUTER), ('pure_owned', PREP / 'rq1-mask-pure09-owned01'),
                   ('cached_outer', CACHED_OUTER), ('cached_owned', PREP / 'rq1-mask-cached-owned01'))
    for prefix, folder in directories:
        for path in sorted(folder.iterdir()):
            add(prefix + '__' + path.name, path)
    for path in sorted(INNER.iterdir()):
        add(path.name, path)
    refs = {}
    reference_pins = dict(expected_proof_inputs)
    reference_pins[REL + 'verify_masking_from_native_snapshots01.py'] = OLD_VERIFIER_SHA
    reference_pins['src/knowledge_tracing/evidence.py'] = '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
    aliases = {path.relative_to(ROOT).as_posix(): alias for alias, path in paths.items()}
    for name, pin in reference_pins.items():
        path = ROOT / name
        need(sha(path) == pin, 'original referenced input/current source unchanged')
        refs[name] = dict(sha256=pin, bytes=path.stat().st_size, copy_alias=aliases.get(name),
                          original_remains_in_place=True, old_scientific_gzip_copied=False)
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)
                 for alias, path in sorted(paths.items())]
    need(sum(row['bytes'] for row in inventory) < 4 * 1024**2, 'compact archive copies under4MiB')
    return inventory, refs, pure, final, independent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--prepare-dry', action='store_true')
    parser.add_argument('--check-dry', action='store_true')
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT / '.venv', 'repository .venv only')
    need(sum((args.prepare_dry, args.check_dry, args.close)) == 1, 'one metadata operation')
    destination = ROOT / 'research_tracking/runs' / RUN_ID
    need(not destination.exists(), 'exclusive new immutable bundle')
    inventory, refs, pure, final, independent = gather(args.report_sha256)
    dry = dict(run_id=RUN_ID, report_sha256=args.report_sha256, copies=inventory, reference_inputs=refs,
        generated_outputs=list(GENERATED), expected_output_count=len(inventory) + len(GENERATED),
        pure_outer_sha256=PURE_SHA, cached_outer_sha256=CACHED_SHA,
        independent_recount_sha256=PINS[REL + 'masking_independent_native_recount02.json'])
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=len(inventory), outputs=dry['expected_output_count'])))
        return
    need(read(DRY) == dry, 'exact reviewed dry/current source bytes')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', outputs=dry['expected_output_count'])))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact-dry closure reference')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# RQ1 — mastery và initial readiness\n\n'
        'Cached full/empty1080pairs/2160arms/30240concept snapshots, không replay/fit/oracle/newN. '
        'Giữ16groups, mọi zero cells,148changed-parent opportunities và source-reconstructed R/C/B admission. '
        '30M-different/R-same có18no-child,8child-mastered khôngexposure,4child-mastered VÀexposure. '
        'Hai flags chồng lấp, không4nguyênnhân exposure-only hoặc causal mediation. '
        'Pure9 và actualcached accepted/Job0 giữraw; independentraw02 cùng expectationfailure01 giữđúngprovenance. '
        'Không có raw subprocess log riêng của failure01. Gzip cũ chỉreferenceSHA. '
        'Manifest xác nhận closure gói, không thêm researchN hoặc masterytruth. '
        'Bản diễn giải tại [report_snapshot.md](report_snapshot.md).\n')
    sources = list(dict.fromkeys([ROOT / r['source'] for r in inventory] + [ROOT / name for name in refs] + [DRY]))
    with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='RQ1_CACHED_MASTERY_READY_PREDICATE_MASKING',
        paired_snapshots=1080, arm_states=2160, concept_pairs=30240, changed_parent_opportunities=148,
        new_independent_N=0, native_model_calls=0, oracle_reads=0, research_RQ_completion=False), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'source before copy')
            with (out / row['copy']).open('xb') as stream:
                stream.write(source.read_bytes())
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'source/copy/source-after SHA')
            copied.append(dict(**row, source_sha256_after_copy=sha(source), copied_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', refs)
        write(out / 'scope.json', dict(initial_R_not_universal_permission_or_served_action=True,
            F_not_R_on_fallback=True, concept_and_parent_units_distinct=True,
            paired_snapshots=1080, reused_histories=9, reused_seed_families=3, new_independent_N=0,
            condition_overlap=dict(child_mastered=12, exposure=4, both=4, exposure_alone=0),
            no_causal_mediation_or_truth_or_calibration_or_learning_benefit=True,
            old_gzip_copied=False, native_model_teacher_optimizer_calls=0, no_reexecution_at_closure=True,
            verifier01_failure_origin='ROOT tool output; no separate raw subprocess log captured'))
        write(out / 'timing_scope.json', dict(pure_outer_stored_seconds=pure['elapsed_before_final_seconds'],
            pure_cap_seconds=20, cached_outer_stored_seconds=final['elapsed_before_final_seconds'], cached_cap_seconds=12,
            root_postwrite_observations=dict(origin='ROOT terminal messages, distinct from stored receipt',
                pure_seconds=1.3707195, cached_seconds=5.0790765),
            independent_recount_seconds=independent['elapsed_seconds'], independent_cap_seconds=15,
            verifier01_elapsed_unknown=True, nested_times_not_summed=True))
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
            report_sha256=args.report_sha256, actual_pure_outer_sha256=PURE_SHA, actual_cached_outer_sha256=CACHED_SHA))
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(DRY.read_bytes())
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'reviewed dry copy pin')
        (out / 'raw_log_paths.txt').write_text('\n'.join(r['source'] for r in inventory if r['source'].endswith('.log')) + '\n', encoding='utf-8')
        need({p.name for p in out.iterdir() if p.name != 'manifest.json'} == set(GENERATED) | {r['copy'] for r in inventory}, 'exact small bundle outputs')
        need(all(sha(ROOT / r['source']) == r['sha256'] for r in inventory)
             and all(sha(ROOT / name) == r['sha256'] for name, r in refs.items()), 'source/reference identities after all copies')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == dry['expected_output_count'], 'verified exact manifest output count')
    print(json.dumps(dict(**verified, manifest_sha256=sha(destination / 'manifest.json'), path=destination.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
