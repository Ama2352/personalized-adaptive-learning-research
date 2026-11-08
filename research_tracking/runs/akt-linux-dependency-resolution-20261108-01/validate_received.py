"""Đối chiếu offline raw receipts/selected metadata; không resolve/install/import Torch."""
from pathlib import Path
import ast
import hashlib
import json
import re
import sys
from urllib.parse import unquote, urlsplit

from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.specifiers import SpecifierSet
from pip._vendor.packaging.tags import cpython_tags, compatible_tags
from pip._vendor.packaging.utils import canonicalize_name, parse_wheel_filename
from pip._vendor.packaging.version import Version

ROOT=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==ROOT/'.venv'
BASE=ROOT/'artifacts/akt/colab/gpu08-linux-20261108-01'
RAW=BASE/'received'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


manifest=read(RAW/'manifest.json')
assert len(manifest['files'])==14
raw_checks=[]
for name,item in manifest['files'].items():
    path=RAW/name
    assert path.resolve().is_relative_to(RAW) and not path.is_symlink() and path.is_file()
    assert path.suffix.lower() not in {'.whl','.bin','.zip','.exe','.so','.dll'}
    assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],name
    raw_checks.append({'path':name,'bytes':item['bytes'],'sha256':item['sha256'],'match':True})
transfer=read(BASE/'transfer/acceptance.json')
assert transfer['status']=='VERIFIED_LOCAL_COPY' and transfer['files']==14
assert transfer['manifest_sha256']==sha(RAW/'manifest.json')
assert sha(BASE/'transfer/gpu08-resolution-evidence.zip')==transfer['archive_sha256']
spec=read(BASE/'resolver-input-spec.json')
assert sha(ROOT/'requirements-akt.lock.txt')==spec['source_lock_sha256']
assert sha(RAW/'resolution-attempt01/requirements-proposed.txt')==spec['requirements_sha256']
source=BASE/'resolve_dependencies.py'
assert sha(source)==sha(RAW/'resolve_dependencies.py')=='39c68ed7921ccd7660ab1e625ab5df6ca3d2cfd473339b2b9babc7de3665b861'
tree=ast.parse(source.read_bytes())
embedded=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='SPEC' for t in n.targets)))
assert embedded==spec
resolution=read(RAW/'resolution-attempt01/resolution.json')
resume=read(BASE/'resume-acceptance.json')
assert resume['status']=='REMOTE_OUTPUT_RECEIVED'
assert resume['source_sha256']==sha(BASE/'resume_resolver.py')=='4109fab102d2fa93b666e0d88b50874e721667bf0a0cf5691d2374d736d47dc9'
for key,value in resolution.items():
    if key!='selected_packages':assert resume['payload'][key]==value,key
assert resume['payload']['resume_action']=='approved_resolver_executed_once'
assert resume['payload']['resume_stages_attempted']==['resolve_dependencies.py']
assert resolution['executed_source_sha256']==sha(source)
assert resolution['status']=='CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED'
assert resolution['returncode']==0 and resolution['stop_reason'] is None
assert resolution['elapsed_seconds']<=180 and resolution['peak_observed_workspace_bytes']<=256*1024**2
assert resolution['packages_installed']==resolution['gpu_model_steps']==resolution['modal_calls']==0
assert resolution['isolated_site_unchanged'] is True
assert resolution['probe_before']==resolution['probe_after']
assert resolution['probe_before']['torch']==resolution['probe_before']['numpy']==resolution['probe_before']['pip']=='None'
venv=read(RAW/'venv.json')
assert venv['system_site_packages'] is False and venv['packages_installed']==0 and venv['torch_imported'] is False
assert sha(RAW/'.venv/pyvenv.cfg')==venv['pyvenv_cfg_sha256']
assert 'include-system-site-packages = false' in (RAW/'.venv/pyvenv.cfg').read_text().lower()
assert '--without-pip' in (RAW/'.venv/pyvenv.cfg').read_text()
report_path=RAW/'resolution-attempt01/pip-report.json'
lock_path=RAW/'resolution-attempt01/candidate-linux-cuda.lock.txt'
assert sha(report_path)==resolution['report_sha256']==manifest['report_sha256']
assert sha(lock_path)==resolution['candidate_lock_sha256']==manifest['candidate_lock_sha256']
report=read(report_path)
environment=report['environment']
assert environment==resolution['environment']
assert environment['implementation_name']=='cpython' and environment['sys_platform']=='linux'
assert environment['platform_system']=='Linux' and environment['platform_machine']=='x86_64'
assert environment['python_full_version']=='3.13.18' and report['pip_version']=='26.2.2'
selected={};wheel_checks=[];requested=[]
for item in report['install']:
    metadata=item['metadata'];name=canonicalize_name(metadata['name'])
    assert name not in selected and not item['is_yanked'] and not item.get('requested_extras')
    url=item['download_info']['url'];parts=urlsplit(url)
    assert parts.scheme=='https' and parts.hostname in {'files.pythonhosted.org','download.pytorch.org','download-r2.pytorch.org'}
    assert not parts.username and not parts.password and not parts.query and not parts.fragment
    filename=unquote(parts.path.rsplit('/',1)[-1])
    wheel_name,wheel_version,build,tags=parse_wheel_filename(filename)
    assert canonicalize_name(wheel_name)==name and wheel_version==Version(metadata['version'])
    platforms={tag.platform for tag in tags}
    assert all(p=='any' or (p.endswith('_x86_64') and p.startswith(('manylinux','linux_'))) for p in platforms)
    target_tags=set(cpython_tags((3,13),abis=['cp313'],platforms=platforms))
    target_tags.update(compatible_tags((3,13),interpreter='cp313',platforms=platforms))
    assert tags & target_tags,(name,filename)
    if metadata.get('requires_python'):
        assert SpecifierSet(metadata['requires_python']).contains(Version(environment['python_full_version']))
    digest=item['download_info']['archive_info']['hashes']['sha256']
    assert re.fullmatch('[a-f0-9]{64}',digest)
    selected[name]={'version':metadata['version'],'url':url,'sha256_from_index_report':digest,
                    'requires_dist':metadata.get('requires_dist',[])}
    assert resolution['selected_packages'][name]=={'version':metadata['version'],'url':url,
        'sha256_from_pip_index_report':digest,'requires_dist':metadata.get('requires_dist',[])}
    wheel_checks.append({'name':name,'version':metadata['version'],'filename':filename,
                         'sha256_from_index_report':digest,'compatible_python_abi_tag':True})
    if item['requested']:requested.append(name)
assert len(selected)==len(report['install'])==44 and set(selected)==set(spec['root_pins'])|set(spec['cuda_pins'])
assert set(requested)==set(spec['root_pins']) and len(requested)==29
for name,version in {**spec['root_pins'],**spec['cuda_pins']}.items():assert selected[name]['version']==version
assert sum(name.startswith('nvidia-') for name in selected)==14
assert selected['torch']['sha256_from_index_report']==spec['torch_sha256']=='a05c0001fd1d0ceae9cda8c8c1b8a16ed5def858fe996c9237a28016559dad52'
assert selected['triton']['sha256_from_index_report']==spec['triton_sha256']=='b89d846b5a4198317fec27a5d3a609ea96b6d557ff44b56c23176546023c4240'
expected_lock='\n'.join(f"{name} @ {value['url']} --hash=sha256:{value['sha256_from_index_report']}"
                        for name,value in sorted(selected.items()))+'\n'
assert lock_path.read_bytes()==expected_lock.encode()
active=[];inactive=0
target_environment={**environment,'extra':''}
for source_name,item in selected.items():
    for text in item['requires_dist']:
        requirement=Requirement(text)
        if requirement.marker is not None and not requirement.marker.evaluate(target_environment):
            inactive+=1;continue
        # No extras are requested in this recorded profile. Validate given selection,
        # never choose versions or implement a dependency resolver.
        assert not requirement.extras and requirement.url is None,(source_name,text)
        dependency=canonicalize_name(requirement.name)
        assert dependency in selected,(source_name,text)
        assert requirement.specifier.contains(Version(selected[dependency]['version']),prereleases=True),(source_name,text)
        active.append({'source':source_name,'requirement':text,'selected':dependency,
                       'version':selected[dependency]['version'],'satisfied':True})
old=ROOT/'research_tracking/runs/gpu08-environment-proposal-20261108-01'
old_manifest=read(old/'manifest.json')
for name,digest in old_manifest['outputs_sha256'].items():assert sha(old/name)==digest
assert sha(ROOT/'experiments/akt/configs/linux-cuda-runtime-proposal.json')=='fda8af1e714763640294280fb577c9c4cc285868b33085b9db8b83e372ebbc33'
assert sha(ROOT/'docs/akt-linux-cuda-environment.md')=='161da353c6e90dd21e2c23b404558768d589aa24e3bedfeca5b78b9192981a0c'
assert 'torch' not in sys.modules
result={'kind':'OFFLINE_INDEPENDENT_ACTUAL_LINUX_RESOLUTION_VERIFICATION','status':'PASS_CANDIDATE_METADATA_CLOSURE_ONLY',
 'raw_file_checks':raw_checks,'raw_files_verified':14,'raw_total_bytes':sum(item['bytes'] for item in raw_checks),
 'selected_package_count':44,'root_pins_verified':29,'nvidia_pins_verified':14,'triton_pins_verified':1,
 'wheel_metadata_checks':wheel_checks,'active_requires_dist_checks':active,'active_dependency_constraints_verified':len(active),
 'inactive_optional_platform_marker_entries':inactive,'target_marker_environment':target_environment,
 'candidate_lock_sha256':sha(lock_path),'pip_report_sha256':sha(report_path),
 'resolver_sha256':sha(source),'resume_sha256':sha(BASE/'resume_resolver.py'),
 'source_windows_lock_sha256':spec['source_lock_sha256'],'raw_manifest_sha256':sha(RAW/'manifest.json'),
 'resume_receipt_sha256':sha(BASE/'resume-acceptance.json'),'transfer_receipt_sha256':sha(BASE/'transfer/acceptance.json'),
 'old_proposal_bundle_outputs_verified':len(old_manifest['outputs_sha256']),
 'raw_resolution_seconds':resolution['elapsed_seconds'],'peak_observed_attempt_bytes':resolution['peak_observed_workspace_bytes'],
 'packages_installed':0,'wheel_bytes_verified':False,'new_resolver_network_model_gpu_calls':0,
 'limits_vi':['Kiểm metadata của selection đã có, không chạy resolver hoặc chọn dependency version mới.',
              'Target before/after module specs và tên site entries do source ghi; không là full filesystem/global-byte attestation.',
              'Không có wheel bytes, installed imports, image digest hoặc CUDA/main-worker acceptance.']}
output=BASE/'independent-validation.json'
with output.open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({key:value for key,value in result.items() if key in {
 'status','raw_files_verified','raw_total_bytes','selected_package_count','root_pins_verified','nvidia_pins_verified',
 'active_dependency_constraints_verified','inactive_optional_platform_marker_entries','old_proposal_bundle_outputs_verified',
 'packages_installed','new_resolver_network_model_gpu_calls'}}))
