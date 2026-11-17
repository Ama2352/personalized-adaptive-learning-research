"""Index calibration metadata bằng Drive giả, không đọc dữ liệu nghiên cứu."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

SPEC = importlib.util.spec_from_file_location('calibration_index', Path(__file__).resolve().parents[2]/
    'research_tracking/runs/junyi-calibration-real-20261117-01/fetch_calibration_metadata01.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class Response:
    status_code = 200
    def __init__(self, payload=None, raw=b''):
        self.payload, self.raw = payload, raw
    def json(self):
        return self.payload
    def iter_content(self, size):
        yield self.raw
    def close(self):
        pass


class Drive:
    def __init__(self):
        self.account = module.ACCOUNT
        self.items, self.content = {}, {}
        self.downloads = []
        self.folder('run',module.RUN,module.PARENT)
        tranche='a0-fit-calibration-a0-join-20261117-01'
        self.folder('tranche',tranche,'run')
        self.folder('fit','fit','tranche')
        binding=dict(model_id='A0_JUNYI_REFIT')
        temperature=dict(binding=binding, total_targets=1621484, supported_targets=1621484,
            status='fitted_response_temperature',temperature=1.2,raw_log_loss=.4,calibrated_log_loss=.39,
            recipe='response-temperature-reference-v1',clip=1e-6,temperature_bounds=[.05,20.],
            objective_evaluations=50,class_counts=[277836,1343648])
        self.file('temperature','temperature.json','fit',temperature)
        self.file('manifest','manifest.json','fit',dict(calibration_identity=module.identity(temperature),
            binding=binding,population=dict(identity='population')))
        self.file('config','config.json','tranche',dict(binding=binding,population_identity='population',
            tranche_id=tranche,source_pins={}))
        self.file('resource','resource.json','tranche',dict(device='cpu',wall_seconds=1.))
        inventory={relative:dict(bytes=int(self.items[file_id]['size']),sha256=self.items[file_id]['sha256Checksum'])
            for relative,file_id in [('fit/temperature.json','temperature'),('fit/manifest.json','manifest'),
                                     ('config.json','config'),('resource.json','resource')]}
        self.file('complete','COMPLETE.json','tranche',dict(status='JUNYI_CLOUD_CPU_CALIBRATION_FIT_COMPLETE',
            total_targets=1621484,supported_targets=1621484,calibration_identity=module.identity(temperature),files=inventory))
    def folder(self, file_id, name, parent):
        self.items[file_id]=dict(id=file_id,name=name,parents=[parent],mimeType=module.FOLDER)
    def file(self, file_id, name, parent, payload):
        raw=json.dumps(payload).encode()
        self.content[file_id]=raw
        self.items[file_id]=dict(id=file_id,name=name,parents=[parent],size=str(len(raw)),
            sha256Checksum=hashlib.sha256(raw).hexdigest(),mimeType='application/json')
    def get(self,url,**kwargs):
        assert kwargs['allow_redirects'] is False
        if url.endswith('/about'):
            return Response(dict(user=dict(emailAddress=self.account)))
        if url.endswith('/files'):
            match=re.match(r"'([^']+)' in parents and name = '([^']+)'",kwargs['params']['q'])
            return Response(dict(files=[row for row in self.items.values()
                if match[1] in row['parents'] and row['name']==match[2]]))
        file_id=url.rsplit('/',1)[-1]
        self.downloads.append(file_id)
        return Response(raw=self.content[file_id])


def test_index_fetches_only_three_small_json_and_indexes_two_large_metadata(tmp_path):
    drive=Drive()
    index=module.index_variants(drive,tmp_path,('A0',))
    row=index['variants'][0]
    assert row['status']=='CALIBRATION_DRIVE_METADATA_VERIFIED'
    assert row['temperature']==1.2 and row['targets']==1621484
    assert len(drive.downloads)==3 and len(list(tmp_path.glob('*.json')))==3
    assert row['files']['config.json']['index_only']
    assert row['files']['fit/manifest.json']['local_file'] is None
    assert set(row['files'])==set(module.NAMES)
    assert module.index_variants(drive,tmp_path,('A0',))['downloaded_bytes']==0


def test_pending_fit_has_no_download(tmp_path):
    drive=Drive()
    assert module.index_variants(drive,tmp_path,('A3',))['variants'][0]['status'].endswith('YET')
    assert not drive.downloads


def test_wrong_account_no_download(tmp_path):
    drive=Drive();drive.account='other@example.com'
    with pytest.raises(ValueError,match='account'):
        module.index_variants(drive,tmp_path,('A0',))
    assert not drive.downloads


@pytest.mark.parametrize('failure',['duplicate','oversize','sha'])
def test_invalid_drive_metadata_rejected(tmp_path,failure):
    drive=Drive()
    if failure=='duplicate':
        drive.items['duplicate']=dict(drive.items['tranche'],id='duplicate')
    elif failure=='oversize':
        drive.items['complete']['size']=str(module.MAX_FILE+1)
    else:
        drive.items['complete']['sha256Checksum']='0'*64
    with pytest.raises(ValueError):
        module.index_variants(drive,tmp_path,('A0',))


def test_frozen_request_binding_is_checked(tmp_path):
    expected = dict(A0=dict(binding=dict(model_id='A0_JUNYI_REFIT'),
        population_identity='population',source_pins={}))
    assert module.index_variants(Drive(),tmp_path,('A0',),expected)['variants'][0]['status'].endswith('VERIFIED')
    expected['A0']['binding']['checkpoint_sha256'] = 'changed'
    with pytest.raises(ValueError,match='frozen'):
        module.index_variants(Drive(),tmp_path,('A0',),expected)


def test_large_config_index_only_and_complete_inventory_checked(tmp_path):
    drive=Drive()
    drive.items['config']['size']=str(2*1024**2)
    complete=json.loads(drive.content['complete'])
    complete['files']['config.json']['bytes']=2*1024**2
    drive.file('complete','COMPLETE.json','tranche',complete)
    row=module.index_variants(drive,tmp_path,('A0',))['variants'][0]
    assert row['files']['config.json']['bytes']==2*1024**2
    assert 'config' not in drive.downloads and 'manifest' not in drive.downloads


def frozen_publication(drive, tranche):
    return dict(status='DRIVE_SHA256_VERIFIED',account=module.ACCOUNT,parent_id=module.PARENT,
        run_id=module.RUN,tranche_id=tranche,folder_id='tranche',
        files=[dict(path=name,file_id=file_id,bytes=int(drive.items[file_id]['size']),
                    sha256=drive.items[file_id]['sha256Checksum'])
               for name,file_id in [('COMPLETE.json','complete'),('config.json','config'),
                   ('resource.json','resource'),('fit/manifest.json','manifest'),
                   ('fit/temperature.json','temperature')]])


def test_recovery_tranche_override_uses_frozen_publication_pins(tmp_path):
    drive=Drive();tranche='a0-fit-calibration-a0-recover-20261117-02'
    drive.items['tranche']['name']=tranche
    receipt=frozen_publication(drive,tranche)
    index=module.index_variants(drive,tmp_path,('A0',),tranche_overrides={'A0':tranche},
        publication_receipts={'A0':receipt})
    assert index['variants'][0]['tranche']==tranche
    assert len(drive.downloads)==3
    receipt['files'][0]['sha256']='0'*64
    with pytest.raises(ValueError,match='frozen stage publication'):
        module.index_variants(drive,tmp_path,('A0',),tranche_overrides={'A0':tranche},
            publication_receipts={'A0':receipt})


@pytest.mark.parametrize('tranche',['../escape','a1-fit-other',"a0-fit-'quoted"] )
def test_override_rejects_wrong_variant_or_path(tmp_path,tranche):
    with pytest.raises(ValueError,match='tranche'):
        module.index_variants(Drive(),tmp_path,('A0',),tranche_overrides={'A0':tranche})


def test_stage_result_extracts_recovery_tranche_and_identity(tmp_path):
    drive=Drive();tranche='a0-fit-calibration-a0-recover-20261117-02'
    receipt=frozen_publication(drive,tranche)
    path=tmp_path/'stage.json'
    path.write_text(json.dumps(dict(status='STAGE_COMMITTED',result=dict(
        calibration_identity='frozen-temperature',publish_receipts=[receipt]))))
    expected={'A0':{}}
    tranches,receipts=module.stage_publications([('A0',path)],expected,('A0',))
    assert tranches=={'A0':tranche} and receipts['A0']==receipt
    assert expected['A0']['calibration_identity']=='frozen-temperature'


def test_temperature_counts_must_match_complete_inventory(tmp_path):
    drive=Drive()
    temperature=json.loads(drive.content['temperature'])
    temperature['total_targets']=1
    drive.file('temperature','temperature.json','fit',temperature)
    complete=json.loads(drive.content['complete'])
    complete['calibration_identity']=module.identity(temperature)
    complete['files']['fit/temperature.json']=dict(bytes=int(drive.items['temperature']['size']),
        sha256=drive.items['temperature']['sha256Checksum'])
    drive.file('complete','COMPLETE.json','tranche',complete)
    with pytest.raises(ValueError,match='identity mismatch'):
        module.index_variants(drive,tmp_path,('A0',))
