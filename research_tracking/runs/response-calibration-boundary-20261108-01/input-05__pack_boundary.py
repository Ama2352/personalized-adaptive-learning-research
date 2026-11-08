"""Đóng bundle nhỏ đã được parent cho phép; không chạy lại kiểm thử."""
import collections
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    run_id = 'response-calibration-boundary-20261108-01'
    report = ROOT/'research_tracking/reports/response_calibration_boundary_20261108.md'
    assert not report.exists()
    report.write_bytes((PREP/'README.md').read_bytes())
    counts = dict(collections.Counter(node.attrib['classname'] for node in ET.parse(
        PREP/'trial02-green/pytest.xml').iter('testcase')))
    assert counts == {'tests.shared_kt.test_response_calibration':43,
                      'tests.shared_kt.test_reference_controller':24}
    selected = [report, PREP/'README.md', PREP/'run_boundary.py', PREP/'verify_boundary.py',
                Path(__file__).resolve(), PREP/'budget.json', PREP/'final-verification.json']
    for folder in ['before','after','trial01-red/source-before','trial02-green/source-before']:
        selected.extend(sorted((PREP/folder).iterdir()))
    for trial in ['trial01-red','trial02-green']:
        selected.extend(PREP/trial/name for name in ['pytest.log','pytest.xml','run.json'])
    assert all(p.is_file() and not p.is_symlink() for p in selected)
    records = [dict(source=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size,
                    sha256_before_copy=sha(p)) for p in selected]
    original_sources = [ROOT/'src/knowledge_tracing/response_calibration.py',
                        ROOT/'tests/shared_kt/test_response_calibration.py']
    sources = list(dict.fromkeys([*selected,*original_sources]))
    os.environ.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory', GIT_CONFIG_VALUE_0=str(ROOT))
    with record_evidence_run(ROOT, run_id,
        metadata=dict(kind='local-synthetic-calibration-boundary-engineering',
                      red_tests=4, red_failures=4, green_tests=67, green_failures=0,
                      green_classname_counts=counts, controller_seconds=1.9824764999793842,
                      controller_budget_seconds=30, optimizer_steps=0, neural_network_calls=0,
                      remote_calls=0, source_scope='two calibration files only'),
        sources=sources,
        note='# Sửa ranh giới response calibration\n\n4FAIL nguồn cũ→67PASS nguồn mới, gồm43calibration+24controller. Chỉ fixture scalar tổng hợp;0NN/optimizer/remote, không nghiên cứu trên corpus. Giữ nguyên logs và snapshots; copy inventory ghi aliases và SHA trước/sau. Không sửa bundle cũ. Manifest completed là integrity closure; không phải research/RQ PASS.\n') as bundle:
        copied = {}
        for index,(path,row) in enumerate(zip(selected,records),1):
            digest=row['sha256_before_copy']
            if digest not in copied:
                destination=bundle/f'input-{index:02d}__{path.name}'
                with destination.open('xb') as handle:
                    handle.write(path.read_bytes())
                copied[digest]=destination
            destination=copied[digest]
            row.update(destination=destination.name, sha256_after_copy=sha(destination),
                       source_sha256_after_copy=sha(path))
            assert row['sha256_before_copy']==row['sha256_after_copy']==row['source_sha256_after_copy']
        with (bundle/'copy-inventory.json').open('x',encoding='utf-8') as handle:
            json.dump(dict(aliases=len(records),unique_copies=len(copied),copies=records,
                           green_classname_counts=counts),handle,ensure_ascii=False,indent=2)
            handle.write('\n')
    verification=verify_evidence_bundle(bundle)
    closure=dict(**verification,bundle=bundle.relative_to(ROOT).as_posix(),
                 manifest_sha256=sha(bundle/'manifest.json'),report_sha256=sha(report),
                 input_aliases=len(records),unique_copies=len(copied),
                 physical_files=len(list(bundle.iterdir())))
    with (PREP/'closure.json').open('x',encoding='utf-8') as handle:
        json.dump(closure,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(json.dumps(closure))
