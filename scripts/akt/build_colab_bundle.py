"""Đóng gói allowlist source và synthetic tests cho notebook Colab."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    allowed = (ROOT / 'artifacts/akt/colab').resolve()
    if not output.is_relative_to(allowed) or output.suffix != '.zip':
        parser.error('output must be a new .zip under artifacts/akt/colab')
    paths = sorted((ROOT / 'src/knowledge_tracing').rglob('*.py'))
    paths += sorted((ROOT / 'tests/akt').glob('*.py'))
    paths += sorted((ROOT / 'tests/shared_kt').glob('*.py'))
    paths += [ROOT / 'scripts/akt/synthetic_device_probe.py', ROOT / 'scripts/akt/check_runtime.py']
    paths += [ROOT / 'experiments/akt/configs' / name for name in ('smoke.json', 'pilot.json', 'fold0.json')]
    contents = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in paths}
    manifest = {'schema_version': 1, 'scope': 'source_and_synthetic_tests_only',
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
        archive.writestr('BUNDLE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(json.dumps({'bundle': str(output), 'files': len(contents), 'sha256': digest}))


if __name__ == '__main__':
    main()
