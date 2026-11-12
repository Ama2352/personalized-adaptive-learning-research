"""Chọn metadata packet TRAIN80 bằng vị trí, đọc geometry không đọc responses."""
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def strata(histogram):
    return {label: int(histogram[begin:end+1].sum()) for label, begin, end in
            (('1-10',1,10),('11-50',11,50),('51-100',51,100),('101-199',101,199),('200',200,200))}


def padding_for_epoch_one(lengths):
    rng = random.Random(43)
    buffer = []
    shuffled = []
    for value in lengths:
        value = int(value)
        if len(buffer) < 1024:
            buffer.append(value)
        else:
            index = rng.randrange(len(buffer)); shuffled.append(buffer[index]); buffer[index] = value
    rng.shuffle(buffer); shuffled.extend(buffer)
    padded = sum(len(shuffled[start:start+4])*max(shuffled[start:start+4]) for start in range(0,len(shuffled),4))
    return dict(valid_tokens=int(sum(shuffled)), padded_tokens=padded,
                padding_tokens=padded-int(sum(shuffled)), seed=43, batch_size=4, shuffle_buffer=1024)


def main():
    started = time.monotonic()
    bundle = Path(__file__).parent
    assert json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))['is_closed'] is False
    receipt = json.loads((bundle/'full-cache-receipt02.json').read_text())
    root = ROOT/'artifacts/akt/window-cache/full-train80-20261112-02'
    pin = receipt['cache']['manifest_sha256']
    assert sha(root/'manifest.json') == pin
    manifest = json.loads((root/'manifest.json').read_text())
    assert manifest['summary']['records'] == 232662 and manifest['summary']['unseen_targets'] == 0
    rng = np.random.Generator(np.random.PCG64(42))
    groups = np.array_split(np.arange(len(manifest['shards'])),16)
    choices = {}
    for group in groups:
        index = int(group[int(rng.integers(len(group)))])
        choices[index] = sorted(int(value) for value in rng.choice(manifest['shards'][index]['records'],64,replace=False))
    histogram = np.zeros(201,dtype=np.int64); sampled = histogram.copy()
    all_lengths = np.empty(manifest['summary']['records'],dtype=np.int16)
    selected_lengths = []; packet = []; users = set(); target_total = token_total = sampled_targets = 0
    offset = 0
    for index, entry in enumerate(manifest['shards']):
        path = root/entry['name']
        assert not path.is_symlink() and path.stat().st_size == entry['bytes']
        with np.load(path,allow_pickle=False) as arrays:
            ends = arrays['offsets']; mask = arrays['target_mask']
            lengths = np.diff(ends)
            assert ends.dtype == np.int64 and len(lengths) == entry['records']
            assert ends[0] == 0 and ends[-1] == entry['tokens'] == len(mask)
            assert mask.dtype == np.bool_ and np.all((lengths>=1)&(lengths<=200))
            counts = np.add.reduceat(mask,ends[:-1],dtype=np.int64)
            assert np.all((counts>=1)&(counts<=100))
            histogram += np.bincount(lengths,minlength=201)
            all_lengths[offset:offset+len(lengths)] = lengths
            token_total += int(lengths.sum()); target_total += int(counts.sum())
            if index in choices:
                selected = np.asarray(choices[index],dtype=np.int64)
                metadata = json.loads(arrays['metadata'].tobytes())
                assert all(metadata[int(local)]['kind']=='training' for local in selected)
                users.update(metadata[int(local)]['user_id'] for local in selected)
                sampled += np.bincount(lengths[selected],minlength=201)
                sampled_targets += int(counts[selected].sum())
                selected_lengths.extend(int(value) for value in lengths[selected])
                packet.append(dict(shard_index=index,name=entry['name'],bytes=entry['bytes'],sha256=entry['sha256'],
                    record_indexes=choices[index],windows=64,target_rows=int(counts[selected].sum()),
                    window_tokens=int(lengths[selected].sum())))
        if index in choices:
            assert sha(path)==entry['sha256']
        offset += len(lengths)
    assert offset == 232662 and target_total == 13347331 and token_total == 23936131
    assert int(sampled.sum())==1024 and len(selected_lengths)==1024
    assert sha(root/'manifest.json')==pin and 'torch' not in sys.modules
    p,q = histogram/histogram.sum(),sampled/sampled.sum()
    output = dict(status='PROPOSED_TRAIN80_PACKET_SELECTION_METADATA_ONLY',
        source_root=root.relative_to(ROOT).as_posix(),source_manifest_sha256=pin,source_key=manifest['key'],
        sampling=dict(seed=42,generator='numpy.PCG64',shard_strata=16,shards_per_stratum=1,
            windows_per_shard=64,uses_correctness=False,redraws=0,order='source shard then record index'),
        full_geometry=dict(windows=offset,targets=target_total,tokens=token_total,length_histogram=histogram.tolist(),
            length_strata=strata(histogram),mean_length=token_total/offset,
            epoch_one_padding=padding_for_epoch_one(all_lengths)),
        packet_geometry=dict(windows=1024,targets=sampled_targets,tokens=int(sum(selected_lengths)),
            distinct_learners=len(users),full_role_coverage=False,length_histogram=sampled.tolist(),
            length_strata=strata(sampled),mean_length=sum(selected_lengths)/1024,
            epoch_one_padding=padding_for_epoch_one(selected_lengths)),
        total_variation_exact_lengths=float(.5*np.abs(p-q).sum()),
        total_variation_length_strata=float(.5*sum(abs(strata(sampled)[key]/1024-strata(histogram)[key]/offset)
                                                   for key in strata(histogram))),
        selected_shards=packet,selected_shards_full_sha_verified=True,all_shards_full_sha_rehashed=False,
        arrays_read=['offsets','target_mask','selected-shard record metadata'],
        arrays_not_read=['targets','prior_responses','qa/model tensors'],
        elapsed_seconds=time.monotonic()-started,torch_imported=False,cloud_execution=False,
        training_performed=False,packet_payload_created=False,
        limits='Geometry représentative đánhgiá trênhistogram; learnerability/profile/labeldistribution chưa kiểm. Future workerphảighi engineeringpacket scope vàgiữ originalphase/encoding lineage.')
    with (bundle/'representative-packet-selection.json').open('x',encoding='utf-8') as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({key:output[key] for key in ('elapsed_seconds','total_variation_exact_lengths','total_variation_length_strata')}))
    print(json.dumps(dict(full=output['full_geometry']['length_strata'],packet=output['packet_geometry']['length_strata'],
        packet_targets=sampled_targets,packet_learners=len(users),full_mean=output['full_geometry']['mean_length'],
        packet_mean=output['packet_geometry']['mean_length'],full_padding=output['full_geometry']['epoch_one_padding'],
        packet_padding=output['packet_geometry']['epoch_one_padding'])))


if __name__=='__main__':
    main()
