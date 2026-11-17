"""Compact raw complete thành shard tối đa32krow, giữ stream/source nguyên vẹn."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil

from knowledge_tracing.akt.provenance import sha256_file
from knowledge_tracing.akt.types import PredictionRecord
from knowledge_tracing.akt.prediction import _validate_record
from knowledge_tracing.akt.research_junyi_calibration import iter_pinned_prediction_export


def _need(value,reason):
    if not value:
        raise ValueError(reason)


def _update(digest,row):
    _validate_record(row)
    digest.update(json.dumps(asdict(row),sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n')


def compact_raw_export(raw,output,*,expected_manifest_sha256,shard_sha256,
        max_source_bytes=4*1024**3,min_free_bytes=4*1024**3,max_rows_per_shard=32768):
    """Copy batch→shards bounded, public-readback exact digest trước COMPLETE."""
    import pyarrow.parquet as pq
    raw,output=Path(raw).absolute(),Path(output).absolute()
    _need(type(max_rows_per_shard) is int and 0<max_rows_per_shard<=32768,'bounded compact shard rows required')
    _need(raw.resolve()==raw and output.resolve()==output and not output.exists(),'new physical compact output required')
    _need(not any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in (*raw.parents,raw,*output.parents)),
          'compact path aliases rejected')
    _need(sha256_file(raw/'manifest.json')==expected_manifest_sha256,'original manifest pin changed')
    original=json.loads((raw/'manifest.json').read_text(encoding='utf-8'))
    names=[row['path'] for row in original['shards']]
    _need(original['status']=='complete' and names and len(set(names))==len(names)
          and set(names)==set(shard_sha256) and all(Path(name).name==name for name in names),'complete pinned raw source required')
    _need(sum((raw/name).stat().st_size for name in names)<=max_source_bytes
          and shutil.disk_usage(output.parent).free>=min_free_bytes,'compact disk budget unavailable')
    for name in names:
        _need(not (raw/name).is_symlink() and sha256_file(raw/name)==shard_sha256[name],'original shard pin changed')
    output.mkdir()
    fields=list(PredictionRecord.__dataclass_fields__)
    before=hashlib.sha256();total=0;writer=None;compact_shards=[];current_rows=0
    try:
        for entry in original['shards']:
            parquet=pq.ParquetFile(raw/entry['path'])
            _need(parquet.schema_arrow.names==fields,'PredictionRecord columns/order changed')
            if total==0:
                schema=parquet.schema_arrow
            _need(parquet.schema_arrow.equals(schema,check_metadata=False),'PredictionRecord field types changed')
            rows=0
            for batch in parquet.iter_batches(batch_size=1024):
                _need(batch.nbytes<=8*1024**2,'compact batch exceeds8MiB budget')
                for values in batch.to_pylist():
                    _update(before,PredictionRecord(**values));rows+=1
                offset=0
                while offset<batch.num_rows:
                    if writer is None:
                        name=f'part-compact-{len(compact_shards):05d}.parquet'
                        writer=pq.ParquetWriter(output/name,schema,compression='zstd')
                        current_rows=0
                    count=min(max_rows_per_shard-current_rows,batch.num_rows-offset)
                    writer.write_batch(batch.slice(offset,count),row_group_size=1024)
                    current_rows+=count;offset+=count
                    if current_rows==max_rows_per_shard:
                        writer.close();writer=None
                        compact_shards.append(dict(path=name,rows=current_rows))
            _need(rows==entry['rows'] and sha256_file(raw/entry['path'])==shard_sha256[entry['path']],
                  'original shard rows/content changed while compacting')
            total+=rows
        if writer is not None:
            writer.close();writer=None
            compact_shards.append(dict(path=name,rows=current_rows))
        _need(total==original['prediction_rows'],'compacted target count changed')
        compact=dict(original,shards=compact_shards,
            storage_layout='complete_multi_learner_compact_v1',resume_supported=False)
        manifest=output/'manifest.json'
        manifest.write_text(json.dumps(compact,indent=2)+'\n',encoding='utf-8')
        pins={row['path']:sha256_file(output/row['path']) for row in compact_shards}
        after=hashlib.sha256();count=0
        for row in iter_pinned_prediction_export(output,expected_manifest_sha256=sha256_file(manifest),shard_sha256=pins):
            _update(after,row);count+=1
        _need(total==count and before.digest()==after.digest(),'compacted prediction stream/order changed')
        _need(sha256_file(raw/'manifest.json')==expected_manifest_sha256,'original manifest changed while compacting')
        receipt=dict(status='COMPLETE_RAW_COMPACTION_EXACT_STREAM',rows=total,original_shards=len(names),compacted_shards=len(compact_shards),
            original_manifest_sha256=expected_manifest_sha256,original_shard_sha256=shard_sha256,
            compact_manifest_sha256=sha256_file(manifest),compact_shard_sha256=pins,
            stream_sha256=after.hexdigest(),helper_sha256=sha256_file(Path(__file__)),
            reader_memory_limit='128MB',reader_spill=False,resume_supported=False,
            max_rows_per_shard=max_rows_per_shard,max_batch_bytes=8*1024**2,row_group_rows=1024)
        (output/'COMPLETE.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        return receipt
    except BaseException:
        if writer is not None:
            writer.close()
        if (output/'manifest.json').exists():
            failed=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
            failed['status']='incomplete'
            (output/'manifest.json').write_text(json.dumps(failed,indent=2)+'\n',encoding='utf-8')
        raise
