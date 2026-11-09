"""Root kiểm dry hoặc áp đúng ba payload GKT, chưa chạy tests/model."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP/'gkt-research-data-apply04'
OLD_INIT = '90c9db6ea986694aa9e5b7a9aa6bf1c54f7afa9f8e449d3a6d30880d24c3a1aa'
PAYLOADS = (
    ('gkt_research_data_candidate01.py', 'src/knowledge_tracing/gkt/research_data.py',
     '1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873'),
    ('gkt_research_data_canonical_test03_final.py', 'tests/gkt/test_research_data.py',
     'e426e42e82c34319ed04214c2248656b08c94e60eaf52579188a22650de41b89'),
    ('gkt_research_package_init03.py', 'src/knowledge_tracing/gkt/__init__.py',
     '80fd45e6176831f00be7496b1549d3a98485d6b1addd26113130e3c1fcd7fd3f'),
)
UNCHANGED = {
    'src/knowledge_tracing/gkt/config.py': '8785a608e017ed4f6f77f8bd027ed3b3ee8a57d6e5b34bbb6d787acd9952c5d2',
    'src/knowledge_tracing/gkt/core.py': '4663e25d158a08d344d2f5f85735d8db927f96e14199b5d16f40b8e32701b3e1',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, raw, *, new=True):
    with path.open('xb' if new else 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    need(path.read_bytes() == raw, 'Readback bytes mismatch '+str(path))


def record(path, value):
    write(path, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == (ROOT/'.venv').resolve(), 'Repository .venv required')
    inventory, buffers = {}, {}
    for source, target, expected in PAYLOADS:
        raw = (PREP/source).read_bytes()
        need(sha(raw) == expected, 'Reviewed payload changed '+source)
        compile(raw, target, 'exec')  # Syntax only, không thực thi import/body.
        buffers[target] = raw
        path = ROOT/target
        need(path.parent.resolve() == path.parent and not path.is_symlink(), 'Physical fixed target')
        before = path.read_bytes() if path.exists() else None
        if target.endswith('/__init__.py'):
            need(before is not None and sha(before) == OLD_INIT, 'Prior public GKT package changed')
        else:
            need(before is None, 'New canonical source must be absent')
        inventory[target] = dict(payload=source, payload_sha256=expected,
            prior_sha256=None if before is None else sha(before), prior_bytes=None if before is None else len(before))
    for path, expected in UNCHANGED.items():
        need(sha((ROOT/path).read_bytes()) == expected, 'Existing core/config changed')
    dry = dict(status='DRY_THREE_REVIEWED_GKT_SOURCES_NOT_APPLIED', files=inventory,
        unchanged=UNCHANGED, apply_directory=str(OUT.relative_to(ROOT)), expected_unittest_methods=20,
        scope_vi='17data cases và3lazy-package unit cases; không fitted/training/numerical change.')
    if not args.apply:
        print(json.dumps(dry, ensure_ascii=False, indent=2)); return
    OUT.mkdir(exist_ok=False)
    record(OUT/'inventory_before_copy.json', dry)
    prior = (ROOT/'src/knowledge_tracing/gkt/__init__.py').read_bytes()
    write(OUT/'before_gkt_init.py', prior)
    need(sha(prior) == OLD_INIT, 'Snapshot before first canonical write')
    try:
        for target, raw in buffers.items():
            path = ROOT/target
            if target.endswith('/__init__.py'):
                temporary = OUT/'prepared_gkt_init.py'
                write(temporary, raw)
                need(sha(path.read_bytes()) == OLD_INIT, 'Initializer changed after snapshot')
                os.replace(temporary, path)
                need(path.read_bytes() == raw, 'Atomic initializer readback')
            else:
                write(path, raw)
        after = {target: sha((ROOT/target).read_bytes()) for target in buffers}
        need(all(after[target] == sha(raw) for target, raw in buffers.items()), 'All canonical copies exact')
        need(all(sha((ROOT/path).read_bytes()) == pin for path, pin in UNCHANGED.items()), 'Core/config after copy')
        record(OUT/'receipt.json', dict(status='APPLIED_THREE_SOURCE_FILES_NOT_RUNTIME_TESTED', files=inventory,
            after_sha256=after, unchanged=UNCHANGED, helper_sha256=sha(Path(__file__).read_bytes()),
            tests_executed=False, automatic_retry=False))
    except BaseException as error:
        record(OUT/'failure.json', dict(error=repr(error), automatic_retry=False, automatic_rollback=False,
            current={target: sha((ROOT/target).read_bytes()) if (ROOT/target).exists() else None for target in buffers}))
        raise
    print(json.dumps(dict(status='APPLIED_THREE_SOURCE_FILES_NOT_RUNTIME_TESTED', after_sha256=after)))


if __name__ == '__main__':
    main()
