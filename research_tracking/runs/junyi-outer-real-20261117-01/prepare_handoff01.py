"""Chuẩn bị metadata bất biến cho outer đã được người dùng duyệt17/11."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
B = Path(__file__).resolve().parent
SOURCE = ROOT/'artifacts/akt/local-calibration/20261117/outer-source-guard-release/source'
sys.path[:0] = [str(SOURCE/'src'),str(ROOT/'scripts/akt')]
from free_outer_evaluation import build_compatibility_receipt, validate_compatibility
from knowledge_tracing.response_calibration import PredictionBinding, TemperatureCalibration

def sha(path):
    return hashlib.file_digest(Path(path).open('rb'),'sha256').hexdigest()

def save(path,value):
    encoded = (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    if path.exists():
        assert path.read_bytes() == encoded, path
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(encoded)

def main():
    prep = ROOT/'research_tracking/runs/junyi-outer-gpu-preparation-20261117-01'
    plan = json.loads((prep/'STAGING_PLAN01.json').read_text())
    template = json.loads((prep/'REQUEST_TEMPLATE_UNAPPROVED01.json').read_text())
    maps = json.loads((ROOT/'research_tracking/runs/junyi-outer-cache-release-20261117-01/SOURCE_DELTA01.json').read_text())
    uploads = list(plan['upload_files'])
    calib = ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'
    for variant in ('A0','A1','A2','A3'):
        if variant in ('A0','A1'):
            path = calib/(variant+'_CALIBRATION_TEMPERATURE01.json')
        else:
            tranche = 'a2-fit-freecpu-a2-100' if variant=='A2' else 'a3-fit-freecpu-a3-101'
            path = ROOT/'artifacts/akt/local-calibration/20261117/junyi-calibration-real-20261117-01'/tranche/'payloads/fit/temperature.json'
        payload = json.loads(path.read_text())
        fitted = TemperatureCalibration.from_payload(payload,binding=PredictionBinding(**payload['binding']))
        assert fitted.binding.model_id == variant+'_JUNYI_REFIT'
        receipt = build_compatibility_receipt(maps['frozen_files'],maps['proposed_frozen_plus_one_guard_files'],
            checkpoint_sha256=fitted.binding.checkpoint_sha256,calibration_identity=fitted.identity)
        validate_compatibility(receipt,checkpoint_sha256=fitted.binding.checkpoint_sha256,
            calibration_identity=fitted.identity,calibrated_source=fitted.binding.model_source_sha256,
            current_source=template['source_identity'])
        compatibility_path = B/'handoff'/(variant+'.compatibility.json')
        save(compatibility_path,receipt)
        for group,local in (('calibrators',path),('compatibility',compatibility_path)):
            entry = template[group][variant]
            entry['sha256'] = sha(local)
            if group=='calibrators':
                entry['identity'] = fitted.identity
            uploads.append(dict(local_path=str(local),remote_path=entry['path'],bytes=local.stat().st_size,sha256=sha(local)))
    template['full_cohort_approved'] = True
    from outer_gpu_worker import validate_outer_request
    for variant in ('A0','A1','A2','A3'):
        request = dict(template,variant=variant,gpu_output=template['run_id']+'/'+variant.lower()+'-outer-numeric/payloads')
        validate_outer_request(request)
        path = B/('REQUEST_'+variant+'_GPU01.json')
        save(path,request)
        remote = plan['physical_volume_root']+'/requests/'+template['run_id']+'-'+variant.lower()+'-outer01.json'
        uploads.append(dict(local_path=str(path),remote_path=remote,bytes=path.stat().st_size,sha256=sha(path)))
    for entry in uploads:
        assert Path(entry['local_path']).stat().st_size == entry['bytes']
        assert sha(entry['local_path']) == entry['sha256'], entry['local_path']
    save(B/'HANDOFF_INVENTORY01.json',dict(status='LOCAL_INPUT_HASHES_VERIFIED',
        user_authorization='17/11 người dùng duyệt H100 outer A0–A3, cấu hình chung, Drive Sang',
        files=uploads,total_bytes=sum(e['bytes'] for e in uploads)))
    print('HANDOFF_LOCAL_VERIFIED',len(uploads),sum(e['bytes'] for e in uploads),flush=True)

if __name__=='__main__':
    main()
