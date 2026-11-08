import json, os, platform, shutil, sys
from pathlib import Path
ROOT = Path('/content/KLTN_GPU08_20261108_01')
assert platform.system() == 'Linux' and platform.machine() == 'x86_64'
assert sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 13)
ROOT.mkdir(exist_ok=False)
info = {'stage':'GPU08_CPU_CONNECTION_ONLY','python':sys.version,'executable':sys.executable,
        'platform':platform.platform(),'machine':platform.machine(),'prefix':sys.prefix,
        'accelerator_environment':os.environ.get('COLAB_GPU'),'disk_free_bytes':shutil.disk_usage('/content').free,
        'root':str(ROOT),'packages_installed':0,'torch_imported':False,'gpu_model_steps':0,
        'scope':'stdlib discovery; no package mutation, GPU calls or Modal'}
(ROOT/'connection.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info,indent=2))
