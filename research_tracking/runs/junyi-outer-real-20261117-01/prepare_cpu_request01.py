"""Nối vị trí numeric tạm với nguồn outer đã pin, không thay metadata gốc."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
CACHE=ROOT/'artifacts/akt/local-calibration/20261117'

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def main(variant):
    request=json.loads((ROOT/'research_tracking/runs/outer-numeric-cpu-export-20261117-01/REQUEST_TEMPLATE.json').read_text())
    source=json.loads((B/'SOURCE_ACCEPTANCE01.json').read_text())
    cpu=json.loads((B/'CACHE_REQUEST_READY01.json').read_text())
    gpu=json.loads((B/('REQUEST_'+variant+'_GPU01.json')).read_text())
    cache=json.loads((B/'CACHE_RESULT01.json').read_text())
    inventory=json.loads((B/(variant+'_NUMERIC_INVENTORY01.json')).read_text())
    assert (B/(variant+'_DRIVE_BACKUP01.json')).is_file()
    download=Path(inventory['cache_root'])
    paths={}
    for entry in inventory['files']:
        paths['/__modal/volumes/vo-dv1975utRQbmagCjA0brSe/'+entry['path']]=str(download/entry['path'])
    windows=cache['windows']
    paths[str(windows['path']).rstrip('/\\')+'/manifest.json']=str(Path(windows['path'])/'manifest.json')
    paths[windows['admission_path']]=windows['admission_path']
    numeric=download/'junyi-outer-real-20261117-01'/(variant.lower()+'-outer-numeric')/'payloads/RECEIPT.json'
    handoff=json.loads((B/'HANDOFF_INVENTORY01.json').read_text())
    calib=next(x for x in handoff['files'] if x['remote_path']==gpu['calibrators'][variant]['path'])
    compatibility=B/'handoff'/(variant+'.compatibility.json')
    request.update(source_root=cpu['source_root'],variant=variant,export_index=cpu['export_indexes'][variant],
        data_paths=source['data_paths'],source_pins=source['source_pins'],
        cache_receipt=dict(path=str(B/'CACHE_RESULT01.json'),sha256=sha(B/'CACHE_RESULT01.json')),
        gpu_receipt=dict(path=str(numeric),sha256=sha(numeric)),
        calibration=dict(path=calib['local_path'],sha256=calib['sha256']),
        compatibility=dict(path=str(compatibility),sha256=sha(compatibility)),
        calibration_data_sha256=gpu['calibration_data_sha256'],path_map=paths,
        output=str(CACHE/'outer-export01'/variant),metrics=True)
    path=B/(variant+'_CPU_EXPORT_REQUEST01.json')
    with path.open('x',encoding='utf-8') as stream:
        json.dump(request,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print('CPU_REQUEST_READY',variant,sha(path),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',required=True,choices=('A0','A1','A2','A3'))
    main(parser.parse_args().variant)
