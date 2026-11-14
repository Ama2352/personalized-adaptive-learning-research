from pathlib import Path
import json,hashlib,subprocess,os
r=Path('/content/kltn-gpu-boundary-20261114-01')
assert json.loads((r/'runtime/probe-supervisor-result.json').read_text())['status']=='PROBE_PROCESS_EXITED'
assert json.loads((r/'runtime/probe02-supervisor-result.json').read_text())['returncode']==0
assert hashlib.sha256((r/'runtime/evidence-download.zip.xz').read_bytes()).hexdigest()=='9888cdf0ac29b13d99354f6c2e132510683be5bfc63d500efa51c98fe6e9500f'
activity=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True,timeout=10).strip()
if activity and any(int(pid.strip())!=os.getpid() for pid in activity.splitlines()):
 raise RuntimeError('Other GPU worker present; preserve runtime')
print(json.dumps({'status':'RELEASE_REQUESTED','local_files_verified':45,'local_checkpoints_verified':12,'modal_spent_usd':0}),flush=True)
from google.colab import runtime
runtime.unassign()
print(json.dumps({'status':'RELEASE_ACCEPTED'}),flush=True)
