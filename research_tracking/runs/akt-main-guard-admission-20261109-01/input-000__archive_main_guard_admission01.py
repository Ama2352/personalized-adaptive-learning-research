"""ROOT-only dry inventory/closure cho ba actual Main A0 guard operations."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'akt-main-guard-admission-20261109-01'
REPORT = ROOT/'research_tracking/reports/akt_main_guard_admission_20261109.md'
STAGES = (
    ('main-guard-package01', '15d1ae1fd0ae5d8aeb905eb07dbe44c1968eb44a2d8a1fd23aa356401769756c', 10),
    ('main-guard-package01-materialize', '6f219c5f26797b1e6b6cda5f06ad0c4a8c5bdd679c516eb4927571087c683b04', 10),
    ('main-selected-actual-guard01', '5a0a0b7e8d03f2f9fd3b5d123fea86f7071f3d4a5aa9069baeee6822ce18ff2d', 20),
)
CONFIG = ROOT/'experiments/akt/configs/main-a0-guard-only-20261109-01.json'
AUTH = ROOT/'experiments/akt/authorizations/main-a0-guard-only-20261109-01.json'
REQUEST = PREP/'main_selected_actual_guard01_request.ROOT.json'
DRY = PREP/'main_guard_package01_dry.json'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts, 'fixed project path')
    cursor = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            cursor /= part
        need(not cursor.is_symlink() and not cursor.is_junction(), 'physical evidence path')
    need(path.is_file(), 'regular evidence file')
    return path


def sha(path):
    with safe(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def gather(report_sha):
    payloads, references, summaries = {}, {}, []
    def read(path):
        safe(path)
        if path not in payloads:
            need(path.suffix in ('.py', '.json', '.md', '.log'), 'small textual evidence only')
            payload = path.read_bytes()
            need(len(payload) <= 1024**2, 'per-file1MiB')
            payloads[path] = payload
            need(sum(map(len, payloads.values())) <= 4*1024**2, 'compact4MiB total')
        return payloads[path]
    def load(path):
        return json.loads(read(path))
    def reference(path, expected, scope):
        need(sha(path) == expected, 'reference bytes unchanged')
        name = path.relative_to(ROOT).as_posix()
        if name in references:
            need(references[name]['sha256'] == expected, 'reference collision')
        references[name] = dict(sha256=expected, bytes=path.stat().st_size, scope=scope, copy=False)
    def flat(folder):
        need(folder.is_dir() and not folder.is_symlink() and not folder.is_junction(), 'physical terminal folder')
        for path in sorted(folder.iterdir()):
            if path.name == 'runtime-temp':
                continue
            need(path.is_file(), 'flat terminal evidence')
            read(path)
    need(digest(read(REPORT)) == report_sha, 'ROOT-reviewed report bytes')
    proposal = load(DRY)
    request = load(REQUEST)
    config, auth = load(CONFIG), load(AUTH)
    expected = {
        DRY: '7ff29a16c0e0a6573032f1eaec69f40956ca7f7bf9cc9497c00b68d423a2dcfd',
        CONFIG: 'ba0aee4990597c218a2d31c5d2e941cc26e335825acf79d01e754d4faed35646',
        AUTH: '212b78911bae2228e984eabe0ec292bd4d4b52ad748f834c6ed53b6177703f03',
        REQUEST: 'ef07d3430baa81d45d6eda2354c5ff03721ff97bd73093c5fe2115626797e50f',
    }
    need(all(digest(read(path)) == pin for path, pin in expected.items()), 'actual materialized artifact bindings')
    need(proposal['execution_authority'] is False and proposal['proposal'] == dict(config=config, authorization=auth, request=request),
         'dry proposal/materialization equality')
    need(config['max_steps'] == config['max_seconds'] == 1 and config['max_epochs'] == 20 and config['patience'] == 3
         and config['context'] == config['target_block'] == 100 and config['seed'] == 42, 'guard resource envelope/frozen recipe')
    need(not Path(config['output_dir']).exists(), 'no selected-fit directory')
    for name, pin in request['source_pins'].items():
        reference(ROOT/name, pin, 'actual_guard_source_docs_pre_post')
    for filename, pin in proposal['public_inputs_sha256'].items():
        reference(ROOT/'artifacts/simulator/corpora/grade10-development-lifecycle01-20261108'/filename,
                  pin, 'exact_public10_reference_only')
    admission = load(PREP/'main-selected-actual-guard01/actual-admission.json')
    need(admission['kind'] == 'ACTUAL_MAIN_A0_GUARD_ADMISSION_ONLY' and admission['identity'] == auth['identity']
         and admission['authorization_sha256'] == expected[AUTH] and admission['run_main_selected_candidate_called'] is False,
         'actual genuine admission identity')
    for role, learners, targets in (('train', 48, 10080), ('selection', 6, 1260), ('calibration', 6, 1260)):
        need(admission['roles'][role] == dict(learners=learners, targets=targets, reference_complete=True), 'full public role counts')
    need(admission['actual_model_calls'] == admission['actual_optimizer_calls'] == admission['actual_teacher_calls'] == 0,
         'admission scope zero bodies')
    for folder, final_pin, git_count in STAGES:
        out, owned = PREP/folder, PREP/(folder+'-owned')
        need(not any((out/name).exists() for name in ('postwrite-rejection.json', 'outer-postwrite-rejection.json',
                  'resource-failure.json', 'call-guard-failure.json')), 'no late rejection sidecars')
        final, child = load(out/'outer-final.json'), load(out/'result.json')
        receipt = load(owned/'receipt.json')
        need(digest(read(out/'outer-final.json')) == final_pin, 'actual accepted outer SHA')
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['errors'] == receipt['cleanup_errors'] == []
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True, 'actual owned Job0')
        for name, pin in receipt['output_sha256'].items():
            need(digest(read(owned/name)) == pin, 'owned raw stream bytes')
        need(child['error'] is None and child['monitor_errors'] == [] and child['monitor_stopped'] is True
             and len(child['git_calls']) == git_count and child['model_calls'] == child['optimizer_calls'] == child['teacher_calls'] == 0
             and child['actual_selected_fit'] is False and 0 < child['elapsed_seconds'] < 50, 'actual metadata/guard body scope')
        resources = child['resources']
        need(resources['samples'] > 0 and resources['peak_rss_bytes'] <= 1024**3
             and resources['min_available_ram_bytes'] >= 2*1024**3, 'actual sampled resources')
        if git_count == 10:
            need(final['status'] == 'ACCEPTED_METADATA_PACKAGE_ONLY' and final['error'] is None
                 and final['worker_result'] == child and final['owned_receipt'] == receipt and final['environment_restored'] is True
                 and final['actual_guard_verified'] is False and final['actual_fit_verified'] is False and child['denied'] == [], 'accepted package only')
            elapsed = final['elapsed_seconds']
            outputs = child['output_sha256']
        else:
            need(final['status'] == 'ACCEPTED_ACTUAL_MAIN_GUARD_ONLY' and final['errors'] == []
                 and final['actual_guard_admitted'] is True and final['main_selected_fit_verified'] is False
                 and final['source_before'] == final['source_after'] == request['source_pins']
                 and final['owned_receipt_sha256'] == digest(read(owned/'receipt.json'))
                 and child['source_before'] == child['source_after'] == request['source_pins']
                 and child['public_before'] == child['public_after'] == proposal['public_inputs_sha256']
                 and child['inputs_before'] == child['inputs_after'] and child['forbidden'] == []
                 and child['selected_environment_restored'] is True and child['git_environment_unchanged'] is True
                 and child['actual_guard_created'] is True, 'accepted actual admission only')
            elapsed = final['elapsed_before_receipt_seconds']
            outputs = {str((out/name).relative_to(ROOT).as_posix()): pin for name, pin in final['output_sha256'].items()}
        need(0 < elapsed < 60, 'actual operation whole60')
        for name, pin in outputs.items():
            need(digest(read(ROOT/name)) == pin, 'prepared/guard output posthash')
        flat(out); flat(owned)
        summaries.append(dict(operation=folder, status=final['status'], outer_seconds=elapsed,
                              worker_seconds=child['elapsed_seconds'], git_commands=git_count, resources=resources))
    for mode in ('prepare', 'materialize', 'guard'):
        folder = PREP/('main-guard-profile-'+mode+'01')
        record, reservation = load(folder/'result.json'), load(folder/'reservation.json')
        need(record['returncode'] == 0 and record['parent_environment_unchanged'] is True
             and record['excluded_inherited_display_variable_names'] == ['GH_PAGER', 'GIT_PAGER']
             and reservation['excluded_inherited_display_variable_names'] == ['GH_PAGER', 'GIT_PAGER']
             and reservation['mode'] == mode, 'actual reviewed child profile and parent unchanged')
        profile = reservation['child_git_environment']
        need(profile['GIT_CONFIG_COUNT'] == '3' and profile['GIT_CONFIG_NOSYSTEM'] == '1'
             and profile['GIT_CONFIG_GLOBAL'] == 'nul' and profile['GIT_CONFIG_KEY_0'] == 'core.fsmonitor'
             and profile['GIT_CONFIG_VALUE_0'] == 'false' and profile['GIT_CONFIG_KEY_1'] == 'safe.directory'
             and profile['GIT_CONFIG_VALUE_1'] == (ROOT/'artifacts/akt/dependencies/upstream').as_posix()
             and profile['GIT_CONFIG_KEY_2'] == 'core.autocrlf' and profile['GIT_CONFIG_VALUE_2'] == 'true'
             and profile['GIT_OPTIONAL_LOCKS'] == '0' and profile['GIT_TERMINAL_PROMPT'] == '0'
             and profile['GIT_ALLOW_PROTOCOL'] == '__NO_TRANSPORT__' and len(profile) == 12, 'actual Win03 child profile')
        for name in ('stdout', 'stderr'):
            need(digest(read(folder/(name+'.log'))) == record[name+'_sha256'], 'profile raw stream bytes')
        flat(folder)
    for name in ('prepare_main_selected_guard_package01.py', 'run_prepare_main_selected_guard_package01.py',
                 'check_main_selected_guard01.py', 'run_main_selected_guard01.py', 'launch_main_guard_profile01.py',
                 'MAIN_GUARD_PACKAGE_SOURCE_CONTRACT01.md', 'MAIN_GUARD_PACKAGE_STATIC_REVIEW01.md',
                 'ROOT_MAIN_A0_GUARD_PACKAGE_REVIEW01.md', 'ROOT_MAIN_A0_GUARD_EXACT_DRY_REVIEW01.md',
                 'check_main_guard_parents_post01.py', 'main_guard_parent_postcheck01.json'):
        read(PREP/name)
    post = load(PREP/'main_guard_parent_postcheck01.json')
    need(digest(read(PREP/'main_guard_parent_postcheck01.json')) == 'b7347f991815e576a5753d56ac058d98c671f6e3d7a71a404fbd94d65bc7dbdd'
         and post['kind'] == 'POST_MATERIALIZATION_AND_GUARD_PHYSICAL_PARENT_RECHECK'
         and post['recipe_sha256'] == digest(read(PREP/'check_main_guard_parents_post01.py'))
         and all(row['directory'] is True and row['symlink'] is False and row['junction'] is False
                 for parent in post['parents'] for row in parent['ancestors']), 'actual postcheck not backdated precheck')
    native = auth['identity']['native_evidence']
    for field, pin in (('runtime_report', proposal['runtime_sha256']), ('gate_pointer', proposal['index_sha256'])):
        reference(ROOT/request['runtime_evidence'][field], pin, 'actual_runtime_or_index_reference_only')
    for key in ('evidence_path', 'test_log_path'):
        field = 'report_sha256' if key == 'evidence_path' else 'test_log_sha256'
        reference(Path(native['gate'][key]), native['gate'][field], 'actual_Gate05_reference_only')
    reference(ROOT/request['runtime_evidence']['lock_file'], request['runtime_evidence']['lock_sha256'], 'actual_lock')
    reference(ROOT/'artifacts/akt/preflight/gate2-current.json',
              '9e768aadcf084482a2eeb9be814fc399100dd1a507eaa89afbbae87100365cd6', 'global_pointer_preserved')
    for name, pin in (
        ('akt-windows-gate-accepted177-20261109-01', '003784431a4080b7a18d5220da279e008b35226b6750e81fca7de9dbdb36b20d'),
        ('akt-windows-runtime-gate-index-20261109-01', 'aff19b45036b3a0cb1651d563e7f9aed8725eeea7e1f3207af67ef69c0f8cff8'),
    ):
        reference(ROOT/'research_tracking/runs'/name/'manifest.json', pin, 'prior_closed_prerequisite_manifest_only')
    read(Path(__file__).resolve())
    return payloads, references, dict(kind='ACTUAL_MAIN_A0_GUARD_ADMISSION_ONLY', operations=summaries,
        roles=admission['roles'], source_pins=len(request['source_pins']), native_sources=len(native['build_hashes']),
        actual_guard_admitted=True, actual_selected_fit=False, model_calls=0, optimizer_calls=0, teacher_calls=0,
        limits_vi='Admission envelope1step/1target/1trainingsecond, chưa selected fit/refit/calibration/CUDA.')


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-dry', action='store_true'); mode.add_argument('--close', action='store_true')
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--inventory-sha256'); parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv')
    need(args.inventory.is_absolute() and args.inventory.parent == PREP and '..' not in args.inventory.parts
         and not args.inventory.is_symlink() and not args.inventory.is_junction(), 'inventory within existing prep')
    payloads, references, summary = gather(args.report_sha256)
    inputs = [dict(source=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256_before_copy=digest(raw))
              for path, raw in sorted(payloads.items())]
    inventory = dict(run_id=RUN_ID, inputs=inputs, references=references, summary=summary,
                     input_occurrences=len(inputs), unique_copies=len({row['sha256_before_copy'] for row in inputs}),
                     total_copy_bytes=sum(map(len, payloads.values())))
    if args.prepare_dry:
        write(args.inventory, inventory)
        print(json.dumps(dict(status='DRY_INVENTORY_READY', sha256=sha(args.inventory),
                              inputs=len(inputs), unique_copies=inventory['unique_copies']))); return
    need(args.review_reference and args.inventory_sha256 and sha(args.inventory) == args.inventory_sha256
         and json.loads(args.inventory.read_bytes()) == inventory, 'exact ROOT-reviewed inventory')
    destination = ROOT/'research_tracking/runs'/RUN_ID
    need(not destination.exists(), 'exclusive immutable bundle')
    for row in inputs:
        need(sha(ROOT/row['source']) == row['sha256_before_copy'], 'input SHA before copy')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = '''# Actual Main A0 guard admission ngày09/11/2026

Ba actual operations đã ACCEPTED, Git10/10/20 và owned Job0.
Giữ raw logs/receipts/profile setup, exact dry/config/auth/request và reviews.
Config vẫn20epochs/patience3 nhưng envelope chỉ1step/1target/1trainingsecond.
Actual guard có0model/optimizer/teacher, chưa selected fit hoặc refit/calibration.
Child Win03 setup chỉ loại hai PAGER đã review, parent environment giữ nguyên.
Physical-parent receipt là POST sau materialize/guard, không backdate thành precheck.
Precheck g2:3402 do ROOT báo từ transcript, tool006417 là kiểm bytes sau metadata.
Writer chưa có generic parent-alias protection. Không suy thành mọi-path/race proof.
copy_inventory.json giữ SHA trước/sau, references.json giữ public10/Gate/source refs.
Không copy corpus, dependencies hoặc Gate JUnit. Không chạy fit/CUDA/cloud tại closure.
'''
    with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind=summary['kind'], closure_review=args.review_reference),
                             sources=sorted(set(payloads) | {ROOT/name for name in references}), note=note) as out:
        copies = {}
        for row in inputs:
            source = ROOT/row['source']; raw = payloads[source]; pin = row['sha256_before_copy']
            if pin not in copies:
                target = out/f'input-{len(copies):03d}__{source.name}'
                with target.open('xb') as stream:
                    stream.write(raw)
                copies[pin] = target
            target = copies[pin]
            need(target.read_bytes() == raw and sha(source) == pin, 'copy readback/source unchanged')
            row.update(copy=target.name, sha256_after_copy=sha(target), source_sha256_after_copy=pin)
        write(out/'copy_inventory.json', inputs); write(out/'references.json', references)
        write(out/'validated_summary.json', summary)
        write(out/'closure_review.json', dict(reference=args.review_reference, inventory_sha256=args.inventory_sha256))
    verification = verify_evidence_bundle(destination)
    for row in inputs:
        need(sha(ROOT/row['source']) == row['sha256_before_copy'], 'final source byte integrity')
    force = PREP/'main_guard_admission_force_paths01.txt'
    with force.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(path.relative_to(ROOT).as_posix() for path in sorted(destination.iterdir()))+'\n')
    print(json.dumps(dict(status='CLOSED_BY_ROOT_METADATA_EXECUTION', verification=verification,
                          manifest_sha256=sha(destination/'manifest.json'),
                          files_including_manifest=len(list(destination.iterdir())), force_paths=str(force))))


if __name__ == '__main__':
    main()
