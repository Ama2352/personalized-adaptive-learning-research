"""Immutable BATCH2 archive; exact version aliases, no tests/model rerun."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
RUN='akt-research-execution-engineering-20261108-01'


def main():
    inputs={
        'source__config.py':ROOT/'src/knowledge_tracing/akt/config.py',
        'source__research_execution.py':ROOT/'src/knowledge_tracing/akt/research_execution.py',
        'tests__test_research_execution.py':ROOT/'tests/akt/test_research_execution.py',
        'report__akt_research_execution_readiness_20261108.md':ROOT/'research_tracking/reports/akt_research_execution_readiness_20261108.md',
        'CORPUS_SCHEMA_V1.json':PREP/'CORPUS_SCHEMA_V1.json',
        'source__evidence.py':ROOT/'src/knowledge_tracing/evidence.py',
        'pack_evidence.py':Path(__file__).resolve(),
    }
    expected={
        'source__config.py':'beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f',
        'source__research_execution.py':'5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6',
        'tests__test_research_execution.py':'9289f3aa4c8948f3e62344d11f01ea596764f78a42f1e2291aafc92178f72ba4',
        'CORPUS_SCHEMA_V1.json':'ba4a3d8ca412395b4b3841da010c736f1ceac3d5bd1a67e5de87ef7c7287e578',
    }
    for alias,digest in expected.items():assert sha(inputs[alias])==digest
    for p in sorted(PREP.iterdir()):
        if p.is_file() and p.name!='pack_evidence.py':inputs.setdefault('prep__'+p.name,p)
    for trial,total,failures in [('trial01',61,1),('trial02',61,0),('trial03',87,0),('trial04',85,0)]:
        directory=PREP/trial
        xml=ET.parse(directory/'junit.xml').getroot().find('testsuite')
        assert int(xml.attrib['tests'])==total and int(xml.attrib['failures'])==failures
        assert int(xml.attrib['errors'])==int(xml.attrib['skipped'])==0
        receipt=json.loads((directory/'receipt.json').read_bytes())
        assert receipt['source_sha256_before']==receipt['source_sha256_after']
        assert receipt['model_calls']==receipt['optimizer_updates']==receipt['inner_subprocess_calls']==receipt['torch_imports']==0
        assert receipt['cumulative_seconds']<=receipt['cap_seconds']
        for p in sorted(directory.iterdir()):
            if p.is_file():inputs[trial+'__'+p.name]=p
    final=json.loads((PREP/'trial04/receipt.json').read_bytes())
    assert final['cumulative_seconds']==32.357475514666106 and final['cap_seconds']==60
    golden=json.loads((PREP/'legacy-defaults01.json').read_bytes())
    assert golden['status']=='PASS_AST_AND_SERIALIZED_DEFAULTS_IDENTICAL'
    assert golden['default_asdict_sha256']=='f46eb29594ff7a468e2cd7f8d149cc909a8453372701cd68ce216648f1d4f8c5'
    assert sha(PREP/'research_execution.pre-repro.py')=='8a6221b3a7101911ad4a38e937007ef52c57921cba25467ea565f3eadff7cad9'
    assert sha(PREP/'research_execution.pre-junction.py')=='72f5a1e981b63c3edf6ff51013a80c9b5680abe18f98d03e190da0d2ed675e5a'
    before={alias:dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for alias,p in inputs.items()}
    physical={};aliases={};seen={}
    must_copy={'CORPUS_SCHEMA_V1.json','trial04__receipt.json','trial04__junit.xml'}
    for alias,row in before.items():
        destination=alias if row['sha256'] not in seen or alias in must_copy else seen[row['sha256']]
        aliases[alias]=destination
        if destination==alias:physical[alias]=inputs[alias];seen.setdefault(row['sha256'],alias)
    metadata=dict(kind='research-execution-guard-pure-metadata-validation',run_purpose='A0-single-candidate-lifecycle-pilot-contract-only',
        latest_tests=85,latest_failures=0,historical_tests_by_trial=[61,61,87,85],
        historical_failures_by_trial=[1,0,0,0],final_cumulative_seconds=32.357475514666106,cap_seconds=60,
        budget_revision='30to60 by root beforetrial03; prior spending retained',native_gate_runtime='UNIT_MOCKS_NOT_ACTUAL',
        model_calls=0,optimizer_updates=0,corpus_generated=False,execution_performed=False,
        parent_review='source review approved final config/guard and archive; no independent execution',
        external_publisher31='not copied; historicalguard72, not relabeled currentguard5ea3')
    note='# Guard A0 simulator-research — kiểm thuần metadata\n\nFinal85PASS04; old87PASS03 gồm81guard+6legacyconfig, old61PASS02 và60PASS+1fixturefail01 giữ nguyên.\nCumulative32,357475514666106/60s;0Torch/model/optimizer/innerprocess. NativeGate/runtime mocks, không actualexecution/corpus/fittedclaim.\nPlan3keys/provenance16keys sửa criticalrestartgap trướcpublication; nestedjunction portablecanaries, không actualjunction.\nCopyinventory giữ mọi version/source alias trước/sau, dedup byte-identical copies; không sửa sauclosure.\n'
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=list(inputs.values()),note=note) as directory:
        for alias,p in physical.items():
            assert sha(p)==before[alias]['sha256']
            (directory/alias).write_bytes(p.read_bytes())
            assert sha(directory/alias)==before[alias]['sha256']
        after={alias:dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for alias,p in inputs.items()}
        assert before==after
        for alias,destination in aliases.items():assert sha(directory/destination)==before[alias]['sha256']
        (directory/'copy_inventory.json').write_text(json.dumps(dict(inputs_before=before,inputs_after=after,
            aliases_to_bundle_members=aliases,selected_aliases=len(inputs),physical_copies=len(physical)),indent=2)+'\n',encoding='utf-8')
    verified=verify_evidence_bundle(directory)
    manifest=json.loads((directory/'manifest.json').read_bytes())
    assert {p.name for p in directory.iterdir()}==set(manifest['outputs_sha256'])|{'manifest.json'}
    for name in must_copy|{'copy_inventory.json'}:assert (directory/name).is_file()
    result=dict(bundle=str(directory),manifest_sha256=sha(directory/'manifest.json'),verification=verified,
        outputs=len(manifest['outputs_sha256']),files=len(manifest['outputs_sha256'])+1,
        input_aliases=len(inputs),physical_copies=len(physical),
        report_sha256=sha(inputs['report__akt_research_execution_readiness_20261108.md']))
    (PREP/'closure-verification.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2)+'\n')
    (PREP/'force_add_paths.txt').open('x',encoding='utf-8').write('\n'.join(p.relative_to(ROOT).as_posix() for p in sorted(directory.iterdir()))+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
