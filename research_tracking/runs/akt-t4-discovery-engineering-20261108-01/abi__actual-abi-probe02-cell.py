import json,os,platform,subprocess,sys,sysconfig
from pathlib import Path
def abi():
    gil=sysconfig.get_config_var('Py_GIL_DISABLED')
    return dict(platform_id=sys.platform,implementation=sys.implementation.name,
        python_version=platform.python_version(),machine=platform.machine(),libc=list(platform.libc_ver()),
        cache_tag=sys.implementation.cache_tag,soabi=sysconfig.get_config_var('SOABI'),
        extension_suffix=sysconfig.get_config_var('EXT_SUFFIX'),gil_disabled=0 if gil is None else gil)
target=Path('/content/KLTN_GPU08_20261108_01/.venv/bin/python')
if not target.is_file(): raise RuntimeError('existing project venv absent; no bootstrap permitted')
child="import json,platform,sys,sysconfig; g=sysconfig.get_config_var('Py_GIL_DISABLED'); print(json.dumps(dict(platform_id=sys.platform,implementation=sys.implementation.name,python_version=platform.python_version(),machine=platform.machine(),libc=list(platform.libc_ver()),cache_tag=sys.implementation.cache_tag,soabi=sysconfig.get_config_var('SOABI'),extension_suffix=sysconfig.get_config_var('EXT_SUFFIX'),gil_disabled=0 if g is None else g)))"
env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','CUDA_VISIBLE_DEVICES':'','NVIDIA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1'}
p=subprocess.run([str(target),'-I','-S','-B','-c',child],env=env,capture_output=True,text=True,timeout=10)
if p.returncode or len(p.stdout)>4096 or p.stderr: raise RuntimeError('bounded ABI child failed')
print(json.dumps(dict(status='ACTUAL_STDLIB_ABI_ONLY_NOT_GPU_READY',host_abi=abi(),target_abi=json.loads(p.stdout),target_executable=str(target),model_imports=0,gpu_queries=0,installs=0)))
