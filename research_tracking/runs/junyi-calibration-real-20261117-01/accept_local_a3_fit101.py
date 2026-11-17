"""Đọc lại artifact A3 trên Drive, kiểm lineage compact và cohort chung A2."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
VOLUME=ROOT/'artifacts/akt/local-calibration/20261117'
sys.path.insert(0,str(VOLUME/'calibration-inputs-20261117-01/source/src'))
sys.path.insert(1,str(ROOT/'scripts/akt'))
from local_calibration_migration import prepare_context,raw_storage_lineage
from knowledge_tracing.response_calibration import TemperatureCalibration


def main():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import AuthorizedSession
    result=json.loads((BUNDLE/'local-a3-fit101.txt').read_text(encoding='utf-8').splitlines()[-1])
    payload=json.loads((ROOT/'research_tracking/runs/colab-token-calibration-20261117-01/PAYLOAD.json').read_text())
    context=prepare_context(payload,VOLUME,'A3')
    assert result['publish_receipt']['status']=='DRIVE_SHA256_VERIFIED'
    downloaded={};verified=[]
    with AuthorizedSession(Credentials.from_authorized_user_file(str(
            ROOT/'artifacts/akt/private/colab-session/drive-controller-credentials.json'))) as session:
        who=session.get('https://www.googleapis.com/drive/v3/about',params={'fields':'user(emailAddress)'},timeout=30)
        who.raise_for_status();assert who.json()['user']['emailAddress']=='honguyenminhsang2005@gmail.com'
        for row in result['publish_receipt']['files']:
            url='https://www.googleapis.com/drive/v3/files/'+row['file_id']
            response=session.get(url,params={'fields':'size,sha256Checksum,parents,owners(emailAddress)'},timeout=30)
            response.raise_for_status();metadata=response.json()
            assert int(metadata['size'])==row['bytes'] and metadata['sha256Checksum']==row['sha256']
            assert row['folder_id'] in metadata['parents']
            assert any(owner.get('emailAddress')=='honguyenminhsang2005@gmail.com' for owner in metadata['owners'])
            response=session.get(url,params={'alt':'media'},timeout=60)
            response.raise_for_status();data=response.content
            assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
            downloaded[row['path']]=json.loads(data);verified.append(row)
    calibration=TemperatureCalibration.from_payload(downloaded['fit/temperature.json'],binding=context['binding'])
    assert asdict(calibration.binding)==asdict(context['binding'])
    assert json.loads(json.dumps(calibration.to_payload()))==result['calibration']
    assert calibration.status=='fitted_response_temperature'
    assert calibration.total_targets==calibration.supported_targets==1621484 and not calibration.unsupported_counts
    assert calibration.identity==downloaded['resource.json']['calibration_identity']
    assert downloaded['config.json']==downloaded['fit/manifest.json']
    metadata=downloaded['config.json']
    assert metadata['population']==context['population'] and metadata['source_pins']==context['request']['source_pins']
    raw=VOLUME/'a3-compact101'
    lineage=raw_storage_lineage(raw,json.loads((raw/'manifest.json').read_text()),metadata['raw_shard_sha256'])
    assert metadata['raw_storage_lineage']==lineage
    old=json.loads((BUNDLE/'LOCAL_A3_RAW_ACCEPTANCE101.json').read_text())
    assert lineage['compaction_receipt']['original_manifest_sha256']==old['raw_manifest_sha256']
    a2=json.loads((BUNDLE/'LOCAL_A2_FIT_ACCEPTANCE100.json').read_text(encoding='utf-8'))['calibration']
    assert list(calibration.class_counts)==a2['class_counts']
    assert calibration.partition_sha256==a2['partition_sha256']
    shared=lambda value:{key:val for key,val in value.items() if key not in ('model_id','checkpoint_sha256')}
    assert shared(asdict(calibration.binding))==shared(a2['binding'])
    receipt=dict(status='A3_LOCAL_CALIBRATION_INDEPENDENT_DRIVE_READBACK_ACCEPTED',
        account='honguyenminhsang2005@gmail.com',files=verified,calibration=calibration.to_payload(),
        calibration_identity=calibration.identity,resource=downloaded['resource.json'],
        raw_storage_lineage_verified=True,A2_shared_population_partition_binding_verified=True,
        scope='Junyi outer-fold4 calibration10, outer evaluation pending',
        accepted_calibrators=['A0','A1','A2','A3'],pending_calibrators=[])
    (BUNDLE/'LOCAL_A3_FIT_ACCEPTANCE101.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(receipt['status'],calibration.temperature,flush=True)


if __name__=='__main__':main()
