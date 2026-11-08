import hashlib,json,os,pip
from pathlib import Path
from pip._internal.configuration import Configuration
c=Configuration(isolated=False);c.load()
for key,value in c.items():
 if not (key.endswith('config-file') and value==os.devnull):raise ValueError('unexpected effective pip config; values not logged')
p=Path(pip.__file__);assert pip.__version__=='26.2.2'
assert str(p).startswith('/usr/local/lib/python3.13/dist-packages/pip/')
print(json.dumps({'version':pip.__version__,'file':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'effective_config_keys':sorted(key for key,_ in c.items()),'config_files_disabled_by_devnull':True}))
