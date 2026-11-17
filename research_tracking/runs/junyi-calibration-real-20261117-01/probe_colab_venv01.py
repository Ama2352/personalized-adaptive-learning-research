"""Đọc khả năng bootstrap venv trong Colab, không cài package."""
from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys

_source=Path('/__modal/volumes/vo-dv1975utRQbmagCjA0brSe/calibration-inputs-20261117-01/source')
_python=_source/'.venv/bin/python'
_result={'source_exists':_source.is_dir(),'venv_python_exists':_python.exists(),
         'base_pip_available':importlib.util.find_spec('pip') is not None,
         'uv_executable':shutil.which('uv')}
if _python.exists():
    _probe=subprocess.run([str(_python),'-m','pip','--version'],capture_output=True,text=True,timeout=15)
    _result.update(venv_pip_status=_probe.returncode,venv_pip_stdout=_probe.stdout,venv_pip_stderr=_probe.stderr)
print(json.dumps(_result))
