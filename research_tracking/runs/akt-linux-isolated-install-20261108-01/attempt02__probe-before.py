import importlib.metadata as m,importlib.util,json,platform,site,sys,sysconfig
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
