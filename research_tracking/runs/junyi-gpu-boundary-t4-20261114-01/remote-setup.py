import json,subprocess,sys,time,traceback,os
from pathlib import Path
root=Path('/content/kltn-gpu-boundary-20261114-01');started=time.monotonic()
result={'status':'FAILED'}
try:
 subprocess.run([sys.executable,'-m','venv','--without-pip',str(root/'.venv')],check=True,timeout=45)
 subprocess.run([sys.executable,'-m','pip','--python',str(root/'.venv/bin/python'),'install','--disable-pip-version-check','--no-input','--require-hashes','--cache-dir',str(root/'runtime/pip-cache'),'-r',str(root/'runtime/linux-cuda.lock.txt')],check=True,timeout=480,env=dict(os.environ,TMPDIR=str(root/'runtime/tmp')))
 subprocess.run([str(root/'.venv/bin/python'),'-B','-c',"import torch,numpy,sys,json;print(json.dumps(dict(python=sys.executable,prefix=sys.prefix,torch=torch.__version__,numpy=numpy.__version__,torch_origin=torch.__file__)))"],check=True,timeout=90)
 result['status']='PROJECT_VENV_READY'
except BaseException as error:
 result.update(error_type=type(error).__name__,error=str(error));traceback.print_exc()
finally:
 result['seconds']=time.monotonic()-started;(root/'runtime/setup-result.json').write_text(json.dumps(result))
