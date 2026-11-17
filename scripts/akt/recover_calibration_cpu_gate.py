"""Tiếp tục upload log CPU gate đã chạy, không gọi lại pytest hoặc GPU."""
import json
from pathlib import Path
import modal_drive_artifact_worker as worker
import modal

ROOT=Path(__file__).resolve().parents[2]
if __name__=='__main__':
    output=ROOT/'research_tracking/runs/cloud-calibration-fit-20261117-01/LINUX_CPU_GATE_RECOVERY01.json'
    if output.exists():
        raise SystemExit('Đã có receipt recovery, cần đọc trạng thái trước.')
    request=dict(run_id='cloud-calibration-linux-20261117-01',tranche_id='cpu-tests01',
                 files=['config.json','tests.txt','result.json'],max_total_bytes=1024**2)
    with modal.enable_output(),worker.app.run(environment_name='main'):
        receipt=worker.publish.remote(request)
    output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
