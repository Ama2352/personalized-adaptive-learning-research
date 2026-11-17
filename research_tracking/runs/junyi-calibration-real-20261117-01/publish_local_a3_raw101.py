"""Lưu raw A3 đã kiểm đầy đủ lên Drive Sang trước bước fit."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
VOLUME=ROOT/'artifacts/akt/local-calibration/20261117'
sys.path.insert(0,str(ROOT/'scripts/akt'))
import free_cpu_calibration as free


def main():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import AuthorizedSession
    result=json.loads((BUNDLE/'local-a3-join101.txt').read_text(encoding='utf-8').splitlines()[-1])
    raw=Path(result['raw'])
    assert raw==VOLUME/'junyi-calibration-real-20261117-01/a3-raw-freecpu-a3-101/payloads/raw'
    manifest=json.loads((raw/'manifest.json').read_text())
    assert manifest['status']=='complete' and manifest['prediction_rows']==manifest['expected_rows']==1621484
    assert manifest['unique_users']==15847 and manifest['output_coverage']==1.0
    free.VOLUME=VOLUME
    with AuthorizedSession(Credentials.from_authorized_user_file(str(
            ROOT/'artifacts/akt/private/colab-session/drive-controller-credentials.json'))) as session:
        result['publish_receipt']=free.publish(session,result['publish_request'],
            ROOT/'artifacts/akt/private/local-calibration/20261117')
    assert result['publish_receipt']['status']=='DRIVE_SHA256_VERIFIED'
    source=raw/'manifest.json'
    receipt=dict(status='LOCAL_RAW_AUDIT_COMPLETE_DRIVE_VERIFIED',result=result,
        raw_manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        counts={key:manifest[key] for key in ('prediction_rows','expected_rows','unique_users','output_coverage')})
    (BUNDLE/'LOCAL_A3_RAW_ACCEPTANCE101.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(receipt['status'],'A3',manifest['prediction_rows'],flush=True)


if __name__=='__main__':main()
