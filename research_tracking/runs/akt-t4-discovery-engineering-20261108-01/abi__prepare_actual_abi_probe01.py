"""Chuẩn bị một cell chỉ đọc ABI stdlib thực tế, không import Torch/GPU."""
import json
from pathlib import Path

work = Path(__file__).resolve().parent
code = '''import json,os,platform,subprocess,sys,sysconfig
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
p=subprocess.run([str(target),'-I','-B','-c',child],env=env,capture_output=True,text=True,timeout=10)
if p.returncode or len(p.stdout)>4096 or p.stderr: raise RuntimeError('bounded ABI child failed')
print(json.dumps(dict(status='ACTUAL_STDLIB_ABI_ONLY_NOT_GPU_READY',host_abi=abi(),target_abi=json.loads(p.stdout),target_executable=str(target),model_imports=0,gpu_queries=0,installs=0)))
'''
compile(code, '<actual-abi-probe01>', 'exec')
with (work / 'actual-abi-probe01-cell.py').open('x', encoding='utf-8') as stream:
    stream.write(code)
request = work.parent / 'requests/gpu09-add-actual-abi-probe01.json'
with request.open('x', encoding='utf-8') as stream:
    json.dump(dict(cellIndex=0, language='python', code=code), stream)
private = work.parents[1] / 'private/colab-bridge/session-a67c8207b6224b9398ad00cfa0876435'
with (work / 'actual-abi-probe01-before-add.json').open('x', encoding='utf-8') as stream:
    json.dump([p.name for p in private.glob('result-*.json')], stream)
print(json.dumps({'status':'PREPARED_READONLY_ABI_PROBE', 'request':str(request), 'max_child_seconds':10}))
