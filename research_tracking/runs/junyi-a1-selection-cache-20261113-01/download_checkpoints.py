"""Lấy checkpoint đã COMPLETE về D trong khi job chạy, kiểm SHA trước publish."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',default='modal-junyi-a1-b128-h100-20261113-07')
    parser.add_argument('--max-checkpoints',type=int,default=2)
    args=parser.parse_args()
    assert re.fullmatch(r'modal-junyi-a1-b128-h100-\d{8}-\d{2}',args.run_id)
    assert 1<=args.max_checkpoints<=30
    os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE']='kltn'
    import modal
    volume=modal.Volume.from_name('kltn-akt-'+args.run_id,create_if_missing=False)
    index=json.loads(b''.join(volume.read_file(args.run_id+'/checkpoint-index.json')))
    selected=sorted(name for name in index if re.fullmatch(r'epoch-\d{3}',name))[-args.max_checkpoints:]
    results=[]
    for name in selected:
        folder=ROOT/'experiments/akt/results'/args.run_id/'checkpoints'/name
        folder.mkdir(parents=True,exist_ok=True)
        files=index[name]['files']
        assert set(files)=={'state.pt','metadata.json','COMPLETE.json'}
        for filename in ('state.pt','metadata.json','COMPLETE.json'):
            entry=files[filename];target=folder/filename
            assert 0<entry['bytes']<=64*1024**2
            if not target.exists():
                temporary=folder/(filename+'.'+uuid.uuid4().hex+'.download')
                with temporary.open('xb') as stream:
                    for block in volume.read_file(args.run_id+'/checkpoints/'+name+'/'+filename):stream.write(block)
                assert temporary.stat().st_size==entry['bytes'] and sha(temporary)==entry['sha256']
                temporary.rename(target)
            assert target.stat().st_size==entry['bytes'] and sha(target)==entry['sha256']
        metadata=json.loads((folder/'metadata.json').read_text())
        complete=json.loads((folder/'COMPLETE.json').read_text())
        assert sha(folder/'metadata.json')==complete['metadata_sha256']
        assert sha(folder/'state.pt')==metadata['checkpoint_sha256']==complete['checkpoint_sha256']
        results.append(dict(checkpoint=name,sha256=sha(folder/'state.pt'),path=folder.relative_to(ROOT).as_posix()))
    receipt=dict(status='VERIFIED_PUBLISHED_CHECKPOINT_DOWNLOADS',run_id=args.run_id,checkpoints=results)
    (HERE/'checkpoint-download-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
