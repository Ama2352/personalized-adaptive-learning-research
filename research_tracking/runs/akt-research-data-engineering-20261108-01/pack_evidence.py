"""Archive BATCH1 only; dedup exact bytes, preserve both attempts, no reruns."""
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
RUN='akt-research-data-engineering-20261108-01'


def main():
    inputs={
        'source__research_simulator_data.py':ROOT/'src/knowledge_tracing/akt/research_simulator_data.py',
        'tests__test_research_simulator_data.py':ROOT/'tests/akt/test_research_simulator_data.py',
        'historical__test_research_simulator_data_trial01.py':PREP/'trial01/11-test_research_simulator_data.py.before',
        'report__akt_research_data_readiness_20261108.md':ROOT/'research_tracking/reports/akt_research_data_readiness_20261108.md',
        'READINESS.md':PREP/'READINESS.md', 'run_pure01.py':PREP/'run_pure01.py', 'run_pure02.py':PREP/'run_pure02.py',
        'parent-review-message.md':PREP/'parent-review-message.md', 'pack_evidence.py':Path(__file__).resolve(),
        'source__evidence.py':ROOT/'src/knowledge_tracing/evidence.py',
    }
    expected={
        'source__research_simulator_data.py':'9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b',
        'tests__test_research_simulator_data.py':'bee16620e1bdc2c98dd66e65b2ddddd82160098582b83b53a34120b50fb3645b',
        'historical__test_research_simulator_data_trial01.py':'b965cf2352716bd259a9206f043a1d08747b64592615ba52c9c53b01201fe577',
    }
    for alias,digest in expected.items():assert sha(inputs[alias])==digest
    for trial,passed,failed in [('trial01',24,1),('trial02',25,0)]:
        directory=PREP/trial
        xml=ET.parse(directory/'junit.xml').getroot().find('testsuite')
        assert int(xml.attrib['tests'])==passed+failed and int(xml.attrib['failures'])==failed
        assert int(xml.attrib['errors'])==int(xml.attrib['skipped'])==0
        receipt=json.loads((directory/'receipt.json').read_bytes())
        assert receipt['source_sha256_before']==receipt['source_sha256_after']
        assert receipt['neural_model_calls']==receipt['optimizer_updates']==0
        assert receipt['cumulative_seconds']<=30
        for p in sorted(directory.iterdir()):
            if p.is_file():inputs[trial+'__'+p.name]=p
    before={alias:dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for alias,p in inputs.items()}
    # Stable aliases with public report links remain physical copies even at equal SHA.
    physical={};destinations={};seen={}
    must_copy={'trial01__receipt.json','trial02__receipt.json','trial02__junit.xml'}
    for alias,row in before.items():
        key=row['sha256']
        destination=alias if key not in seen or alias in must_copy else seen[key]
        destinations[alias]=destination
        if destination==alias:physical[alias]=inputs[alias];seen.setdefault(key,alias)
    note='# AKT research data BATCH1 — dữ liệu/geometry\n\nGiữ nguyên25PASS02,24PASS+1fixturefailure01;0model/optimizer;3,520126804127358s/30.\nFixture protocolSHA giả không execution authority. Actualrunner còn phải kiểm docs21bytes/protocol/G_env/recipe crossroles.\nSHA aliases trong copy_inventory.json giữ mọi input và snapshot trước/sau, byte-identical snapshots được dedup.\nKhông trainer/refit/calibration/Gate hoặc fittedresearchclaim. Không sửa sauclosure.\n'
    metadata=dict(kind='research-data-geometry-software-validation',trial01_tests=25,trial01_passed=24,
        trial01_failures=1,trial02_tests=25,trial02_passed=25,neural_model_calls=0,optimizer_updates=0,
        cumulative_seconds=3.520126804127358,execution_authority=False,generated_research_corpus=False,
        parent_review='message-derived source review, no independent execution')
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=list(inputs.values()),note=note) as output:
        for alias,p in physical.items():
            assert sha(p)==before[alias]['sha256']
            (output/alias).write_bytes(p.read_bytes())
            assert sha(output/alias)==before[alias]['sha256']
        after={alias:dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for alias,p in inputs.items()}
        assert before==after
        for alias,destination in destinations.items():
            assert sha(output/destination)==before[alias]['sha256']
        inventory=dict(inputs_before=before,inputs_after=after,aliases_to_bundle_members=destinations,
                       selected_aliases=len(inputs),physical_copies=len(physical),all_copy_hashes_verified=True)
        (output/'copy_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    verified=verify_evidence_bundle(output)
    manifest=json.loads((output/'manifest.json').read_bytes())
    actual={p.name for p in output.iterdir()}
    assert actual==set(manifest['outputs_sha256'])|{'manifest.json'}
    for name in must_copy|{'copy_inventory.json'}:assert (output/name).is_file()
    result=dict(bundle=str(output),manifest_sha256=sha(output/'manifest.json'),verification=verified,
        files=len(actual),outputs=len(manifest['outputs_sha256']),input_aliases=len(inputs),physical_copies=len(physical),
        report_sha256=sha(inputs['report__akt_research_data_readiness_20261108.md']))
    (PREP/'closure-verification.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2)+'\n')
    (PREP/'force_add_paths.txt').open('x',encoding='utf-8').write('\n'.join(p.relative_to(ROOT).as_posix() for p in sorted(output.iterdir()))+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
