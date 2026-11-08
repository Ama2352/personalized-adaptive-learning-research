import hashlib,importlib.metadata as m,json,re,sys,sysconfig
from pathlib import Path
expected={'cloudpickle': '3.1.2', 'colorama': '0.4.6', 'duckdb': '1.5.6', 'filelock': '4.2.5', 'fsspec': '2026.9.0', 'iniconfig': '2.3.1', 'jinja2': '3.1.6', 'joblib': '1.6.0', 'markupsafe': '3.0.4', 'mpmath': '1.3.0', 'narwhals': '2.28.0', 'networkx': '3.7', 'numpy': '2.5.4', 'packaging': '26.3', 'pandas': '3.0.6', 'pluggy': '1.7.0', 'psutil': '7.2.2', 'pygments': '2.21.0', 'pytest': '9.1.1', 'python-dateutil': '3.0.0', 'scikit-learn': '1.9.1', 'scipy': '1.18.1', 'setuptools': '84.2.1', 'six': '1.17.0', 'sympy': '1.14.0', 'threadpoolctl': '3.7.0', 'torch': '2.7.1+cu126', 'typing-extensions': '4.16.0', 'tzdata': '2026.6', 'nvidia-cublas-cu12': '12.6.4.1', 'nvidia-cuda-cupti-cu12': '12.6.80', 'nvidia-cuda-nvrtc-cu12': '12.6.77', 'nvidia-cuda-runtime-cu12': '12.6.77', 'nvidia-cudnn-cu12': '9.5.1.17', 'nvidia-cufft-cu12': '11.3.0.4', 'nvidia-cufile-cu12': '1.11.1.6', 'nvidia-curand-cu12': '10.3.7.77', 'nvidia-cusolver-cu12': '11.7.1.2', 'nvidia-cusparse-cu12': '12.5.4.2', 'nvidia-cusparselt-cu12': '0.6.3', 'nvidia-nccl-cu12': '2.26.2', 'nvidia-nvjitlink-cu12': '12.6.85', 'nvidia-nvtx-cu12': '12.6.77', 'triton': '3.3.1'}
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
