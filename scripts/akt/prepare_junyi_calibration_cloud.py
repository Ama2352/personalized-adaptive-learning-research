"""Lập allowlist đầu vào calibration cloud, CLI ghi plan nhỏ ở local.

API ZIP hỗ trợ cloud scratch. Cờ local_input_staging mở riêng vùng runtime
trong repository với trần160MiB để chuyển input, output nghiên cứu giữ ở cloud.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DATA_RUN = 'research_tracking/runs/junyi-calibration-data-20261117-01'
CACHE = 'artifacts/akt/junyi-cohorts/outer4-calibration-full-20261117-01'
EXPORTS = tuple(f'experiments/akt/results/model-export-a{i}-refit-20261114-01' for i in range(4))
SUPPORT_NAMES = {
    'run-manifest.json', 'COMPLETE.json', 'metadata.json', 'INVENTORY.json',
    *(f'inputs/{name}' for name in ('config.json', 'cuda_profile.json', 'epoch_plan.json',
       'selected_index.json', 'lock_file.txt', 'graph.json', 'confidence.json', 'roles.json',
       'encoding90.json', 'encoding90_receipt.json', 'encoding80.json', 'encoding80_receipt.json')),
}


def relative_path(name):
    if not isinstance(name, str):
        raise ValueError('Đường dẫn archive cần chuỗi.')
    path = PurePosixPath(name)
    forbidden = {'private', '.private', '.git', '__pycache__', 'holdout', 'test'}
    if ('\\' in name or ':' in name or len(name) > 240 or any(ord(char) < 32 for char in name)
            or path.is_absolute()
            or not path.parts or '..' in path.parts or str(path) != name
            or any(part.lower() in forbidden for part in path.parts)):
        raise ValueError('Đường dẫn archive vượt allowlist.')
    return path


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def allowed_paths(root):
    root = Path(root)
    names = [path.relative_to(root).as_posix()
             for path in (root / 'src/knowledge_tracing').rglob('*.py')]
    names += [f'{DATA_RUN}/{name}' for name in ('PREPARED.json', 'POPULATION.json')]
    names += [f'{CACHE}/{name}' for name in ('canonical.parquet', 'assignments.parquet', 'manifest.json')]
    names += ['artifacts/bkt_baseline/splits/manifest.json',
              'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
              'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md',
              'scripts/akt/drive_artifact_sink.py', 'scripts/akt/drive_resumable_upload.py']
    for directory in EXPORTS:
        index = json.loads((root / directory / 'MODEL_INDEX.json').read_text(encoding='utf-8'))
        checkpoint = index['checkpoint_file']
        if PurePosixPath(checkpoint).name != checkpoint or not checkpoint.endswith('.pt'):
            raise ValueError('Checkpoint cần basename .pt rõ ràng.')
        names += [f'{directory}/{name}' for name in ('MODEL_INDEX.json', 'SUPPORT.zip', checkpoint)]
    return sorted(set(names))


def build_plan(root, *, max_total_bytes=160 * 1024**2, max_file_bytes=64 * 1024**2):
    root = Path(root).resolve()
    rows = []
    total = 0
    for name in allowed_paths(root):
        relative_path(name)
        path = root / name
        if (not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root)
                or any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                       for p in (path, *path.parents) if p.is_relative_to(root))):
            raise ValueError('Nguồn cần file vật lý trong repository.')
        size = path.stat().st_size
        total += size
        if size > max_file_bytes or total > max_total_bytes:
            raise ValueError('Vượt ngân sách file hoặc tổng byte.')
        rows.append(dict(path=name, bytes=size, sha256=sha256(path)))
    pins = {row['path']: row for row in rows}
    prepared = json.loads((root / DATA_RUN / 'PREPARED.json').read_text(encoding='utf-8'))
    population = json.loads((root / DATA_RUN / 'POPULATION.json').read_text(encoding='utf-8'))
    manifest = json.loads((root / CACHE / 'manifest.json').read_text(encoding='utf-8'))
    if (prepared['status'] != 'FULL_CALIBRATION10_SOURCE_PREPARED'
            or prepared['counts']['targets'] != 1621484 or population['targets'] != 1621484
            or prepared['counts']['learners'] != 15847
            or prepared['manifest_sha256'] != pins[f'{CACHE}/manifest.json']['sha256']
            or any(manifest[key] is not False for key in ('train_events_included',
                'selection_events_included', 'outer_events_included', 'holdout_events_included'))):
        raise ValueError('Calibration source receipt không khớp phạm vi.')
    for name in ('canonical.parquet', 'assignments.parquet'):
        if any(manifest['outputs'][name][key] != pins[f'{CACHE}/{name}'][key] for key in ('bytes', 'sha256')):
            raise ValueError('Calibration cache không khớp manifest.')
    for directory in EXPORTS:
        index = json.loads((root / directory / 'MODEL_INDEX.json').read_text(encoding='utf-8'))
        if (pins[f"{directory}/{index['checkpoint_file']}"]['sha256'] != index['checkpoint_sha256']
                or pins[f'{directory}/SUPPORT.zip']['sha256'] != index['support_sha256']):
            raise ValueError('Portable model index không khớp payload.')
        with zipfile.ZipFile(root / directory / 'SUPPORT.zip') as archive:
            members = archive.infolist()
            if (len({m.filename for m in members}) != len(members)
                    or not {m.filename for m in members}.issubset(SUPPORT_NAMES)
                    or sum(m.file_size for m in members) > 32 * 1024**2):
                raise ValueError('SUPPORT có member ngoài metadata allowlist.')
    return dict(schema='junyi-calibration-cloud-inputs-v1', files=rows, bytes=total,
                targets=1621484, learners=15847, phase='calibration_predict',
                contains_calibration_answers=True, contains_holdout_events=False,
                contains_outer_events=False, upstream=dict(
                    strategy='clone_public_pinned_git_checkout_in_cloud',
                    url='https://github.com/arghosh/AKT.git',
                    commit='01b7e8d7d7c862cabc9467108e3e7f2555653a88',
                    destination='artifacts/akt/dependencies/upstream'),
                gaps=['Root gắn GPU inference worker hiện hành vào image sau source freeze.',
                      'Xác minh Git checkout upstream thật trong cloud trước nạp model.',
                      'Chuyển inputs qua cloud staging theo SHA, chưa upload trong lượt này.'])


def write_archive(root, plan, output, *, max_total_bytes, max_files=256, local_input_staging=False):
    """Stream ZIP theo pin, có vùng staging input local khai báo rõ và hữu hạn."""
    if (type(max_files) is not int or not 1 <= max_files <= 256
            or type(max_total_bytes) is not int or max_total_bytes <= 0):
        raise ValueError('Cần ngân sách byte và số file hữu hạn.')
    if plan.get('schema') != 'junyi-calibration-cloud-inputs-v1':
        raise ValueError('Sai schema input plan.')
    rows = plan['files']
    names = [row['path'] for row in rows]
    if (len(rows) > max_files or len(set(names)) != len(names)
            or sum(row['bytes'] for row in rows) != plan['bytes'] or plan['bytes'] > max_total_bytes):
        raise ValueError('Archive vượt giới hạn hoặc trùng đường dẫn.')
    root = Path(root).resolve()
    if type(local_input_staging) is not bool:
        raise ValueError('Local input staging cần Boolean rõ ràng.')
    local = local_input_staging and root == ROOT.resolve()
    if local_input_staging and not local:
        raise ValueError('Local input staging chỉ dùng repository hiện hành.')
    if not local and not root.is_relative_to(Path('/artifacts').resolve()) and not root.is_relative_to(Path('/tmp').resolve()):
        raise ValueError('ZIP payload chỉ tạo trên cloud Volume hoặc /tmp.')
    output = Path(output).resolve()
    if local and (not output.is_relative_to((ROOT/'artifacts/akt/runtime/calibration-cloud-inputs').resolve())
                  or max_total_bytes > 160*1024**2):
        raise ValueError('Local input ZIP cần vùng staging riêng và trần160MiB.')
    if not local and not output.is_relative_to(Path('/artifacts').resolve()) and not output.is_relative_to(Path('/tmp').resolve()):
        raise ValueError('ZIP output cần cloud Volume hoặc /tmp.')
    allowed = set(allowed_paths(root))
    for row in rows:
        relative_path(row['path'])
        path = root / row['path']
        if (row['path'] not in allowed or path.is_symlink() or not path.resolve().is_relative_to(root)
                or path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']):
            raise ValueError('Input archive khác allowlist/pin.')
    plan_bytes=json.dumps(plan,ensure_ascii=False,indent=2).encode('utf-8')
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for row in rows:
            digest = hashlib.sha256()
            size = 0
            with (root / row['path']).open('rb') as source, archive.open(row['path'], 'w') as member:
                while block := source.read(1024**2):
                    digest.update(block)
                    size += len(block)
                    member.write(block)
            if size != row['bytes'] or digest.hexdigest() != row['sha256']:
                raise ValueError('Input đổi trong lúc ghi archive; giữ ZIP lỗi để rà cloud.')
        archive.writestr('CLOUD_INPUT_PLAN.json', plan_bytes)
    return dict(bytes=output.stat().st_size, sha256=sha256(output), files=len(rows),
                embedded_plan_sha256=hashlib.sha256(plan_bytes).hexdigest(),
                plan_identity_sha256=hashlib.sha256(json.dumps(plan,sort_keys=True,
                    separators=(',',':')).encode()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    args = parser.parse_args()
    destination = args.plan.resolve()
    evidence = ROOT / 'research_tracking/runs/cloud-calibration-inputs-20261117-01'
    if destination.parent != evidence.resolve() or destination.exists():
        parser.error('Plan mới cần nằm đúng bundle cloud-calibration-inputs.')
    plan = build_plan(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(plan, stream, ensure_ascii=False, indent=2)
    print(json.dumps(dict(files=len(plan['files']), bytes=plan['bytes'], plan_sha256=sha256(destination))))


if __name__ == '__main__':
    main()
