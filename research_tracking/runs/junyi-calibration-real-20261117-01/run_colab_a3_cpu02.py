"""Calibration CPU A3, bootstrap UV trong venv đã pin."""
from pathlib import Path
import hashlib
import subprocess

assert hashlib.sha256(Path('/content/kltn-free-cpu-tools/colab_calibration_token_runner-b80c20a05a1a.py').read_bytes()).hexdigest() == 'b80c20a05a1ad7c7733785fdf6d03e9e68fe7c03b1f4538989db6231bdf14ea1'
assert hashlib.sha256(Path('/content/kltn-free-cpu-tools/PAYLOAD-6fa3012a6d2f.json').read_bytes()).hexdigest() == '6fa3012a6d2f321d12d4ae42be2c1fb4ee2e832f26f45459cdb2c51e8e652647'
_access=Path('/content/kltn-agent-private/drive-access.json')
_access.parent.chmod(0o700)
_access.chmod(0o600)
_log=Path('/content/kltn-free-cpu-tools/A3_CPU02.log')
with _log.open('a',encoding='utf-8') as _stream:
    subprocess.run(['/usr/bin/python3', '-B', '/content/kltn-free-cpu-tools/colab_calibration_token_runner-b80c20a05a1a.py', '--payload', '/content/kltn-free-cpu-tools/PAYLOAD-6fa3012a6d2f.json', '--payload-sha256', '6fa3012a6d2f321d12d4ae42be2c1fb4ee2e832f26f45459cdb2c51e8e652647', '--token-file', '/content/kltn-agent-private/drive-access.json', '--variant', 'A3'],stdout=_stream,stderr=subprocess.STDOUT,check=True,timeout=10800)
