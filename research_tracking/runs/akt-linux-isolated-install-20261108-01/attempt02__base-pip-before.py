import hashlib,json,os,pip
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
