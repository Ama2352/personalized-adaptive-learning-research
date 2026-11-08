"""Kiểm hash bytes/receipt lưu bền vững; không load model hay Parquet."""
import hashlib
import json
from pathlib import Path
import zipfile

W = Path(__file__).resolve().parent
ROOT = W.parents[3]
T = W / 'transfer-cpu-worker-binary02'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    p = ROOT / 'experiments/akt/results/ctx-linux-20261108-01/transfer-copy-inventory.json'
    inventory = load(p)
    acceptance = load(T / 'acceptance.json')
    before = W / 'cpu-worker-binary-preservation01-before.json'
    assert sha(before) == inventory['before_inventory_sha256']
    assert sha(p) == acceptance['canonical_inventory_sha256']
    assert inventory['status'] == 'PRESERVED_EXACT_CPU_COLAB_DUMMY_ARTIFACT_BYTES'
    assert inventory['binary_files'] == 4 and inventory['native_text_files'] == 5
    assert len(inventory['copies']) == 9 and inventory['binary_bytes'] == 448378
    native_phase = load(W / 'received-cpu-worker-evidence01/linux-cpu-dummy-execution-20261108-01/result.json')
    context = load(W / 'received-cpu-worker-evidence01/artifacts/akt/synthetic/ctx-linux-20261108-01/worker-context.json')
    expected = {**native_phase['native_output_hashes'], **context['input_hashes']}
    for row in inventory['copies']:
        path = Path(row['local_destination'])
        assert path.resolve().is_relative_to(p.parent.resolve()) and not path.is_symlink()
        assert path.stat().st_size == row['bytes']
        assert sha(path) == row['sha256_before_copy'] == row['sha256_after_copy'] == expected[row['original_ROOT_relative']]
    assert sum(x['bytes'] for x in inventory['copies'] if x['kind'] == 'binary') == 448378
    archive = T / 'cpu-worker-binary-preservation02.zip'
    assert archive.stat().st_size == acceptance['archive_bytes'] == 339800
    assert sha(archive) == acceptance['archive_sha256']
    joined = hashlib.sha256()
    total = 0
    for i in range(8):
        receipt = load(T / f'chunk-{i:04d}.receipt.json')
        path = T / f'chunk-{i:04d}.bin'
        assert receipt['index'] == i and sha(path) == receipt['sha256']
        assert path.stat().st_size == receipt['bytes'] <= 48000
        joined.update(path.read_bytes())
        total += receipt['bytes']
    assert total == 339800 and joined.hexdigest() == acceptance['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    envelope = T / 'local-receiver01-envelope.json'
    assert sha(envelope) == inventory['transport_sha256']
    result = {'status': 'INDEPENDENT_LOCAL_DURABILITY_9_COPIES_VERIFIED',
              'canonical_inventory_sha256': sha(p), 'before_inventory_sha256': sha(before),
              'verified_files': 9, 'binary_files': 4, 'binary_bytes': 448378, 'native_text_files': 5,
              'all_local_SHA_and_sizes_match_original_pinned_inputs_or_native_outputs': True,
              'archive_sha256': sha(archive), 'archive_bytes': 339800,
              'frames': 8, 'max_frame_bytes': 48000, 'frame_bytes_SHA_and_joined_archive_SHA_verified': True,
              'zip_crc_verified': True, 'canonical_transport_sha256_semantics': 'SHA of verified locally assembled receiver01 envelope, NOT raw MCP response',
              'envelope_bytes_hash_verified_without_archiving_envelope': True,
              'model_Parquet_loads_or_fit_reruns': 0,
              'limits': 'Only raw byte/hash/CRC checks; no local checkpoint reload, model rerun or CUDA/efficacy proof.'}
    with (W / 'worker-durability-independent-check01.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
