"""ROOT dry/close receipts đã có; không chạy lại tests/model/provenance probes."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'cgakt-research-core-engineering-20261109-01'
REPORT = ROOT/'research_tracking/reports/cgakt_research_core_20261109.md'
PINNED_CONTROLLERS = {
    'check_cgakt_research_model01.py': '33ed5e862f9e409859b8f45d3f6d160826fcb228e951f79f706ade61d29bdd00',
    'run_cgakt_research_model01.py': '1e83fe60233a242acd7e272365ae32f6517909873617b10fac660a3521cc6056',
    'cgakt_research_model01_allocation.json': 'b63e7c4c86d81eff973cfbe7f0fe2b0b4a120738e936e9a6f08747d4b7ca155d',
    'check_cgakt_research_model02.py': '0e3f1065fbcb9bead795e436814e11f163c46e6bcb9729c7c77617383c16b71e',
    'run_cgakt_research_model02.py': '156bafecd9e0aa84ffed34fa60f51f50d7a7a3a44625b819a5c6b5cdc8099ef0',
    'cgakt_research_model02_allocation.json': '423144d833b7f77f1cebacd5ed8e5f1a9e13e4e0477630b33509f03f6d3391f6',
    'check_cgakt_research_model03.py': '713c48dccf07ce52bbe41998db91deb3dbd9fa6d890a5688f62a42f5ee72f70d',
    'run_cgakt_research_model03.py': '79165d8307acd05cbf7da99493a4d3df357b0d9b40bd63ddbd385b318e443549',
    'cgakt_research_model03_allocation.json': '66f394724ba0be4afeb7770d398a0c469380c8bdb57733a90e3a425dc7d0771d',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path, *, existing=True):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.is_relative_to(ROOT), 'fixed project path required')
    cursor = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'archive alias rejected')
    need(path.resolve().is_relative_to(ROOT.resolve()), 'physical project path required')
    if existing:
        need(path.is_file(), 'regular evidence input required')
    return path


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def gather():
    payloads, checked = {}, {}

    def read(path):
        path = safe(path)
        if path not in payloads:
            need(path.stat().st_size <= 2*1024**2, 'input2MiB cap')
            raw = path.read_bytes()
            need(len(raw) <= 2*1024**2, 'input readback cap')
            payloads[path] = raw
            need(sum(map(len, payloads.values())) <= 10*1024**2, 'total10MiB cap')
        return payloads[path]

    def load(path):
        return json.loads(read(path))

    for name, digest in PINNED_CONTROLLERS.items():
        need(sha(read(PREP/name)) == digest, 'dispatched controller/packet changed:'+name)
    packets = [load(PREP/f'cgakt_research_model0{i}_allocation.json') for i in (1, 2, 3)]
    accepted_pins = packets[2]['source_pins']
    need(len(accepted_pins) == 28, 'exact28source bindings')
    for name, digest in accepted_pins.items():
        path = safe(ROOT/name)
        need(path.stat().st_size <= 262144 and sha(path.read_bytes()) == digest, 'accepted source changed:'+name)
        checked[name] = digest  # Hash all28; do not copy all dependency sources.
    for packet in packets:
        need(set(packet['source_pins']) == set(accepted_pins), 'same source membership')
        need(all(digest == accepted_pins[name] for name, digest in packet['source_pins'].items()
                 if name != 'tests/akt/test_research_graph_model.py'), 'only known fixture overlay permitted')
        need(all(not (ROOT/name).exists() for name in packet['absent_source_paths']), 'namespace absence changed')
    need(accepted_pins['src/knowledge_tracing/akt/research_graph_model.py'] == '7ed0878f844d67598a6b684be92e770ea98d9b57ebbdb6a67c89cfef65020150'
         and accepted_pins['tests/akt/test_research_graph_model.py'] == 'dd1e0bae0374c90159837d97d0f09d3936faae3227bf214ede9b2ffe598e9a9e', 'frozen model/test')
    stages, names_before = [], None
    for i, packet in zip((1, 2, 3), packets):
        label = f'cgakt-research-model0{i}'
        child = load(PREP/label/'result.json'); final = load(PREP/(label+'-owned')/'final.json')
        owned = load(PREP/(label+'-owned')/'receipt.json')
        need(sha(read(PREP/(label+'-owned')/'receipt.json')) == final['owned_receipt_sha256'], 'outer binds owned receipt')
        for name, row in final['output_inventory'].items():
            need(name in ('case_events.jsonl','junit.xml','pytest.log','reservation.json','result.json')
                 and sha(read(PREP/label/name)) == row['sha256']
                 and len(read(PREP/label/name)) == row['bytes'], 'outer binds exact child outputs')
        for name, digest in owned['output_sha256'].items():
            need(name in ('stdout.log','stderr.log') and sha(read(PREP/(label+'-owned')/name)) == digest,
                 'owned stdout/stderr bytes')
        tree = ET.fromstring(read(PREP/label/'junit.xml'))
        counts = {k: sum(int(s.get(k, '0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
        names = [case.get('name') for case in tree.iter('testcase')]
        expected_counts = dict(tests=18, failures=0, errors=0 if i == 3 else 18, skipped=0)
        need(counts == child['counts'] == final['counts'] == expected_counts, 'actual trial JUnit counts')
        need(len(names) == len(set(names)) == 18 and set(names) == set(packet['expected_test_names']), 'actual18case population')
        need(names_before is None or set(names_before) == set(names), 'same18cases across trials')
        names_before = names
        need(owned['cleanup_accepted'] is True and owned['job_active_after_cleanup'] == 0
             and owned['popen_handle_closed'] is True and owned['actual_worker_in_job_before_GO'] is True, 'actual owned cleanup')
        need(child['source_before'] == child['source_after'] == packet['source_pins']
             and child['methods_restored'] and child['environment_restored'] and child['runtime_restored'], 'trial source/restoration')
        if i != 3:
            need(final['status'] == 'REJECTED_CGAKT_RESEARCH_CORE_CHECK' and child['pytest_exit_code'] != 0, 'retain failed trial')
            need(all(value == 0 for value in child['native_body_returned'].values()), 'no returned native work in failures')
            expected_started = {key: (1 if i == 2 and key == 'wrapper_constructors' else 0) for key in packet['expected_native_counts']}
            need(child['native_started'] == expected_started, 'failed01/02 actual starts')
            log = read(PREP/label/'pytest.log').decode('utf-8')
            need(('exactly three reference difficulties' if i == 1 else 'source content mismatch: akt.py') in log,
                 'actual setup diagnosis evidence')
        else:
            need(final['status'] == 'ACCEPTED_CGAKT_RESEARCH_CORE_ENGINEERING_ONLY' and owned['accepted'] is True
                 and owned['returncode'] == 0 and child['pytest_exit_code'] == 0, 'actual03 accepted')
            need(child['native_started'] == child['native_body_returned'] == packet['expected_native_counts'], 'exact native8/5/0')
            need(child['upstream_cuda_availability'] == [dict(phase='local_git_provenance', result=False)]
                 and child['torch_profile']['cuda_initialized_after'] is False, 'actual CPU availability/init')
            git = child['local_git_provenance']
            need(len(git['commands']) == 10 and git['original_loader_used'] and git['original_loader_calls'] == 1
                 and git['cached_module_used'] is False and git['process_environment_actual'] == packet['local_git_provenance']['process_config'],
                 'normal Git/loader, exact process settings')
            need(child['resources']['observed_peak_rss_bytes'] <= 1024**3
                 and child['resources']['observed_minimum_available_ram_bytes'] >= 2*1024**3
                 and child['elapsed_seconds'] < 80 and final['elapsed_seconds'] < 90, 'actual accepted resource caps')
        stages.append(dict(trial=i, status=final['status'], counts=counts,
            stored_outer_seconds=final['elapsed_seconds'], child_seconds=child['elapsed_seconds'],
            native_started=child['native_started'], native_body_returned=child['native_body_returned'],
            resources=child['resources'], result_sha256=sha(read(PREP/label/'result.json')),
            outer_sha256=sha(read(PREP/(label+'-owned')/'final.json'))))
        for name in ('case_events.jsonl','junit.xml','pytest.log','reservation.json','result.json'):
            read(PREP/label/name)
        for name in ('final.json','GO.json','launch.json','ready.json','receipt.json','stderr.log','stdout.log'):
            read(PREP/(label+'-owned')/name)
    snapshot_groups = {
        'pre-model-source-row-fix01': ('inventory.json','test_research_graph_model.before.py'),
        'pre-model-cpu-seed-fix01': ('inventory.json','test_research_graph_model.before.py'),
        'pre-cgakt-windows-git-audit-fix01': ('inventory.json','check_cgakt_research_model01.py','run_cgakt_research_model01.py','cgakt_research_model01_allocation.json'),
        'pre-cgakt-process-git-trust-fix01': ('inventory.json','check_cgakt_research_model01.py','run_cgakt_research_model01.py'),
        'pre-cgakt-bank84-fix01': ('inventory.json','research_graph_model.before.py','test_research_graph_model.before.py','check_cgakt_research_model01.py','run_cgakt_research_model01.py','cgakt_research_model01_allocation.json'),
        'pre-cgakt-process-eol-fix01': ('inventory.json','check_cgakt_research_model02.py','run_cgakt_research_model02.py','cgakt_research_model02_allocation.json'),
    }
    for folder, names in snapshot_groups.items():
        inventory = load(PREP/folder/'inventory.json')
        if 'copies' in inventory:
            for row in inventory['copies']:
                snapshot = row.get('snapshot', row.get('name', row.get('path')))
                need(sha(read(PREP/folder/snapshot)) == row['sha256_before_copy'] == row['sha256_after_copy'], 'historical snapshot integrity')
        else:
            need(sha(read(PREP/folder/inventory['snapshot'])) == inventory['sha256_before_copy'] == inventory['sha256_after_copy'], 'historical test snapshot')
        for name in names:
            read(PREP/folder/name)
    for name in ('windows_git_audit_shape01.json','upstream_git_env_preflight01.json',
                 'upstream_git_eol_preflight01.json','upstream_verify_process_eol03.json',
                 'CGAKT_RESEARCH_CONTEXT_MODEL_BATCH01.md','CGAKT_CONTEXT_INTEGRITY_HOTPATH01.md',
                 'CGAKT_MODEL_FIXTURE02_STATIC_AUDIT.md'):
        read(PREP/name)
    references = []
    for label, count in (('cgakt-research-condition-engineering-20261109-01',13), ('cgakt-research-context-engineering-20261109-01',52)):
        path = ROOT/'research_tracking/runs'/label/'manifest.json'; manifest = load(path)
        need(manifest['status'] == 'completed' and len(manifest['outputs_sha256']) == count, 'prior completed manifest reference')
        references.append(dict(run_id=label, manifest_sha256=sha(read(path)), outputs=count, copied_whole_bundle=False))
    for name in ('src/knowledge_tracing/akt/research_graph_model.py','tests/akt/test_research_graph_model.py',
                 'artifacts/akt/dependencies/upstream/akt.py','artifacts/akt/dependencies/upstream/README.md',
                 'artifacts/akt/dependencies/upstream/LICENSE'):
        read(ROOT/name)
    read(REPORT); read(Path(__file__))
    by_hash, rows = {}, []
    for path, raw in sorted(payloads.items()):
        digest = sha(raw)
        if digest not in by_hash:
            by_hash[digest] = f'input-{len(by_hash)+1:03d}-'+path.name
        rows.append(dict(source=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256_before_copy=digest,
                         archived_as=by_hash[digest]))
    inventory = dict(schema_version=1, run_id=RUN_ID, input_aliases=rows, unique_input_copies=len(by_hash),
        checked_not_all_copied_source_pins=checked, trials=stages, prior_bundle_references=references,
        limits_vi='Không rerun/model/GPU/Gitmutation. Hash toàn28source, chỉ snapshot selectedsources; cùngbytes chỉ copy1lần nhưng giữmọialias.')
    return inventory, payloads


def recheck(inventory):
    for row in inventory['input_aliases']:
        need(sha(safe(ROOT/row['source']).read_bytes()) == row['sha256_before_copy'], 'source drift before/after copy')
    for name, digest in inventory['checked_not_all_copied_source_pins'].items():
        need(sha(safe(ROOT/name).read_bytes()) == digest, 'accepted dependency drift')


def main():
    need(os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(str(ROOT/'.venv/Scripts/python.exe'))
         and Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv entry and prefix only')
    parser = argparse.ArgumentParser(description='ROOT archive metadata-only, không rerun test/model')
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-inventory-sha256')
    args = parser.parse_args()
    path = safe(args.inventory.absolute(), existing=args.close)
    need(path.parent == PREP and path.suffix == '.json', 'inventory must be exclusive prep JSON')
    need(not (ROOT/'research_tracking/runs'/RUN_ID).exists(), 'immutable run already exists')
    inventory, payloads = gather(); raw_inventory = canonical(inventory); recheck(inventory)
    if not args.close:
        need(args.expected_inventory_sha256 is None and not path.exists(), 'exclusive dry inventory only')
        with path.open('xb') as handle:
            handle.write(raw_inventory); handle.flush(); os.fsync(handle.fileno())
        print(json.dumps(dict(status='DRY_INVENTORY_ONLY_NOT_CLOSED', inventory_sha256=sha(raw_inventory),
            aliases=len(inventory['input_aliases']), unique_copies=inventory['unique_input_copies'], trials=inventory['trials'])))
        return
    need(args.expected_inventory_sha256 == sha(path.read_bytes()) == sha(raw_inventory), 'external reviewed exact dry inventory required')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = '''# Core CG-AKT recipe26 — engineering09/11/2026

Actual01/02:18setup errors/0bodies; actual03:18PASS/0FES,1backbone+1wrapper+1gate,
8Architecture.forward/5logicalbackward/0Adamctor/0optimizerstep. A3 và off trên cùng
backbone; không train A0 độc lập/A1/A2, actualcorpus, checkpoint/lifecycle/CUDA.
Core/report/current28source bindings cố định; toàn rawlogs/JUnit/failures giữbytes.
4Gitproof là preflight, không ModelPASS. Original10Gitcommands/load thật; process
config khôi phục actualsystemautocrlf, exactsafe.directory, không global/source edit.
Copies deduplicate bằng SHA; inventory-before giữ mọi alias+source, copy-verification
giữ before/after. Hai manifest13/52 chỉ là references, không duplicate toàn bundles.
Observed277712896B peak/minfree5426839552B và90s chỉ kiểm2x6fixture.7fullcache
JSONhash/trainbatch còn pendingfix; không maintraining/throughput/fit approval.
Archive chỉ copy/hash receipts đã có, không thực thi artifact hoặc model.
'''
    git_before = {key: value for key, value in os.environ.items() if key.startswith('GIT_')}
    try:
        for key in list(git_before):
            os.environ.pop(key, None)
        os.environ.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory', GIT_CONFIG_VALUE_0=ROOT.as_posix())
        sources = sorted(set(payloads) | {ROOT/name for name in inventory['checked_not_all_copied_source_pins']} | {path})
        with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='CGAKT_TINY_A3_CORE_NOT_FITTED_OR_MAIN_READY',
                trials=inventory['trials'], source_bindings=inventory['checked_not_all_copied_source_pins'],
                aliases=len(inventory['input_aliases']), unique_input_copies=inventory['unique_input_copies'],
                prior_bundle_references=inventory['prior_bundle_references']), sources=sources, note=note) as directory:
            with (directory/'inventory-before.json').open('xb') as handle:
                handle.write(raw_inventory)
            copied = {}
            for row in inventory['input_aliases']:
                target = directory/row['archived_as']
                if row['archived_as'] not in copied:
                    with target.open('xb') as handle:
                        handle.write(payloads[ROOT/row['source']]); handle.flush(); os.fsync(handle.fileno())
                    digest = sha(target.read_bytes())
                    need(digest == row['sha256_before_copy'], 'archive copy integrity')
                    copied[row['archived_as']] = digest
            recheck(inventory)
            verification = dict(status='VERIFIED_BYTE_COPIES_NOT_MODEL_RERUN', before_inventory_sha256=sha(raw_inventory),
                copied_sha256=copied, sources_after={r['source']: sha(safe(ROOT/r['source']).read_bytes()) for r in inventory['input_aliases']})
            with (directory/'copy-verification.json').open('xb') as handle:
                handle.write(canonical(verification))
            names = [*copied, 'README.md','execution.log','inventory-before.json','copy-verification.json','force-add-files.txt','manifest.json']
            force = [str((directory/name).relative_to(ROOT)).replace('\\','/') for name in names]
            force += ['src/knowledge_tracing/akt/research_graph_model.py','tests/akt/test_research_graph_model.py',REPORT.relative_to(ROOT).as_posix()]
            with (directory/'force-add-files.txt').open('x', encoding='utf-8', newline='\n') as handle:
                handle.write('\n'.join(force)+'\n')
    finally:
        for key in list(os.environ):
            if key.startswith('GIT_'):
                os.environ.pop(key, None)
        os.environ.update(git_before)
    verified = verify_evidence_bundle(directory); recheck(inventory)
    print(json.dumps(dict(verified=verified, manifest_sha256=sha((directory/'manifest.json').read_bytes()),
        force_add_list=(directory/'force-add-files.txt').relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
