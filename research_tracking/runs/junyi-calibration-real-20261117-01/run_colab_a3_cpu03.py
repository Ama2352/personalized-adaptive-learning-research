"""Calibration A3 CPU với nhóm tiến trình riêng, nguồn theo COLAB_CPU_STAGING02."""
from contextlib import suppress
from pathlib import Path
import hashlib
import os
import signal
import subprocess
import time

RUNNER = Path('/content/kltn-free-cpu-tools/colab_calibration_token_runner-b80c20a05a1a.py')
RUNNER_SHA = 'b80c20a05a1ad7c7733785fdf6d03e9e68fe7c03b1f4538989db6231bdf14ea1'
PAYLOAD = Path('/content/kltn-free-cpu-tools/PAYLOAD-6fa3012a6d2f.json')
PAYLOAD_SHA = '6fa3012a6d2f321d12d4ae42be2c1fb4ee2e832f26f45459cdb2c51e8e652647'
ACCESS = Path('/content/kltn-agent-private/drive-access.json')
LOG = Path('/content/kltn-free-cpu-tools/A3_CPU03.log')


def main():
    try:
        if hashlib.sha256(RUNNER.read_bytes()).hexdigest() != RUNNER_SHA or hashlib.sha256(PAYLOAD.read_bytes()).hexdigest() != PAYLOAD_SHA:
            raise RuntimeError('STAGED_SOURCE_SHA_MISMATCH')
        ACCESS.parent.chmod(0o700)
        ACCESS.chmod(0o600)
        command = ['/usr/bin/python3', '-B', str(RUNNER), '--payload', str(PAYLOAD),
            '--payload-sha256', PAYLOAD_SHA, '--token-file', str(ACCESS), '--variant', 'A3']
        with LOG.open('a', encoding='utf-8') as stream:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                returncode = process.wait(timeout=10800)
            except subprocess.TimeoutExpired:
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
                time.sleep(2)
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
            if returncode:
                raise subprocess.CalledProcessError(returncode, command)
    finally:
        ACCESS.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
