"""Lưu actual hai episode domain28 đã nghiệm thu, không chạy lại simulator."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
INNER = ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01'
OUTER = PREP/'paper1-seeded-domain01-outer'
OWNED = PREP/'paper1-seeded-domain01-owned'
RUN = 'paper1-seeded-domain-smoke-engineering-20261109-01'
FILES = (
    ('scientific__B1_observable.jsonl', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/B1_observable.jsonl', '3da1af69928a16902d05b0f8a4a25edc30a811c6c27874556876fca720dac36d'),
    ('scientific__B1_oracle.jsonl', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/B1_oracle.jsonl', '0b0bf9453496bf7049a11837d887cae4372b17b3ea3b35943601508e93af895b'),
    ('scientific__domain.json', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/domain.json', '6ff076ba8f1c59c077f2d5860bd9694a77c51b9d7ab8accac4072f9c6a802a4a'),
    ('scientific__draw_manifest.json', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/draw_manifest.json', '77fb359353c0e4fd74f900fb806ebeefb8ffcff6d43c10e8fd72473a3b32e8fe'),
    ('scientific__GA_observable.jsonl', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/GA_observable.jsonl', 'b52c6b4b4651a550de14ce8679ba906e5515d9f2503a1a2acc0f360af2d256f5'),
    ('scientific__GA_oracle.jsonl', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/GA_oracle.jsonl', '8caf6dcbf89f9dacd40cc4135ba3b2c70dce736b69463bd30ab87db7b5ba86e7'),
    ('scientific__manifest.json', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/manifest.json', '1364da669043bcfc70f9e1bfb81a20550bd2a7990e5315a08b334665623f6f30'),
    ('scientific__oracle_initial_profile.json', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/oracle_initial_profile.json', '8a7dc5357c3456f43bce5d1e7cfb4f7ef3cc4108b8e495242cf015a59449825b'),
    ('scientific__reservation.json', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/reservation.json', 'b7ad0105296be2121fec33ea8d40370e3d196572bb7f5adeb7d54e9403011506'),
    ('scientific__result.json', ROOT/'experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/result.json', 'cbe892e42cdcf969b4c1c7e8ef5b7f8462d66f0a72d39ed9c07b990c01704e0b'),
    ('outer__final.json', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1-seeded-domain01-outer/final.json', 'bea520db3612a5fb5b611c85ab80eacf29b3259eb046c94d02ca23a6eb6a3201'),
    ('outer__memory.jsonl', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1-seeded-domain01-outer/memory.jsonl', '71517a51d88984a4d970bf17ad46d791a785af4f2423b46dd9a34c5444095f15'),
    ('owned__GO.json', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1-seeded-domain01-owned/GO.json', '9bbc7f011de5b89377d18f7652cf5f6116e440751daf4759f379061c7c3103fa'),
    ('owned__launch.json', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1-seeded-domain01-owned/launch.json', '6812be45497d184cee712f1d3e3f7ef3a0b9ee19c5682b58a23695641edb8297'),
    ('owned__ready.json', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1-seeded-domain01-owned/ready.json', '26aec100f35fe19be5236db83289d9f56add68363d236266fefb9823d1196bf8'),
    ('owned__receipt.json', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1-seeded-domain01-owned/receipt.json', 'b11e534b93998b7bc3c2d0f046ae24508063e80b169667b9f15bc1ed9a5add91'),
    ('owned__stderr.log', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1-seeded-domain01-owned/stderr.log', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    ('owned__stdout.log', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1-seeded-domain01-owned/stdout.log', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    ('worker_paper1_seeded_domain01.py', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/worker_paper1_seeded_domain01.py', '94b2c034237fdc977efb1df5ef58d16ac8ac57c6e2eaf6836a7b7ea7ba810833'),
    ('run_paper1_seeded_domain01.py', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/run_paper1_seeded_domain01.py', 'd63df355455f37f351da676e6efa51c7939956d4d8b4b29c78e936d3b3ecc13f'),
    ('paper1_seeded_domain01_allocation.json', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1_seeded_domain01_allocation.json', 'a4c0d87f3dfe86a4a9688aafe6f21e1711eb2cbee1014db432880a3f34811942'),
    ('ROOT_PAPER1_DOMAIN_SMOKE_REVIEW01.md', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/ROOT_PAPER1_DOMAIN_SMOKE_REVIEW01.md', '4e36cc340854bbb2afd5dd94e6df501ac615d1911335c45becd2e775ab1ed012'),
    ('readiness_report.md', ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01/PAPER1_SEEDED_DOMAIN_SMOKE_READINESS_REPORT01.md', 'a9b64f662f0bb05a8bc0ac076638fa5a238cea59d26ae699db3d838ccd4ffd19'),
)
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    need(path.is_absolute() and path.resolve() == path, 'physical absolute evidence/input file')
    cursor = Path(path.anchor)
    for part in path.parts[1:]:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no input aliases')
    need(path.is_file() and path.stat().st_size <= 2*1024**2, 'bounded actual source/input')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable file bytes')
    return raw


def sha(path):
    return hashlib.sha256(read(path)).hexdigest()


def parse(path):
    return json.loads(read(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry', action='store_true')
    mode.add_argument('--close', action='store_true')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    destination = ROOT/'research_tracking/runs'/RUN
    need(not destination.exists(), 'exclusive new engineering archive')
    copies = {name: (path, pin) for name, path, pin in FILES}
    copies['archiver.py'] = (Path(__file__).resolve(), sha(Path(__file__)))
    before = {}
    for alias, (path, pin) in copies.items():
        need(sha(path) == pin and path.is_relative_to(ROOT), 'selected actual artifact SHA '+alias)
        before[alias] = dict(source=path.relative_to(ROOT).as_posix(), sha256=pin, bytes=path.stat().st_size)
    packet = parse(PREP/'paper1_seeded_domain01_allocation.json')
    actual, result = parse(OUTER/'final.json'), parse(INNER/'result.json')
    need(actual['status'] == 'ACCEPTED_TWO_PROSPECTIVE_DOMAIN28_EPISODES' and actual['errors'] == []
         and actual['allocation_sha256'] == result['allocation_sha256'] == sha(PREP/'paper1_seeded_domain01_allocation.json'),
         'accepted outer operation bound to exact allocation')
    need(packet['draw_request'] == dict(persona='US', function_chapter='Hàm số bậc 2 và đồ thị', root_seed=42,
         replicate_id='paper1-rng-smoke01', horizon=500) and packet['limits'] == dict(whole_seconds=35,
         owned_seconds=30, cleanup_seconds=3, worker_seconds=26, family_rss_bytes=268435456,
         min_available_ram_bytes=536870912), 'frozen scope/resources, no extension')
    receipt = actual['receipt']
    need(receipt == parse(OWNED/'receipt.json') and receipt['accepted'] is True and receipt['returncode'] == 0
         and receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup'] == 0
         and receipt['actual_worker_in_job_before_GO'] is True and receipt['popen_handle_closed'] is True
         and receipt['errors'] == receipt['cleanup_errors'] == [], 'actual owned success and cleanup/Job0')
    for name, pin in receipt['output_sha256'].items():
        need(name in ('stdout.log', 'stderr.log') and sha(OWNED/name) == pin, 'actual raw owned streams')
    resources = actual['resources']
    need(resources['errors'] == [] and resources['monitor_stopped'] is True and resources['child_family_samples'] > 0
         and resources['family_peak_rss_bytes'] <= 256*1024**2
         and resources['minimum_available_ram_bytes'] >= 512*1024**2
         and actual['elapsed_seconds'] < 35 and result['elapsed_seconds'] < result['worker_cap_seconds'] == 26,
         'sampled resource observations and original clocks')
    need(len(packet['pins']) == packet['pin_count'] == 33
         and actual['source_before'] == actual['source_after'] == result['source_before'] == result['source_after'] == packet['pins']
         and result['methods_restored'] is True and result['global_rng_unchanged'] is True
         and result['scientific_modules_absent'] is True and result['forbidden'] == [], 'complete source/runtime/scope receipts')
    need(result['status'] == 'COMPLETED_TWO_PROSPECTIVE_EPISODES_PENDING_OUTER'
         and result['consumed_feedback'] == actual['validation']['consumed_feedback'] == 344
         and actual['validation']['branches'] == dict(B1=172, GA=172)
         and actual['validation']['acceptance_uses_graph_ranking_or_zero_reentry'] is False, 'actual engineering population')
    expected_calls = dict(controllers=2, worlds=2, select=346, observe=344, respond=344,
                          prepare=1, random_events=14028, episodes=2)
    need(result['counters'] == {name: dict(started=n, returned=n) for name, n in expected_calls.items()}, 'actual started/body-return counters')
    manifest = parse(INNER/'manifest.json')
    expected_files = set(actual['validation']['files'])
    need(len(expected_files) == 10 and {p.name for p in INNER.iterdir()} == expected_files
         and manifest['status'] == 'COMPLETE_TWO_EPISODE_ENGINEERING'
         and manifest['source_after'] == packet['pins'], 'complete exact scientific output set')
    for name, row in actual['validation']['files'].items():
        need(sha(INNER/name) == row['sha256'] and (INNER/name).stat().st_size == row['bytes'], 'outer accepted output bytes')
        if name != 'manifest.json':
            need(manifest['files'][name] == row, 'scientific manifest output binding')
    for label, switches, reentries in (('B1', 2, 0), ('GA', 4, 2)):
        branch = result['branches'][label]
        metrics = dict(branch['metadata']['metrics'])
        need(branch['rows'] == 172 and branch['metadata']['stop_reason'] == 'ALL_ESTIMATED_MASTERED'
             and branch['metadata']['budget_exhausted'] is False and metrics['interactions'] == 172
             and metrics['estimated_mastered_concepts'] == metrics['concept_denominator'] == 28
             and metrics['chapter_switches'] == switches and metrics['chapter_reentry'] == reentries,
             'preserve all observed witness outcomes, not a favorable acceptance requirement')
    need(result['branches']['B1']['final_latent_sha256'] == result['branches']['GA']['final_latent_sha256']
         == 'b62b8c760f53fa489a79f9c8baa2c992e1221748c9a99e1edcd8470c73895ac3', 'observed final-state identity')
    references = {}
    copy_aliases = {path: alias for alias, (path, _) in copies.items()}
    for name, pin in packet['pins'].items():
        path = Path(name) if Path(name).is_absolute() else ROOT/name
        need(sha(path) == pin, 'actual source/input/runtime remains unchanged '+name)
        references[name] = dict(sha256=pin, bytes=path.stat().st_size, copied=path in copy_aliases,
            copy_alias=copy_aliases.get(path),
            repository_path=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else None)
    outputs = sorted((*copies, *GENERATED))
    need(len(outputs) == len(set(outputs)) == 28, 'exact twenty-eight writing outputs excluding manifest')
    dry = dict(status='ACTUAL_ENGINEERING_INPUTS_VERIFIED_NOT_CLOSED', run_id=RUN, copies=before,
        references=references, outputs=outputs, outputs_excluding_manifest=28, analysis_or_simulation_rerun=False)
    if args.dry:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    with (PREP/'paper1_domain_smoke_copy_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(dry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    inputs = list(dict.fromkeys([path for path, _ in copies.values()]+[
        ROOT/row['repository_path'] for row in references.values() if row['repository_path'] is not None]))
    note = ('# Hai episode continuity trên prospective domain28\n\n'
        'Actual một US/seed42, cùng profile/tape,172feedback mỗi B1/GA, tổng344. '
        'B1switch2/reentry0 vàGAswitch4/reentry2 đều giữ; không graph ranking hoặc matrix nghiên cứu. '
        'Toàn10scientific outputs được sao lưu nhỏ, originals ởexperiments/simulator/results. '
        '33source/input/runtime chỉ tham chiếuSHA, không copy CSV/PDF/runtime. '
        'Giữ raw outer/monitor/owned, không chạy lại simulator hoặc inference.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='PAPER1_PROSPECTIVE_DOMAIN28_ENGINEERING',
        logical_profiles=1, continuity_episodes=2, actual_feedback=344, same_immutable_draws=True,
        research_matrix=False, research_RQ_completion=False), sources=inputs, note=note) as directory:
        checked = {}
        for alias, (path, pin) in copies.items():
            raw = read(path)
            need(hashlib.sha256(raw).hexdigest() == pin, 'input before copy')
            with (directory/alias).open('xb') as stream:
                stream.write(raw)
            need(sha(directory/alias) == sha(path) == pin and len(raw) == before[alias]['bytes'], 'copy/source after SHA')
            checked[alias] = dict(before[alias], copied_sha256=pin, source_after_sha256=sha(path))
        for name, row in references.items():
            path = Path(name) if Path(name).is_absolute() else ROOT/name
            need(sha(path) == row['sha256'], 'reference after copy')
        (directory/'copy_inventory.json').write_text(json.dumps(checked, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (directory/'reference_sources.json').write_text(json.dumps(references, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        need(sorted(path.name for path in directory.iterdir() if path.name != 'manifest.json') == outputs, 'exact output membership')
    verification = verify_evidence_bundle(destination)
    need(verification['artifacts'] == 28, 'exact closed bundle count')
    print(json.dumps(dict(verification=verification, manifest_sha256=sha(destination/'manifest.json'))))


if __name__ == '__main__':
    main()
