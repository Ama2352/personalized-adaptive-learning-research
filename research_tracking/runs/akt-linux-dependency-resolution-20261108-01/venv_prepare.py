import hashlib, json, os, subprocess, sys
from pathlib import Path
ROOT = Path('/content/KLTN_GPU08_20261108_01')
assert (ROOT/'connection.json').is_file()
VENV = ROOT/'.venv'
assert not VENV.exists()
command=[sys.executable,'-m','venv','--without-pip',str(VENV)]
result=subprocess.run(command,capture_output=True,text=True,timeout=30)
(ROOT/'venv-create.stdout').write_text(result.stdout)
(ROOT/'venv-create.stderr').write_text(result.stderr)
assert result.returncode==0, result.stderr
code="""import importlib.util,json,platform,sys,sysconfig
print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,
 'purelib':sysconfig.get_path('purelib'),'python':sys.version,'platform':platform.platform(),
 'torch_spec':str(importlib.util.find_spec('torch')),'numpy_spec':str(importlib.util.find_spec('numpy')),
 'pip_spec':str(importlib.util.find_spec('pip'))}))
"""
target=VENV/'bin/python'
probe=json.loads(subprocess.check_output([str(target),'-B','-c',code],text=True,timeout=15))
assert probe['prefix']==str(VENV) and probe['prefix']!=probe['base_prefix']
assert Path(probe['purelib']).is_relative_to(VENV)
assert probe['torch_spec']==probe['numpy_spec']==probe['pip_spec']=='None'
cfg=(VENV/'pyvenv.cfg').read_text()
assert 'include-system-site-packages = false' in cfg.lower()
pip_info=subprocess.check_output([sys.executable,'-m','pip','--version'],text=True,timeout=15).strip()
target_pip=subprocess.check_output([sys.executable,'-m','pip','--python',str(target),'--version'],text=True,timeout=15).strip()
payload={'stage':'GPU08_ISOLATED_VENV_PREPARED','root':str(ROOT),'venv':str(VENV),'probe':probe,
 'pyvenv_cfg_sha256':hashlib.sha256(cfg.encode()).hexdigest(),'base_pip_readonly':pip_info,
 'target_pip_bootstrap_version':target_pip,'bootstrap':'base pip --python target; no packages installed',
 'system_site_packages':False,'torch_imported':False,'packages_installed':0,'gpu_model_steps':0}
(ROOT/'venv.json').write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps(payload,indent=2))
