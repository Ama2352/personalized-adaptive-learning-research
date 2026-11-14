"""Kiểm inventory và checkout AKT trong snapshot thật trước cấp GPU."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments/akt')]
from junyi_staged_io import verify_project
from knowledge_tracing.akt.provenance import verify_upstream


def main():
    variant = sys.argv[1].lower()
    if variant not in ('a2', 'a3'):
        raise ValueError('Chỉ kiểm snapshot A2/A3')
    version = sys.argv[2] if len(sys.argv)>2 else '02'
    assert version in ('02','03')
    snapshot = ROOT / f'artifacts/akt/staged/junyi-{variant}-expert-20261114-{version}'
    source = snapshot / 'project/artifacts/akt/dependencies/upstream'
    os.environ.update(GIT_OPTIONAL_LOCKS='0', GIT_CONFIG_COUNT='3',
                      GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false',
                      GIT_CONFIG_KEY_1='safe.directory', GIT_CONFIG_VALUE_1=str(source),
                      GIT_CONFIG_KEY_2='core.autocrlf', GIT_CONFIG_VALUE_2='false')
    before = verify_project(snapshot)
    identity = verify_upstream(source, '01b7e8d7d7c862cabc9467108e3e7f2555653a88')
    toplevel = subprocess.check_output(['git', '-C', str(source), 'rev-parse', '--show-toplevel'], text=True).strip()
    assert Path(toplevel).resolve() == source.resolve()
    expected = json.loads((HERE / 'upstream-portable-inventory.json').read_text())
    assert identity == expected['identity']
    assert verify_project(snapshot) == before
    result = dict(status='PASS_SNAPSHOT_DEPENDENCY_AND_INVENTORY', variant=variant.upper(),
                  snapshot=str(snapshot.relative_to(ROOT)), files=len(before['files']),
                  dependency=identity, inventory_unchanged=True, gpu_started=False)
    output = HERE / f'{variant}-snapshot-dependency-verification{version}.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
