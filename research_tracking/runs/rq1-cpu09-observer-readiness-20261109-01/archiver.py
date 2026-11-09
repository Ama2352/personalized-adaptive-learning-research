"""Đóng observer readiness03, giữ failure02/RAM refusal, không replay hoặc fit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
RUN = 'rq1-cpu09-observer-readiness-20261109-01'
REPORT_SHA = '397f6f6e47ed5973f42a40974ef4672e23fde6f10c5cdb6a3f2eb33afebdf441'
PINNED = {
    'pilot_rq1_cpu09_targeted_observer03.py': '1c84c3271556d2aa7b5d0ae709122504c2a4a008e8e9c4aa524d0345a10f5baf',
    'run_rq1_cpu09_targeted_observer03.py': '89d654a26e0c6120c88fd10820330c702cb6a8525d332973f560d6124deac130',
    'rq1_cpu09_targeted_observer_contract03.json': '0280db8bfcaf844f2646a2c60c2f7cdac3808ba54e6c94ea476b815dcb5bdb90',
    'CPU09_TARGETED_OBSERVER_ROOT_REVIEW04.md': '2311418d4a71bea7e1b3d7173cf09db8f59d9ed6760850d69c599786ff782736',
    'CPU09_TARGETED_OBSERVER_ROOT_REVIEW03.md': '3640332c4d619d026a4a651725330925ae04492758e1810b180692bf745f25b3',
    'rq1_cpu09_targeted_observer_contract02.json': '34ca70174d055a3c6e222f5ac48913dde1f797b69ea93fc68e98043a1282f024',
    'cpu09-targeted-observer-native03/result.json': '3641869970dd612569f2849d919f616abce8196e0892c71d1d612457198922c6',
    'cpu09-targeted-observer-native03-outer/final.json': '96ed606befb8205083db3caf3a325368483d609492ba709d0aabd4798486904d',
    'cpu09-targeted-observer-native02/failure.json': 'e71cb8897b6f37e4aebeefbd74619fcd1961ea4406446e17c8daedd26710dc38',
    'cpu09-targeted-observer-native02-outer/final.json': '735b0fc5ec7daf45acdf65164fee57c2fb6ca1c309dafba848967e7cea8e06c5',
    'cpu09_targeted_observer02_prelaunch_ram_refusal01.json': 'dcf45f18123d4de134193c167913d467cef14e02447a40e86f2ceddd37bc6a03',
    'CPU09_OBSERVER_READINESS_REPORT01.md': REPORT_SHA,
}
OLD_MANIFEST = 'research_tracking/runs/rq1-cpu09-targeted-observer-attempt-20261109-01/manifest.json'
OLD_SHA = '75b9df64ec07f73c09f2b88f51f9f7c51391cb1a12c4140b5ba91430e278db3e'
UTC = '.venv/Lib/site-packages/tzdata/zoneinfo/UTC'
UTC_SHA = 'fddce1e648a1732ac29afd9a16151b2973cdf082e7ec0c690f7e42be6b598b93'
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(relative):
    return json.loads((WORK/relative).read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry', action='store_true')
    parser.add_argument('--inventory-sha256', help='Hash inventory_sha256 từ dry đã được Root review')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv required')
    out = ROOT/'research_tracking/runs'/RUN
    need(not out.exists(), 'exclusive new readiness bundle required')
    for name, digest in PINNED.items():
        need(sha(WORK/name) == digest, 'pinned evidence drift '+name)
    final = read('cpu09-targeted-observer-native03-outer/final.json')
    result = read('cpu09-targeted-observer-native03/result.json')
    owned = read('cpu09-targeted-observer-native03-owned/receipt.json')
    need(final['status'] == 'ACCEPTED_ONE_HISTORY_TARGETED_OBSERVER_OPERATIONAL_PILOT'
         and final['errors'] == [] and final['environment_restored'] is True
         and 0 <= final['elapsed_before_receipt_seconds'] < final['whole_cap_seconds'] == 60,
         'actual03 accepted outer required')
    need(final['receipt'] == owned and owned['accepted'] is True and owned['returncode'] == 0
         and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup'] == 0
         and owned['popen_handle_closed'] is True and owned['actual_worker_in_job_before_GO'] is True,
         'genuine03 owned terminal/cleanup required')
    resource = final['resources']
    need(resource['monitor_stopped'] is True and resource['errors'] == []
         and resource['observed_family_peak_rss_bytes'] <= 1024**3
         and resource['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'sampled resources required')
    sources = result['source_before']
    need(len(sources) == 38 and sources == result['source_after'] == final['source_input_before'] == final['source_input_after'],
         'actual38 source/input before-after binding')
    counts = dict(constructors=2, select=240, predict=240, update=240, native_capture=240)
    need(result['status'] == 'COMPLETE_ONE_HISTORY_OFF_ON_PARITY_PENDING_ROOT'
         and result['direct_started'] == result['direct_returned'] == result['reservation'] == counts
         and result['errors'] == result['restoration_errors'] == [] and result['audit_denial_count'] == 0
         and result['policy_oracle_exposure'] is False and result['profiler_installed'] is False,
         'actual declared method accounting/restoration required')
    off, on = read('cpu09-targeted-observer-native03/off.json'), read('cpu09-targeted-observer-native03/on.json')
    need(off['events'] == on['events'] == len(off['readouts']) == len(on['readouts']) == 120
         and off['key'] == on['key'] == [21000, 'PG', False, False] and off['readouts'] == on['readouts'],
         'complete one-history readout parity required')
    for field, expected in (
        ('initial_state_sha256', 'f6b64156fbdbd07800fd9086aa555e437a20fe58f459de8ac7521e2336797ac7'),
        ('final_state_sha256', 'e44d4f12343f25693c2fac90cf538111f02581bb01240d1dccb26f82cfb4e205')):
        need(off[field] == on[field] == expected, 'endpoint fingerprint parity')
    observer_counts = dict(__init__=1, select=120, predict=120, update=120, _decayed_pi=360)
    observer = on['observer']
    need(observer['started'] == observer['returned'] == observer_counts and observer['raised'] == {}
         and observer['class_attributes_restored'] is True and observer['live'] is False
         and observer['pending_attributes'] == observer['cleanup_errors'] == [], 'ON observer actual method parity')
    need(read('cpu09-targeted-observer-native03/pure_checks.json')['manufactured_checks'] == 5, 'five synthetic checks')
    failure = read('cpu09-targeted-observer-native02/failure.json')
    need(failure['status'] == 'REJECTED_KEEP_PILOT_NO_RETRY' and failure['audit_denial_count'] == 1
         and failure['direct_started'] == failure['direct_returned'] == {}, 'preserved02 import rejection')
    need(failure['deny_contexts'][0]['raw_path'].replace('\\', '/').endswith('/'+UTC), 'exact02 UTC denial context')
    owned02 = read('cpu09-targeted-observer-native02-owned/receipt.json')
    need(owned02['accepted'] is False and owned02['returncode'] == 1 and owned02['cleanup_accepted'] is True
         and owned02['job_active_after_cleanup'] == 0, 'rejected02 still has genuine cleanup')
    refusal = read('cpu09_targeted_observer02_prelaunch_ram_refusal01.json')
    need(refusal['worker_dispatched'] is False and refusal['output_directories_created'] is False, 'prelaunch refusal scope')
    copies = {name: WORK/name for name in PINNED if '/' not in name}
    for category, names in (
        ('', ('native_metadata.json', 'off.json', 'on.json', 'pure_checks.json', 'reservation.json', 'result.json')),
        ('-outer', ('admission.json', 'final.json', 'memory.jsonl')),
        ('-owned', ('GO.json', 'launch.json', 'ready.json', 'receipt.json', 'stdout.log', 'stderr.log'))):
        for name in names:
            copies['03'+category+'__'+name] = WORK/('cpu09-targeted-observer-native03'+category)/name
    copies.update({'02_failure.json': WORK/'cpu09-targeted-observer-native02/failure.json',
                   '02_outer_final.json': WORK/'cpu09-targeted-observer-native02-outer/final.json',
                   '02_owned_receipt.json': WORK/'cpu09-targeted-observer-native02-owned/receipt.json'})
    copies['UTC_111bytes.bin'] = ROOT/UTC
    copies['archiver.py'] = Path(__file__).resolve()
    need(sha(ROOT/UTC) == UTC_SHA and (ROOT/UTC).stat().st_size == 111, 'exact UTC runtime data')
    for name, expected in final['outputs'].items():
        need(sha(WORK/'cpu09-targeted-observer-native03'/name) == expected['sha256'], 'actual inner output manifest')
    for name, expected in owned['output_sha256'].items():
        need(sha(WORK/'cpu09-targeted-observer-native03-owned'/name) == expected, 'owned log SHA')
    references = dict(sources)
    references[OLD_MANIFEST] = OLD_SHA
    references['src/knowledge_tracing/evidence.py'] = '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
    for name, expected in (
        ('inventory-before.json', 'ac96da3d02d02405dd8b962c6ed123449a1fc5d68f3340e9e79ce0f470603210'),
        ('copy-verification.json', '76f87d52999ac6c3f510d7635c5bac91344dc7d5ee6d453eb265a5d2b8b24071'),
        ('parent02-reference-verification.json', '5ce7ccf60e0bdd1006eda9004515b2b0d7064b15018675812ae01d7295b8e20c')):
        references[(WORK/'targeted-observer-before-utc-resource03'/name).relative_to(ROOT).as_posix()] = expected
    for name, expected in references.items():
        need(sha(ROOT/name) == expected, 'reference SHA drift '+name)
    inventory = {alias: dict(source=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)
                 for alias, path in copies.items()}
    freeze = dict(copies=inventory, references=references)
    inventory_sha = hashlib.sha256(json.dumps(freeze, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    outputs = sorted((*copies, *GENERATED))
    need(len(outputs) <= 40, 'compact output cap')
    dry = dict(status='DRY_VERIFIED_NOT_CLOSED', run_id=RUN, inventory_sha256=inventory_sha,
               outputs_excluding_manifest=len(outputs), outputs=outputs, **freeze)
    if args.dry:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    need(args.inventory_sha256 == inventory_sha, 'Root-reviewed dry inventory SHA required')
    with (WORK/'cpu09_observer_readiness_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(dry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    source_paths = list(dict.fromkeys([*copies.values(), *[ROOT/name for name in references]]))
    note = ('# Observer CPU09, một lịch sử120event\n\n'
            'Actual03 OFF/ON exact readout/endpoints, 2constructors/240calls mỗi loại, ONdecayed360, 5purechecks. '
            'Giữ actual02import failure và prelaunch RAM refusal. Original01closed34 chỉ tham chiếuSHA. '
            'Không truth accuracy/full120streams/learning claim; OFFtrướcON không là causal overhead benchmark.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='CPU09_TARGETED_OBSERVER_READINESS',
        reused_history_count=1, events_per_phase=120, new_independent_N=0,
        truth_accuracy_analysed=False, full_cache_replay=False), sources=source_paths, note=note) as directory:
        after = {}
        for alias, path in copies.items():
            raw = path.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == inventory[alias]['sha256'], 'source drift before copy')
            with (directory/alias).open('xb') as stream:
                stream.write(raw)
            need(sha(directory/alias) == sha(path) == inventory[alias]['sha256'], 'copy/source post-SHA drift')
            need((directory/alias).stat().st_size == inventory[alias]['bytes'], 'copy byte count')
            after[alias] = dict(inventory[alias], copy_sha256=sha(directory/alias), source_after_sha256=sha(path))
        for name, expected in references.items():
            need(sha(ROOT/name) == expected, 'reference changed during copy')
        (directory/'copy_inventory.json').write_text(json.dumps(after, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (directory/'reference_inputs.json').write_text(json.dumps(references, indent=2)+'\n', encoding='utf-8')
        need(sorted(path.name for path in directory.iterdir() if path.name != 'manifest.json') == outputs, 'exact output set')
    verification = verify_evidence_bundle(out)
    need(verification['artifacts'] == len(outputs), 'exact final output count')
    print(json.dumps(dict(verification=verification, manifest_sha256=sha(out/'manifest.json'))))


if __name__ == '__main__':
    main()
