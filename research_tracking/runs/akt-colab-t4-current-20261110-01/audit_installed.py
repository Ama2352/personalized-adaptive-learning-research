import hashlib,importlib,importlib.metadata as m,json,platform,re,site,sys,sysconfig
from email.parser import BytesParser
from pathlib import Path,PurePosixPath
expected={'cloudpickle': '3.1.2', 'colorama': '0.4.6', 'duckdb': '1.5.6', 'filelock': '4.2.5', 'fsspec': '2026.9.0', 'iniconfig': '2.3.1', 'jinja2': '3.1.6', 'joblib': '1.6.0', 'markupsafe': '3.0.4', 'mpmath': '1.3.0', 'narwhals': '2.28.0', 'networkx': '3.7', 'numpy': '2.5.4', 'packaging': '26.3', 'pandas': '3.0.6', 'pluggy': '1.7.0', 'psutil': '7.2.2', 'pygments': '2.21.0', 'pytest': '9.1.1', 'python-dateutil': '3.0.0', 'scikit-learn': '1.9.1', 'scipy': '1.18.1', 'setuptools': '84.2.1', 'six': '1.17.0', 'sympy': '1.14.0', 'threadpoolctl': '3.7.0', 'torch': '2.7.1+cu126', 'typing-extensions': '4.16.0', 'tzdata': '2026.6', 'nvidia-cublas-cu12': '12.6.4.1', 'nvidia-cuda-cupti-cu12': '12.6.80', 'nvidia-cuda-nvrtc-cu12': '12.6.77', 'nvidia-cuda-runtime-cu12': '12.6.77', 'nvidia-cudnn-cu12': '9.5.1.17', 'nvidia-cufft-cu12': '11.3.0.4', 'nvidia-cufile-cu12': '1.11.1.6', 'nvidia-curand-cu12': '10.3.7.77', 'nvidia-cusolver-cu12': '11.7.1.2', 'nvidia-cusparse-cu12': '12.5.4.2', 'nvidia-cusparselt-cu12': '0.6.3', 'nvidia-nccl-cu12': '2.26.2', 'nvidia-nvjitlink-cu12': '12.6.85', 'nvidia-nvtx-cu12': '12.6.77', 'triton': '3.3.1'}
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
v=Path('/content/kltn-current-t4-20261110-01/.venv');pure=Path(sysconfig.get_path('purelib'))
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
