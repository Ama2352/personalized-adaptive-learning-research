"""Đóng bằng chứng ledger metadata; không rerun tests/model."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'akt-research-lifecycle-ledger-engineering-20261108-01'
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    trial = PREP/'trial01'
    receipt = json.loads((trial/'receipt.json').read_bytes())
    before_run = json.loads((trial/'sources_before.json').read_bytes())
    assert before_run == json.loads((trial/'sources_after.json').read_bytes())
    assert len(before_run) == 12 and all(sha(ROOT/name) == digest for name, digest in before_run.items())
    suites = list(ET.parse(trial/'junit.xml').getroot().iter('testsuite'))
    counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    assert counts == receipt['counts'] == dict(tests=45, failures=0, errors=0, skipped=0)
    assert receipt['status'] == 'PASS_PURE_METADATA_NOT_EXECUTION_PROOF'
    assert receipt['controller_elapsed_seconds'] == 0.7860216999542899
    assert all(receipt[k] == 0 for k in ('neural_calls','optimizer_steps','corpus_reads','subprocess_calls'))
    parent = json.loads((PREP/'parent-execution-reference.json').read_bytes())
    assert parent['actual_tool_wall_seconds'] == 1.2566407 < 20
    pins = {'src/knowledge_tracing/akt/research_lifecycle.py':'7a00442d39dd6bb82b4eb5af57b6de2cfa46057ac147d0230bf926d673d1b85b',
            'tests/akt/test_research_lifecycle.py':'14b02640009d9e0f1d0fe01bc3249eb11cb72d0f27b0d50aca4056db2a9668bd'}
    assert all(sha(ROOT/name) == digest for name,digest in pins.items())
    assert sha(PREP/'run_pure01.py') == parent['controller_sha256']
    inputs = {'report__akt_research_lifecycle_ledger_readiness_20261108.md':
                  ROOT/'research_tracking/reports/akt_research_lifecycle_ledger_readiness_20261108.md',
              'contract__22_A0_RESEARCH_LIFECYCLE_CONTRACT.md':ROOT/'docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md',
              'source__evidence.py':ROOT/'src/knowledge_tracing/evidence.py',
              'pack_evidence.py':Path(__file__).resolve(),
              'run_pure01.py':PREP/'run_pure01.py',
              'parent-execution-reference.json':PREP/'parent-execution-reference.json'}
    for index,(name,digest) in enumerate(before_run.items()):
        # JSON uses sorted keys; snapshot index uses controller SOURCES order. Match by bytes/name.
        inputs['current__'+name.replace('/','__')] = ROOT/name
    for path in sorted(trial.rglob('*')):
        if path.is_file():
            inputs['trial01__'+path.relative_to(trial).as_posix().replace('/','__')] = path
    before = {alias:dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)
              for alias,path in inputs.items()}
    physical = {}; aliases = {}; seen = {}
    for alias,row in before.items():
        destination = seen.setdefault(row['sha256'], alias)
        aliases[alias] = destination
        if alias == destination:
            physical[alias] = inputs[alias]
    metadata = dict(kind='akt-research-lifecycle-ledger-pure-engineering', tests=45, failures=0,
        execution_scope='metadata consistency only; not trainer/current Gate/authorization proof',
        controller_elapsed_seconds=receipt['controller_elapsed_seconds'],
        parent_tool_wall_seconds=parent['actual_tool_wall_seconds'], cumulative_cap_seconds=20,
        timer='18s GIL-dependent daemon; not hard OS quota', neural_calls=0,optimizer_steps=0,
        corpus_reads=0,actual_fit=False,parent_review='Root source review and actual one controller run')
    note = '# Ledger lifecycle A0 — engineering metadata\n\n45PASS,0NN/optimizer/corpus/test-subprocess; controller0,7860217s/toolwall1,2566407s/20.\nKhông trainer/currentGate/fitted research; clocks và ledgerhead do caller hợp tác.\nTimer18s phụ thuộcGIL; không native owned-process proof. Exact SHA copies/inventory trước=sau.\n'
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=list(inputs.values()),note=note) as directory:
        for alias,path in physical.items():
            assert sha(path) == before[alias]['sha256']
            (directory/alias).write_bytes(path.read_bytes())
            assert sha(directory/alias) == before[alias]['sha256']
        after = {alias:dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)
                 for alias,path in inputs.items()}
        assert before == after
        assert all(sha(directory/target) == before[alias]['sha256'] for alias,target in aliases.items())
        (directory/'copy_inventory.json').write_text(json.dumps(dict(inputs_before=before,inputs_after=after,
            aliases_to_bundle_members=aliases,physical_copies=len(physical)),indent=2)+'\n',encoding='utf-8')
    verified = verify_evidence_bundle(directory)
    manifest = json.loads((directory/'manifest.json').read_bytes())
    assert {p.name for p in directory.iterdir()} == set(manifest['outputs_sha256'])|{'manifest.json'}
    for name in ('trial01__receipt.json','trial01__junit.xml','copy_inventory.json'):
        assert (directory/name).is_file()
    result = dict(bundle=str(directory),manifest_sha256=sha(directory/'manifest.json'),verification=verified,
        outputs=len(manifest['outputs_sha256']),files=len(manifest['outputs_sha256'])+1,
        input_aliases=len(inputs),physical_copies=len(physical),
        report_sha256=sha(inputs['report__akt_research_lifecycle_ledger_readiness_20261108.md']))
    (PREP/'closure-verification.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2)+'\n')
    (PREP/'force_add_paths.txt').open('x',encoding='utf-8').write('\n'.join(p.relative_to(ROOT).as_posix() for p in sorted(directory.iterdir()))+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
