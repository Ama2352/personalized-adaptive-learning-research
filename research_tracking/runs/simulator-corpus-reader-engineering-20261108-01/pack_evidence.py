"""Archive reader bốn lượt, không rerun; giữ raw failure và fixture/time scope."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
RUN='simulator-corpus-reader-engineering-20261108-01'
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    final=json.loads((PREP/'trial04/receipt.json').read_bytes())
    final_sources=json.loads((PREP/'trial04/sources_before.json').read_bytes())
    assert final_sources==json.loads((PREP/'trial04/sources_after.json').read_bytes())
    assert len(final_sources)==12 and all(sha(ROOT/name)==digest for name,digest in final_sources.items())
    assert final_sources['src/knowledge_tracing/simulator_corpus_reader.py']=='e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90'
    assert final_sources['tests/shared_kt/test_simulator_corpus_reader.py']=='b92ecab03a1bbcef58406cd6e3cf53628a76181511497a446ee9c44753e0e2fb'
    suites=list(ET.parse(PREP/'trial04/junit.xml').getroot().iter('testsuite'))
    counts={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    assert counts==final['counts']==dict(tests=47,failures=0,errors=0,skipped=0)
    assert final['status']=='PASS_READER_WITH_EXPLICIT_PLATFORM_FIXTURE_NOT_RUNTIME'
    assert final['cumulative_seconds']==49.10621936238428<90 and final['controller_elapsed_seconds']==18.043351400003303
    assert final['denied_process_events']==0 and not final['torch_imported']
    assert all(final[k]==0 for k in ('model_calls','optimizer_updates','teacher_collection_calls','subprocess_calls'))
    fixture=json.loads((PREP/'trial04/platform-fallback-fixture.json').read_bytes())
    assert fixture==final['platform_metadata_fixture'] and fixture['platform_version']==[10,0,26100]
    assert fixture['platform_module_sha256']=='e398f1c9a6581395534242c9d256997ba8921602bb50f21d63ea5999cd800482'
    old=json.loads((PREP/'trial01/receipt.json').read_bytes())
    assert old['counts'] is None and old['exit_code'] is None and not (PREP/'trial01/junit.xml').exists()
    assert old['source_sha256_before']==old['source_sha256_after']==final_sources
    assert (PREP/'trial02/junit.xml').stat().st_size==38 and (PREP/'trial03/junit.xml').stat().st_size==38
    old03=json.loads((PREP/'trial03/receipt.json').read_bytes())
    assert old03['counts'] is None and old03['denied_process_events']==2 and old03['junit_parse_error']
    assert not (PREP/'trial02/receipt.json').exists()
    root04=json.loads((PREP/'reader04-root-observation.json').read_bytes())
    assert root04['whole_external_elapsed_seconds'] is None and root04['tool_terminal_exit_code']==0
    inputs={}
    for trial in ('trial01','trial02','trial03','trial04'):
        directory=PREP/trial
        if trial!='trial01':
            assert json.loads((directory/'sources_before.json').read_bytes())==json.loads((directory/'sources_after.json').read_bytes())==final_sources
        # Chỉ top-level raw và source_snapshots; tuyệt đối không copy tmp corpus/oracle.
        for path in sorted(directory.iterdir()):
            if path.is_file():inputs[trial+'__'+path.name]=path
        snapshots=directory/'source_snapshots'
        if snapshots.is_dir():
            for path in sorted(snapshots.iterdir()):
                assert path.is_file()
                inputs[trial+'__source_snapshots__'+path.name]=path
    for index in range(1,5):
        inputs[f'run_pure0{index}.py']=PREP/f'run_pure0{index}.py'
    for name in ('reader02-root-observation.json','reader03-root-observation.json','reader04-root-observation.json','reader02_diagnosis.md'):
        inputs[name]=PREP/name
    for name in final_sources:
        inputs['current__'+name.replace('/','__')]=ROOT/name
    report=ROOT/'research_tracking/reports/simulator_corpus_reader_readiness_20261108.md'
    inputs.update({'report__simulator_corpus_reader_readiness_20261108.md':report,
                   'source__evidence.py':ROOT/'src/knowledge_tracing/evidence.py','pack_evidence.py':Path(__file__).resolve()})
    before={alias:dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size) for alias,path in inputs.items()}
    physical={};aliases={};seen={}
    for alias,row in before.items():
        force=alias.endswith(('.log','.xml','receipt.json'))
        destination=alias if force else seen.get(row['sha256'],alias)
        aliases[alias]=destination
        if destination==alias:
            physical[alias]=inputs[alias];seen.setdefault(row['sha256'],alias)
    metadata=dict(kind='public-simulator-corpus-reader-fixture-engineering',latest_tests=47,latest_failures=0,
        trial_status=['UNKNOWN_TIMEOUT_NO_JUNIT','COLLECTION_ERROR_LOST_TRACE','METADATA_SUBPROCESS_AUDIT_DENIAL','PASS_WITH_PLATFORM_FIXTURE'],
        cumulative_recorded_seconds=49.10621936238428,cap_seconds=90,
        budget_revision='Root30to90; old charge retained; controller04 timing not whole external duration',
        whole_external_duration04=None,terminal04='Root same exec session18689 polled toRC0',
        platform_fixture='TEST_ONLY_sys.getwindowsversion.platform_version10.0.26100; no library edits',
        model_calls=0,optimizer_updates=0,actual_corpus=False,actual_runtime_gate=False,
        parent_review='Root full source/test review and actual controller runs; no extra rerun')
    note='# Reader corpus public — engineering với fixture\n\n47PASS04; giữ nguyên raw UNKNOWN01, lỗi02 và metadata bị audit chặn03.\nFallback Windows metadata chỉ dành cho test; không Torch/teacher/model/optimizer hoặc child được launch thành công.\nCộng dồn ghi được49,10621936/90s; wholeouter04chưa đo, không cộng các đoạn đợi thành wholewall.\nKhông actualcorpus/runtimeGate/GPU/trainer; copies/SHA trước=sau, không sửa sauclosure.\n'
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=list(inputs.values()),note=note) as directory:
        for alias,path in physical.items():
            assert sha(path)==before[alias]['sha256']
            (directory/alias).write_bytes(path.read_bytes())
            assert sha(directory/alias)==before[alias]['sha256']
        after={alias:dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size) for alias,path in inputs.items()}
        assert before==after
        assert all(sha(directory/target)==before[alias]['sha256'] for alias,target in aliases.items())
        (directory/'copy_inventory.json').write_text(json.dumps(dict(inputs_before=before,inputs_after=after,
            aliases_to_bundle_members=aliases,physical_copies=len(physical)),indent=2)+'\n',encoding='utf-8')
    verified=verify_evidence_bundle(directory)
    manifest=json.loads((directory/'manifest.json').read_bytes())
    assert {p.name for p in directory.iterdir()}==set(manifest['outputs_sha256'])|{'manifest.json'}
    for name in ('trial04__junit.xml','trial04__receipt.json','reader04-root-observation.json','copy_inventory.json'):
        assert (directory/name).is_file()
    result=dict(bundle=str(directory),manifest_sha256=sha(directory/'manifest.json'),verification=verified,
        outputs=len(manifest['outputs_sha256']),files=len(manifest['outputs_sha256'])+1,input_aliases=len(inputs),
        physical_copies=len(physical),report_sha256=sha(report))
    (PREP/'closure-verification.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2)+'\n')
    files=[p.relative_to(ROOT).as_posix() for p in sorted(directory.iterdir())]
    (PREP/'force_add_paths.txt').open('x',encoding='utf-8').write('\n'.join(files)+'\n')
    (PREP/'force_add_log_paths.txt').open('x',encoding='utf-8').write('\n'.join(p for p in files if p.endswith(('.log','.xml')))+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
