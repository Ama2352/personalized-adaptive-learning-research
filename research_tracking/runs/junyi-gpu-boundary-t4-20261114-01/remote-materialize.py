from pathlib import Path,PurePosixPath
import hashlib,json,zipfile,subprocess,traceback,time,os
root=Path('/content/kltn-gpu-boundary-20261114-01');started=time.monotonic();result={'status':'FAILED'}
try:
 p=root/'runtime/input.zip'
 assert hashlib.sha256(p.read_bytes()).hexdigest()=='fe80bbc39d2a399b4ce939532ed475e5b12434dac0b7a1d8699ea2796f95d914'
 with zipfile.ZipFile(p) as saved:
  manifest=json.loads(saved.read('BOUNDARY_MANIFEST.json'));pins=manifest['files']
  assert set(saved.namelist())==set(pins)|{'BOUNDARY_MANIFEST.json'} and len(saved.namelist())==len(pins)+1
  for name,pin in pins.items():
   relative=PurePosixPath(name)
   assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] not in ('dataset','.venv','venv','.git','.wsl') and 'private' not in relative.parts
   raw=saved.read(name);assert hashlib.sha256(raw).hexdigest()==pin
   path=root.joinpath(*relative.parts);assert path.resolve().is_relative_to(root)
   path.parent.mkdir(parents=True,exist_ok=True)
   if path.exists():assert path.read_bytes()==raw
   else:path.write_bytes(raw)
 upstream=root/'artifacts/akt/dependencies/upstream';upstream.parent.mkdir(parents=True,exist_ok=True)
 env=dict(os.environ,GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_TERMINAL_PROMPT='0',PYTHONDONTWRITEBYTECODE='1')
 for command in [['git','init','-q',str(upstream)],['git','-C',str(upstream),'remote','add','origin','https://github.com/arghosh/AKT.git'],['git','-C',str(upstream),'fetch','--depth','1','origin','01b7e8d7d7c862cabc9467108e3e7f2555653a88'],['git','-C',str(upstream),'checkout','--detach','FETCH_HEAD']]:
  subprocess.run(command,check=True,timeout=90,env=env)
 result.update(status='SOURCE_AND_OFFLINE_CACHES_MATERIALIZED',files=len(pins),input_sha256='fe80bbc39d2a399b4ce939532ed475e5b12434dac0b7a1d8699ea2796f95d914')
except BaseException as error:
 result.update(error_type=type(error).__name__,error=str(error));traceback.print_exc()
finally:
 result['seconds']=time.monotonic()-started;(root/'runtime/materialization-result.json').write_text(json.dumps(result))
