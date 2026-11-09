"""ROOT metadata-only dry/close local inventory evidence; no ZIP/test/model/export."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
RUN_ID='colab-contract-dependency-inventory-20261109-01'
CANDIDATE=P/'akt_colab_contract_inventory_20261109.candidate.md'
CANONICAL=R/'research_tracking/reports/akt_colab_contract_inventory_20261109.md'
REPORT_SHA='5bf52d48564516026cf77e5ada2fda00d7dce5250222bfd7d7bfd0d9ca13143a'
PINS={
    'scripts/akt/build_colab_bundle.py':'4fdb7e9512653984d2ebf30a982284dfe0303a6dfc467a4f6f4a2c918a94aabb',
    'tests/akt/test_colab_bundle.py':'29f3ccea4aa2efed5c32af3bd8eb2c44b140c83be01e63ab3e59a99a3b699295',
    'CURRENT_GATE_REFRESH_GAP01.md':'f38af8dacda8763c7137570b84477c08f14d78ebafdb8835b1be06bc70c04324',
    'root_colab_canary02_tool_capture.json':'619b28771e90e0bfa759a075d6e9767654afeeae4cd219e68d9f3ac567a7350f',
    'check_colab_null_sink_guard02.py':'df23b1d24ca341108516251aaeb35a18fdd643b9d43c2c9bc951b335b5fed1b3',
}
PACKET_SHAS={
    '01':'34525b4d828133f438743e33fd01ccd4aab6ffd95247bbba2d3544bdbde12fe0',
    '02':'6704a140c9d70ff018d77205e3c94ac82d6b51838eb4c41004c4d223cd7fc980',
    '03':'812ff1d356d8968f1d36470fbd444b770f76ae11977fc9b5f33e8c5e1162378d',
    '04':'6bbb0bf71a6d137a53fcefb94fdd0e4d57892ff0525bfccf9a6a8b36a92cc403',
}


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')


def safe(path,existing=True):
    path=Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.is_relative_to(R),'fixed project path')
    cursor=R
    for part in (None,*path.relative_to(R).parts):
        if part is not None:cursor/=part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'path alias rejected')
    need(path.resolve().is_relative_to(R.resolve()),'physical project path')
    if existing:need(path.is_file(),'regular file required')
    return path


def gather(report):
    payloads={};sources={};inputs={};runtimes={};trials={}
    def read(path):
        path=safe(path)
        if path not in payloads:
            need(path.stat().st_size<=2*1024**2,'small raw evidence cap')
            raw=path.read_bytes();need(len(raw)<=2*1024**2,'bounded readback')
            payloads[path]=raw;need(sum(map(len,payloads.values()))<=8*1024**2,'compact total cap')
        return payloads[path]
    load=lambda path:json.loads(read(path))
    def merge(target,mapping):
        for name,digest in mapping.items():
            need(name not in target or target[name]==digest,'cross-attempt pinned dependency conflict')
            target[name]=digest
    for name,digest in PINS.items():need(sha(read(R/name if name.startswith(('scripts/','tests/')) else P/name))==digest,'reviewed source/note/canary drift')
    need(report in (CANDIDATE,CANONICAL) and sha(read(report))==REPORT_SHA,'reviewed report bytes')
    for number,digest in PACKET_SHAS.items():
        packet_path=P/('colab_contract_inventory'+number+'_allocation.json')
        need(sha(read(packet_path))==digest,'exact executed allocation')
        packet=load(packet_path);child_dir=P/('colab-contract-inventory'+number);owned_dir=P/(child_dir.name+'-owned')
        child=load(child_dir/'result.json');final=load(owned_dir/'final.json');owned=load(owned_dir/'receipt.json')
        need(child['allocation_sha256']==final['allocation_sha256']==digest,'actual packet identity')
        need(child['source_before']==child['source_after']==final['source_before']==final['source_after']==packet['source_pins']
             and child['fixture_inputs_before']==child['fixture_inputs_after']==final['fixture_inputs_before']==final['fixture_inputs_after']==packet['fixture_input_pins']
             and child['runtime_before']==child['runtime_after']==final['runtime_before']==final['runtime_after']==packet['runtime_pins'],
             'selected dependencies before/after')
        merge(sources,packet['source_pins']);merge(inputs,packet['fixture_input_pins']);merge(runtimes,packet['runtime_pins'])
        need(len(packet['source_pins'])==9 and len(packet['fixture_input_pins'])==18,'selected source9/input18, not global freeze')
        need(owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed']
             and owned['actual_worker_in_job_before_GO'] and owned['cleanup_errors']==[],'actual cleanup all attempts')
        need(child['zip_observer_counts']==dict(constructor_started=0,read_constructor_returned=0,write_attempts=0)
             and child['zip_observer_intact_before_restore'] and child['zip_method_restored']
             and child['scientific_modules_present']==[] and child['environment_restored']
             and child['global_source_inventory_stability_claim'] is False,'no ZIP/scientific/global-stability claim')
        if number!='04':
            need(final['status']=='REJECTED_KEEP_ALL_LOCAL_INVENTORY' and child['counts'] is None and final['counts'] is None
                 and not (child_dir/'junit.xml').exists() and owned['returncode']==1,
                 'preserve bootstrap failure/countsNULL, not8failing cases')
            need(child['forbidden_attempts']==['write_outside_owned_outputs'],'actual blocked write retained')
            if number in ('01','02'):
                need(child['original_error']==dict(type='RuntimeError',message='no source/fixture/runtime writes'),
                     'pre-pytest bootstrap error retained')
            else:
                # Pytest caught the logging-plugin audit error internally in03.
                # Preserve that shape instead of inventing an outer exception.
                need(child['original_error'] is None and child['pytest_exit_code']==3
                     and child['junit_error']['type']=='FileNotFoundError'
                     and b'INTERNALERROR' in read(child_dir/'pytest.log'),
                     '03 original Pytest INTERNALERROR retained')
        else:
            need(sha(read(child_dir/'result.json'))=='27e1d1ad38355a0eb8e5229fd3db0d0be7026af602cd90084e4bd2c86259925a'
                 and sha(read(owned_dir/'final.json'))=='798d347cab9d3e1c50baf28f0b1136f8c7a010c7ec13e3c8bc5a880cbcaf6e8a','accepted04 identities')
            tree=ET.fromstring(read(child_dir/'junit.xml'))
            counts={k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
            cases=list(tree.iter('testcase'))
            need(counts==child['counts']==final['counts']==dict(tests=8,failures=0,errors=0,skipped=0)
                 and len(cases)==8 and len({c.get('name') for c in cases})==8
                 and all(c.get('classname')=='tests.akt.test_colab_bundle' for c in cases),'actual8JUnit cases0FES')
            need(final['status']=='ACCEPTED_8_LOCAL_SOURCE_INVENTORY_CASES_NO_ZIP_EXPORT' and final['errors']==[]
                 and owned['accepted'] and owned['returncode']==0 and child['forbidden_attempts']==[]
                 and child['blocked_write_details']==[] and child['original_error'] is None and child['junit_error'] is None
                 and child['monitor_errors']==[] and child['monitor_stopped'],'actual04 acceptance')
            need(child['runtime_temp']['path']==child['runtime_temp']['actual_gettempdir']==str(child_dir/'runtime-temp')
                 and child['runtime_temp']['cache_restored'] and child['runtime_temp']['separate_from_pytest_basetemp'],
                 'actual owned runtime-temp/cache restoration')
            need(child['resources']['observed_peak_rss_bytes']<=1024**3
                 and child['resources']['observed_minimum_available_ram_bytes']>=2*1024**3,'actual RAM guard observations')
        if number=='01':need(child['native_windows_metadata'] is None,'01 actual raw path not recorded; no invented NUL fact')
        if number in ('02','03','04'):
            need(len(child['native_windows_metadata']['commands'])==1 and child['metadata_phase_closed']
                 and child['allowed_metadata_devnull_events']==[dict(raw_path='nul',mode=None,flags=130,phase='windows_metadata')],
                 'actual scoped NUL stdio/platform command')
        if number=='02':
            need(len(child['blocked_write_details'])==1 and child['blocked_write_details'][0]['flags']==34178,
                 '02 recorded global temp write')
        if number=='03':
            need(child['blocked_write_details']==[dict(raw_path='\\\\.\\nul',raw_path_type='str',mode='w',flags=33665,
                 phase='inventory_tests_no_subprocess')],'03 recorded pytest logging device alias')
        need(sha(read(owned_dir/'receipt.json'))==final['owned_receipt_sha256'],'outer-owned raw binding')
        for name,row in final['output_inventory'].items():
            need(Path(name).name==name and sha(read(child_dir/name))==row['sha256'] and len(read(child_dir/name))==row['bytes'],
                 'child exact raw output binding')
        for name,h in owned['output_sha256'].items():need(name in ('stdout.log','stderr.log') and sha(read(owned_dir/name))==h,'owned raw log binding')
        # All small top-level raw files; bootstrap/cache/binary directories excluded.
        for directory in (child_dir,owned_dir):
            for path in sorted(directory.iterdir()):
                if path.is_file():read(path)
        for prefix in ('check','run'):read(P/(prefix+'_colab_contract_inventory'+number+'.py'))
        trials[number]=dict(status=final['status'],counts=child['counts'],child_seconds=child['elapsed_seconds'],
            outer_stored_seconds=final['elapsed_seconds'],zip_counts=child['zip_observer_counts'],owned_cleanup=True,
            metadata=child['native_windows_metadata'],blocked_write_details=child.get('blocked_write_details'),
            runtime_temp=child.get('runtime_temp'),resources=child['resources'])
    for directory in ('colab-contract-docs-before01','colab-inventory-before02','colab-inventory-before03','colab-inventory-before04'):
        before=P/directory;inv=load(before/'inventory.json')
        for row in inv['copies']:
            snapshot=row.get('snapshot',row.get('source'))
            need(sha(read(before/snapshot))==row['sha256_before_copy']==row['sha256_after_copy']==row['source_sha256_after_copy'],
                 'before/copy/after source snapshot')
        for key in ('actual01_raw','actual02_raw','actual03_raw'):
            for row in inv.get(key,[]):need(sha(read(P/row['path']))==row['sha256'],'preserved pre-correction raw files')
    read(P/'colab_inventory_null_stdio_diagnosis02.json')
    for name in ('before_inventory.json','archiver.py.before','root_dry_failure_capture.json'):
        read(P/'colab_inventory_archiver_before_fix01'/name)
    read(P/'colab-contract-archive-dry01.json')  # Superseded successful dry before adding this history.
    capture=load(P/'root_colab_canary02_tool_capture.json')
    need(capture['status']=='NORMALIZED_ROOT_TOOL_CAPTURE_NOT_SEPARATE_RAW_STREAM_FILES' and capture['tool_exit_code']==0
         and capture['observed_json_stdout']==dict(kind='FOUR_STDLIB_AST_NULL_SINK_GUARD_CASES_NOT_NATIVE',tests=4,
             failures=0,errors=0,skipped=0,worker_sha256='aec80b850e06e6e3130fc2bfcd6b7731e0511203241024032b68f9213c58a2d7')
         and len(capture['observed_case_results'])==4 and capture['separate_original_stdout_stderr_files_available'] is False
         and capture['rerun_performed_to_create_this_record'] is False,'actual normalized canary capture, not fake raw streams')
    read(Path(__file__).resolve())
    aliases=[];unique={}
    for path,raw in sorted(payloads.items()):
        digest=sha(raw)
        unique.setdefault(digest,f'input-{len(unique)+1:03d}-'+path.name)
        aliases.append(dict(source=path.relative_to(R).as_posix(),bytes=len(raw),sha256_before_copy=digest,archived_as=unique[digest]))
    inventory=dict(schema_version=1,run_id=RUN_ID,report_source=report.relative_to(R).as_posix(),input_aliases=aliases,
        unique_input_copies=len(unique),checked_source_bindings=sources,fixed_fixture_input_bindings=inputs,
        runtime_fingerprint_bindings=runtimes,trials=trials,canary_capture=capture,
        scope_vi='Only dependency closure/inmemoryinventory/noZIP proof; no globalWIPfreeze/Gate/sourceexport/GPU authority.')
    recheck(inventory)
    return inventory,payloads


def recheck(inventory):
    for row in inventory['input_aliases']:need(sha(safe(R/row['source']).read_bytes())==row['sha256_before_copy'],'evidence input drift')
    for mapping in (inventory['checked_source_bindings'],inventory['fixed_fixture_input_bindings']):
        for name,digest in mapping.items():need(sha(safe(R/name).read_bytes())==digest,'selected source/fixed fixture drift')
    for name,digest in inventory['runtime_fingerprint_bindings'].items():need(sha(Path(name).read_bytes())==digest,'runtime fingerprint drift')


def main():
    need(os.path.normcase(os.path.abspath(sys.executable))==os.path.normcase(str(R/'.venv/Scripts/python.exe'))
         and Path(sys.prefix).resolve()==R/'.venv','repository .venv only')
    parser=argparse.ArgumentParser(description='ROOT metadata dry/close only; no ZIP/test/model or export')
    parser.add_argument('--report',type=Path,default=CANDIDATE)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--close',action='store_true')
    parser.add_argument('--expected-inventory-sha256')
    args=parser.parse_args();report=safe(args.report.absolute());target=safe(args.inventory.absolute(),existing=args.close)
    need(target.parent==P and target.suffix=='.json','exclusive prep inventory')
    need(not (R/'research_tracking/runs'/RUN_ID).exists(),'immutable run already exists')
    inventory,payloads=gather(report);raw=encoded(inventory)
    if not args.close:
        need(not target.exists() and args.expected_inventory_sha256 is None,'exclusive dry inventory')
        with target.open('xb') as handle:handle.write(raw);handle.flush();os.fsync(handle.fileno())
        print(json.dumps(dict(status='DRY_ONLY_NOT_CLOSED',inventory_sha256=sha(raw),aliases=len(inventory['input_aliases']),
            unique_copies=inventory['unique_input_copies'],trial_statuses={n:r['status'] for n,r in inventory['trials'].items()})))
        return
    need(args.expected_inventory_sha256==sha(target.read_bytes())==sha(raw),'external exact reviewed dry SHA')
    sys.path.insert(0,str(R/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note='''# Local contract dependency inventory —09/11/2026

Actual04 pytest8PASS0FES/noZIPwriter.01–03 bootstraprejected/countsNULL/noJUnit,
không24testfailures. Actual4ASTguardcanaries có normalizedmixedtoolcapture only,
không separate rawstreams/khôngrerun tạo evidence. RawNUL stdio02/03/04, ownedtemp
andexplicitpytest-filelog preserved. NoZIP/build/upload/sourceexport/remote/GPU/
Gate/globalWIPsourcefreeze claims. Priorremoteexportdenial remains binding.
Exact5docs/18fixture inputSHA references, no notebook/corpus/dependency copies.
Sources/controllers/packets/beforeversions+rawlogs only, dedupidenticalbytes with
alloriginalaliases. Precopyinventory/readback/sourceafter verified. No tests/model
whenarchiving; ordinarymetadataGitHEAD read is not research executionauthority.
'''
    previous={k:v for k,v in os.environ.items() if k.startswith('GIT_')}
    try:
        for key in list(previous):os.environ.pop(key,None)
        os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=R.as_posix())
        sources=sorted(set(payloads)|{R/n for n in inventory['checked_source_bindings']}|{R/n for n in inventory['fixed_fixture_input_bindings']}|{target})
        with record_evidence_run(R,RUN_ID,metadata=dict(kind='LOCAL_DEPENDENCY_INVENTORY_NO_ZIP_EXPORT',
                trials=inventory['trials'],canary_kind=inventory['canary_capture']['status'],global_source_freeze=False),sources=sources,note=note) as directory:
            with (directory/'inventory-before.json').open('xb') as handle:handle.write(raw)
            copied={}
            for row in inventory['input_aliases']:
                if row['archived_as'] in copied:continue
                destination=directory/row['archived_as']
                with destination.open('xb') as handle:
                    handle.write(payloads[R/row['source']]);handle.flush();os.fsync(handle.fileno())
                copied[row['archived_as']]=sha(destination.read_bytes())
                need(copied[row['archived_as']]==row['sha256_before_copy'],'copy SHA mismatch')
            recheck(inventory)
            with (directory/'copy-verification.json').open('xb') as handle:
                handle.write(encoded(dict(status='VERIFIED_BYTE_COPIES_NOT_RERUN',inventory_sha256=sha(raw),copied_sha256=copied,
                    sources_after={row['source']:sha(safe(R/row['source']).read_bytes()) for row in inventory['input_aliases']})))
            names=[*copied,'README.md','execution.log','inventory-before.json','copy-verification.json','force-add-files.txt','manifest.json']
            force=[(directory/name).relative_to(R).as_posix() for name in names]+list(PINS)[:2]
            if report==CANONICAL:force.append(report.relative_to(R).as_posix())
            with (directory/'force-add-files.txt').open('x',encoding='utf-8',newline='\n') as handle:handle.write('\n'.join(force)+'\n')
    finally:
        for key in list(os.environ):
            if key.startswith('GIT_'):os.environ.pop(key,None)
        os.environ.update(previous)
    verified=verify_evidence_bundle(directory);recheck(inventory)
    print(json.dumps(dict(verified=verified,manifest_sha256=sha((directory/'manifest.json').read_bytes()),
        force_add_list=(directory/'force-add-files.txt').relative_to(R).as_posix())))


if __name__=='__main__':main()
