"""Chạy calibration CPU A3 bằng runner đã pin trên own Colab."""
from pathlib import Path
import hashlib
import subprocess

assert hashlib.sha256(Path('/content/kltn-free-cpu-tools/colab_calibration_token_runner-d8a184345a2b.py').read_bytes()).hexdigest() == 'd8a184345a2b516524f8146da2828a71695f375554fb6ba4058ac2f9529f343b'
assert hashlib.sha256(Path('/content/kltn-free-cpu-tools/PAYLOAD-6fa3012a6d2f.json').read_bytes()).hexdigest() == '6fa3012a6d2f321d12d4ae42be2c1fb4ee2e832f26f45459cdb2c51e8e652647'
_access=Path('/content/kltn-agent-private/drive-access.json')
_access.parent.chmod(0o700)
_access.chmod(0o600)
_log=Path('/content/kltn-free-cpu-tools/A3_CPU.log')
with _log.open('a',encoding='utf-8') as _stream:
    subprocess.run(['/usr/bin/python3', '-B', '/content/kltn-free-cpu-tools/colab_calibration_token_runner-d8a184345a2b.py', '--payload', '/content/kltn-free-cpu-tools/PAYLOAD-6fa3012a6d2f.json', '--payload-sha256', '6fa3012a6d2f321d12d4ae42be2c1fb4ee2e832f26f45459cdb2c51e8e652647', '--token-file', '/content/kltn-agent-private/drive-access.json', '--variant', 'A3'],stdout=_stream,stderr=subprocess.STDOUT,check=True,timeout=10800)
