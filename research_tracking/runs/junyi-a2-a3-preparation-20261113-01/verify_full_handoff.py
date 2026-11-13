"""Đo nhận lại cache đã kiểm CPU, đối chiếu prefix, không tạo GPU."""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time
import argparse

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession,iter_junyi_window_cache
from knowledge_tracing.akt.types import TrainingWindow


def main():
    import numpy as np
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',default='full-train80-cpu-admission-20261113-01.json')
    parser.add_argument('--output',default='full-handoff-verification.json')
    args=parser.parse_args()
    assert Path(args.receipt).name==args.receipt and Path(args.output).name==args.output
    request=json.loads((ROOT/'research_tracking/runs/junyi-a1-selection-cache-20261113-01/h100-request09.json').read_text())
    data=request['inputs']
    inputs=load_full_selected_cache(ROOT/data['selected_cache_root'],ROOT/data['roles_path'],
        expected_manifest_sha256=data['selected_cache_manifest_sha256'],expected_roles_sha256=data['roles_sha256'])
    encoding=load_prepared_junyi_encoding(ROOT/data['encoding_file'],ROOT/data['encoding_receipt'],
        view=inputs.train,source_data_sha256=inputs.source_identity,
        expected_file_sha256=data['encoding_sha256'],expected_receipt_sha256=data['encoding_receipt_sha256'])
    receipt=ROOT/'artifacts/akt/window-cache'/args.receipt
    kwargs=dict(view=inputs.train,encoding=encoding,source_data_sha256=inputs.source_identity,
                expected_target_rows=inputs.train_targets,expected_manifest_sha256=data['train_window_manifest_sha256'])
    started=time.monotonic()
    admitted=JunyiWindowCacheSession(ROOT/data['train_window_cache'],**kwargs,admission_receipt=receipt,
        expected_admission_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest())
    seconds=time.monotonic()-started
    actual=list(itertools.islice(admitted.iter_windows(),5))
    expected=list(itertools.islice(iter_junyi_window_cache(ROOT/data['train_window_cache'],**kwargs),5))
    assert len(actual)==len(expected)==5
    for left,right in zip(actual,expected):
        assert type(left) is type(right) is TrainingWindow
        assert left.window.window_id==right.window.window_id
        assert np.array_equal(left.targets,right.targets)
        for name in ('item_ids','prior_responses','source_rows','timestamps'):
            assert np.array_equal(getattr(left.window.inputs,name),getattr(right.window.inputs,name))
        assert np.array_equal(left.window.target_mask,right.window.target_mask)
    result=dict(status='PASS_FULL_CACHE_CPU_HANDOFF',train_targets=inputs.train_targets,
        records=admitted.strict_records_verified,handoff_seconds=seconds,prefix_windows_compared=5,
        gpu_used=False,limits_vi='Đo CPU trên Windows, chưa là thời gian GPU/Linux. Handoff kiểm toàn SHA shard, prefix đối chiếu5window; toàn geometry đã kiểm ở CPU receipt.')
    (HERE/args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
