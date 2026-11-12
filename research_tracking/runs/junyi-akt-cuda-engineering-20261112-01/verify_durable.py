"""Đọc lại ba file checkpoint từ Volume sau khi App GPU đã dừng."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent
RUN = 'modal-junyi-a0-epoch-20261112-02'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
sys.path.insert(0, str(ROOT/'experiments/akt'))
import modal
from modal_graph_selected import read_billing

volume = modal.Volume.from_name('kltn-akt-'+RUN)
prefix = 'experiments/akt/results/'+RUN+'/checkpoints/epoch-001/'
with zipfile.ZipFile(ROOT/'experiments/akt/results'/RUN/'artifacts.zip') as saved:
    pins = json.loads(saved.read('SHA256.json'))
verified = {}
for name in ('state.pt','metadata.json','COMPLETE.json'):
    digest = hashlib.sha256()
    size = 0
    for block in volume.read_file(RUN+'/checkpoints/epoch-001/'+name):
        digest.update(block)
        size += len(block)
    assert digest.hexdigest()==pins[prefix+name]['sha256'] and size==pins[prefix+name]['bytes']
    verified[name] = dict(sha256=digest.hexdigest(), bytes=size)
result = dict(status='THREE_DURABLE_FILES_VERIFIED',volume='kltn-akt-'+RUN,
    directory=RUN+'/checkpoints/epoch-001',files=verified,
    archive=str(Path('experiments/akt/results')/RUN/'artifacts.zip').replace('\\','/'))
(BUNDLE/'checkpoint-index.json').write_text(json.dumps(result,indent=2)+'\n')
billing = asyncio.run(read_billing())
(BUNDLE/'billing-after.json').write_text(json.dumps(billing,indent=2)+'\n')
print(json.dumps(dict(status=result['status'], metered_usd=billing['billing']['metered_cost'],
    billed_usd=billing['billing']['billed_cost'])))
