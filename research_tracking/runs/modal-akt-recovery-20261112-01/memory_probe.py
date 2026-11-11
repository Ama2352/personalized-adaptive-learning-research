"""Đo bộ nhớ trước/sau import Torch trên CPU Modal, không train."""
import json
import os
from pathlib import Path
import subprocess

if __name__ == '__main__':
    ROOT = Path(__file__).resolve().parent.parent.parent.parent
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'
import modal

app = modal.App('kltn-akt-memory-observation')


@app.function(image=modal.Image.from_id('im-PcG3UeRJq1Qu86G1dHDXz8'),
              cpu=(0.25, 1), memory=(1024, 8192), timeout=40, startup_timeout=60,
              retries=0, max_containers=1)
def observe():
    code = '''
import json,os,platform,resource
from pathlib import Path
import psutil
def sample():
    p=psutil.Process()
    value={'memory_info':p.memory_info()._asdict(),
           'rusage_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'statm':Path('/proc/self/statm').read_text(),
           'status_memory':[line for line in Path('/proc/self/status').read_text().splitlines() if line.startswith(('Vm','Rss'))]}
    try:value['full_info']=p.memory_full_info()._asdict()
    except Exception as e:value['full_info_error']=str(e)
    return value
before=sample()
import torch
after=sample()
print(json.dumps({'kernel':platform.release(),'torch':torch.__version__,'before':before,'after':after}))
'''
    p = subprocess.run(['/opt/kltn/.venv/bin/python', '-I', '-B', '-c', code],
                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=''),
                       capture_output=True, text=True, timeout=30)
    return dict(returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)


if __name__ == '__main__':
    with modal.enable_output(), app.run(environment_name='main'):
        result = observe.spawn().get(timeout=100)
        with (Path(__file__).parent / 'memory-probe-result.json').open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
        print(json.dumps(result), flush=True)
