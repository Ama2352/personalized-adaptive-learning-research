"""Drive server-copy giả, không network hoặc payload."""
import importlib.util
from pathlib import Path
import re

import pytest
import requests

SPEC=importlib.util.spec_from_file_location('backup_copy',Path(__file__).resolve().parents[2]/
    'research_tracking/runs/junyi-calibration-real-20261117-01/copy_verified_model_backups01.py')
module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class Response:
    status_code=200
    def __init__(self,payload):self.payload=payload
    def json(self):return self.payload


class Drive:
    def __init__(self,inventory):
        self.items={row['id']:dict(id=row['id'],name=row['name'],size=str(row['bytes']),
            sha256Checksum=row['sha256'],parents=[module.PARENT],owners=[dict(emailAddress='other@example.com')],
            capabilities=dict(canCopy=True)) for row in inventory}
        self.posts=[]
        self.crash_after_copy=False
        self.remaining=1024**3
    def get(self,url,**kwargs):
        assert kwargs['allow_redirects'] is False and kwargs['params'].get('alt')!='media'
        if url.endswith('/about'):
            return Response(dict(user=dict(emailAddress=module.ACCOUNT),storageQuota=dict(limit=self.remaining,usage=0)))
        if url.endswith('/files'):
            match=re.match(r"'([^']+)' in parents and name = '([^']+)'",kwargs['params']['q'])
            return Response(dict(files=[row for row in self.items.values()
                if match[1] in row['parents'] and row['name']==match[2]]))
        return Response(self.items[url.rsplit('/',1)[-1]])
    def post(self,url,**kwargs):
        self.posts.append(url)
        if url.endswith('/files'):
            row=dict(kwargs['json'],id='destination',owners=[dict(emailAddress=module.ACCOUNT)])
        else:
            source=url.rsplit('/',2)[-2]
            row=dict(self.items[source],**kwargs['json'],id='copied-'+source,owners=[dict(emailAddress=module.ACCOUNT)])
        self.items[row['id']]=row
        if self.crash_after_copy and url.endswith('/copy'):
            self.crash_after_copy=False
            raise requests.Timeout('synthetic uncertain POST acknowledgement')
        return Response(row)


@pytest.fixture
def case(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'STATE',tmp_path/'state.json')
    inventory=[dict(id='source'+str(i),name='backup'+str(i),bytes=1,sha256=str(i)*64) for i in range(13)]
    return inventory,Drive(inventory)


def test_all_server_copies_verified_and_repeat_is_idempotent_with_zero_free_quota(case):
    inventory,drive=case
    result=module.execute(drive,inventory)
    assert len(result['copies'])==13 and result['status'].startswith('COMPLETE')
    assert len(drive.posts)==14
    drive.remaining=0
    result=module.execute(drive,inventory)
    assert len(drive.posts)==14 and all(row['mode']=='REUSED_VERIFIED_COPY' for row in result['copies'])


def test_uncertain_copy_ack_reconciles_without_second_copy(case):
    inventory,drive=case
    drive.crash_after_copy=True
    result=module.execute(drive,inventory)
    assert len(result['copies'])==13 and len([url for url in drive.posts if url.endswith('/copy')])==13


def test_cannot_copy_stops_before_any_post(case):
    inventory,drive=case
    drive.items['source0']['capabilities']['canCopy']=False
    with pytest.raises(ValueError,match='canCopyFalse'):
        module.execute(drive,inventory)
    assert not drive.posts


def test_insufficient_storage_never_copies_payload(case):
    inventory,drive=case
    drive.remaining=1
    with pytest.raises(ValueError,match='quota'):
        module.execute(drive,inventory)
    assert not [url for url in drive.posts if url.endswith('/copy')]


def test_fresh_source_and_copy_verification_without_mutation(case):
    inventory,drive=case
    state=module.execute(drive,inventory)
    before={row['id']:dict(owners=['other@example.com']) for row in inventory}
    posts=len(drive.posts)
    verified=module.verify_copies(drive,state,before)
    assert len(verified['files'])==13 and len(drive.posts)==posts
    drive.items['source0']['owners']=[dict(emailAddress='changed@example.com')]
    with pytest.raises(ValueError,match='Post-copy'):
        module.verify_copies(drive,state,before)
