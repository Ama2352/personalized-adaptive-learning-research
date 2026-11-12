"""Tổng hợp metricselection bằng đúng hàm metric GAM-KT hiện có."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.gam_kt.evaluation import _metrics

native=ROOT/'experiments/akt/results/modal-junyi-a0-b128-h100-20261112-03'
receipt=json.loads((native/'receipt.json').read_text())
assert receipt['status']=='JUNYI_A0_SELECTED_ONLY_COMPLETE' and receipt['download_inventory_verified']
terminal=receipt['worker_result']['terminal']
count=terminal['validation']['targets']
labels=np.empty(count,dtype=np.uint8)
probabilities=np.empty(count,dtype=np.float64)
member='experiments/akt/results/modal-junyi-a0-b128-h100-20261112-01/'+terminal['predictions_file']
with zipfile.ZipFile(native/'artifacts.zip') as archive:
    inventory=json.loads(archive.read('SHA256.json'))
    assert inventory[member]['sha256']==terminal['predictions_sha256']
    rows=0
    with archive.open(member) as stream:
        for line in stream:
            record=json.loads(line)
            assert rows<count
            labels[rows]=record['correct']
            probabilities[rows]=record['prediction']
            rows+=1
assert rows==count==1600343
metrics=_metrics(pd.DataFrame(dict(correct=labels,prediction=probabilities)))
assert abs(metrics['log_loss']-terminal['validation']['native_bce'])<1e-6
source=ROOT/'src/knowledge_tracing/gam_kt/evaluation.py'
result=dict(scope='SELECTION_USED_FOR_EPOCH_CHOICE',selected_epoch=terminal['selected_epoch'],
    targets=count,learners=15847,oov=0,metrics=metrics,ece_equal_width_bins=15,
    metrics_implementation=source.relative_to(ROOT).as_posix(),
    metrics_implementation_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    predictions_sha256=terminal['predictions_sha256'],independent_evaluation=False,
    limits_vi='Dự đoán trên tập đã dùng chọn epoch, dùng mô tả tiến độ. Chưa dùng làm kết quả đánh giá độc lập hoặc so sánh với BKT/GAM-KT khác tập.')
with (BUNDLE/'selection-metrics.json').open('x',encoding='utf-8') as stream:
    stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
