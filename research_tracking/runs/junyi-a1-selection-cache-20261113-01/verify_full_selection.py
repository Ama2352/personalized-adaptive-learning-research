"""Đối chiếu toàn input và metadata selection, CPU, không gọi model."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding,iter_junyi_phase_learners
from knowledge_tracing.akt.prediction_batch import prepare_prediction_windows
from knowledge_tracing.akt.research_junyi_selection_cache import SelectionCacheSession
from knowledge_tracing.akt.research_junyi_window_cache import _parts
from knowledge_tracing.akt.types import UnseenTarget


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',choices=('lookup','stream'),default='stream')
    args=parser.parse_args()
    request=json.loads((HERE/'full-selection-request.json').read_text())
    inputs=load_full_selected_cache(ROOT/request['selected_cache_root'],ROOT/request['roles_file'],
        expected_manifest_sha256=request['selected_manifest_sha256'],expected_roles_sha256=request['roles_sha256'])
    encoding=load_prepared_junyi_encoding(ROOT/request['encoding_file'],ROOT/request['encoding_receipt'],
        view=inputs.train,source_data_sha256=inputs.source_identity,
        expected_file_sha256=request['encoding_sha256'],expected_receipt_sha256=request['encoding_receipt_sha256'])
    cache_root=ROOT/request['output_root']
    receipt=json.loads((cache_root/'COMPLETE.json').read_text())
    start=time.perf_counter()
    session=SelectionCacheSession(cache_root,view=inputs.selection,encoding=encoding,
        source_sha256=inputs.source_identity,expected_targets=inputs.selection_targets,
        expected_manifest_sha256=receipt['manifest_sha256'])
    admission=time.perf_counter()-start
    reference=json.loads((ROOT/'research_tracking/runs/junyi-comparison-preflight-20261113-01/data-audit.json').read_text())['reference']
    assert session.manifest['population_sha256']==reference['selection_population_sha256']
    adapter=SimpleNamespace(encoding=encoding.native,config=SimpleNamespace(context=100,target_block=100))
    allowed=frozenset(inputs.selection.users)
    rows=[]
    for label in ('raw','cached'):
        started=time.perf_counter()
        records=session.iter_prepared() if label=='cached' else prepare_prediction_windows(adapter,
            iter_junyi_phase_learners(inputs.paths,inputs.selection,temp_dir=ROOT/'artifacts/akt/tmp/selection-verify'))
        digest=hashlib.sha256()
        count=windows=oov=0
        for record in records:
            if type(record) is UnseenTarget:
                meta,arrays,_=_parts(record,inputs.selection,encoding,allowed)
                target_meta=[]
                oov+=1;count+=1
            else:
                window,targets=record
                meta,arrays,_=_parts(window,inputs.selection,encoding,allowed)
                target_meta=[(index,event.source_row,event.user_id,event.exercise,event.time_done,
                              event.correct,event.suggested,event.fold) for index,event in targets]
                windows+=1;count+=len(targets)
            digest.update(json.dumps((meta,target_meta),sort_keys=True,separators=(',',':')).encode())
            for key,value in sorted(arrays.items()):
                digest.update(key.encode());digest.update(value.dtype.str.encode());digest.update(value.tobytes())
        rows.append(dict(method=label,seconds=time.perf_counter()-started,digest=digest.hexdigest(),
                         targets=count,windows=windows,oov=oov))
    assert rows[0]['digest']==rows[1]['digest'] and rows[0]['targets']==rows[1]['targets']==1600343
    result=dict(status='PASS_ALL_SELECTION_INPUTS_AND_METADATA_EXACT',conditions=rows,
        cache_admission_seconds=admission,population_sha256=session.manifest['population_sha256'],
        a0_population_matched=True,holdout_accessed=False,gpu_used=False,modal_spent_usd=0,
        limits_vi='CPU kiểm toàn input và metadata, chưa là thời gian inference GPU. Có strict geometry/hash để so sánh, không dùng tốc độ này dự toán epoch.')
    destination=HERE/('full-selection-parity-'+args.label+'.json')
    with destination.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
