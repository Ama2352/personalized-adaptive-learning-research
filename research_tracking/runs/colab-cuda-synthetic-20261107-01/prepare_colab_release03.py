import json
from pathlib import Path

root=Path.cwd()
proof=json.loads((root/'artifacts/akt/colab/actual-cuda-verification-20261107.json').read_text(encoding='utf-8'))
assert proof['status']=='VERIFIED_ACTUAL_COLAB_CUDA_SYNTHETIC' and proof['output_files']==44
code='''# Giải phóng đúng runtime synthetic sau khi local đã nhận và kiểm đủ44outputs.
from google.colab import runtime
assert str(ROOT)=='/content/kltn-synthetic-b82b6de2333a4c5a85ef98491ad5c6b1'
assert file_sha(archive_path)=='64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188'
assert KLTN_TRANSFER_INDEX03==144
assert recovery_report['status']=='passed_synthetic_recovery'
activity=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True,timeout=15).strip()
if activity and any(int(pid.strip())!=os.getpid() for pid in activity.splitlines()):
    raise RuntimeError('Có GPU process khác; không giải phóng runtime tự động')
print('KLTN_RUNTIME_RELEASE_REQUEST; local ZIP/all44file hashes verified; no active GPU worker',flush=True)
runtime.unassign()
print('KLTN_RUNTIME_RELEASE_ACCEPTED',flush=True)
'''
(root/'artifacts/akt/colab/requests/add-runtime-release03.json').write_text(json.dumps({'cellIndex':15,'language':'python','code':code}),encoding='utf-8')
print('Prepared guarded current-runtime cleanup after verified local artifacts')
