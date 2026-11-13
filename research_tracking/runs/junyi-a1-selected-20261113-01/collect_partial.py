"""Tải checkpoint A1 đã commit và logs trước khi dừng đúng App của đợt."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
RUN = 'modal-junyi-a1-b128-h100-20261113-04'
NATIVE = ROOT/'experiments/akt/results'/RUN
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
os.environ['TEMP'] = os.environ['TMP'] = str(ROOT/'artifacts/akt/runtime/modal-client-temp')
sys.path.insert(0,str(ROOT/'experiments/akt'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stop-after-verified',action='store_true')
    args = parser.parse_args()
    import modal
    from modal_budget_guard import OwnedModalApp,stop_owned_app_cli
    dispatch = json.loads((NATIVE/'dispatch.json').read_text())
    volume = modal.Volume.from_name('kltn-akt-'+RUN)
    raw = b''.join(volume.read_file(RUN+'/checkpoint-index.json'))
    index = json.loads(raw)
    assert index, 'Chưa có checkpoint đã commit, không dừng App'
    (BUNDLE/'durable-checkpoint-index04.json').write_bytes(raw)
    copied = {}
    for name, entry in index.items():
        assert Path(name).name == name and name.startswith('inner-batch-epoch-1-step-')
        for filename, pin in entry['files'].items():
            assert Path(filename).name == filename
            destination = NATIVE/'checkpoints'/name/filename
            destination.parent.mkdir(parents=True,exist_ok=True)
            if not destination.exists():
                with destination.open('xb') as stream:
                    for block in volume.read_file(RUN+'/checkpoints/'+name+'/'+filename):
                        stream.write(block)
            assert destination.stat().st_size==pin['bytes'] and sha(destination)==pin['sha256']
            copied[destination.relative_to(ROOT).as_posix()] = pin
    for filename in ('run-manifest.json','initial-backbone.json','COMPLETE.json'):
        destination=NATIVE/'preserved-run-control'/filename
        destination.parent.mkdir(exist_ok=True)
        raw=b''.join(volume.read_file(RUN+'/run-control/'+filename))
        if not destination.exists():destination.write_bytes(raw)
        assert destination.read_bytes()==raw

    command=[sys.executable,'-B','-m','modal']
    containers=json.loads(subprocess.run(command+['container','list','--json'],check=True,
        capture_output=True,text=True,timeout=25).stdout)
    owned=[row for row in containers if row['app_id']==dispatch['app_id']]
    if owned:
        assert len(owned)==1
        source='RUN='+repr(RUN)+'\n'+r'''
import base64,hashlib,json
from pathlib import Path
root=Path('/opt/kltn')
files={}
for folder in [root/'experiments/akt/results'/RUN,root/'experiments/akt/results'/(RUN+'-operation'),root/'experiments/akt/results'/(RUN+'-driver')]:
    for path in folder.rglob('*'):
        if path.is_file() and path.suffix!='.pt' and 'checkpoints' not in path.parts and path.stat().st_size<8*1024**2:
            raw=path.read_bytes()
            files[path.relative_to(root).as_posix()]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),data=base64.b64encode(raw).decode())
print(json.dumps(files))
'''
        result=subprocess.run(command+['container','exec','--no-pty',owned[0]['container_id'],'--',
            '/opt/kltn/.venv/bin/python','-B','-c',source],check=True,capture_output=True,text=True,timeout=40)
        for relative,entry in json.loads(result.stdout).items():
            assert relative.startswith('experiments/akt/results/'+RUN) and '..' not in Path(relative).parts
            raw=base64.b64decode(entry['data'],validate=True)
            assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
            destination=NATIVE/'preserved-live-evidence'/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            if not destination.exists():destination.write_bytes(raw)
            assert destination.read_bytes()==raw
            copied[destination.relative_to(ROOT).as_posix()]={k:v for k,v in entry.items() if k!='data'}
    result=dict(status='VERIFIED_PARTIAL_CHECKPOINT_AND_LIVE_EVIDENCE',run_id=RUN,
        checkpoint_names=sorted(index),files=copied,selected_fit_complete=False,
        limits_vi='Checkpoint giữa epoch để resume, chưa có validation A1 hoặc model được chọn.')
    (BUNDLE/'partial-retrieval04.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.stop_after_verified:
        acknowledgment=stop_owned_app_cli(OwnedModalApp(RUN,dispatch['app_id'],'kltn-akt-'+RUN))
        (BUNDLE/'manual-stop04.json').write_text(json.dumps(dict(app_id=dispatch['app_id'],acknowledgment=acknowledgment),default=str,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],checkpoint_names=sorted(index),files=len(copied),stop_requested=args.stop_after_verified)))

if __name__=='__main__':
    main()
