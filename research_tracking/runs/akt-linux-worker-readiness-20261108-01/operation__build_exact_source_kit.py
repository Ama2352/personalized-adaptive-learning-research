"""Build local exact-source kit; no model/tests/network/install or Git execution."""
from pathlib import Path
import hashlib
import json
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.akt.authorization import gate2_build_hashes

MAX_FILE = 1024**2
MAX_TOTAL = 8 * 1024**2
MAX_ARCHIVE = 4 * 1024**2
LINUX_SHA = '60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a'
LINUX_MEMBER = 'artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt'
FORBIDDEN = {'.git', '.venv', 'venv', '.wsl', 'dataset', '__pycache__', 'private', '.aws', '.ssh'}
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def safe_source(path):
    path = Path(path)
    assert path.is_file() and path.resolve().is_relative_to(ROOT)
    relative = path.relative_to(ROOT)
    assert not FORBIDDEN.intersection(part.casefold() for part in relative.parts)
    assert path.suffix.lower() not in {'.pt', '.parquet', '.zip', '.whl', '.dll', '.pyd', '.so'}
    for parent in [path, *path.parents]:
        if parent == ROOT:
            break
        assert not parent.is_symlink() and not parent.is_junction()
    assert path.stat().st_size <= MAX_FILE
    return path


gate_before = gate2_build_hashes()
paths = {ROOT / name for name in gate_before}
paths.update((ROOT / 'src/knowledge_tracing').rglob('*.py'))
for folder in ['tests/akt', 'tests/shared_kt', 'scripts/akt', 'scripts/research']:
    paths.update((ROOT / folder).rglob('*.py'))
for name in ['pyproject.toml', 'requirements-akt.in', 'requirements-akt.lock.txt',
             'experiments/akt/configs/smoke.json', 'experiments/akt/configs/pilot.json',
             'experiments/akt/configs/fold0.json', 'conftest.py', 'tests/conftest.py',
             'tests/akt/conftest.py', 'tests/shared_kt/conftest.py', 'tests/__init__.py',
             'scripts/__init__.py', 'scripts/akt/__init__.py', 'scripts/research/__init__.py']:
    if (ROOT / name).is_file():
        paths.add(ROOT / name)
mapping = {path.relative_to(ROOT).as_posix(): safe_source(path) for path in sorted(paths)}
linux = ROOT / 'research_tracking/runs/akt-linux-dependency-resolution-20261108-01/candidate-linux-cuda.lock.txt'
mapping[LINUX_MEMBER] = safe_source(linux)
payloads = {name: path.read_bytes() for name, path in mapping.items()}
assert sha(payloads[LINUX_MEMBER]) == LINUX_SHA
assert len(payloads) + 1 <= 256 and sum(map(len, payloads.values())) <= MAX_TOTAL
assert {name: sha(payloads[name]) for name in gate_before} == gate_before
before = [{'source': path.relative_to(ROOT).as_posix(), 'member': name, 'bytes': len(payloads[name]),
           'source_sha256_before': sha(payloads[name])} for name, path in mapping.items()]
manifest = {
    'schema_version': 1, 'kind': 'EXACT_UNTRANSFORMED_LINUX_CPU_WORKER_SOURCE_KIT',
    'scope': 'source transport only; no installed runtime, Gate acceptance, model or GPU execution',
    'files': {name: {'bytes': len(raw), 'sha256': sha(raw)} for name, raw in payloads.items()},
    'gate2_build_hashes': gate_before,
    'notebook_transform': 'NONE; preserve every source/output/metadata byte',
    'linux_lock_source': linux.relative_to(ROOT).as_posix(), 'linux_lock_member': LINUX_MEMBER,
    'linux_lock_sha256': LINUX_SHA,
    'upstream_strategy': {
        'included_git_metadata': False,
        'future_public_url': 'https://github.com/arghosh/AKT.git',
        'required_commit': '01b7e8d7d7c862cabc9467108e3e7f2555653a88',
        'required_path': 'artifacts/akt/dependencies/upstream',
        'acceptance': 'bounded public clone/fetch separately; actual clean checkout and verify_upstream required; no synthetic Git metadata',
    },
    'missing_conftests': [name for name in ['conftest.py', 'tests/conftest.py', 'tests/akt/conftest.py',
                         'tests/shared_kt/conftest.py'] if not (ROOT / name).exists()],
    'caps': {'members': 256, 'member_bytes': MAX_FILE, 'total_payload_bytes': MAX_TOTAL,
             'compressed_archive_bytes': MAX_ARCHIVE},
}
manifest_raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
assert len(manifest_raw) <= MAX_FILE and sum(map(len, payloads.values())) + len(manifest_raw) <= MAX_TOTAL
archive = OUT / 'exact-linux-cpu-source-kit.zip'
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as target:
    for name, raw in payloads.items():
        info = zipfile.ZipInfo(name, date_time=(2026, 11, 8, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        target.writestr(info, raw)
    target.writestr('KIT_MANIFEST.json', manifest_raw)
assert archive.stat().st_size <= MAX_ARCHIVE
after = []
with zipfile.ZipFile(archive) as check:
    assert len(check.namelist()) == len(set(check.namelist())) == len(payloads) + 1
    for item in before:
        current = mapping[item['member']].read_bytes()
        copied = check.read(item['member'])
        assert current == payloads[item['member']] == copied
        after.append({**item, 'source_sha256_after': sha(current), 'archived_sha256': sha(copied), 'exact_match': True})
    assert check.read('KIT_MANIFEST.json') == manifest_raw
assert gate2_build_hashes() == gate_before
for name, value in [('source-manifest.json', manifest), ('copy-inventory-before.json', before),
                    ('copy-inventory-after.json', after)]:
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
result = {'status': 'LOCAL_SOURCE_ARCHIVE_VERIFIED_NOT_EXECUTED_REMOTELY',
          'archive': str(archive), 'archive_sha256': sha(archive.read_bytes()),
          'archive_bytes': archive.stat().st_size, 'payload_files': len(payloads),
          'archive_members_including_manifest': len(payloads) + 1,
          'payload_bytes': sum(map(len, payloads.values())), 'gate_paths': len(gate_before),
          'manifest_sha256': sha(manifest_raw), 'all_source_pre_post_and_zip_sha_match': True,
          'source_or_Gate_or_runtime_changes': False, 'upstream_clone_still_required': True}
with (OUT / 'build-verification.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result, indent=2))
