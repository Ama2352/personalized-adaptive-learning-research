"""Lưu bằng chứng85tests Paper1, không rerun hoặc chạy pilot miền thật."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
RUN = 'paper1-seeded-episode-engineering-20261109-01'
REPORT_SHA = '79009714df71783957c1a99e552f6ff840afd59931f05aa0e6034450815e6623'
FILES = (
    ('seeded_episode.py', ROOT/'src/knowledge_tracing/paper1_pdf/seeded_episode.py', '7c7ac305cd49fd79f5768173198705be7fa32586114acf5871950c7540dda1b2'),
    ('test_seeded_episode.py', ROOT/'tests/paper1_pdf/test_seeded_episode.py', 'f97674bc764988271c091a00560bf31f2afba2f951b72819a150ae64a83b48e2'),
    ('run_paper1_seeded_tests01.py', WORK/'run_paper1_seeded_tests01.py', '16af2814389c6b161d983e0f0319cf5b619d3c217a7d8223917ee69ef42704eb'),
    ('result.json', WORK/'paper1-seeded-tests01/result.json', 'aebb792bb319307d7a16aac24699a9ec652ec1e29bd315aa277bda44d8a21de9'),
    ('stdout.log', WORK/'paper1-seeded-tests01/stdout.log', '576b0ad34fed9fcc639d7dd4bc874a6c9ecd8d7c5da586f40f80161547593df7'),
    ('stderr.log', WORK/'paper1-seeded-tests01/stderr.log', '1e0b11fd607bd1d996b2823f9f15c9f65937bb127e4d502d08915206503ae504'),
    ('dependencies_before.json', WORK/'paper1_seeded_dependencies_before01.json', 'd16696e28f04ecc21744f84d3f0ea1e300f3119ec3d9c88c335782abbbe44aa7'),
    ('dependencies_after.json', WORK/'paper1_seeded_dependencies_after01.json', '22da8a6e4449f30f7121dd6325f2580f8138db61ae375e497e1416c211abfcca'),
    ('rng_proposal01.md', WORK/'PAPER1_RNG_OWNED_RUNNER_PROPOSAL01.md', '06a5bf51326c972e24b685c2e35103200f1293a7f4a74f6193b8a9b94705055d'),
    ('readiness_report.md', WORK/'PAPER1_SEEDED_EPISODE_READINESS_REPORT01.md', REPORT_SHA),
)
REFERENCES = {
    'src/knowledge_tracing/paper1_pdf/__init__.py': '0a9e0faa63680643c3526ce13135de2c033f105d82bf5ea8e7a55afdc2df7df7',
    'src/knowledge_tracing/paper1_pdf/simulator.py': 'b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f',
    'src/knowledge_tracing/paper1_pdf/domain.py': 'c37e32420c90f98289b9e21c2e6ea9197324f77a2452b7faae79f8c60985fb18',
    'src/knowledge_tracing/paper1_pdf/episode.py': 'e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471',
    'src/knowledge_tracing/simulator_bridge.py': 'b29105acd8de84b060ca27573bb7f7cf8e85599a4596e50e4a21ab63c82329d2',
    'tests/paper1_pdf/test_simulator.py': '0810c04847a0461bcb2ed8ddf5cb17fda13ab90dca1709adc7bc16ee847c8a03',
    'tests/paper1_pdf/test_domain.py': '5443ff36d437c4ed9a758089a0114e6a5b4da1396a137ec5b7ec5e4b16e9afdb',
    'tests/paper1_pdf/test_reentry_mechanism.py': '365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074',
    'tests/paper1_pdf/test_episode.py': 'd0bf6e052d9e2618b0b2d3ecf729164da68d99fc49a42e4c6dc0eadf6b4db1c0',
    'paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf': '984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/PAPER1_PDF_EPISODE_SPEC02.md': '2c83655f63d973e3d009a5d091bfd2405513b89e00f782b1f68ab2b03268b176',
    'src/knowledge_tracing/evidence.py': '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49',
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry', action='store_true')
    parser.add_argument('--inventory-sha256')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv required')
    out = ROOT/'research_tracking/runs'/RUN
    need(not out.exists(), 'exclusive new bundle required')
    copies = {alias: (path, digest) for alias, path, digest in FILES}
    copies['archiver.py'] = (Path(__file__).resolve(), sha(Path(__file__)))
    before = {}
    for alias, (path, digest) in copies.items():
        need(path.is_file() and not path.is_symlink() and sha(path) == digest, 'selected source SHA '+alias)
        before[alias] = dict(source=path.relative_to(ROOT).as_posix(), sha256=digest, bytes=path.stat().st_size)
    for name, digest in REFERENCES.items():
        need(sha(ROOT/name) == digest, 'reference SHA '+name)
    result = json.loads((WORK/'paper1-seeded-tests01/result.json').read_bytes())
    expected = {name: digest for name, digest in REFERENCES.items() if name.startswith('tests/')
                or name.startswith('src/knowledge_tracing/paper1_pdf/')}
    expected.update({path.relative_to(ROOT).as_posix(): digest for _, path, digest in FILES[:2]})
    need(result['source_before'] == result['source_after'] == expected, 'exact tested ten-source inventory')
    need(result['status'] == 'ACCEPTED85_PAPER1_CASES_WITH13_SEEDED_CASES'
         and result['counts'] == dict(tests=85, failures=0, errors=0, skipped=0, scientific_modules_absent=True)
         and result['new_seeded_cases'] == 13 and result['returncode'] == 0 and result['timeout'] is False
         and 0 <= result['elapsed_seconds'] < result['cap_seconds'] == 30, 'actual85/13 receipt required')
    stderr = (WORK/'paper1-seeded-tests01/stderr.log').read_bytes().replace(b'\r\n', b'\n')
    need(b'Ran 85 tests' in stderr and b'\nOK\n' in stderr, 'actual unittest terminal evidence')
    stdout = json.loads((WORK/'paper1-seeded-tests01/stdout.log').read_bytes())
    need(stdout == result['counts'], 'actual stdout counts agree')
    dependency_before = json.loads((WORK/'paper1_seeded_dependencies_before01.json').read_bytes())
    dependency_after = json.loads((WORK/'paper1_seeded_dependencies_after01.json').read_bytes())
    need(dependency_after['before_inventory_sha256'] == FILES[6][2]
         and len(dependency_before['files']) == len(dependency_after['files']) == 7, 'seven preparation dependencies')
    dependencies = {}
    for old, new in zip(dependency_before['files'], dependency_after['files'], strict=True):
        need(old['path'] == new['path'] and old['bytes'] == new['bytes']
             and old['sha256'] == new['sha256_before'] == new['sha256_after'], 'preparation before/after binding')
        path = Path(old['path'])
        need(path.stat().st_size == old['bytes'] and sha(path) == old['sha256'], 'actual dependency bytes unchanged')
        dependencies[old['path']] = dict(bytes=old['bytes'], sha256=old['sha256'])
    outputs = sorted((*copies, *GENERATED))
    need(len(outputs) == len(set(outputs)) == 15, 'exact fifteen outputs excluding manifest')
    inventory = dict(run_id=RUN, inventory=before, references=REFERENCES, dependency_sources=dependencies,
                     outputs=outputs, outputs_excluding_manifest=15)
    inventory_sha = hashlib.sha256(canonical(inventory)).hexdigest()
    dry = dict(status='DRY_VERIFIED_NOT_CLOSED', inventory_sha256=inventory_sha, **inventory,
               tests=85, new_seeded_cases=13, tests_rerun=False, actual_domain_pilot=False, research_matrix=False)
    if args.dry:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    need(args.inventory_sha256 == inventory_sha, 'Root reviewed exact dry inventory required')
    with (WORK/'paper1_seeded_copy_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(dry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(dict.fromkeys([path for path, _ in copies.values()]+[ROOT/name for name in REFERENCES]))
    note = ('# Paper1 seeded continuity engineering\n\n'
            '85tests đạt, gồm13seeded cases mới; wrapper2,4102863000007346giây/30. '
            'Bank dựng tay và hồi quy. Recipe keyed private Random prospective, không historical draw reproduction. '
            'Chưa actual domain pilot28concept, B0/unlock hoặc matrix50seeds. '
            'Runtime random.py được kiểmSHA nhưng không copy thư viện hoặc runtime vào bundle.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='PAPER1_SEEDED_EPISODE_ENGINEERING',
        tests=85, new_seeded_cases=13, elapsed_test_wrapper_seconds=result['elapsed_seconds'],
        actual_domain_pilot=False, research_matrix=False, new_independent_N=0), sources=sources, note=note) as directory:
        checked = {}
        for alias, (path, digest) in copies.items():
            raw = path.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == digest, 'input changed before copy')
            with (directory/alias).open('xb') as stream:
                stream.write(raw)
            need(sha(directory/alias) == sha(path) == digest and len(raw) == before[alias]['bytes'], 'copy/source post-SHA')
            checked[alias] = dict(before[alias], copy_sha256=digest, source_after_sha256=sha(path))
        for name, digest in REFERENCES.items():
            need(sha(ROOT/name) == digest, 'reference changed during copying')
        for name, row in dependencies.items():
            need(sha(Path(name)) == row['sha256'] and Path(name).stat().st_size == row['bytes'], 'dependency post-copy unchanged')
        (directory/'copy_inventory.json').write_text(json.dumps(checked, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (directory/'reference_sources.json').write_text(json.dumps(dict(repository=REFERENCES, preparation_dependencies=dependencies),
            ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        need(sorted(p.name for p in directory.iterdir() if p.name != 'manifest.json') == outputs, 'exact output set')
    verification = verify_evidence_bundle(out)
    need(verification['artifacts'] == 15, 'exact closed output count')
    print(json.dumps(dict(verification=verification, manifest_sha256=sha(out/'manifest.json'))))


if __name__ == '__main__':
    main()
