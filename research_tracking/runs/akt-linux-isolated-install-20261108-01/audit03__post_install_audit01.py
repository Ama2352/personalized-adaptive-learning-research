"""Proposal: read-only audit existing installed venv, not a reinstall/retry of02.

One CPU-only child, <=90s overall including cleanup. No pip/network/model calls.
Audit evidence is separate: both original install attempts remain FAILED.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import signal
import stat
import subprocess
import sys
import time
import traceback

ROOT=Path('/content/KLTN_GPU08_20261108_01')
VENV=ROOT/'.venv'
TARGET=VENV/'bin/python'
AUDIT=ROOT/'post-install-audit01'
CAP_SECONDS=90
CAP_BYTES=20*1024**3
MIN_FREE=30*1024**3
PINS={
 'resolution-attempt01/pip-report.json':'92a2bbae1cdf285491bac1d67082d16c824aeb2ca9447d841a8182807be671dd',
 'resolution-attempt01/candidate-linux-cuda.lock.txt':'60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a',
 'install-attempt02/pip-install-report.json':'a689302643eef8b3e6699a074ad6421933086195430614d88de81cc2b34a54ce',
 'install-attempt02/result.json':'2ce1bb8efceb4baccab106565280b1a987a9989fcc2116ef4f803687f08b3918',
 'install-attempt02/output-manifest.json':'1e449f86d8da250347ffe0ebbe2ab292b787466c57ba27a5fbcc737bc38282eb',
 'install-attempt02/pip-check.stdout':'9261363b733079a641c2e4cc9bc46ffa1d8336945a87f807b6cf68847dbc9b09',
 'install_stage_attempt02.py':'021dcbe8a4a4a994d56572eb0ac76743c9a1bb3854cb56ca205da7017cb1a21f',
 '.venv/pyvenv.cfg':'0b85377496947675cd146fc9bcdab419ca9ab7eb4ce40d9a05df459330043366'}

CHILD="""import hashlib,importlib,importlib.metadata as m,json,platform,re,site,sys,sysconfig
from email.parser import BytesParser
from pathlib import Path,PurePosixPath
expected=EXPECTED_VERSIONS
def select_root_metadata(files,locate_file,venv,purelib):
 # Validate ALL RECORD origins, including nested vendored metadata and bin scripts.
 for item in files:
  if not Path(locate_file(item)).resolve().is_relative_to(venv.resolve()):raise ValueError('record file origin outside venv')
 candidates=[]
 for item in files:
  parts=PurePosixPath(str(item)).parts
  if len(parts)==2 and parts[0].endswith('.dist-info') and parts[1]=='METADATA':candidates.append(item)
 if len(candidates)!=1:raise ValueError('exactly one top-level dist-info/METADATA required')
 p=Path(locate_file(candidates[0]))
 if p.resolve().parent.parent!=purelib.resolve() or not p.resolve().is_relative_to(venv.resolve()):raise ValueError('root metadata origin mismatch')
 return p
norm=lambda x:re.sub(r'[-_.]+','-',x).lower()
v=Path('/content/KLTN_GPU08_20261108_01/.venv');pure=Path(sysconfig.get_path('purelib'))
assert sys.prefix==str(v) and sys.base_prefix=='/usr' and sys.executable==str(v/'bin/python')
assert platform.python_version()=='3.13.18' and platform.system()=='Linux' and platform.machine()=='x86_64'
assert platform.libc_ver()==('glibc','2.39') and pure.resolve().is_relative_to(v.resolve()) and site.ENABLE_USER_SITE is False
for entry in sys.path:
 if ('site-packages' in entry or 'dist-packages' in entry) and not Path(entry).resolve().is_relative_to(v.resolve()):raise ValueError('external site path')
rows={}
for d in m.distributions():
 name=norm(d.metadata['Name'])
 if name in rows:raise ValueError('duplicate distribution')
 assert name in expected and d.version==expected[name]
 files=list(d.files or ());assert files
 p=select_root_metadata(files,d.locate_file,v,pure);assert p.is_file()
 data=p.read_bytes();headers=BytesParser().parsebytes(data,headersonly=True)
 assert norm(headers['Name'])==name and headers['Version']==expected[name]
 all_depth=sum(str(f).endswith('.dist-info/METADATA') for f in files)
 rows[name]={'version':d.version,'metadata_file':str(p),'metadata_sha256':hashlib.sha256(data).hexdigest(),
             'file_count':len(files),'all_depth_metadata_count':all_depth,'nested_metadata_ignored':all_depth-1}
assert set(rows)==set(expected) and len(rows)==44
origins={}
for name in ('torch','numpy','pandas','duckdb','sklearn','scipy','psutil','pytest'):
 module=importlib.import_module(name);p=Path(module.__file__)
 assert p.resolve().is_relative_to(v.resolve())
 origins[name]={'file':str(p),'version':str(getattr(module,'__version__','not_exposed'))}
import torch
assert str(torch.__version__)=='2.7.1+cu126' and torch.version.cuda=='12.6'
assert not torch.cuda.is_initialized()
with torch.device('cpu'):scalar=torch.zeros(1,device='cpu')
assert scalar.device.type=='cpu' and scalar.item()==0. and not torch.cuda.is_initialized()
print(json.dumps({'prefix':sys.prefix,'executable':sys.executable,'python':platform.python_version(),
 'distributions':rows,'package_count':len(rows),'external_distribution_origins':0,'origins':origins,
 'torch_build':str(torch.__version__),'cuda_build_metadata':torch.version.cuda,'cuda_initialized':False,
 'cpu_scalar_check':True,'gpu_device_queries':0,'gpu_model_steps':0,'optimizer_steps':0}))
"""


def sha(data):return hashlib.sha256(data).hexdigest()
def read_regular(path,cap=1024**2):
    assert path.is_absolute() and path.is_relative_to(ROOT)
    for part in (path,*path.parents):
        assert not part.is_symlink()
        if part==ROOT:break
    assert stat.S_ISREG(path.stat().st_mode)
    with path.open('rb') as stream:data=stream.read(cap+1)
    assert len(data)<=cap
    return data


def selected(report):
    rows={}
    for item in report['install']:
        name=item['metadata']['name'];name=__import__('re').sub(r'[-_.]+','-',name).lower()
        assert name not in rows
        rows[name]={'version':item['metadata']['version'],'url':item['download_info']['url'],
                    'sha256':item['download_info']['archive_info']['hashes']['sha256']}
    assert len(rows)==44 and sum(n.startswith('nvidia-') for n in rows)==14
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-source-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args()
    start=time.monotonic();wall=time.time()
    assert os.name=='posix' and platform.system()=='Linux' and ROOT.is_dir() and ROOT.resolve()==ROOT
    assert ROOT.stat().st_uid==os.getuid() and Path(sys.executable)==Path('/usr/bin/python3') and sys.prefix=='/usr'
    assert not AUDIT.exists() and not AUDIT.is_symlink()
    AUDIT.mkdir(exist_ok=False)
    result={'status':'FAILED_READ_ONLY_POST_INSTALL_AUDIT','stage':'POST_INSTALL_AUDIT01_SEPARATE_FROM_FAILED_INSTALL02',
            'source_sha256':args.expected_source_sha256,'approval_reference':args.approval_reference,
            'install_calls':0,'pip_calls':0,'network_calls':0,'gpu_model_steps':0,'optimizer_steps':0,'modal_calls':0,
            'prior_install02_status':'FAILED_RETAIN_PARTIAL_NO_RETRY','cpu_only':True,'whole_host_attestation':False}
    process=None;cleanup_attempted=False;cleanup_ok=False;candidate=False;peak=0;sample_count=0;cleanup=[]
    def check():
        nonlocal peak,sample_count
        elapsed=time.monotonic()-start;elapsed_wall=time.time()-wall
        assert all(math.isfinite(v) and 0<=v<=CAP_SECONDS for v in (elapsed,elapsed_wall)), 'overall90s limit'
        assert not (AUDIT/'CANCEL').exists(), 'audit cancelled'
        logical=allocated=0
        for directory,_,names in os.walk(ROOT,followlinks=False):
            for name in names:
                try:st=os.lstat(Path(directory)/name)
                except FileNotFoundError:continue
                logical+=st.st_size;allocated+=getattr(st,'st_blocks',0)*512
        total=max(logical,allocated);peak=max(peak,total);sample_count+=1
        assert total<=CAP_BYTES, 'workspace20GiB cooperative limit'
        import shutil
        assert shutil.disk_usage(ROOT).free>=MIN_FREE, 'min30GiB free'
        assert sum(p.stat().st_size for p in AUDIT.iterdir() if p.suffix in {'.stdout','.stderr'})<=4*1024**2
    def cleanup_once():
        nonlocal cleanup_attempted,cleanup_ok
        if process is None or cleanup_attempted:return
        cleanup_attempted=True;failed=False;pgid=process.pid
        if pgid<=1 or pgid==os.getpgrp():failed=True;cleanup.append({'error':'refuse controller/global PGID'})
        else:
            for sig in (signal.SIGTERM,signal.SIGKILL):
                try:os.killpg(pgid,sig);cleanup.append({'signal':sig.name,'sent':True})
                except ProcessLookupError:cleanup.append({'signal':sig.name,'already_absent':True})
                except OSError as error:failed=True;cleanup.append({'signal':sig.name,'error':str(error)})
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:failed=True;cleanup.append({'error':'leader reap timeout'})
        result['child_returncode']=process.poll();cleanup_ok=not failed
    try:
        assert args.approval_reference.strip() and len(args.expected_source_sha256)==64
        source=Path(__file__).absolute();assert source==ROOT/'post_install_audit01.py'
        assert sha(read_regular(source))==args.expected_source_sha256
        assert os.environ.get('COLAB_GPU') in (None,'','0') and not os.environ.get('COLAB_TPU_ADDR') and not list(Path('/dev').glob('nvidia[0-9]*'))
        raw={name:read_regular(ROOT/name) for name in PINS}
        assert all(sha(raw[name])==h for name,h in PINS.items())
        target=selected(json.loads(raw['resolution-attempt01/pip-report.json']))
        assert selected(json.loads(raw['install-attempt02/pip-install-report.json']))==target
        prior=json.loads(raw['install-attempt02/result.json'])
        assert prior['status']=='FAILED_RETAIN_PARTIAL_NO_RETRY' and prior['error']=='distribution-origins failed; retain stdout/stderr'
        assert prior['owned_group_cleanup_accepted'] is True and prior['resource_time_verdict']=='ACCEPTED'
        assert [e['name'] for e in prior['children']]==['probe-before','base-pip-before','pip-install','pip-check','distribution-origins']
        assert [e['returncode'] for e in prior['children']]==[0,0,0,0,1]
        assert all(e['source_sha256']==PINS['install_stage_attempt02.py'] for e in prior['children'])
        assert raw['install-attempt02/pip-check.stdout'].decode().strip()=='No broken requirements found.'
        assert VENV.is_dir() and not VENV.is_symlink() and TARGET.is_file() and os.access(TARGET,os.X_OK)
        assert b'include-system-site-packages = false' in raw['.venv/pyvenv.cfg'].lower()
        env=os.environ.copy()
        for key in tuple(env):
            if key.startswith(('PIP_','UV_','PYTHON','CONDA_')) or key in {'HOME','VIRTUAL_ENV'}:env.pop(key,None)
        for name in ('home','tmp','cache'):(AUDIT/name).mkdir()
        env.update(HOME=str(AUDIT/'home'),TMPDIR=str(AUDIT/'tmp'),XDG_CACHE_HOME=str(AUDIT/'cache'),
                   TORCH_HOME=str(AUDIT/'cache'),TRITON_CACHE_DIR=str(AUDIT/'cache'),CUDA_CACHE_PATH=str(AUDIT/'cache'),
                   CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
                   OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PIP_CONFIG_FILE=os.devnull)
        code=CHILD.replace('EXPECTED_VERSIONS',repr({name:row['version'] for name,row in target.items()}))
        script=AUDIT/'audit-child.py'
        with script.open('x',encoding='utf-8') as stream:stream.write(code)
        check()
        with (AUDIT/'audit.stdout').open('xb') as stdout,(AUDIT/'audit.stderr').open('xb') as stderr:
            process=subprocess.Popen([str(TARGET),'-I','-B',str(script)],cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            result['child_pid']=process.pid
            try:
                while process.poll() is None:
                    check()
                    try:process.wait(timeout=.25)
                    except subprocess.TimeoutExpired:pass
                result['child_returncode']=process.returncode
            finally:cleanup_once()
            assert cleanup_ok, 'read-only audit cleanup unverified'
            check();assert process.returncode==0, 'read-only audit child failed; retain stderr'
        payload=json.loads(read_regular(AUDIT/'audit.stdout'))
        assert payload['package_count']==44 and payload['cuda_initialized'] is False and payload['cpu_scalar_check'] is True
        result['audit']=payload;result['input_sha256']=PINS
        assert sha(read_regular(source))==args.expected_source_sha256
        assert all(sha(read_regular(ROOT/name))==h for name,h in PINS.items())
        check();candidate=True
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error))
        with (AUDIT/'failure.log').open('x',encoding='utf-8') as stream:stream.write(traceback.format_exc())
    finally:
        cleanup_once()
        try:check();resource_ok=True
        except Exception as error:resource_ok=False;result['final_resource_error']=str(error)
        if candidate:
            try:
                assert sha(read_regular(source))==args.expected_source_sha256
                assert all(sha(read_regular(ROOT/name))==h for name,h in PINS.items())
            except Exception as error:candidate=False;result['final_binding_error']=str(error)
        elapsed=time.monotonic()-start;elapsed_wall=time.time()-wall
        if not all(math.isfinite(v) and 0<=v<=CAP_SECONDS for v in (elapsed,elapsed_wall)):
            resource_ok=False;result['final_resource_error']='post-check overall90s limit'
        if candidate and cleanup_ok and resource_ok:result['status']='EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY'
        result.update(elapsed_seconds=elapsed,elapsed_wall_seconds=elapsed_wall,timeout_seconds=90,
                      cleanup_attempted=cleanup_attempted,cleanup_accepted=cleanup_ok,cleanup=cleanup,
                      peak_observed_workspace_bytes=peak,cooperative_storage_monitor=True,resource_sample_count=sample_count,
                      resource_accepted=resource_ok,child_count=int(process is not None))
        with (AUDIT/'result.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
        inventory={p.name:{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in AUDIT.iterdir() if p.is_file()}
        with (AUDIT/'output-manifest.json').open('x',encoding='utf-8') as stream:json.dump({'status':result['status'],'outputs':inventory},stream,indent=2);stream.write('\n')
        print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'child_count':result['child_count'],
                          'result_sha256':sha((AUDIT/'result.json').read_bytes()),'output_manifest_sha256':sha((AUDIT/'output-manifest.json').read_bytes())}))
    return 0 if result['status']=='EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY' else 1


if __name__=='__main__':raise SystemExit(main())
