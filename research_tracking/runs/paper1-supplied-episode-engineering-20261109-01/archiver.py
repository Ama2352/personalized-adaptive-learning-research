"""Đóng episode engineering đã kiểm72tests, dry không ghi và không rerun."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
RUN = 'paper1-supplied-episode-engineering-20261109-01'
REPORT_SHA = 'f479fd439dd14e6f9cb076bd95a119d0de203b82c54c5929a47abca437e97096'
FILES = (
    ('episode.py', ROOT/'src/knowledge_tracing/paper1_pdf/episode.py', 'e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471'),
    ('test_episode.py', ROOT/'tests/paper1_pdf/test_episode.py', 'd0bf6e052d9e2618b0b2d3ecf729164da68d99fc49a42e4c6dc0eadf6b4db1c0'),
    ('run_paper1_episode_tests01.py', WORK/'run_paper1_episode_tests01.py', '2ad916cba7c9765872be31cddaa928928d906ac884bcf3d7fa1da99e0700d800'),
    ('result.json', WORK/'paper1-episode-tests01/result.json', '013690ce194175525525f06bc4afd8a0b94085c4b47b61d5937c169886b7beff'),
    ('stdout.log', WORK/'paper1-episode-tests01/stdout.log', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    ('stderr.log', WORK/'paper1-episode-tests01/stderr.log', '0fd480a1cc6c3e1c8891c468e3fc59f48c8062d3ea8e6338c0a2322b519ab76d'),
    ('readiness_report.md', WORK/'PAPER1_EPISODE_READINESS_REPORT01.md', REPORT_SHA),
    ('episode_spec02.md', WORK/'PAPER1_PDF_EPISODE_SPEC02.md', '2c83655f63d973e3d009a5d091bfd2405513b89e00f782b1f68ab2b03268b176'),
)
OLD = {
    'src/knowledge_tracing/paper1_pdf/__init__.py': '0a9e0faa63680643c3526ce13135de2c033f105d82bf5ea8e7a55afdc2df7df7',
    'src/knowledge_tracing/paper1_pdf/simulator.py': 'b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f',
    'src/knowledge_tracing/paper1_pdf/domain.py': 'c37e32420c90f98289b9e21c2e6ea9197324f77a2452b7faae79f8c60985fb18',
    'tests/paper1_pdf/test_simulator.py': '0810c04847a0461bcb2ed8ddf5cb17fda13ab90dca1709adc7bc16ee847c8a03',
    'tests/paper1_pdf/test_domain.py': '5443ff36d437c4ed9a758089a0114e6a5b4da1396a137ec5b7ec5e4b16e9afdb',
    'tests/paper1_pdf/test_reentry_mechanism.py': '365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074',
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry', action='store_true')
    parser.add_argument('--canonical-report', action='store_true', help='Kiểm thêm bản canonical Root đã copy đúng SHA')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv required')
    out = ROOT/'research_tracking/runs'/RUN
    need(not out.exists(), 'exclusive new bundle required')
    copies = {alias: (path, digest) for alias, path, digest in FILES}
    copies['archiver.py'] = (Path(__file__).resolve(), sha(Path(__file__)))
    references = OLD | {
        'paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf': '984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4',
        'src/knowledge_tracing/evidence.py': '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49',
    }
    if args.canonical_report:
        references['research_tracking/reports/paper1_supplied_episode_readiness_20261109.md'] = REPORT_SHA
    before = {}
    for alias, (path, digest) in copies.items():
        need(path.is_file() and not path.is_symlink() and sha(path) == digest, 'selected source SHA '+alias)
        before[alias] = dict(source=path.relative_to(ROOT).as_posix(), sha256=digest, bytes=path.stat().st_size)
    for relative, digest in references.items():
        need(sha(ROOT/relative) == digest, 'reference SHA '+relative)
    result = json.loads((WORK/'paper1-episode-tests01/result.json').read_text(encoding='utf-8'))
    expected = OLD | {path.relative_to(ROOT).as_posix(): digest for _, path, digest in FILES[:2]}
    need(result['source_before'] == result['source_after'] == expected, 'exact tested eight-source inventory')
    need(result['status'] == 'ACCEPTED_72_PAPER1_TESTS_WITH_18_EPISODE_CASES' and result['tests'] == 72
         and result['new_episode_cases'] == 18 and result['returncode'] == 0 and result['timeout'] is False
         and 0 <= result['elapsed_seconds'] < result['cap_seconds'] == 30, 'actual72/18 receipt required')
    stderr = (WORK/'paper1-episode-tests01/stderr.log').read_bytes().replace(b'\r\n', b'\n')
    need(b'Ran 72 tests' in stderr and b'\nOK\n' in stderr, 'actual unittest terminal evidence')
    outputs = sorted((*copies, *GENERATED))
    dry = dict(status='DRY_VERIFIED_NOT_CLOSED', run_id=RUN, copies=len(copies),
        outputs_excluding_manifest=len(outputs), outputs=outputs, inventory=before, references=references,
        tests=72, new_episode_cases=18, tests_rerun=False, gaussian_sampling=False, research_matrix=False)
    if args.dry:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    with (WORK/'paper1_episode_copy_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(dry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(dict.fromkeys([path for path, _ in copies.values()]+[ROOT/name for name in references]))
    note = ('# Episode continuity với draws cấp sẵn theo PDF Paper1\n\n'
            '72tests đạt, gồm18episode cases mới, wrapper2,675402899971232giây/30. '
            'Bank và draws dựng tay, không Gaussian sampling, RNG-owned runner, B0/unlock hoặc matrix nghiên cứu. '
            'Không có kết quả graph/learning benefit mới hoặc tuyên bố tái lập số liệu PDF. '
            'Sáu source/test cũ và PDF chỉ tham chiếuSHA. Không copy TEMP.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='PAPER1_SUPPLIED_EPISODE_ENGINEERING',
        tests=72, new_episode_cases=18, elapsed_test_wrapper_seconds=result['elapsed_seconds'],
        gaussian_sampling=False, research_matrix=False, new_independent_N=0), sources=sources, note=note) as directory:
        checked = {}
        for alias, (path, digest) in copies.items():
            raw = path.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == digest, 'input changed before copy')
            with (directory/alias).open('xb') as stream:
                stream.write(raw)
            need(sha(directory/alias) == sha(path) == digest, 'copy/source post-SHA drift')
            need((directory/alias).stat().st_size == before[alias]['bytes'], 'copy byte count')
            checked[alias] = dict(before[alias], copy_sha256=digest, source_after_sha256=sha(path))
        for relative, digest in references.items():
            need(sha(ROOT/relative) == digest, 'reference changed during copying')
        (directory/'copy_inventory.json').write_text(json.dumps(checked, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (directory/'reference_sources.json').write_text(json.dumps(references, indent=2)+'\n', encoding='utf-8')
        need(sorted(p.name for p in directory.iterdir() if p.name != 'manifest.json') == outputs, 'exact output set')
    verification = verify_evidence_bundle(out)
    need(verification['artifacts'] == len(outputs), 'exact closed output count')
    print(json.dumps(dict(verification=verification, manifest_sha256=sha(out/'manifest.json'))))


if __name__ == '__main__':
    main()
