"""Archive actual Linux resolver receipts; không rerun resolver/install/model/network."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle

count=int(os.environ.get('GIT_CONFIG_COUNT','0'))
os.environ[f'GIT_CONFIG_KEY_{count}']='safe.directory'
os.environ[f'GIT_CONFIG_VALUE_{count}']=ROOT.as_posix()
os.environ['GIT_CONFIG_COUNT']=str(count+1)
BASE=ROOT/'artifacts/akt/colab/gpu08-linux-20261108-01'
RAW=BASE/'received'
RUN='akt-linux-dependency-resolution-20261108-01'
REPORT=ROOT/'research_tracking/reports/akt_linux_dependency_resolution_20261108.md'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))


validation=read(BASE/'independent-validation.json')
assert validation['status']=='PASS_CANDIDATE_METADATA_CLOSURE_ONLY'
assert validation['raw_files_verified']==14 and validation['selected_package_count']==44
assert validation['active_dependency_constraints_verified']==46
assert validation['nvidia_pins_verified']==14 and validation['root_pins_verified']==29
raw_manifest=read(RAW/'manifest.json')
assert len(raw_manifest['files'])==14
raw_pairs=[]
for name,item in raw_manifest['files'].items():
    path=RAW/name
    assert path.resolve().is_relative_to(RAW) and path.is_file() and not path.is_symlink()
    assert path.suffix.lower() not in {'.zip','.bin','.whl','.exe','.so','.dll'}
    assert sha(path)==item['sha256'] and path.stat().st_size==item['bytes']
    alias=Path(name).name
    raw_pairs.append((path,alias))
assert len({alias for _,alias in raw_pairs})==14
resume=read(BASE/'resume-acceptance.json')
transfer=read(BASE/'transfer/acceptance.json')
resolution=read(RAW/'resolution-attempt01/resolution.json')
assert sha(RAW/'manifest.json')==transfer['manifest_sha256']==validation['raw_manifest_sha256']
assert sha(BASE/'resume_resolver.py')==resume['source_sha256']==validation['resume_sha256']
assert sha(BASE/'resolve_dependencies.py')==sha(RAW/'resolve_dependencies.py')==validation['resolver_sha256']
assert resolution['status']=='CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED'
assert resolution['packages_installed']==resolution['gpu_model_steps']==resolution['modal_calls']==0
pairs=raw_pairs+[
 (RAW/'manifest.json','remote_manifest.json'),
 (BASE/'resume_resolver.py','resume_resolver.py'),
 (BASE/'export_evidence.py','export_evidence.py'),
 (BASE/'receive_transfer.py','receive_transfer.py'),
 (BASE/'resolver-input-spec.json','resolver-input-spec.json'),
 (BASE/'resume-acceptance.json','resume-acceptance.json'),
 (BASE/'transfer/acceptance.json','transfer-acceptance.json'),
 (ROOT/'requirements-akt.lock.txt','source-windows-cpu.lock.txt'),
 (ROOT/'artifacts/akt/gpu08-env-20261108-01/torch-candidate-02.json','official-torch-candidate.json'),
 (ROOT/'artifacts/akt/gpu08-env-20261108-01/triton-candidate-03.json','official-triton-candidate.json'),
 (BASE/'independent-validation.json','independent-validation.json'),
 (BASE/'validate_received.py','validate_received.py'),
 (REPORT,'resolution_report.md'),
 (ROOT/'src/knowledge_tracing/evidence.py','evidence_helper_source.py'),
 (Path(__file__).resolve(),'pack_resolution_evidence.py')]
assert len(pairs)==len({alias for _,alias in pairs})==29
before=[{'source':path.relative_to(ROOT).as_posix(),'copy':alias,'sha256_before_copy':sha(path),
         'bytes':path.stat().st_size} for path,alias in pairs]
canonical_sources=[BASE/name for name in ['connection_probe.py','venv_prepare.py','resolve_dependencies.py',
    'resume_resolver.py','export_evidence.py','receive_transfer.py','validate_received.py']]
sources=sorted({path for path,_ in pairs}|set(canonical_sources))
normalized={'kind':'NORMALIZED_ACTUAL_LINUX_CPU_RESOLUTION_RECEIPT','evidence_role':'candidate_metadata_closure_not_install',
 'status':resolution['status'],'returncode':resolution['returncode'],'stop_reason':resolution['stop_reason'],
 'elapsed_seconds':resolution['elapsed_seconds'],'peak_observed_attempt_tree_bytes':resolution['peak_observed_workspace_bytes'],
 'limits':{'child_wall_seconds':180,'observed_attempt_bytes':256*1024**2,'cooperative_polling':True,
           'network_byte_cap':False,'wheel_fetch_absence_proven':False},
 'target_environment':resolution['environment'],'probe_before':resolution['probe_before'],
 'probe_after':resolution['probe_after'],'source_reports_site_names_unchanged':resolution['isolated_site_unchanged'],
 'full_site_bytes_inventory_received':False,'packages_installed':0,'gpu_model_steps':0,'modal_calls':0,
 'package_count':44,'root_pins':29,'nvidia_packages':14,'triton_packages':1,
 'active_metadata_dependency_constraints_checked':46,
 'inactive_optional_platform_entries':validation['inactive_optional_platform_marker_entries'],
 'resolver_sha256':validation['resolver_sha256'],'resume_sha256':validation['resume_sha256'],
 'resume_action':resume['payload']['resume_action'],'resume_stages_attempted':resume['payload']['resume_stages_attempted'],
 'candidate_lock_sha256':validation['candidate_lock_sha256'],'pip_report_sha256':validation['pip_report_sha256'],
 'transfer_archive_sha256_reference_only':transfer['archive_sha256'],'remote_manifest_sha256':transfer['manifest_sha256'],
 'resume_remote_receipt_sha256_reference_only':resume['receipt_sha256'],
 'transfer_remote_receipt_sha256_reference_only':transfer['remote_receipt_sha256'],
 'raw_files':14,'raw_bytes':validation['raw_total_bytes'],
 'wheel_bytes_verified':False,'installed_origins_verified':False,'image_digest_verified':False,
 'cuda_runtime_accepted':False,'main_worker_cuda_accepted':False}
metadata={'kind':'ACTUAL_LINUX_CPU_DEPENDENCY_RESOLUTION_ARCHIVE','evidence_role':'candidate_metadata_closure_only',
 'raw_selected_files':14,'raw_selected_bytes':validation['raw_total_bytes'],'selected_packages':44,
 'root_pins':29,'nvidia_packages':14,'triton_packages':1,'active_dependency_constraints_verified':46,
 'packages_installed':0,'gpu_model_steps':0,'modal_calls':0,
 'new_remote_network_resolver_model_calls_during_archive':0,
 'wheel_bytes_verified':False,'install_accepted':False,'image_accepted':False,'cuda_accepted':False,
 'old_proposal_unchanged':True,'source_windows_lock_sha256':validation['source_windows_lock_sha256'],
 'resolver_source_sha256':validation['resolver_sha256'],'resume_source_sha256':validation['resume_sha256'],
 'candidate_lock_sha256':validation['candidate_lock_sha256'],'pip_report_sha256':validation['pip_report_sha256'],
 'purpose_vi':'Giữ raw metadata/receipts Linux CPU đã nhận, kiểm closure và source/copy SHA; không install/GPU readiness.'}
note='''# AKT Linux dependency resolution — 08/11/2026

Actual Colab CPU/Linux CPython3.13.18/pip26.2.2 đã phân giải44packages:29root pins,
14NVIDIA dependencies vàTriton3.3.1. Torch2.7.1+cu126/Triton wheel hashes khớp
official index metadata đã lưu. Đây là candidate closure/index hashes, không
wheel-bytes verification, installation, image digest hoặc CUDA/main-worker acceptance.

Lượt resolver10.095353s,peak OBSERVED attempt-tree7350021bytes; limits180s/256MiB
là cooperative polling/postexit checks, cóovershoot, không hard network/disk cap.
Source có thể fetch wheel bytes nếu metadata khôngusable; không claim no-wheelGET.
Base pip --python điều khiển isolated .venv --without-pip; target Torch/NumPy/pip
specNone trước/sau, names/probe unchanged được source ghi. Không full content-hash
inventory của toàn site/globalfilesystem, nên không byte-attestation ngoài phạm vi.

Offline independent validation đối chiếu14rawfiles/512166bytes, transfer/archive
digests,44selected names/versions/URLs/SHA/CP313ABI tags,46active Requires-Dist
constraints với actualLinux markers;432optional/platform entriesinactive. Không
resolve version mới, chạy pip, install, model/GPU/cloud/network trong archive.

remote_manifest.json là manifest raw14 gốc; copy_inventory maps original nested
paths tới aliases phẳng và giữ bytes exact. Python sources là text, không Python
binary. Không wheels/caches/ZIP/chunks/privatefiles/rawMCPbase64 transfer data.
resume_resolver.py có literal verified approved-source embedding như code đã chạy;
receiver source chỉ tham chiếu private-folder path, không có nội dung/auth củafolder.
Receipt JSON được normalize riêng; remote receipt digests là provenance references,
không signed remote attestation hoặc bản copy raw private bridge responses.

Trạng thái completed chỉ archive integrity. Chínhproposal/bundleGPU08trước vẫn
giữ nguyên; actual resolver-source39c68... vàresume4109... có snapshot riêng.
Futureinstall script đang được chuẩn bị riêng không thuộc bundle này. Next cần
wheel-byteSHA/installreport/pipcheck/origins, freshschema2CPU/CUDA đúng stage,
immutableimage và actualboundedCUDA mainworker/Volume/throughput acceptance.
ProofT4kitv12Torch2.14.1+cu130 không certify2.7.1+cu126 hoặc source mới.

record_evidence_run/verify_evidence_bundle đóng và kiểm outputs, sau đó chỉ đọc.
29copies có inventory trước/sauSHA; canonical report links giữ theo repository.
git_ignore_check.json dùng từng explicit argv path, không stdin;force_add_paths.txt
ghi chính xác ignored logs. Git chỉ đọc, safe.directory process-only; parent quản
tracking/Git, không add/commit/push hoặc đổi globalconfig. Không có permission chạy
install/GPU/data/model/Modal từ việc archive này thành công.
'''
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=sources,note=note) as directory:
    (directory/'copy_inventory_before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    after=[]
    for row in before:
        path=ROOT/row['source'];assert sha(path)==row['sha256_before_copy']
        target=directory/row['copy']
        with target.open('xb') as stream:stream.write(path.read_bytes())
        item={**row,'sha256_after_copy':sha(target),'exact_match':sha(target)==row['sha256_before_copy']}
        assert item['exact_match'];after.append(item)
    (directory/'copy_inventory.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (directory/'normalized-receipt.json').write_text(json.dumps(normalized,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    provenance={'source_snapshots_sha256':{path.relative_to(ROOT).as_posix():sha(path) for path in canonical_sources},
       'source_binding_scope':{'resolver':'remote bytes plus executed_source_sha256 and pre/post guard',
                               'resume':'normalized receipt source_sha256 plus embedded source digests',
                               'export_receive':'current local source snapshots; no invented independent execution signature'},
       'official_candidate_proof_bundle':'research_tracking/runs/gpu08-environment-proposal-20261108-01',
       'official_urls':['https://download.pytorch.org/whl/cu126/torch/','https://download.pytorch.org/whl/cu126/triton/'],
       'independent_validation_scope':'Selected metadata constraints only; no resolver/model/network rerun',
       'original_raw14_mapping':{row['source']:row['copy'] for row in before[:14]}}
    (directory/'source_inventory.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    planned={'manifest.json','README.md','execution.log','copy_inventory_before.json','copy_inventory.json',
             'normalized-receipt.json','source_inventory.json','git_ignore_check.json','force_add_paths.txt',
             *(alias for _,alias in pairs)}
    checks=[];force=[]
    for name in sorted(planned):
        relative=(directory/name).relative_to(ROOT).as_posix()
        command=['git','check-ignore','--no-index','--verbose','--',relative]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=10)
        assert result.returncode in (0,1),(command,result.stderr)
        ignored=result.returncode==0
        checks.append({'path':relative,'argv':command,'returncode':result.returncode,'ignored':ignored,
                       'stdout':result.stdout.strip(),'stderr':result.stderr.strip(),'stdin_used':False})
        if ignored:force.append(relative)
    assert force==[f'research_tracking/runs/{RUN}/execution.log',f'research_tracking/runs/{RUN}/pip.stderr.log',
                   f'research_tracking/runs/{RUN}/pip.stdout.log']
    (directory/'git_ignore_check.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    (directory/'force_add_paths.txt').write_text('\n'.join(force)+'\n',encoding='utf-8')
    assert {path.name for path in directory.iterdir()}==planned
verified=verify_evidence_bundle(directory)
closed=read(directory/'manifest.json')
assert {path.name for path in directory.iterdir()}=={'manifest.json',*closed['outputs_sha256']}
for row in after:assert sha(ROOT/row['source'])==sha(directory/row['copy'])==row['sha256_before_copy']
links=[]
for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',REPORT.read_text(encoding='utf-8')):
    if target.startswith(('http:','https:')):continue
    assert (REPORT.parent/target).is_file(),target
    links.append(target)
print(json.dumps({'bundle':directory.relative_to(ROOT).as_posix(),'verified':verified,'raw_files':14,
 'copies_exact':len(after),'report_links_checked':len(links),'manifest_sha256':sha(directory/'manifest.json'),
 'report_sha256':sha(REPORT),'independent_validation_sha256':sha(BASE/'independent-validation.json'),
 'force_add_paths':force},indent=2))
