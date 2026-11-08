"""ROOT dry/close GRAPH16 data-only35; không rerun test/model hoặc mở corpus."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
RUN_ID = 'cgakt-online-query-context-engineering-20261109-01'
CANDIDATE = P/'cgakt_online_query_context_20261109.candidate.md'
CANONICAL = R/'research_tracking/reports/cgakt_online_query_context_20261109.md'
REPORT_SHA = 'a82abcd9d724f356993580ffdbaf8a39e66f5c9e2b06645a5eb9a24c210d7c45'
PINS = {
    'src/knowledge_tracing/akt/research_graph_online.py': 'c44ad90a699e76ce3bcf2e0cc7264a7f9d87f6639ee59f8033d51a87ef1b2c88',
    'tests/akt/test_research_graph_online.py': 'd9dc5e62458c1d357722d1502cc5f14775501daa49e4de9a887de4867844a8f9',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/check_graph_online_pure01.py': '7cf9c3202aa2feacda9725b5556aa2861b43cfc86b2192335ec418c581a6d991',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/run_graph_online_pure01.py': 'efb65be0ade55460fa405ae5a4e269e66b7d6e8be302e4e50dcea6dea23c0897',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/graph_online_pure01_allocation.json': '4af4f3c91f79862a4fcc9163baf05dfc21df4e48da6c27bb3e7a56ea648e0ce7',
}


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def safe(path, existing=True):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.is_relative_to(R), 'project-bound path')
    cursor = R
    for part in (None, *path.relative_to(R).parts):
        if part is not None: cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(), 'alias rejected')
    need(path.resolve().is_relative_to(R.resolve()), 'physical project path')
    if existing: need(path.is_file(), 'regular input file')
    return path


def gather(report):
    payloads = {}
    def read(path):
        path = safe(path)
        if path not in payloads:
            need(path.stat().st_size <= 1024**2, 'small input cap')
            raw = path.read_bytes(); need(len(raw) <= 1024**2, 'small readback cap')
            payloads[path] = raw
            need(sum(map(len,payloads.values())) <= 2*1024**2, 'compact total cap')
        return payloads[path]
    load = lambda path: json.loads(read(path))
    for name,digest in PINS.items(): need(sha(read(R/name)) == digest, 'source/controller pin:'+name)
    need(report in (CANDIDATE,CANONICAL) and sha(read(report)) == REPORT_SHA, 'reviewed report bytes')
    packet = load(P/'graph_online_pure01_allocation.json')
    child_dir = P/'graph-online-pure01'; owned_dir = P/'graph-online-pure01-owned'
    final = load(owned_dir/'final.json'); child = load(child_dir/'result.json'); owned = load(owned_dir/'receipt.json')
    need(sha(read(owned_dir/'final.json')) == '393d8b341afbdfe55585bca106d8eb95f898735af6955f93c49523d539efdcce'
         and sha(read(child_dir/'result.json')) == '89b17d1a27eb1c633bde28baa86672f081be1f0e84b2ef37eb1837b196efea3a', 'actual receipt identities')
    tree = ET.fromstring(read(child_dir/'junit.xml'))
    counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    cases = list(tree.iter('testcase'))
    need(counts == child['counts'] == final['counts'] == dict(tests=35,failures=0,errors=0,skipped=0)
         and len(cases) == 35 and len({c.get('name') for c in cases}) == 35
         and all(c.get('classname') == 'tests.akt.test_research_graph_online' for c in cases), 'actual35exactclass0FES')
    need(final['status'] == 'ACCEPTED_GRAPH16_35_NUMPY_QUERY_CASES_ONLY' and final['errors'] == []
         and child['status'] == 'ACCEPTED_35_NUMPY_QUERY_CASES_PENDING_OUTER' and child['pytest_exit_code'] == 0,
         'actual NumPy-only verdict')
    sources, runtimes = packet['source_pins'], packet['runtime_pins']
    need(len(sources) == packet['source_count'] == 25 and len(runtimes) == 9
         and sources == child['source_before'] == child['source_after'] == final['source_before'] == final['source_after']
         and runtimes == child['runtime_before'] == child['runtime_after'] == final['runtime_before'] == final['runtime_after'], 'source25/runtime9prepost')
    need(child['allocation_sha256'] == final['allocation_sha256'] == sha(read(P/'graph_online_pure01_allocation.json')),
         'actual packet binding')
    need(owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup'] == 0
         and owned['actual_worker_in_job_before_GO'] and owned['popen_handle_closed']
         and owned['cleanup_errors'] == [] and owned['returncode'] == 0, 'actual owned Job cleanup')
    need(child['cold_import'] == load(child_dir/'cold_import.json')
         and child['cold_import']['numpy_loaded'] is True and child['cold_import']['torch_loaded'] is False
         and child['cold_import']['fresh_import_accepted'] and child['held_class_identity_stable']
         and child['verified_no_forbidden_imports'], 'actual fresh NumPy/noTorch import')
    need(child['metadata_phase_closed'] and child['native_windows_metadata']['fixture_replaced'] is False
         and len(child['native_windows_metadata']['commands']) == 1 and child['forbidden_attempts'] == []
         and child['monitor_errors'] == [] and child['monitor_stopped'] and child['environment_restored']
         and child['original_error'] is None and child['junit_error'] is None, 'scope/restoration/errors')
    need(child['elapsed_seconds'] < 80 and final['elapsed_seconds'] < 90
         and child['resources']['observed_peak_rss_bytes'] <= 1024**3
         and child['resources']['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'actual resource bounds')
    for name,row in final['output_inventory'].items():
        need(name in ('case_events.jsonl','cold_import.json','junit.xml','pytest.log','reservation.json','result.json')
             and sha(read(child_dir/name)) == row['sha256'] and len(read(child_dir/name)) == row['bytes'], 'child raw byte binding')
    need(sha(read(owned_dir/'receipt.json')) == final['owned_receipt_sha256'], 'outer-owned receipt binding')
    for name,digest in owned['output_sha256'].items():
        need(name in ('stdout.log','stderr.log') and sha(read(owned_dir/name)) == digest, 'owned raw stdout/stderr')
    for name in ('case_events.jsonl','cold_import.json','junit.xml','pytest.log','reservation.json','result.json'): read(child_dir/name)
    for name in ('final.json','GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log'): read(owned_dir/name)
    read(Path(__file__).resolve())
    aliases = [dict(source=path.relative_to(R).as_posix(), bytes=len(raw), sha256_before_copy=sha(raw),
                    archived_as=f'input-{ordinal:03d}-'+path.name)
               for ordinal,(path,raw) in enumerate(sorted(payloads.items()),1)]
    inventory = dict(schema_version=1,run_id=RUN_ID,report_source=report.relative_to(R).as_posix(),
        input_aliases=aliases, source_bindings=sources, runtime_bindings=runtimes,
        actual=dict(counts=counts,junit_seconds=sum(float(s.get('time','0')) for s in tree.iter('testsuite')),
            child_seconds=child['elapsed_seconds'], outer_stored_seconds=final['elapsed_seconds'],
            resources=child['resources'], cold_import=child['cold_import'], owned_cleanup=True,
            scope_vi='GRAPH16partial evidence/geometry; no dynamicmodel/backend/fitted/GRAPH17/Gate/RQacceptance'))
    recheck(inventory)
    return inventory,payloads


def recheck(inventory):
    for row in inventory['input_aliases']:
        need(sha(safe(R/row['source']).read_bytes()) == row['sha256_before_copy'], 'selected input drift')
    for name,digest in inventory['source_bindings'].items():
        need(sha(safe(R/name).read_bytes()) == digest, 'pinned source drift')
    # Exact externally reviewed paths from runtime packet: hash only, never archive/import bytes.
    for name,digest in inventory['runtime_bindings'].items():
        need(sha(Path(name).read_bytes()) == digest, 'runtime fingerprint drift')


def main():
    need(os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(str(R/'.venv/Scripts/python.exe'))
         and Path(sys.prefix).resolve() == R/'.venv', 'repository .venv only')
    parser = argparse.ArgumentParser(description='ROOT metadata-only dry/close, không chạy lại fixtures/model')
    parser.add_argument('--report',type=Path,default=CANDIDATE)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--close',action='store_true')
    parser.add_argument('--expected-inventory-sha256')
    args=parser.parse_args(); report=safe(args.report.absolute()); target=safe(args.inventory.absolute(),existing=args.close)
    need(target.parent == P and target.suffix == '.json', 'prep-only inventory')
    need(not (R/'research_tracking/runs'/RUN_ID).exists(), 'immutable bundle already exists')
    inventory,payloads=gather(report); raw=encoded(inventory)
    if not args.close:
        need(not target.exists() and args.expected_inventory_sha256 is None, 'exclusive dry inventory')
        with target.open('xb') as handle: handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        print(json.dumps(dict(status='DRY_ONLY_NOT_CLOSED',inventory_sha256=sha(raw),copies=len(payloads),actual=inventory['actual'])))
        return
    need(args.expected_inventory_sha256 == sha(target.read_bytes()) == sha(raw), 'external exact dry SHA required')
    sys.path.insert(0,str(R/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note='''# GRAPH16 online query evidence — engineering09/11/2026

35NumPy cases0FES; actualcoldimport NumPyTrue/TorchFalse. Evidence/geometry only:
global anchors/OOV/past-only/counterfactualitemidentity; no dynamicmodel/backend/
fitted/GRAPH17/researchfit or completeRQclaim. Context offline guards unchanged.
25source/9runtime fingerprints stable, ownedJob0/handlesclosed/envrestored.
Raw13child/owner files +2newsource +controllers/packet +report/helper copied exact.
No runtimes/deps/corpus/testtemp copies. SHAinventory beforecopy + readback +
sourceaftercopy. Monitorcooperative, nothardOSquota. Caller history attribution
still required. NumPy data allowed; actual neural calls absent via coldimportguard.
'''
    git_before={k:v for k,v in os.environ.items() if k.startswith('GIT_')}
    try:
        for key in list(git_before): os.environ.pop(key,None)
        os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=R.as_posix())
        with record_evidence_run(R,RUN_ID,metadata=dict(kind='GRAPH16_NUMPY_QUERY35_PARTIAL_ENGINEERING',actual=inventory['actual']),
                sources=sorted(set(payloads)|{R/n for n in inventory['source_bindings']}|{target}),note=note) as directory:
            with (directory/'inventory-before.json').open('xb') as handle: handle.write(raw)
            copied={}
            for row in inventory['input_aliases']:
                destination=directory/row['archived_as']
                with destination.open('xb') as handle:
                    handle.write(payloads[R/row['source']]); handle.flush(); os.fsync(handle.fileno())
                copied[row['archived_as']]=sha(destination.read_bytes())
                need(copied[row['archived_as']] == row['sha256_before_copy'], 'copy readback mismatch')
            recheck(inventory)
            with (directory/'copy-verification.json').open('xb') as handle:
                handle.write(encoded(dict(status='VERIFIED_BYTES_NOT_RERUN',inventory_sha256=sha(raw),copied_sha256=copied,
                    sources_after={row['source']:sha(safe(R/row['source']).read_bytes()) for row in inventory['input_aliases']})))
            names=[*copied,'README.md','execution.log','inventory-before.json','copy-verification.json','force-add-files.txt','manifest.json']
            force=[(directory/name).relative_to(R).as_posix() for name in names]+list(PINS)[:2]
            if report == CANONICAL: force.append(report.relative_to(R).as_posix())
            with (directory/'force-add-files.txt').open('x',encoding='utf-8',newline='\n') as handle: handle.write('\n'.join(force)+'\n')
    finally:
        for key in list(os.environ):
            if key.startswith('GIT_'): os.environ.pop(key,None)
        os.environ.update(git_before)
    verified=verify_evidence_bundle(directory); recheck(inventory)
    print(json.dumps(dict(verified=verified,manifest_sha256=sha((directory/'manifest.json').read_bytes()),
        force_add_list=(directory/'force-add-files.txt').relative_to(R).as_posix())))


if __name__ == '__main__': main()
