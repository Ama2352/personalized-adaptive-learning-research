"""Chuẩn bị offline, không chạy install/remote/model và không tự tạo báo cáo PASS.

Outline báo cáo tiếng Việt cần parent/agent review trước khi --close-reviewed-report:
1. Actual attempt01 FAILED trước pip-install; source289…, raw lỗi và probe rỗng.
2. Diagnostic26.2.2 exact nested API; old guard RED28, corrected GREEN28, cleanup6.
3. Actual attempt02 theo raw result/children/install-report/origins/CPU imports;
   nếu chưa nhận thì UNKNOWN, tuyệt đối không suy từ source hoặc preparation.
4. Caps600s/20GiB/min30GiB cooperative, cleanup/source/44hash binding và giới hạn.
5. Phân biệt metadata resolution, installed CPU evidence, wheelhouse, CUDA/image/
   main-worker/throughput; không research efficacy hoặc quyền compute mới.
6. Bảng SHA nguồn/raw/transfer; giữ cả failure01 và trial02, không private/ZIP/venv.

Mặc định chỉ kiểm inputs; đóng bundle cần report đã có + SHA rõ và flag riêng.
Không chạy helper khi02 chưa nhận; nó fail-closed trước mọi output mutation.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'artifacts/akt/colab/gpu08-linux-20261108-01'
RUN='akt-linux-isolated-install-20261108-01'
REPORT=ROOT/'research_tracking/reports/akt_linux_isolated_install_20261108.md'
SOURCES={1:('install_stage.py','28927535b16b66167e4c71a42a406d9a1c138b388806df093434cba6c0010a87'),
         2:('install_stage_attempt02.py','021dcbe8a4a4a994d56572eb0ac76743c9a1bb3854cb56ca205da7017cb1a21f')}
STATUSES={'INSTALLED_CPU_IMPORT_ACCEPTED_NOT_GPU_READY','FAILED_RETAIN_PARTIAL_NO_RETRY',
          'REJECTED_RESOURCE_BOUND_RETAIN_PARTIAL','CLEANUP_UNVERIFIED_RETAIN_PARTIAL','FAILED'}
POST_STATUS='EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY'
POST_SHA='dd7738bfe06032ffaea6a921619767fd659e626ff53ee5a2a7203fb33f885132'
OUTPUT_CAP=80  # Expanded from60: retain separate actual audit03, its RED/GREEN, WindowsGate22.


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def checked_file(path):
    assert path.is_relative_to(ROOT) and path.resolve().is_relative_to(ROOT)
    assert not path.is_symlink() and stat.S_ISREG(path.stat().st_mode)
    assert path.stat().st_size<=32*1024**2
    assert path.suffix.lower() not in {'.zip','.bin','.whl','.exe','.so','.dll'}
    return path


def verify_transfer(directory,raw,manifest):
    acceptance=directory/'acceptance.json';accepted=read(checked_file(acceptance))
    assert accepted['stage_status']==manifest['stage_status'] and accepted['manifest_sha256']==sha(raw/'manifest.json')
    assert accepted['files']==len(manifest['files'])+1 and accepted['zip_crc_verified'] and accepted['all_output_hashes_verified']
    archives=list(directory.glob('*.zip'));assert len(archives)==1
    assert sha(archives[0])==accepted['archive_sha256']  # Reference only; never copy ZIP.
    return acceptance,accepted


def inspect_trial(number):
    suffix='' if number==1 else '02'
    raw=BASE/('received-install'+suffix)
    assert raw.is_dir() and not raw.is_symlink(), 'Actual received attempt02 is required; no archive or report created.'
    manifest=read(checked_file(raw/'manifest.json'))
    assert manifest['kind']=='GPU08_ISOLATED_INSTALL_EVIDENCE_SUCCESS_OR_FAILURE'
    files=manifest['files'];assert isinstance(files,dict) and 1<=len(files)<=34
    pairs=[(raw/'manifest.json',f'attempt{number:02d}__remote-manifest.json')]
    for name,item in files.items():
        relative=Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name and ':' not in name
        path=checked_file(raw/relative)
        assert sha(path)==item['sha256'] and path.stat().st_size==item['bytes']
        pairs.append((path,f'attempt{number:02d}__'+relative.name))
    assert len({alias for _,alias in pairs})==len(pairs)
    assert {p.relative_to(raw).as_posix() for p in raw.rglob('*') if p.is_file()}==set(files)|{'manifest.json'}
    source_name,source_sha=SOURCES[number]
    assert sha(raw/source_name)==manifest['source_sha256']==source_sha==sha(BASE/source_name)
    output=read(raw/f'install-attempt{number:02d}/output-manifest.json')
    assert sha(raw/f'install-attempt{number:02d}/output-manifest.json')==manifest['output_manifest_sha256']
    for name,item in output['outputs'].items():
        key=f'install-attempt{number:02d}/'+name
        assert Path(name).name==name and files[key]==item
    assert set(files)=={source_name,f'install-attempt{number:02d}/output-manifest.json'}|{
        f'install-attempt{number:02d}/'+name for name in output['outputs']}
    result=read(raw/f'install-attempt{number:02d}/result.json')
    assert result['status']==output['stage_status']==manifest['stage_status'] and result['status'] in STATUSES
    assert result['gpu_model_steps']==result['optimizer_steps']==result['modal_calls']==0
    assert all(e['source_sha256']==source_sha for e in result['children'])
    if number==1:
        assert result['status']=='FAILED_RETAIN_PARTIAL_NO_RETRY'
        assert [e['name'] for e in result['children']]==['probe-before','base-pip-before']
        assert result['children'][-1]['returncode']==1
    if result['status']=='INSTALLED_CPU_IMPORT_ACCEPTED_NOT_GPU_READY':
        assert number==2 and result['packages_installed']==44 and result['nvidia_packages']==14
        assert result['owned_group_cleanup_accepted'] is True and result['resource_time_verdict']=='ACCEPTED'
        assert result['elapsed_seconds']<=600 and result['elapsed_wall_seconds']<=600
        assert result['peak_observed_workspace_bytes']<=20*1024**3
        assert result['distribution_origins']['package_count']==44 and result['cpu_import']['cuda_initialized'] is False
        assert [e['name'] for e in result['children']]==['probe-before','base-pip-before','pip-install','pip-check','distribution-origins','cpu-import','base-pip-after']
        assert all(e['returncode']==0 and e.get('group_cleanup_completed') is True and not e.get('reap_failed') for e in result['children'])
    acceptance,accepted=verify_transfer(BASE/('transfer-install'+suffix),raw,manifest)
    pairs.append((acceptance,f'attempt{number:02d}__transfer-acceptance.json'))
    return pairs,{'attempt':number,'actual_status':result['status'],'source_sha256':source_sha,
                  'selected_raw_files_including_manifest':len(files)+1,'result_sha256':sha(raw/f'install-attempt{number:02d}/result.json'),
                  'remote_manifest_sha256':sha(raw/'manifest.json'),'transfer_archive_sha256_reference_only':accepted['archive_sha256'],
                  'packages_installed_reported':result.get('packages_installed'),'elapsed_seconds':result['elapsed_seconds'],
                  'peak_observed_workspace_bytes':result['peak_observed_workspace_bytes']}


def selection(report):
    rows={}
    for entry in report['install']:
        import re
        name=re.sub(r'[-_.]+','-',entry['metadata']['name']).lower();assert name not in rows
        rows[name]={'version':entry['metadata']['version'],'url':entry['download_info']['url'],
                    'sha256':entry['download_info']['archive_info']['hashes']['sha256']}
    assert len(rows)==44 and sum(n.startswith('nvidia-') for n in rows)==14
    return rows


def inspect_post_audit():
    raw=BASE/'received-post-audit01';assert raw.is_dir() and not raw.is_symlink()
    manifest=read(checked_file(raw/'manifest.json'))
    assert manifest['kind']=='GPU08_POST_INSTALL_READONLY_AUDIT_EVIDENCE_SUCCESS_OR_FAILURE'
    assert manifest['stage_status']==POST_STATUS and manifest['installation_success_claimed'] is False
    pairs=[(raw/'manifest.json','audit03__remote-manifest.json')]
    for name,item in manifest['files'].items():
        relative=Path(name);assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name and ':' not in name
        path=checked_file(raw/relative);assert sha(path)==item['sha256'] and path.stat().st_size==item['bytes']
        pairs.append((path,'audit03__'+relative.name))
    assert len(manifest['files'])==6 and {p.relative_to(raw).as_posix() for p in raw.rglob('*') if p.is_file()}==set(manifest['files'])|{'manifest.json'}
    assert sha(raw/'post_install_audit01.py')==sha(BASE/'post_install_audit01.py')==manifest['source_sha256']==POST_SHA
    output=read(raw/'post-install-audit01/output-manifest.json')
    assert sha(raw/'post-install-audit01/output-manifest.json')==manifest['output_manifest_sha256']
    assert output['status']==POST_STATUS
    for name,item in output['outputs'].items():assert manifest['files']['post-install-audit01/'+name]==item
    assert set(manifest['files'])=={'post_install_audit01.py','post-install-audit01/output-manifest.json'}|{'post-install-audit01/'+n for n in output['outputs']}
    result=read(raw/'post-install-audit01/result.json');payload=read(raw/'post-install-audit01/audit.stdout')
    assert result['audit']==payload and result['status']==POST_STATUS and result['source_sha256']==POST_SHA
    assert result['prior_install02_status']=='FAILED_RETAIN_PARTIAL_NO_RETRY'
    assert all(result[k]==0 for k in ['install_calls','pip_calls','network_calls','gpu_model_steps','optimizer_steps','modal_calls'])
    assert result['child_count']==1 and result['child_returncode']==0 and result['cleanup_accepted'] is True and result['resource_accepted'] is True
    assert result['timeout_seconds']==90 and 0<=result['elapsed_seconds']<=90 and 0<=result['elapsed_wall_seconds']<=90
    assert result['peak_observed_workspace_bytes']<=20*1024**3 and result['whole_host_attestation'] is False
    tree=ast.parse((raw/'post_install_audit01.py').read_bytes())
    assignments={target.id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                 for target in n.targets if isinstance(target,ast.Name) and target.id in {'PINS','CHILD'}}
    assert result['input_sha256']==assignments['PINS']
    for name,digest in assignments['PINS'].items():
        local=BASE/'received'/name if name.startswith(('resolution-attempt01/','.venv/')) else BASE/'received-install02'/name
        assert sha(local)==digest
    expected=selection(read(BASE/'received/resolution-attempt01/pip-report.json'))
    assert selection(read(BASE/'received-install02/install-attempt02/pip-install-report.json'))==expected
    versions={name:row['version'] for name,row in expected.items()}
    actual_child=assignments['CHILD'].replace('EXPECTED_VERSIONS',repr(versions))
    assert (raw/'post-install-audit01/audit-child.py').read_text(encoding='utf-8')==actual_child
    assert payload['package_count']==44 and set(payload['distributions'])==set(expected)
    venv=PurePosixPath('/content/KLTN_GPU08_20261108_01/.venv')
    assert payload['prefix']==str(venv) and payload['executable']==str(venv/'bin/python') and payload['python']=='3.13.18'
    for name,row in payload['distributions'].items():
        path=PurePosixPath(row['metadata_file'])
        assert path.is_relative_to(venv) and '..' not in path.parts and path.parent.parent==venv/'lib/python3.13/site-packages'
        assert path.name=='METADATA' and path.parent.name.endswith('.dist-info') and row['version']==versions[name]
        assert len(row['metadata_sha256'])==64 and row['file_count']>0
        assert row['all_depth_metadata_count']==row['nested_metadata_ignored']+1
    assert {n:r['nested_metadata_ignored'] for n,r in payload['distributions'].items() if r['nested_metadata_ignored']}=={'setuptools':12}
    modules={'torch':'torch','numpy':'numpy','pandas':'pandas','duckdb':'duckdb','sklearn':'scikit-learn','scipy':'scipy','psutil':'psutil','pytest':'pytest'}
    assert set(payload['origins'])==set(modules)
    for name,package in modules.items():
        row=payload['origins'][name];path=PurePosixPath(row['file'])
        assert path.is_relative_to(venv) and '..' not in path.parts and row['version']==versions[package]
    assert payload['torch_build']=='2.7.1+cu126' and payload['cuda_build_metadata']=='12.6'
    assert payload['cuda_initialized'] is False and payload['cpu_scalar_check'] is True
    assert all(payload[k]==0 for k in ['gpu_device_queries','gpu_model_steps','optimizer_steps','external_distribution_origins'])
    diagnostic=read(BASE/'installed-metadata-diagnostic01.json')['payload']
    assert diagnostic['distribution_count']==44 and len(diagnostic['rows'])==44
    assert all(len(row['top_level_metadata'])==1 for row in diagnostic['rows'])
    assert [(r['name'],r['all_depth_metadata_count']) for r in diagnostic['rows'] if r['all_depth_metadata_count']>1]==[('setuptools',13)]
    acceptance,accepted=verify_transfer(BASE/'transfer-post-audit01',raw,manifest)
    pairs.append((acceptance,'audit03__transfer-acceptance.json'))
    return pairs,{'event_alias':'audit03','actual_directory':'post-install-audit01','status':POST_STATUS,
        'source_sha256':POST_SHA,'raw_files_including_manifest':7,'elapsed_seconds':result['elapsed_seconds'],
        'peak_observed_workspace_bytes':result['peak_observed_workspace_bytes'],'child_count':1,'packages_audited':44,
        'cpu_imports':8,'cpu_scalars':1,'pip_install_network_model_calls':0,'result_sha256':sha(raw/'post-install-audit01/result.json'),
        'remote_manifest_sha256':sha(raw/'manifest.json'),'transfer_archive_sha256_reference_only':accepted['archive_sha256']}


def inspect_windows_gate():
    base=ROOT/'artifacts/akt/preflight';name='20261108-linux-tooling-22'
    report=base/f'gate2-evidence-{name}.json';log=base/f'gate2-tests-{name}.log';xml=base/f'gate2-tests-{name}.xml';pointer=base/'gate2-current.json'
    assert sha(report)=='f2f702408adb2162b0102aaca80eac1b1acd59ebec56a2fb77d8b1a358b276cd'
    value=read(report);current=read(pointer)
    assert current['evidence_file']==report.name and current['evidence_sha256']==sha(report) and current['test_log_sha256']==sha(log)==value['test_log_sha256']
    assert sha(xml)==value['junit_sha256'] and value['test_result']=={'passed':768,'failed':0,'errors':0,'skipped':0}
    suites=list(ET.parse(xml).getroot().iter('testsuite'))
    assert sum(int(s.attrib.get('tests',0)) for s in suites)==768
    assert all(sum(int(s.attrib.get(k,0)) for s in suites)==0 for k in ('failures','errors','skipped'))
    assert value['status']=='PASS' and value['timeout_seconds']==540 and value['elapsed_seconds']<=540 and value['python'].startswith('D:\\Dev\\KLTN\\.venv\\Scripts\\')
    return [(report,'windows_gate22_report.json'),(log,'windows_gate22_tests.log'),(xml,'windows_gate22_tests.xml'),(pointer,'windows_gate22_pointer.json')],{
        'host':'Windows','passed':768,'elapsed_seconds':value['elapsed_seconds'],'timeout_seconds':540,'report_sha256':sha(report),'linux_gate_claimed':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--close-reviewed-report',action='store_true')
    parser.add_argument('--report-sha256')
    args=parser.parse_args()
    assert Path(sys.prefix).resolve()==ROOT/'.venv'
    pairs=[];trials=[]
    for number in (1,2):
        selected,receipt=inspect_trial(number);pairs.extend(selected);trials.append(receipt)
    selected,post_audit=inspect_post_audit();pairs.extend(selected)
    selected,windows_gate=inspect_windows_gate();pairs.extend(selected)
    support=['install-preparation.json','install-attempt02-preparation.json','install-attempt01-cell-receipt.json',
        'pip-config-diagnostic-02.json','test_install_attempt02_config.py','config-old-red.log','config-attempt02-green.log',
        'test_install_cleanup_peer.py','cleanup-peer-persisted.log','install-attempt02-peer-review.json',
        'install-attempt02-peer-validation.json','install-attempt02-static-comparison.json','install-attempt02-source.diff',
        'installed-metadata-diagnostic01.json','post_install_audit01-pre-cleanup-review.py','post-install-audit01-proposal-validation.json',
        'test_post_install_metadata.py','metadata-old-red.log','metadata-root-green.log','post-install-audit01-cleanup-validation.json',
        'test_post_install_cleanup.py','metadata-root-green-after-cleanup.log','post-audit-cleanup-green.log',
        'export_post_install_audit01_evidence.py','receive_post_install_audit01_transfer.py']
    pairs.extend((checked_file(BASE/name),name) for name in support)
    validation=read(BASE/'install-attempt02-peer-validation.json')
    assert validation['status']=='PASS_PROPOSAL_MOCKS_ONLY_NOT_EXECUTED'
    assert [row['returncode'] for row in validation['tests']]==[1,0,0]
    assert validation['cases_per_config_invocation']==28
    for row in validation['tests']:assert sha(BASE/Path(row['log']).name)==row['log_sha256']
    diagnostic_receipt=read(BASE/'pip-config-diagnostic-02.json')
    assert diagnostic_receipt['cell_error_types']==[]
    diagnostic=diagnostic_receipt['payload']
    assert diagnostic['pip']=='26.2.2' and diagnostic['pip_env_names']==['PIP_CONFIG_FILE']
    assert diagnostic['config_file_env_equals_devnull'] is True
    assert len(diagnostic['items'])==1 and diagnostic['items'][0]['key']==':env:'
    nested=diagnostic['items'][0]['nested'];assert len(nested)==1 and nested[0]['key']==':env:.config-file' and nested[0]['equals_devnull'] is True
    normalized={'kind':'TWO_FAILED_INSTALL_TRIALS_SEPARATE_ACCEPTED_CPU_AUDIT_NO_GPU','trials':trials,'post_audit':post_audit,'windows_gate22':windows_gate,
        'mock_guard_tests':{'old':{'passed':18,'failures':6,'errors':4},'corrected':{'passed':28,'failures':0,'errors':0}},
        'cleanup_mock_checks':6,'metadata_mock_tests':{'old_passed':11,'old_failed':5,'corrected_passed':16},'audit_cleanup_mock_checks':7,
        'archive_new_installs_or_remote_calls':0,'wheelhouse_retained_bytes_attested':False,
        'cuda_image_mainworker_accepted':False,'storage_monitoring_cooperative':True}
    if not args.close_reviewed_report:
        print(json.dumps({'status':'INPUTS_VERIFIED_ARCHIVE_NOT_CREATED','normalized':normalized}));return
    independent=read(checked_file(BASE/'independent-install-validation.json'))
    assert independent['returncode']==0 and independent['helper_sha256']==sha(Path(__file__).resolve())
    assert independent['verification']['normalized']==normalized
    pairs.append((BASE/'independent-install-validation.json','independent-install-validation.json'))
    assert args.report_sha256 and checked_file(REPORT) and sha(REPORT)==args.report_sha256
    pairs.extend([(REPORT,'isolated_install_report.md'),(Path(__file__).resolve(),'pack_isolated_install_evidence.py')])
    assert len({name for _,name in pairs})==len(pairs) and len(pairs)+7<=OUTPUT_CAP
    before=[{'source':p.relative_to(ROOT).as_posix(),'copy':alias,'bytes':p.stat().st_size,'sha256_before_copy':sha(p)} for p,alias in pairs]
    # Read-only git commands; explicit path argv avoids stdin check-ignore ambiguity.
    config_count=int(os.environ.get('GIT_CONFIG_COUNT','0'))
    os.environ[f'GIT_CONFIG_KEY_{config_count}']='safe.directory';os.environ[f'GIT_CONFIG_VALUE_{config_count}']=str(ROOT)
    os.environ['GIT_CONFIG_COUNT']=str(config_count+1)
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note=f'# Cài đặt AKT cô lập trên Linux CPU — 08/11/2026\n\nGiữ cả actual install01/02 FAILED và audit03 độc lập `{post_audit["status"]}`. Alias audit03 là event thứ ba; remote directory vẫn post-install-audit01. WindowsGate22 chỉ Windows768PASS, chưa Linux fullGate. Không chứng nhận CUDA/image/main-worker/costforecast, không wheels/venv/ZIP/privateMCP. Archive offline, không cài đặt hoặc cấp compute mới. Cap outputs tăng60→80 có mục đích để giữ raw audit03, RED/GREEN16+cleanup7 và4WindowsGate22 snapshots; actual output count trong manifest.\n'
    with record_evidence_run(ROOT,RUN,metadata={'kind':'ACTUAL_LINUX_ISOLATED_CPU_INSTALL_COMBINED_TRIALS','trials':trials,'post_audit':post_audit,'windows_gate22':windows_gate,
         'new_remote_install_model_calls_during_archive':0,'cuda_image_mainworker_accepted':False},
         sources=sorted({p for p,_ in pairs}),note=note) as directory:
        for path,alias in pairs:shutil.copyfile(path,directory/alias)
        after=[]
        for row in before:
            copied=sha(directory/row['copy']);assert copied==row['sha256_before_copy']==sha(ROOT/row['source'])
            after.append({**row,'sha256_after_copy':copied,'exact_match':True})
        def write(name,value):(directory/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        write('copy_inventory_before.json',before);write('copy_inventory.json',after);write('normalized-receipt.json',normalized)
        expected_names={name for _,name in pairs}|{'README.md','execution.log','copy_inventory_before.json','copy_inventory.json','normalized-receipt.json','git_ignore_check.json','force_add_paths.txt'}
        ignored=[];checks=[]
        for name in sorted(expected_names|{'manifest.json'}):
            relative=(directory/name).relative_to(ROOT).as_posix()
            checked=subprocess.run(['git','check-ignore','--no-index','--verbose','--',relative],cwd=ROOT,capture_output=True,text=True)
            assert checked.returncode in (0,1)
            checks.append({'path':relative,'ignored':checked.returncode==0,'rule':checked.stdout.strip()})
            if checked.returncode==0:ignored.append(relative)
        write('git_ignore_check.json',checks)
        (directory/'force_add_paths.txt').write_text(''.join(p+'\n' for p in ignored),encoding='utf-8')
    verified=verify_evidence_bundle(directory)
    assert verified['artifacts']==len(pairs)+7 and {p.name for p in directory.iterdir()}==expected_names|{'manifest.json'}
    print(json.dumps({**verified,'copy_pairs':len(pairs),'manifest_sha256':sha(directory/'manifest.json'),'force_add_paths':ignored}))


if __name__=='__main__':main()
