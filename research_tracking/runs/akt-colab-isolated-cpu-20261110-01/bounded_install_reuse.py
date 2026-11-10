"""Trích nguyên Stage, PROBE và BASE_PIP đã kiểm; không chạy installer main cũ."""
import hashlib,json,math,os,re,shutil,signal,stat,subprocess,time
from pathlib import Path
ROOT=Path('/content/kltn-isolated-cpu-20261110-01')
ATTEMPT=ROOT/'artifacts/akt/runtime/isolated-install01'
CAP_SECONDS=600
CAP_WORKSPACE=20*1024**3
FLOOR_FREE=30*1024**3
CAP_LOGS=32*1024**2
def digest(data):return hashlib.sha256(data).hexdigest()

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
v=Path('/content/kltn-isolated-cpu-20261110-01/.venv')
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
def verify_effective_config(items,environ,devnull):
 # Accept only the two exact observed API shapes; never flatten arbitrary sections.
 pip_env={k:v for k,v in environ.items() if k.startswith('PIP_')}
 if pip_env!={'PIP_CONFIG_FILE':devnull}:raise ValueError('unexpected pip environment; values not logged')
 rows=list(items)
 if len(rows)!=1:raise ValueError('unexpected effective pip config cardinality; values not logged')
 row=rows[0]
 if not isinstance(row,(tuple,list)) or len(row)!=2:raise ValueError('unexpected pip config item shape')
 key,value=row
 if type(key) is not str:raise ValueError('unexpected pip config key type')
 if key==':env:.config-file' and type(value) is str and value==devnull:
  shape='flat'
 elif key==':env:' and type(value) is dict and len(value)==1 and set(value)=={':env:.config-file'} and type(value[':env:.config-file']) is str and value[':env:.config-file']==devnull:
  shape='nested'
 else:raise ValueError('unexpected effective pip config; values not logged')
 return {'effective_config_keys':[':env:.config-file'],'config_api_shape':shape,'pip_environment_names':['PIP_CONFIG_FILE']}
c=Configuration(isolated=False);c.load()
audit=verify_effective_config(c.items(),os.environ,os.devnull)
p=Path(pip.__file__);assert pip.__version__=='26.2.2'
assert str(p).startswith('/usr/local/lib/python3.13/dist-packages/pip/')
print(json.dumps({'version':pip.__version__,'file':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 **audit,'config_files_disabled_by_devnull':True}))
"""

def normalize(name):return re.sub(r"[-_.]+","-",name).lower()
