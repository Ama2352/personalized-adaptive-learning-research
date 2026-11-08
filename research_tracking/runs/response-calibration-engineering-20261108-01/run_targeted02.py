"""ONE synthetic scalar/reference test invocation;30s cumulative, no NN updates."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
INPUTS = ['src/knowledge_tracing/response_calibration.py', 'tests/shared_kt/test_response_calibration.py',
          'src/knowledge_tracing/simulator_bridge.py', 'src/knowledge_tracing/reference_controller.py', 'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    trial = PREP / 'trial02'
    trial.mkdir()
    before = {name: sha(ROOT / name) for name in INPUTS}
    for index, name in enumerate(INPUTS):
        (trial / (str(index) + '-' + Path(name).name + '.before')).write_bytes((ROOT / name).read_bytes())
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-B', '-c',
               "import sys;sys.path.insert(0,'src');import pytest;raise SystemExit(pytest.main(sys.argv[1:]))",
               'tests/shared_kt/test_response_calibration.py', '-q', '-p', 'no:cacheprovider',
               '--basetemp=' + str(trial / 'tmp'), '--junitxml=' + str(trial / 'junit.xml')]
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    started = time.monotonic(); wall = time.time(); code = None; error = None
    with (trial / 'stdout.log').open('xb') as out, (trial / 'stderr.log').open('xb') as err:
        try:
            code = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=err, timeout=29).returncode
        except BaseException as exc:
            error = type(exc).__name__ + ': ' + str(exc)
    elapsed = max(time.monotonic()-started, time.time()-wall)
    after = {name: sha(ROOT / name) for name in INPUTS}
    result = dict(status='PASS' if code == 0 and error is None and elapsed+1.2795279757904053 <= 30 and before == after else 'FAILED_OR_RESOURCE_REJECTED',
                  exit_code=code, error=error, controller_elapsed_seconds=elapsed, cumulative_seconds=elapsed+1.2795279757904053,
                  cap_seconds=30, neural_model_calls=0, neural_optimizer_updates=0,
                  calibration_scalar_fit_only=True, inputs_before=before, inputs_after=after, command=command)
    (trial / 'receipt.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
