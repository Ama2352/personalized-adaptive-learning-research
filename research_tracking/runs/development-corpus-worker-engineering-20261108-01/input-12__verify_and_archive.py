"""ROOT-ONLY: metadata/hash closure; không tests/native/corpus/model."""
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def dump(path,value):
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')
def counts(path):
    suites=list(ET.parse(path).getroot().iter('testsuite'))
    return {k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}

if __name__=='__main__':
    first=load(PREP/'trial01/run.json');second=load(PREP/'trial02/run.json')
    assert counts(PREP/'trial01/pytest.xml')==dict(tests=19,failures=0,errors=19,skipped=0)
    assert counts(PREP/'trial02/pytest.xml')==dict(tests=19,failures=0,errors=0,skipped=0)==second['counts']
    assert first['returncode']==1 and first['controller_seconds']==1.2762708999798633
    assert second['returncode']==0 and second['controller_seconds']==2.531903400027659
    assert second['status']=='PASS_PURE_DRIVER_ORCHESTRATION_MOCKS_NOT_ACTUAL_CORPUS'
    assert second['cumulative_seconds']==first['controller_seconds']+second['controller_seconds']<=20
    assert second['denied_process_events']==0 and second['actual_heavy_modules_loaded']==[]
    assert second['original_pytest_exception'] is None and not second['controller_errors'] and not second['reported_errors']
    for trial,receipt in [('trial01',first),('trial02',second)]:
        assert receipt['source_before_sha256']==receipt['source_after_sha256']
        for path,digest in receipt['source_before_sha256'].items():
            assert sha(PREP/trial/'source-before'/Path(path).name)==digest
    for path,digest in second['source_after_sha256'].items():assert sha(ROOT/path)==digest
    assert sha(ROOT/'scripts/research/collect_development_corpus.py')=='09c909570e94ecc5bb87fdc7f4e75848fa53b91ea1317ab20a383bac4362e192'
    assert sha(ROOT/'experiments/akt/configs/simulator-research-corpus01.json')=='8e7800482cea61a5f3ab66e4909de996fda57bcc059dd2751c2e4177dbfa263e'
    assert sha(ROOT/'tests/shared_kt/test_development_corpus_worker.py')=='f2d80a0a2e29f86bc42d8ccc68d8e1709f8d7202f16723697a803d36c959fbb0'
    assert sha(PREP/'run_pure02.py')=='2d82045441889d837e80c55df670475578ac238d7c970e34ef9cc24b8e87fefb'
    lengths=load(PREP/'planned-path-lengths03.json')
    assert lengths['max_full_path_characters']==189 and lengths['path_count']==29
    assert max(r['characters'] for r in lengths['paths'])==189
    fixture=load(PREP/'trial02/platform-fallback-fixture.json')
    assert fixture['patched_symbol']=='platform._syscmd_ver' and fixture['actual_value_source']=='sys.getwindowsversion().platform_version'
    assert fixture['production_library_files_edited'] is False and fixture['architecture_patched'] is False
    dispatch=PREP/'root_trial02_dispatch.json'
    assert dispatch.is_file() and dispatch.stat().st_size<=128*1024
    json.loads(dispatch.read_bytes())
    proof=dict(status='VERIFIED_DRIVER_ORCHESTRATION_STUBS_NOT_ACTUAL_CORPUS',
        trial01_setup_errors=19,trial01_test_bodies=0,trial02_passed=19,prior_seconds=first['controller_seconds'],
        controller02_seconds=second['controller_seconds'],cumulative_seconds=second['cumulative_seconds'],cap_seconds=20,
        driver_config_unchanged=True,trial02_audit_denials=0,trial02_heavy_modules=[],
        firsttrial_process_absence_not_globally_audited=True,manufactured12600_counts_not_native=True,root_only_execution=True)
    dump(PREP/'final-verification.json',proof)
    selected=[ROOT/'tests/shared_kt/test_development_corpus_worker.py',ROOT/'scripts/research/collect_development_corpus.py',
        ROOT/'experiments/akt/configs/simulator-research-corpus01.json',
        ROOT/'research_tracking/reports/development_corpus_worker_readiness_20261108.md',
        PREP/'run_pure.py',PREP/'run_pure02.py',PREP/'planned-path-lengths02.json',PREP/'planned-path-lengths03.json',
        PREP/'budget.json',dispatch,PREP/'final-verification.json',Path(__file__)]
    for trial in ('trial01','trial02'):
        folder=PREP/trial
        selected.extend(p for p in sorted(folder.iterdir()) if p.is_file())
        selected.extend(sorted((folder/'source-before').iterdir()))
    assert all(p.is_file() and not p.is_symlink() for p in selected)
    inventory=[dict(source=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256_before_copy=sha(p)) for p in selected]
    dump(PREP/'copy-inventory-before.json',dict(inputs=inventory))
    os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=str(ROOT))
    with record_evidence_run(ROOT,'development-corpus-worker-engineering-20261108-01',
        metadata=dict(kind='driver-orchestration-pure-stubs-not-actual-corpus',trial01_setup_errors=19,trial01_test_bodies=0,
            trial02_passed=19,trial02_failures=0,trial02_errors=0,trial02_skips=0,
            cumulative_seconds=second['cumulative_seconds'],cap_seconds=20,driver_source_sha256=sha(selected[1]),
            config_sha256=sha(selected[2]),actual_native_model_collector_calls=0,
            manufactured12600_counts_not_native=True,trial02_subprocess_audit_denials=0),sources=selected,
        note='''# Development worker orchestration — mocks only

Giữ19MAX_PATH setupERROR/0body của trial01, không driver bug hoặc relabelPASS. Trial02 root review/run19PASS/0F/E/S, controller2,5319034s+prior1,2762709s=3,8081743s/20. Fixture shortordinal và189char metadata; invalidcalculator02 retained/superseded03. Driver09c909/config8e780 unchanged.

Actual driver functions nhưng plan/resources/collection/publisher/reader stub;13+4dummy sources+exactpublicconfig.12600 manufactured counters, không native/actual corpus; reservationactualNone/final0 và success chỉpendingouter. Trial02 heavy modules rỗng/auditdenials0, narrowactualWinAPIplatformfixture; không runtime/Gate/wholehost/hardOSquota proof. V1process0 khôngglobalauditproof, toolRC0/pytest1 mismatch giữ nguyên.

Source/log/XML/receipts/rootdispatch/snapshots/copySHA, không tmp fixture trees/realdata/oracle/credentials. Root-only execution/Git; agent không rerun/closure execution. Actual12600collection/Job120 là phase riêng, không RQ completion.
''') as target:
        copied={}
        for index,(source,row) in enumerate(zip(selected,inventory),1):
            digest=row['sha256_before_copy']
            if digest not in copied:
                destination=target/f'input-{index:02d}__{source.name}'
                with destination.open('xb') as handle:handle.write(source.read_bytes())
                copied[digest]=destination
            destination=copied[digest]
            row.update(destination=destination.name,sha256_after_copy=sha(destination),source_sha256_after_copy=sha(source))
            assert row['sha256_before_copy']==row['sha256_after_copy']==row['source_sha256_after_copy']
            assert destination.stat().st_size==row['bytes']
        with (target/'copy-inventory.json').open('x',encoding='utf-8') as handle:
            json.dump(dict(input_aliases=len(inventory),unique_copies=len(copied),copies=inventory),handle,ensure_ascii=False,indent=2)
            handle.write('\n')
    result=dict(**verify_evidence_bundle(target),manifest_sha256=sha(target/'manifest.json'),physical_files=len(list(target.iterdir())),
        input_aliases=len(inventory),unique_copies=len(copied),test_sha256=sha(selected[0]),driver_sha256=sha(selected[1]),report_sha256=sha(selected[3]))
    dump(PREP/'closure.json',result)
    paths=[p.relative_to(ROOT).as_posix() for p in (selected[0],selected[3])]+[p.relative_to(ROOT).as_posix() for p in sorted(target.iterdir())]
    with (PREP/'stage-paths.txt').open('x',encoding='utf-8') as handle:handle.write('\n'.join(paths)+'\n')
    print(json.dumps(result))
