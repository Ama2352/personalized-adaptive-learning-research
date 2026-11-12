"""Đóng gói16shard TRAIN80 đã chọn, không model, không sửa cache gốc."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from packet_reader import JunyiTrainingPacket, KIND, sha, need


def pin(path):
    return dict(sha256=sha(path), bytes=path.stat().st_size)


def write(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


def main():
    selection_path = ROOT/'research_tracking/runs/junyi-lifecycle-20261112-01/representative-packet-selection.json'
    selection = json.loads(selection_path.read_text())
    base = ROOT/'artifacts/akt/modal/junyi-throughput-20261112-01'
    output = base/'packet-inputs'
    need(not output.exists() and not (base/'packet.zip').exists(), 'Exclusive packet output required')
    source = ROOT/selection['source_root']
    need(sha(source/'manifest.json') == selection['source_manifest_sha256'], 'Full source cache changed')
    manifest = json.loads((source/'manifest.json').read_text())
    need(manifest['key'] == selection['source_key'] and selection['packet_geometry']['windows'] == 1024,
         'Selection/source metadata mismatch')
    output.mkdir(parents=True)
    files = {'full-cache-manifest.json': source/'manifest.json',
        'roles.json': ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json',
        'encoding.json': ROOT/'artifacts/akt/window-cache/full-train80-20261112-02.encoding.json',
        'encoding-receipt.json': ROOT/'artifacts/akt/window-cache/full-train80-20261112-02.encoding.receipt.json',
        'selection.json': selection_path}
    source_entries = {entry['name']:entry for entry in manifest['shards']}
    for entry in selection['selected_shards']:
        name = entry['name']
        need(Path(name).name == name and source_entries[name]['sha256'] == entry['sha256']
             and sha(source/name) == entry['sha256'], 'Selected source shard changed')
        files['shards/'+name] = source/name
    before = {name:pin(path) for name,path in files.items()}
    for name,path in files.items():
        target = output/name;target.parent.mkdir(parents=True,exist_ok=True)
        with path.open('rb') as incoming,target.open('xb') as outgoing:
            shutil.copyfileobj(incoming,outgoing,1024**2)
        need(pin(target) == before[name], 'Packet copy mismatch')
    packet = dict(kind=KIND,status='PREPARED_PARTIAL_ENGINEERING_PACKET',
        full_role_coverage=False,full_train_epoch_complete=False,
        source_manifest_sha256=selection['source_manifest_sha256'],source_key=manifest['key'],
        expected=dict(windows=1024,targets=56332,tokens=100032,learners=755),
        selection_sha256=before['selection.json']['sha256'],selected_shards=selection['selected_shards'],files=before)
    write(output/'packet.json',packet)
    packet_sha = sha(output/'packet.json')
    reader = JunyiTrainingPacket(output,expected_packet_sha256=packet_sha)
    verified = reader.verify()
    payload = {path.relative_to(ROOT).as_posix():pin(path) for path in output.rglob('*') if path.is_file()}
    archive = base/'packet.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as saved:
        for name in sorted(payload):
            saved.write(ROOT/name,name)
        saved.writestr('MANIFEST.json',json.dumps(dict(kind=KIND,files={name:entry['sha256'] for name,entry in payload.items()}),indent=2))
    need(all(pin(path) == before[name] for name,path in files.items()), 'Source bytes changed during preparation')
    need('torch' not in sys.modules, 'CPU packet preparation must not import Torch')
    result = dict(status='REPRESENTATIVE_TRAIN80_PACKET_PREPARED_AND_CPU_VERIFIED',
        packet_root=output.relative_to(ROOT).as_posix(),packet_sha256=packet_sha,
        archive=archive.relative_to(ROOT).as_posix(),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        reader_sha256=sha(Path(__file__).with_name('packet_reader.py')),payload_files=payload,
        verification=verified,torch_imported=False,training_performed=False,cloud_execution=False)
    write(Path(__file__).with_name('packet-preparation.json'),result)
    print(json.dumps({name:result[name] for name in ('status','packet_sha256','archive_sha256','archive_bytes','verification')}))


if __name__=='__main__':
    main()
