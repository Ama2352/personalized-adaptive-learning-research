"""Đọc lại bốn checkpoint trên Volume v2 và đối chiếu archive đã tải."""
import hashlib,json,os,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent.parent.parent
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE']='kltn'
import modal
RUN='modal-checkpoint-pilot-20261112-12'
volume=modal.Volume.from_name('kltn-akt-checkpoint-pilot-20261112-12')
checked=[]
with zipfile.ZipFile(ROOT/'experiments/akt/results'/RUN/'artifacts.zip') as saved:
    inventory=json.loads(saved.read('SHA256.json'))
    for variant in ('A0','A3'):
        for phase in ('interrupted','resumed'):
            prefix='t4-checkpoint-recovery-20261110-01/'+variant+'/'+phase+'/checkpoint/'
            for name in ('state.pt','metadata.json','COMPLETE.json'):
                remote=RUN+'/phase-checkpoints/'+variant+'/'+phase+'/checkpoint/'+name
                h=hashlib.sha256();size=0
                for block in volume.read_file(remote):
                    h.update(block);size+=len(block)
                expected=inventory[prefix+name]
                assert h.hexdigest()==expected['sha256'] and size==expected['bytes'],remote
                checked.append(dict(path=remote,bytes=size,sha256=h.hexdigest()))
result=dict(status='VERIFIED_FOUR_DURABLE_CHECKPOINTS_ON_VOLUME_V2',files=checked)
output=Path(__file__).parent/'checkpoint12-durable-verification.json'
with output.open('x',encoding='utf-8') as stream:
    json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(status=result['status'],files=len(checked),bytes=sum(r['bytes'] for r in checked))))
