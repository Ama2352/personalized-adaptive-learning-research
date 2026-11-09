"""Đóng bằng chứng batchA đã kiểm, không chạy lại model hoặc tests."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'cgakt-cuda-core-cpu-engineering-20261109-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()
    if Path(sys.prefix).resolve() != ROOT / '.venv':
        raise ValueError('Repository .venv required')
    destination = ROOT / 'research_tracking/runs' / RUN
    if destination.exists():
        raise ValueError('Exclusive new bundle required')
    child = load(PREP / 'cgakt-research-model04/result.json')
    outer = load(PREP / 'cgakt-research-model04-owned/final.json')
    owned = load(PREP / 'cgakt-research-model04-owned/receipt.json')
    pure = load(PREP / 'cuda-profile-pure-tests01/result.json')
    assert outer['status'] == 'ACCEPTED_CGAKT_RESEARCH_CORE_ENGINEERING_ONLY'
    assert outer['counts'] == child['counts'] == dict(tests=26, failures=0, errors=0, skipped=0)
    assert outer['native_counts'] == child['native_started'] == child['native_body_returned']
    assert child['source_before'] == child['source_after'] == outer['source_after']
    assert owned['cleanup_accepted'] and owned['job_active_after_cleanup'] == 0
    assert pure['status'] == 'ACCEPTED_13_PURE_CUDA_PROFILE_TESTS' and pure['tests'] == 13
    assert pure['source_before'] == pure['source_after']
    references = child['source_before']
    for name, digest in references.items():
        assert sha(ROOT / name) == digest, name
    copies = {}
    for name in ('src/knowledge_tracing/akt/config.py', 'src/knowledge_tracing/akt/research_graph_model.py',
                 'tests/akt/test_research_cuda_profile.py', 'tests/akt/test_research_graph_model.py'):
        copies['current__' + Path(name).name] = ROOT / name
    for path in (PREP / 'cuda-core-before01').iterdir():
        assert path.is_file()
        copies['before__' + path.name] = path
    before = load(PREP / 'cuda-core-before01/inventory.json')
    for row in before['files']:
        assert sha(ROOT / row['copy']) == row['sha256_before_copy'] == row['sha256_after_copy']
    for name in ('check_cgakt_research_model04.py', 'run_cgakt_research_model04.py',
                 'cgakt_research_model04_allocation.json', 'CUDA_CORE_CPU_COMPAT_ROOT_REVIEW01.md',
                 'CUDA_EXECUTION_IMPLEMENTATION_SPEC02.md', 'run_cuda_profile_pure_tests01.py'):
        copies[name] = PREP / name
    copies['execution_adoption.md'] = ROOT / 'docs/thesis_recovery/28_CUDA_EXECUTION_PROFILE_V1.md'
    copies['readiness_report.md'] = ROOT / 'research_tracking/reports/cgakt_cuda_core_cpu_readiness_20261109.md'
    copies['archiver.py'] = Path(__file__).resolve()
    for prefix, directory in (('pure', 'cuda-profile-pure-tests01'), ('native', 'cgakt-research-model04'),
                              ('owned', 'cgakt-research-model04-owned')):
        for path in (PREP / directory).iterdir():
            assert path.is_file()
            copies[prefix + '__' + path.name] = path
    inventory = {name: dict(source=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                           sha256=sha(path)) for name, path in copies.items()}
    assert sum(row['bytes'] for row in inventory.values()) < 2 * 1024**2
    if args.dry:
        print(json.dumps(dict(copies=len(copies), outputs=len(copies)+4, inventory=inventory), ensure_ascii=False, indent=2))
        raise SystemExit(0)
    with (PREP / 'cuda_core_cpu_copy_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2)
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(dict.fromkeys(list(copies.values()) + [ROOT / name for name in references]))
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='CUDA_CORE_CPU_COMPATIBILITY_ENGINEERING',
            pure_tests=13, model_tests=26, actual_cuda=False), sources=sources,
            note='# Core CUDA, bằng chứng metadata và CPU\n\n13kiểm thuần metadata và26kiểm mô hình CPU đạt. Có8forward/5backward/0Adam. Actual CUDA, checkpoint schema2 và Main GPU còn phải kiểm. Source trước/sau, logs và allocation được giữ cùng run.\n') as out:
        for name, path in copies.items():
            assert sha(path) == inventory[name]['sha256']
            (out / name).write_bytes(path.read_bytes())
            assert sha(out / name) == sha(path) == inventory[name]['sha256']
        (out / 'copy_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (out / 'reference_inputs.json').write_text(json.dumps(references, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    proof = verify_evidence_bundle(destination)
    assert proof['artifacts'] == len(copies) + 4
    print(json.dumps(dict(**proof, manifest_sha256=sha(destination / 'manifest.json')), ensure_ascii=False))
