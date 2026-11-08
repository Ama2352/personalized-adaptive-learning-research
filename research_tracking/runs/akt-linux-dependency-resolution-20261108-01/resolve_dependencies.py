import hashlib, importlib.util, json, os, platform, re, signal, subprocess, sys, time
from pathlib import Path
from urllib.parse import urlsplit

SPEC = {'source_lock_sha256': '3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a', 'root_pins': {'cloudpickle': '3.1.2', 'colorama': '0.4.6', 'duckdb': '1.5.6', 'filelock': '4.2.5', 'fsspec': '2026.9.0', 'iniconfig': '2.3.1', 'jinja2': '3.1.6', 'joblib': '1.6.0', 'markupsafe': '3.0.4', 'mpmath': '1.3.0', 'narwhals': '2.28.0', 'networkx': '3.7', 'numpy': '2.5.4', 'packaging': '26.3', 'pandas': '3.0.6', 'pluggy': '1.7.0', 'psutil': '7.2.2', 'pygments': '2.21.0', 'pytest': '9.1.1', 'python-dateutil': '3.0.0', 'scikit-learn': '1.9.1', 'scipy': '1.18.1', 'setuptools': '84.2.1', 'six': '1.17.0', 'sympy': '1.14.0', 'threadpoolctl': '3.7.0', 'torch': '2.7.1+cu126', 'typing-extensions': '4.16.0', 'tzdata': '2026.6'}, 'cuda_pins': {'nvidia-cuda-nvrtc-cu12': '12.6.77', 'nvidia-cuda-runtime-cu12': '12.6.77', 'nvidia-cuda-cupti-cu12': '12.6.80', 'nvidia-cudnn-cu12': '9.5.1.17', 'nvidia-cublas-cu12': '12.6.4.1', 'nvidia-cufft-cu12': '11.3.0.4', 'nvidia-curand-cu12': '10.3.7.77', 'nvidia-cusolver-cu12': '11.7.1.2', 'nvidia-cusparse-cu12': '12.5.4.2', 'nvidia-cusparselt-cu12': '0.6.3', 'nvidia-nccl-cu12': '2.26.2', 'nvidia-nvtx-cu12': '12.6.77', 'nvidia-nvjitlink-cu12': '12.6.85', 'nvidia-cufile-cu12': '1.11.1.6', 'triton': '3.3.1'}, 'requirements_text': 'cloudpickle==3.1.2\ncolorama==0.4.6\nduckdb==1.5.6\nfilelock==4.2.5\nfsspec==2026.9.0\niniconfig==2.3.1\njinja2==3.1.6\njoblib==1.6.0\nmarkupsafe==3.0.4\nmpmath==1.3.0\nnarwhals==2.28.0\nnetworkx==3.7\nnumpy==2.5.4\npackaging==26.3\npandas==3.0.6\npluggy==1.7.0\npsutil==7.2.2\npygments==2.21.0\npytest==9.1.1\npython-dateutil==3.0.0\nscikit-learn==1.9.1\nscipy==1.18.1\nsetuptools==84.2.1\nsix==1.17.0\nsympy==1.14.0\nthreadpoolctl==3.7.0\ntorch==2.7.1+cu126\ntyping-extensions==4.16.0\ntzdata==2026.6\n', 'requirements_sha256': '395dba5312bc18ee75c8cdda6fcfeeac6ba344ee751f8fcadb3efaba064ce25b', 'torch_sha256': 'a05c0001fd1d0ceae9cda8c8c1b8a16ed5def858fe996c9237a28016559dad52', 'triton_sha256': 'b89d846b5a4198317fec27a5d3a609ea96b6d557ff44b56c23176546023c4240'}
ROOT=Path('/content/KLTN_GPU08_20261108_01')
VENV=ROOT/'.venv';TARGET=VENV/'bin/python'
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==EXPECTED_SOURCE_SHA256
assert platform.system()=='Linux' and platform.machine()=='x86_64' and sys.version_info[:2]==(3,13)
assert (ROOT/'venv.json').is_file() and 'include-system-site-packages = false' in (VENV/'pyvenv.cfg').read_text().lower()
assert os.environ.get('COLAB_GPU','') in ('','0'), 'CPU-only preparation stage; no GPU runtime requested'
probe_code="""import importlib.util,json,sys,sysconfig
print(json.dumps({'prefix':sys.prefix,'executable':sys.executable,'purelib':sysconfig.get_path('purelib'),
 'torch':str(importlib.util.find_spec('torch')),'numpy':str(importlib.util.find_spec('numpy')),
 'pip':str(importlib.util.find_spec('pip'))}))
"""
probe_before=json.loads(subprocess.check_output([str(TARGET),'-B','-c',probe_code],text=True,timeout=15))
assert probe_before['prefix']==str(VENV) and Path(probe_before['purelib']).is_relative_to(VENV)
assert probe_before['torch']==probe_before['numpy']==probe_before['pip']=='None'
site=Path(probe_before['purelib'])
before_site=sorted(p.relative_to(site).as_posix() for p in site.rglob('*'))
attempt=ROOT/'resolution-attempt01';attempt.mkdir(exist_ok=False)
for name in ('tmp','cache'):(attempt/name).mkdir()
requirements=attempt/'requirements-proposed.txt'
requirements.write_bytes(SPEC['requirements_text'].encode())
assert hashlib.sha256(requirements.read_bytes()).hexdigest()==SPEC['requirements_sha256']
report_path=attempt/'pip-report.json'
command=[sys.executable,'-B','-m','pip','--python',str(TARGET),'install','--dry-run','--ignore-installed',
 '--only-binary=:all:','--no-input','--disable-pip-version-check','--progress-bar','off','--retries','0','--timeout','12',
 '--cache-dir',str(attempt/'cache'),'--index-url','https://download.pytorch.org/whl/cu126',
 '--extra-index-url','https://pypi.org/simple','--report',str(report_path),'-r',str(requirements)]
assert '--dry-run' in command and '--ignore-installed' in command and '--only-binary=:all:' in command
env={k:v for k,v in os.environ.items() if not k.startswith(('PIP_','UV_'))}
env.update(PIP_CONFIG_FILE=os.devnull,PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_NO_INPUT='1',
           PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(attempt/'tmp'),CUDA_VISIBLE_DEVICES='')
start=time.monotonic();reason=None;peak=0
def materialized_bytes():
    total=0
    for path in attempt.rglob('*'):
        try:
            if path.is_file() and not path.is_symlink():total+=path.stat().st_size
        except FileNotFoundError:pass  # pip có thể vừa dọn temp file.
    return total
with (attempt/'pip.stdout.log').open('xb') as stdout,(attempt/'pip.stderr.log').open('xb') as stderr:
    process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
    try:
        while process.poll() is None:
            size=materialized_bytes();peak=max(peak,size)
            if time.monotonic()-start>=180:reason='wall_budget_180s'
            elif size>256*1024**2:reason='cooperative_workspace_budget_256MiB'
            if reason:break
            time.sleep(1)
    finally:
        # --python có thể tạo descendant: dọn owned group kể cả leader đã exit.
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        returncode=process.wait(timeout=10)
elapsed=time.monotonic()-start;peak=max(peak,materialized_bytes())
if reason is None and elapsed>180:reason='postexit_wall_budget_180s'
if reason is None and peak>256*1024**2:reason='postexit_cooperative_workspace_budget_256MiB'
probe_after=json.loads(subprocess.check_output([str(TARGET),'-B','-c',probe_code],text=True,timeout=15))
after_site=sorted(p.relative_to(site).as_posix() for p in site.rglob('*'))
summary={'stage':'GPU08_ACTUAL_LINUX_BOUNDED_RESOLVER','returncode':returncode,'stop_reason':reason,
 'elapsed_seconds':elapsed,'peak_observed_workspace_bytes':peak,'workspace_cap_is_cooperative':True,
 'network_byte_cap':False,'wheel_fetch_absence_proven':False,'packages_installed':0,
 'isolated_site_unchanged':probe_after==probe_before and before_site==after_site,
 'python':sys.version,'platform':platform.platform(),'probe_before':probe_before,'probe_after':probe_after,
 'base_pip_controls_target_venv':True,'source_lock_sha256':SPEC['source_lock_sha256'],
 'requirements_sha256':SPEC['requirements_sha256'],'gpu_model_steps':0,'modal_calls':0,
 'executed_source_sha256':EXPECTED_SOURCE_SHA256,
 'source_docs':['https://pip.pypa.io/en/stable/topics/python-option/',
                'https://pip.pypa.io/en/stable/cli/pip_install/'],
 'limitations':['Resolver may fetch wheel bytes for metadata; polling is not a hard network/disk cap.',
                'Index-provided wheel hashes not verified against all wheel bytes; no install/image/runtime/GPU acceptance.']}
assert summary['isolated_site_unchanged'], 'unexpected target site-packages mutation'
if returncode==0 and reason is None:
    report=json.loads(report_path.read_text())
    environment=report['environment']
    assert environment['sys_platform']=='linux' and environment['platform_machine']=='x86_64'
    assert environment['python_full_version']==platform.python_version()
    selected={};lines=[]
    for item in report['install']:
        name=re.sub(r'[-_.]+','-',item['metadata']['name']).lower()
        assert name not in selected and not item.get('is_yanked',False)
        version=item['metadata']['version'];download=item['download_info'];url=download['url'];parts=urlsplit(url)
        assert parts.scheme=='https' and parts.hostname in {'files.pythonhosted.org','download.pytorch.org','download-r2.pytorch.org'}
        assert parts.username is None and parts.password is None and not parts.query and not parts.fragment
        assert parts.path.endswith('.whl') and 'win_amd64' not in parts.path and 'macosx' not in parts.path
        digest=download['archive_info']['hashes']['sha256'];assert re.fullmatch('[a-f0-9]{64}',digest)
        selected[name]={'version':version,'url':url,'sha256_from_pip_index_report':digest,
                        'requires_dist':item['metadata'].get('requires_dist',[])}
    for name,version in SPEC['root_pins'].items():assert selected[name]['version']==version,(name,version)
    for name,version in SPEC['cuda_pins'].items():assert selected[name]['version']==version,(name,version)
    assert selected['torch']['sha256_from_pip_index_report']==SPEC['torch_sha256']
    assert selected['triton']['sha256_from_pip_index_report']==SPEC['triton_sha256']
    for name,row in sorted(selected.items()):lines.append(f"{name} @ {row['url']} --hash=sha256:{row['sha256_from_pip_index_report']}")
    lock=attempt/'candidate-linux-cuda.lock.txt';lock.write_bytes(('\n'.join(lines)+'\n').encode())
    summary.update(status='CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED',pip_version=report['pip_version'],
        selected_packages=selected,package_count=len(selected),nvidia_package_count=sum(n.startswith('nvidia-') for n in selected),
        report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        candidate_lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest(),environment=environment)
else:summary['status']='RESOLUTION_FAILED_NO_AUTOMATIC_RETRY'
(attempt/'resolution.json').write_text(json.dumps(summary,indent=2)+'\n')
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==EXPECTED_SOURCE_SHA256
# Output nhỏ; raw resolver report/logs lưu riêng và sẽ export/hash trước đóng runtime.
output={k:v for k,v in summary.items() if k!='selected_packages'}
print(json.dumps(output,indent=2))
