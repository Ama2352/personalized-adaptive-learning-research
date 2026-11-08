"""Draft GPU08 isolated CPU install controller. DO NOT EXECUTE before peer review.

Stdlib only in controller; exact44direct-wheel lock, one exclusive attempt.
Storage monitoring is cooperative, not a filesystem quota or network byte cap.
"""
import sys
sys.dont_write_bytecode=True
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import subprocess
import time
import traceback
from urllib.parse import urlsplit

ROOT=Path("/content/KLTN_GPU08_20261108_01")
VENV=ROOT/".venv"
TARGET=VENV/"bin/python"  # Keep raw venv entrypoint; do not replace by resolved base.
BASE=Path("/usr/bin/python3")
ATTEMPT=ROOT/"install-attempt01"
CAP_SECONDS=600
CAP_WORKSPACE=20*1024**3
FLOOR_FREE=30*1024**3
CAP_LOGS=32*1024**2
PINS={"resolution-attempt01/candidate-linux-cuda.lock.txt":"60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a",
      "resolution-attempt01/pip-report.json":"92a2bbae1cdf285491bac1d67082d16c824aeb2ca9447d841a8182807be671dd",
      "resolution-attempt01/resolution.json":"32fe949645d44a84e236c5a579be6312cd8c72e19ebd2e8c3c35de0aee216397",
      "venv.json":"5dc1116b951942bb73e765cd180f3b99d9862295c359f02a714402d471e749be",
      ".venv/pyvenv.cfg":"0b85377496947675cd146fc9bcdab419ca9ab7eb4ce40d9a05df459330043366"}


def digest(data):return hashlib.sha256(data).hexdigest()
def normalize(name):return re.sub(r"[-_.]+","-",name).lower()
def write_json(name,value):
    with (ATTEMPT/name).open("x",encoding="utf8") as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write("\n")


def read_owned(path,limit):
    if not path.is_absolute() or not path.is_relative_to(ROOT):raise ValueError("path outside owned root")
    for part in (path,*path.parents):
        if part.is_symlink():raise ValueError("symlink input/root forbidden")
        if part==ROOT:break
    if not stat.S_ISREG(path.stat().st_mode):raise ValueError("regular input required")
    with path.open("rb") as stream:data=stream.read(limit+1)
    if len(data)>limit:raise ValueError("input byte cap")
    return data


class Stage:
    def __init__(self,source_sha,approval_reference):
        self.start=time.monotonic();self.wall=time.time();self.deadline=self.start+CAP_SECONDS
        self.source_sha=source_sha;self.approval=approval_reference
        self.children=[];self.samples=[];self.cleanup=[];self.peak=0
        self.env=os.environ.copy()
        for key in tuple(self.env):
            if key.startswith(("PIP_","UV_","PYTHON","CONDA_")) or key in {"HOME","VIRTUAL_ENV"}:self.env.pop(key,None)
        self.env.update(PIP_CONFIG_FILE=os.devnull,HOME=str(ATTEMPT/"home"),TMPDIR=str(ATTEMPT/"tmp"),
            XDG_CACHE_HOME=str(ATTEMPT/"cache-home"),XDG_CONFIG_HOME=str(ATTEMPT/"config-home"),
            TORCH_HOME=str(ATTEMPT/"torch-home"),TRITON_CACHE_DIR=str(ATTEMPT/"triton-cache"),
            CUDA_CACHE_PATH=str(ATTEMPT/"cuda-cache"),CUDA_VISIBLE_DEVICES="",NVIDIA_VISIBLE_DEVICES="",
            PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1",OMP_NUM_THREADS="2",MKL_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",
            GPU08_INSTALL_ATTEMPT=str(ATTEMPT))

    def check(self):
        elapsed=time.monotonic()-self.start;wall=time.time()-self.wall
        if not all(math.isfinite(v) and 0<=v<=CAP_SECONDS for v in (elapsed,wall)):raise TimeoutError("overall elapsed budget")
        if (ATTEMPT/"CANCEL").exists():raise RuntimeError("owned stage cancellation requested")
        logical=allocated=0
        for directory,_,files in os.walk(ROOT,followlinks=False):
            for name in files:
                try:s=os.lstat(Path(directory)/name)
                except FileNotFoundError:continue
                logical+=s.st_size;allocated+=getattr(s,"st_blocks",0)*512
        total=max(logical,allocated);free=shutil.disk_usage(ROOT).free
        self.peak=max(self.peak,total)
        if len(self.samples)<3000:self.samples.append({"elapsed_seconds":elapsed,"wall_seconds":wall,"workspace_bytes":total,"free_bytes":free})
        if total>CAP_WORKSPACE:raise OSError("owned workspace exceeds20GiB")
        if free<FLOOR_FREE:raise OSError("available disk below30GiB")
        logs=sum(p.stat().st_size for p in ATTEMPT.iterdir() if p.suffix in {".stdout",".stderr"})
        if logs>CAP_LOGS:raise OSError("log cap32MiB")

    def kill_owned(self,entry):
        # Every child starts a new session, so its initial PID is its owned PGID.
        if entry.get("cleanup_attempted"):
            return  # Never re-signal a historical PGID, even after an unverified cleanup.
        entry["cleanup_attempted"]=True
        pgid=entry["pgid"]
        if pgid<=1 or pgid==os.getpgrp():
            entry["group_cleanup_completed"]=False
            self.cleanup.append({"pgid":pgid,"error":"refuse controller/global process-group signal"})
            return
        failed=False
        for sig in (signal.SIGTERM,signal.SIGKILL):
            try:os.killpg(pgid,sig);self.cleanup.append({"pgid":pgid,"signal":sig.name,"sent":True})
            except ProcessLookupError:self.cleanup.append({"pgid":pgid,"signal":sig.name,"already_absent":True})
            except OSError as error:
                failed=True;self.cleanup.append({"pgid":pgid,"signal":sig.name,"error":str(error)})
        entry["group_cleanup_completed"]=not failed

    def run(self,name,command,limit):
        self.check()
        limit=min(limit,max(0.,self.deadline-time.monotonic()))
        if limit<=0:raise TimeoutError("no remaining subprocess budget")
        with (ATTEMPT/(name+".stdout")).open("xb") as stdout,(ATTEMPT/(name+".stderr")).open("xb") as stderr:
            process=subprocess.Popen(command,cwd=ROOT,env=self.env,stdout=stdout,stderr=stderr,start_new_session=True)
            entry={"name":name,"pid":process.pid,"pgid":process.pid,"command":command,"source_sha256":self.source_sha}
            self.children.append(entry);started=time.monotonic()
            try:
                while process.poll() is None:
                    self.check()
                    if time.monotonic()-started>limit:raise TimeoutError(name+" subprocess budget")
                    try:process.wait(timeout=.25)
                    except subprocess.TimeoutExpired:pass
                entry["returncode"]=process.returncode
                entry["elapsed_seconds"]=time.monotonic()-started
                self.check()
                if entry["returncode"]!=0:raise RuntimeError(name+" failed; retain stdout/stderr")
            finally:
                # Also cancel descendants that survived an exited leader. Never pkill.
                entry.setdefault("elapsed_seconds",time.monotonic()-started)
                self.kill_owned(entry)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    entry["reap_failed"]=True
                    entry["group_cleanup_completed"]=False
                entry["returncode"]=process.poll()
                entry["elapsed_including_cleanup_seconds"]=time.monotonic()-started
        if not entry.get("group_cleanup_completed") or entry.get("reap_failed"):
            raise RuntimeError(name+" CLEANUP_UNVERIFIED; no further install acceptance")
        return (ATTEMPT/(name+".stdout")).read_text(encoding="utf8")

    def python(self,name,interpreter,code,limit=30):
        p=ATTEMPT/(name+".py")
        with p.open("x",encoding="utf8") as stream:stream.write(code)
        output=self.run(name,[str(interpreter),"-I","-B",str(p)],limit)
        return json.loads(output)


PROBE="""import importlib.metadata as m,importlib.util,json,platform,site,sys,sysconfig
from pathlib import Path
v=Path('/content/KLTN_GPU08_20261108_01/.venv')
assert sys.prefix==str(v) and sys.base_prefix=='/usr' and sys.executable==str(v/'bin/python')
assert platform.python_version()=='3.13.18' and platform.system()=='Linux' and platform.machine()=='x86_64'
assert platform.libc_ver()==('glibc','2.39') and site.ENABLE_USER_SITE is False
pure=Path(sysconfig.get_path('purelib'));assert pure.is_relative_to(v)
for p in sys.path:
 if ('site-packages' in p or 'dist-packages' in p) and not Path(p).is_relative_to(v):raise ValueError('external site path')
print(json.dumps({'prefix':sys.prefix,'executable':sys.executable,'base_prefix':sys.base_prefix,'purelib':str(pure),
 'python':platform.python_version(),'platform':platform.platform(),'user_site':site.ENABLE_USER_SITE,
 'distributions':sorted((d.metadata['Name'],d.version) for d in m.distributions()),
 'torch_spec':str(importlib.util.find_spec('torch')),'numpy_spec':str(importlib.util.find_spec('numpy')),
 'pip_spec':str(importlib.util.find_spec('pip')),'purelib_entries':sorted(p.name for p in pure.iterdir())}))
"""

BASE_PIP="""import hashlib,json,os,pip
from pathlib import Path
from pip._internal.configuration import Configuration
c=Configuration(isolated=False);c.load()
for key,value in c.items():
 if not (key.endswith('config-file') and value==os.devnull):raise ValueError('unexpected effective pip config; values not logged')
p=Path(pip.__file__);assert pip.__version__=='26.2.2'
assert str(p).startswith('/usr/local/lib/python3.13/dist-packages/pip/')
print(json.dumps({'version':pip.__version__,'file':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'effective_config_keys':sorted(key for key,_ in c.items()),'config_files_disabled_by_devnull':True}))
"""

AUDIT="""import hashlib,importlib.metadata as m,json,re,sys,sysconfig
from pathlib import Path
expected=EXPECTED
norm=lambda x:re.sub(r'[-_.]+','-',x).lower()
v=Path('/content/KLTN_GPU08_20261108_01/.venv');pure=Path(sysconfig.get_path('purelib'))
assert sys.prefix==str(v) and sys.executable==str(v/'bin/python') and pure.is_relative_to(v)
rows={}
for d in m.distributions():
 name=norm(d.metadata['Name'])
 if name in rows:raise ValueError('duplicate distribution')
 assert name in expected and d.version==expected[name]
 files=list(d.files or ());assert files
 for f in files:assert Path(d.locate_file(f)).resolve().is_relative_to(v)
 metadata=[Path(d.locate_file(f)) for f in files if str(f).endswith('.dist-info/METADATA')];assert len(metadata)==1
 p=metadata[0];assert p.is_file() and p.resolve().is_relative_to(v)
 rows[name]={'version':d.version,'metadata_file':str(p),'metadata_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'file_count':len(files)}
assert set(rows)==set(expected) and len(rows)==44
print(json.dumps({'prefix':sys.prefix,'distributions':rows,'package_count':len(rows),'external_distribution_origins':0}))
"""

CPU_IMPORT="""import importlib,json,sys
from pathlib import Path
v=Path('/content/KLTN_GPU08_20261108_01/.venv');assert sys.prefix==str(v)
origins={}
for name in ('torch','numpy','pandas','duckdb','sklearn','scipy','psutil','pytest'):
 module=importlib.import_module(name);p=Path(module.__file__)
 assert p.resolve().is_relative_to(v)
 origins[name]={'file':str(p),'version':str(getattr(module,'__version__','not_exposed'))}
import torch
assert str(torch.__version__)=='2.7.1+cu126' and torch.version.cuda=='12.6'
assert not torch.cuda.is_initialized()
with torch.device('cpu'):scalar=torch.zeros(1,device='cpu')
assert scalar.device.type=='cpu' and scalar.item()==0.
assert not torch.cuda.is_initialized()
print(json.dumps({'origins':origins,'torch_build':str(torch.__version__),'cuda_build_metadata':torch.version.cuda,
 'cuda_initialized':False,'cpu_scalar_check':True,'gpu_device_queries':0,'gpu_model_steps':0,'optimizer_steps':0}))
"""


def parse_inputs():
    raw={name:read_owned(ROOT/name,1024**2) for name in PINS}
    for name,expected in PINS.items():
        if digest(raw[name])!=expected:raise ValueError("pinned input SHA mismatch: "+name)
    report=json.loads(raw["resolution-attempt01/pip-report.json"])
    resolution=json.loads(raw["resolution-attempt01/resolution.json"])
    assert report["pip_version"]=="26.2.2" and resolution["status"]=="CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED"
    assert resolution["package_count"]==44 and resolution["nvidia_package_count"]==14 and resolution["packages_installed"]==0
    assert report["environment"]["python_full_version"]=="3.13.18" and report["environment"]["platform_system"]=="Linux"
    selected={}
    for item in report["install"]:
        name=normalize(item["metadata"]["name"]);version=item["metadata"]["version"]
        info=item["download_info"];url=info["url"];parts=urlsplit(url)
        h=info["archive_info"]["hashes"]["sha256"]
        if (name in selected or not re.fullmatch(r"[a-z0-9-]+",name) or not re.fullmatch(r"[a-f0-9]{64}",h)
            or parts.scheme!="https" or parts.hostname not in {"files.pythonhosted.org","download.pytorch.org","download-r2.pytorch.org"}
            or parts.username or parts.password or parts.query or parts.fragment or parts.port not in (None,443) or not parts.path.endswith(".whl")):
            raise ValueError("direct-wheel allowlist violation")
        selected[name]={"version":version,"url":url,"sha256":h}
    lines=raw["resolution-attempt01/candidate-linux-cuda.lock.txt"].decode("utf8").splitlines()
    parsed={}
    for line in lines:
        fields=line.split()
        if len(fields)!=4 or fields[1]!="@" or not fields[3].startswith("--hash=sha256:"):raise ValueError("lock line grammar")
        name=normalize(fields[0]);assert name not in parsed and name in selected
        parsed[name]={"version":selected[name]["version"],"url":fields[2],"sha256":fields[3].removeprefix("--hash=sha256:")}
    assert parsed==selected and len(selected)==44 and len(lines)==44 and sum(n.startswith("nvidia-") for n in selected)==14
    return selected


def main(argv=None):
    p=argparse.ArgumentParser(description="DRAFT one isolated44wheel CPU install; review before execution")
    p.add_argument("--expected-source-sha256",required=True);p.add_argument("--approval-reference",required=True)
    args=p.parse_args(argv)
    # No output mutation if root/session is not the explicitly named owned root.
    assert os.name=="posix" and platform.system()=="Linux" and ROOT.is_dir() and ROOT.resolve()==ROOT
    assert ROOT.stat().st_uid==os.getuid() and not ATTEMPT.exists() and not ATTEMPT.is_symlink()
    assert Path(sys.executable)==BASE and sys.prefix=="/usr"
    ATTEMPT.mkdir(exist_ok=False)
    stage=Stage(args.expected_source_sha256,args.approval_reference)
    result={"stage":"GPU08_ISOLATED_CPU_INSTALL_ATTEMPT01","status":"FAILED","gpu_model_steps":0,"optimizer_steps":0,"modal_calls":0,
            "hard_storage_quota":False,"network_byte_cap":False,"approval_reference":args.approval_reference}
    error=None
    try:
        if not args.approval_reference.strip() or not re.fullmatch(r"[a-f0-9]{64}",args.expected_source_sha256):raise ValueError("explicit source/approval required")
        source_path=Path(__file__).absolute()
        assert source_path==ROOT/"install_stage.py"
        source=read_owned(source_path,128*1024)
        assert digest(source)==args.expected_source_sha256
        if os.environ.get("COLAB_GPU") not in (None,"","0") or os.environ.get("COLAB_TPU_ADDR") or list(Path('/dev').glob('nvidia[0-9]*')):
            raise ValueError("CPU runtime only, no GPU/TPU runtime")
        for name in ("tmp","home","cache-home","config-home","torch-home","triton-cache","cuda-cache"):(ATTEMPT/name).mkdir()
        selected=parse_inputs()
        assert VENV.is_dir() and not VENV.is_symlink() and TARGET.is_file() and os.access(TARGET,os.X_OK)
        cfg=read_owned(VENV/"pyvenv.cfg",4096).decode("utf8").lower()
        assert "include-system-site-packages = false" in cfg
        stage.check()
        probe=stage.python("probe-before",TARGET,PROBE,20)
        assert probe["distributions"]==[] and probe["purelib_entries"]==[] and probe["torch_spec"]==probe["numpy_spec"]==probe["pip_spec"]=="None"
        base_before=stage.python("base-pip-before",BASE,BASE_PIP,20)
        write_json("invocation.json",{"source_sha256":digest(source),"input_sha256":PINS,"selected_wheels":selected,
             "target":str(TARGET),"base":str(BASE),"caps":{"overall_seconds":600,"workspace_bytes":CAP_WORKSPACE,"min_free_bytes":FLOOR_FREE},
             "probe_before":probe,"base_pip":base_before,"no_global_install":True,"no_retry":True})
        command=[str(BASE),"-I","-B","-m","pip","--python",str(TARGET),"install","--require-hashes","--no-deps","--no-index",
            "--only-binary=:all:","--no-cache-dir","--no-compile","--no-input","--disable-pip-version-check","--progress-bar","off",
            "--retries","0","--timeout","20","--report",str(ATTEMPT/"pip-install-report.json"),"-r",str(ROOT/"resolution-attempt01/candidate-linux-cuda.lock.txt")]
        stage.run("pip-install",command,540)
        installed=json.loads(read_owned(ATTEMPT/"pip-install-report.json",8*1024**2))
        actual={normalize(i["metadata"]["name"]):{"version":i["metadata"]["version"],"url":i["download_info"]["url"],
                "sha256":i["download_info"]["archive_info"]["hashes"]["sha256"]} for i in installed["install"]}
        assert len(installed["install"])==44 and actual==selected
        stage.run("pip-check",[str(BASE),"-I","-B","-m","pip","--python",str(TARGET),"check"],30)
        versions={name:item["version"] for name,item in selected.items()}
        origins=stage.python("distribution-origins",TARGET,AUDIT.replace("EXPECTED",repr(versions)),30)
        cpu=stage.python("cpu-import",TARGET,CPU_IMPORT,45)
        base_after=stage.python("base-pip-after",BASE,BASE_PIP,20)
        assert base_before==base_after
        assert digest(read_owned(source_path,128*1024))==args.expected_source_sha256
        for name,h in PINS.items():assert digest(read_owned(ROOT/name,1024**2))==h
        stage.check()
        result.update(status="INSTALLED_CPU_IMPORT_ACCEPTED_NOT_GPU_READY",packages_installed=44,nvidia_packages=14,
                      install_report_sha256=digest(read_owned(ATTEMPT/"pip-install-report.json",8*1024**2)),
                      distribution_origins=origins,cpu_import=cpu,base_pip_before_after_identical=True,
                      wheel_integrity="pip --require-hashes enforced; no retained wheelhouse/image digest")
    except Exception as exc:
        error=exc
        result.update(status="FAILED_RETAIN_PARTIAL_NO_RETRY",error_type=type(exc).__name__,error=str(exc))
        with (ATTEMPT/"failure.log").open("x",encoding="utf8") as stream:stream.write(traceback.format_exc())
    finally:
        for entry in stage.children:
            if not entry.get("cleanup_attempted"):stage.kill_owned(entry)
        cleanup_ok=all(e.get("group_cleanup_completed") and not e.get("reap_failed") for e in stage.children)
        if not cleanup_ok:result["status"]="CLEANUP_UNVERIFIED_RETAIN_PARTIAL"
        elapsed=time.monotonic()-stage.start;wall=time.time()-stage.wall
        accepted_time=all(math.isfinite(v) and 0<=v<=600 for v in (elapsed,wall))
        if not accepted_time:result["status"]="REJECTED_RESOURCE_BOUND_RETAIN_PARTIAL"
        result.update(elapsed_seconds=elapsed,elapsed_wall_seconds=wall,timeout_seconds=600,
            resource_time_verdict="ACCEPTED" if accepted_time else "REJECTED",peak_observed_workspace_bytes=stage.peak,
            storage_bound_is_cooperative=True,children=stage.children,owned_group_cleanup=stage.cleanup,
            owned_group_cleanup_accepted=cleanup_ok,cleanup_verdict="ACCEPTED" if cleanup_ok else "CLEANUP_UNVERIFIED",
            resource_samples=stage.samples)
        write_json("result.json",result)
        manifest={p.name:{"sha256":digest(p.read_bytes()),"bytes":p.stat().st_size} for p in ATTEMPT.iterdir() if p.is_file()}
        write_json("output-manifest.json",{"stage_status":result["status"],"outputs":manifest,"excludes":"installed .venv and temp/cache directories; no binary export"})
        print(json.dumps({"status":result["status"],"elapsed_seconds":elapsed,"elapsed_wall_seconds":wall,"packages_installed":result.get("packages_installed"),
                          "result_sha256":digest((ATTEMPT/"result.json").read_bytes()),"output_manifest_sha256":digest((ATTEMPT/"output-manifest.json").read_bytes())}))
    return 0 if error is None and result["status"]=="INSTALLED_CPU_IMPORT_ACCEPTED_NOT_GPU_READY" else 1


if __name__=="__main__":raise SystemExit(main())
