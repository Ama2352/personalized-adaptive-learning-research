"""ROOT-only collection: original60s gồm3fresh Jobs, cleanup và posthash.

Không test body; count chỉ là inventory, không phải phần mềm GatePASS.
Packet template không chạy được. ROOT chốt nguồn/packet/review trước invocation.
"""
import time
START = time.perf_counter()
WALL = time.time()
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'gate_collection_worker10.py'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
OUT = PREP/'gate-collection10-outer'
CHILD = PREP/'gate-collection10'
CAP = 60.
NAMESPACE_PROOF_SHA = '318537f3d176fc396ebdc8fb660ffb320e62c4fb8545f7f7168e2512da12f625'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def hexadecimal(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def validate_packet(packet):
    need(type(packet) is dict and type(packet.get('schema_version')) is int
         and packet['schema_version'] == 1 and packet.get('kind') == 'ROOT_FROZEN_GATE2_COLLECTION_INPUT'
         and type(packet.get('root_freeze_reference')) is str and packet['root_freeze_reference'].strip(),
         'ROOT finalized source freeze required; template is not runnable')
    need(packet.get('lock_file') == 'requirements-akt.lock.txt' and hexadecimal(packet.get('lock_sha256')), 'exact Windows lock')
    need(type(packet.get('gate_build_hashes')) is dict and packet['gate_build_hashes'], 'nonempty frozen native source map')
    need(type(packet.get('test_module_sha256')) is dict and packet['test_module_sha256'], 'exact test source hashes')
    need(type(packet.get('module_groups')) is list and len(packet['module_groups']) == 3
         and [g.get('name') for g in packet['module_groups']] == ['stdlib','no-torch','remaining'], 'canonical three fresh groups')
    modules = []
    for group in packet['module_groups']:
        need(set(group) == {'name','modules'} and type(group['modules']) is list and group['modules'], 'explicit group modules')
        modules.extend(group['modules'])
    need(len(modules) == len(set(modules)) and set(modules) == set(packet['test_module_sha256']), 'exact nonoverlapping module population')
    for mapping in (packet['gate_build_hashes'], packet['test_module_sha256']):
        for name, digest in mapping.items():
            need(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts
                 and Path(name).as_posix() == name and hexadecimal(digest), 'relative POSIX path and SHA required')
            safe(ROOT/name)
    need(all(packet['gate_build_hashes'].get(name) == digest for name,digest in packet['test_module_sha256'].items()), 'test population must be within native source map')
    need(type(packet.get('upstream_file_sha256')) is dict
         and set(packet['upstream_file_sha256']) == {'akt.py','README.md','LICENSE','load_data.py'}
         and all(hexadecimal(digest) for digest in packet['upstream_file_sha256'].values()), 'four pinned upstream bytes')
    need('expected_count' not in packet and 'expected_passed' not in packet, 'collection must not inherit a passing count')
    need(type(packet.get('support_document_sha256')) is dict and set(packet['support_document_sha256']) == {
        'docs/thesis_recovery/'+name for name in ('21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
        '22_A0_RESEARCH_LIFECYCLE_CONTRACT.md','23_TRAINING_MATRIX_ACCOUNTING_V1.md',
        '26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md','EXPERIMENT_ALLOCATION_V1.json')}
        and all(hexadecimal(digest) for digest in packet['support_document_sha256'].values()), 'five separate support document pins')


def snapshot(packet):
    # Membership mirror of native gate2_build_hashes; child additionally calls
    # the canonical function before/after each fresh collection process.
    paths = list((ROOT/'src/knowledge_tracing/akt').glob('*.py'))
    paths += list((ROOT/'tests/akt').glob('*.py')) + list((ROOT/'tests/shared_kt').glob('*.py'))
    paths += [ROOT/'src/knowledge_tracing/shared_kt.py', ROOT/'src/knowledge_tracing/paired_bootstrap.py',
              ROOT/'src/knowledge_tracing/gam_kt/evaluation.py']
    for directory in ('src/knowledge_tracing','scripts/research','scripts/akt'):
        paths += list((ROOT/directory).glob('*.py'))
    paper = ROOT/'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
    paths += list((paper/'data/simulator_inputs').glob('*.csv'))
    paths += [path for path in (paper/'source').glob('*.ipynb') if path.name in {
        'adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb',
        'junyi_cycle_corrected_ablation_confirmation.ipynb'}]
    paths += list((ROOT/'paper1').glob('*.ipynb'))
    need({path.relative_to(ROOT).as_posix() for path in paths} == set(packet['gate_build_hashes']), 'native source membership drift')
    source = {name: sha(safe(ROOT/name)) for name in packet['gate_build_hashes']}
    tests = {p.relative_to(ROOT).as_posix() for base in (ROOT/'tests/akt', ROOT/'tests/shared_kt')
             for p in base.rglob('*.py') if p.name.startswith('test_') or p.name.endswith('_test.py')}
    need(tests == set(packet['test_module_sha256']), 'test module population drift')
    need(source == packet['gate_build_hashes'], 'frozen source byte drift')
    lock = sha(safe(ROOT/packet['lock_file']))
    upstream = {name: sha(safe(ROOT/'artifacts/akt/dependencies/upstream'/name)) for name in packet['upstream_file_sha256']}
    need(lock == packet['lock_sha256'] and upstream == packet['upstream_file_sha256'], 'lock/upstream byte drift')
    docs = {name:sha(safe(ROOT/name)) for name in packet['support_document_sha256']}
    need(docs == packet['support_document_sha256'], 'support document drift')
    return dict(gate_build_hashes=source, test_modules=sorted(tests), lock_sha256=lock,
                upstream_file_sha256=upstream, support_document_sha256=docs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--worker-sha256', required=True)
    parser.add_argument('--approval-reference', required=True)
    args = parser.parse_args()
    need(hexadecimal(args.packet_sha256) and hexadecimal(args.worker_sha256) and args.approval_reference.strip(), 'external reviewed source/packet/review pins')
    need(not OUT.exists() and not CHILD.exists(), 'exclusive one attempt, no overwrite/retry')
    need(sha(ROOT/'scripts/research/windows_owned_worker.py') == HELPER_SHA, 'reviewed ownership helper bytes')
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import run_owned, entry
    global safe
    from windows_owned_worker import safe
    entry()
    safe(OUT); safe(CHILD); safe(WORKER)
    packet_path = safe(Path(args.packet))
    with packet_path.open('rb') as stream:
        raw = stream.read(2*1024**2+1)
    need(len(raw) <= 2*1024**2 and hashlib.sha256(raw).hexdigest() == args.packet_sha256, 'bounded exact finalized packet')
    packet = json.loads(raw)
    validate_packet(packet)
    need(sha(WORKER) == args.worker_sha256, 'exact reviewed worker')
    import psutil
    preflight = int(psutil.virtual_memory().available)
    need(preflight >= 4*1024**3, 'fresh4GiB before collection library imports')
    namespace_proof = safe(PREP/'pywin32_namespace_record01.json')
    need(sha(namespace_proof) == NAMESPACE_PROOF_SHA, 'reviewed namespace proof bytes')
    namespace_files = json.loads(namespace_proof.read_bytes())['file_sha256']
    need(all(sha(safe(ROOT/name)) == digest for name,digest in namespace_files.items()), 'installed namespace prehash')
    before = snapshot(packet)
    need(elapsed() < CAP-10, 'setup exhausted original60s; do not launch')
    OUT.mkdir(parents=True, exist_ok=False)
    write(OUT/'before.json', dict(packet_sha256=args.packet_sha256, source=before,
          preflight_available_ram_bytes=preflight, elapsed_seconds=elapsed()))
    env_keys = ('PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS','PYTEST_CURRENT_TEST')
    old_env = {key: os.environ.get(key) for key in env_keys}
    stages, errors, all_nodes, imported = [], [], [], {}
    try:
        os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        os.environ['PYTEST_ADDOPTS'] = ''
        os.environ.pop('PYTEST_PLUGINS', None); os.environ.pop('PYTEST_CURRENT_TEST', None)
        for group in packet['module_groups']:
            need(psutil.virtual_memory().available >= 4*1024**3, 'fresh4GiB admission for next group')
            need(sha(WORKER) == args.worker_sha256 and sha(packet_path) == args.packet_sha256, 'prelaunch pins')
            # Global clock never resets. Reserve3s for outer posthash, plus
            #3s owned cleanup. Worker active timer ends1s before Job deadline.
            owned_seconds = CAP-elapsed()-3.
            active_seconds = owned_seconds-4.
            need(active_seconds > 1., 'insufficient original global budget for next group')
            name = group['name']
            receipt = run_owned(WORKER, ['--packet',str(packet_path),'--packet-sha256',args.packet_sha256,
                '--group',name,'--active-seconds',repr(active_seconds)], OUT/(name+'-owned'),
                expected_worker_sha256=args.worker_sha256, approval_reference=args.approval_reference,
                max_seconds=owned_seconds, cleanup_reserve_seconds=3, max_output_bytes=65536)
            write(OUT/(name+'-owned')/'receipt.json', receipt)
            stage = dict(group=name, owned_receipt=receipt, allocated_seconds=owned_seconds)
            stages.append(stage)
            result_path = safe(CHILD/name/'result.json')
            need(result_path.stat().st_size <= 8*1024**2, 'bounded collection result')
            result = json.loads(result_path.read_bytes())
            stage.update(child_result_sha256=sha(result_path), child_result_relative=result_path.relative_to(ROOT).as_posix(), collected_count=result['collected_count'])
            need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
                 and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
                 and receipt['popen_handle_closed'] is True and receipt['cleanup_errors'] == []
                 and receipt['worker_sha256'] == args.worker_sha256, 'owned Job/worker/cleanup acceptance')
            need(result['status'] == 'COLLECTED_ONLY_PENDING_OUTER' and result['group'] == name
                 and result['modules'] == group['modules'] and result['pytest_exit_code'] == 0
                 and result['terminal_reporter_disabled'] is True and result['root_namespace_verified'] is True
                 and result['namespace_record_proof_sha256'] == NAMESPACE_PROOF_SHA
                 and result['source_before'] == result['source_after'] == packet['gate_build_hashes']
                 and result['packet_sha256'] == args.packet_sha256, 'actual canonical group and exact identities')
            need(result['support_document_before'] == result['support_document_after'] == packet['support_document_sha256']
                 and result['temporary_environment_and_cache_restored'] is True, 'support documents and owned temporary state')
            need(result['forbidden_attempts'] == result['failures'] == result['collection_reports'] == []
                 and result['profiler_restored'] is True and result['monitor_stopped'] is True
                 and result['modules_without_items'] == []
                 and set(result['zero_body_counters']) == {'test_body','model_constructor','backward','optimizer_step','solver_fit','teacher_call','data_read','cuda_execution','runtest_protocol'}
                 and not any(result['zero_body_counters'].values()), 'purity/import/collection guards')
            need(not any((CHILD/name/f).exists() for f in ('resource-failure.json','postwrite-rejection.json','call-guard-failure.json')), 'late or resource failure')
            need(result['resources']['samples'] > 0 and result['resources']['observed_minimum_available_ram_bytes'] >= 1024**3
                 and all(row['observed_peak_bytes'] <= 3*1024**3 for row in result['resources']['workers'].values()), 'observed resource floors')
            nodes = result['nodeids']
            need(nodes and len(nodes) == result['collected_count'] and len(nodes) == len(set(nodes))
                 and not set(nodes).intersection(all_nodes)
                 and {node.split('::',1)[0] for node in nodes} == set(group['modules']), 'exact independent nodeid population')
            all_nodes.extend(nodes)
            for relative,digest in result['imported_repo_source_sha256'].items():
                need(imported.get(relative,digest) == digest, 'imported repo source differs between fresh groups')
                imported[relative] = digest
            need(result['elapsed_seconds'] < active_seconds and elapsed() < CAP-3, 'original global budget')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error)))
    finally:
        for key,value in old_env.items():
            if value is None: os.environ.pop(key,None)
            else: os.environ[key] = value
    after = None
    try:
        after = snapshot(packet)
        need(after == before and sha(WORKER) == args.worker_sha256 and sha(packet_path) == args.packet_sha256
             and sha(ROOT/'scripts/research/windows_owned_worker.py') == HELPER_SHA, 'final source/controller/input drift')
        need(all(sha(safe(ROOT/name)) == digest for name,digest in imported.items()), 'supplemental imported source drift')
        need(sha(namespace_proof) == NAMESPACE_PROOF_SHA
             and all(sha(safe(ROOT/name)) == digest for name,digest in namespace_files.items()), 'installed namespace posthash')
        need(int(psutil.virtual_memory().available) >= 1024**3, 'final available1GiB floor')
        memory = psutil.Process().memory_info()
        need(max(memory.rss,getattr(memory,'peak_wset',0)) <= 3*1024**3, 'outer own process3GiB cap')
    except BaseException as error:
        errors.append(dict(stage='posthash/resources',type=type(error).__name__,message=str(error)))
    env_restored = all(os.environ.get(key) == value for key,value in old_env.items())
    accepted = not errors and len(stages) == 3 and env_restored and elapsed() < CAP
    final = dict(status='ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS' if accepted else 'REJECTED_COLLECTION',
        root_freeze_reference=packet['root_freeze_reference'], approval_reference=args.approval_reference,
        cap_seconds=CAP, elapsed_seconds=elapsed(), packet_sha256=args.packet_sha256,
        worker_sha256=args.worker_sha256, helper_sha256=HELPER_SHA,
        namespace_record_proof_sha256=NAMESPACE_PROOF_SHA,
        source_before=before, source_after=after, stages=stages, nodeids=all_nodes,
        collected_count=len(all_nodes), module_count=len(packet['test_module_sha256']),
        supplemental_imported_repo_source_sha256=imported, errors=errors, environment_restored=env_restored,
        gate_pass=False, test_bodies_executed=False, automatic_retry=False,
        scope_vi='3fresh canonicalgroups collect-only. Count không đo số testPASS. Imports thực thi module tops; guards đo callsites đã nêu, không attestation mọi syscall/site byte. RAMpoll cooperative,1GiBfloor/3GiBperprocess,4GiBadmission. ROOT phải freeze count/source riêng trước fullGate; không upload/remote/currentpointer.')
    write(OUT/'final.json', final)
    if elapsed() >= CAP:
        write(OUT/'postwrite-rejection.json', dict(status='REJECTED_COLLECTION_POSTWRITE_BUDGET', elapsed_seconds=elapsed()))
        accepted = False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_COLLECTION',
                         collected_count=len(all_nodes), elapsed_seconds=elapsed(), gate_pass=False)))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
