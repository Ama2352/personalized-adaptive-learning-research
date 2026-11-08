"""Probe ghép metric thật trên năm hàng tự dựng; không fit hoặc dữ liệu thật."""
from pathlib import Path
import hashlib,json,sys,time
R=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import worker_gate
worker_gate()  # Trước NumPy/pandas/sklearn.
sys.path.insert(0,str(R/'src'))
from knowledge_tracing.akt.resources import memory_snapshot
def guard():
    m=memory_snapshot()
    if max(m['process_rss_bytes'],m['process_peak_rss_bytes'] or 0)>512*1024**2 or m['system_available_ram_bytes']<1024**3:
        raise MemoryError('synthetic metrics512MiB/available1GiB guard')
    return m
before_memory=guard()
pins={name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in (
    'src/knowledge_tracing/akt/research_runner.py','src/knowledge_tracing/gam_kt/evaluation.py')}
from types import SimpleNamespace as NS
import pandas as pd
from knowledge_tracing.gam_kt.evaluation import _metrics
from knowledge_tracing.akt.research_runner import _calibrated_reporting_metrics,POPULATION_SCHEME
after_import=guard()
raw=[];truth=[];calibrated=[]
for i,(p,y,c) in enumerate(((.3,0,.2),(.7,1,.8),(.1,0,0.),(.9,1,1.),(None,0,None))):
    key=dict(learner_id='manufactured-calibration-user',item_id=f'fixture-item-{i}',timestamp=i+1,source_row=i+1,
        global_rank=i,history_sha256='a'*64,history_hash_scheme='MANUFACTURED_NO_REAL_HISTORY',origin_role='calibration',
        phase_scope='calibration_predict',phase_sha256='b'*64,encoding_sha256='c'*64)
    row=dict(**key,probability=p,support_reason='supported' if p is not None else 'oov_item')
    raw.append(row);truth.append(dict(**key,correct=y));calibrated.append(dict(row,calibrated_probability=c))
summary=dict(full_targets=5,supported_targets=4,population_sha256='d'*64,population_scheme=POPULATION_SCHEME)
result=_calibrated_reporting_metrics(NS(pd=pd,_metrics=_metrics),summary,raw,list(reversed(calibrated)),list(reversed(truth)))
expected=_metrics(pd.DataFrame({'correct':[0,1,0,1],'prediction':[.2,.8,0.,1.]}))
assert result['supported_metrics']==expected and result['full_metrics'] is None and result['unsupported_counts']=={'oov_item':1}
assert abs(expected['brier']-.02)<1e-14 and expected['auc']==1.
assert abs(expected['ece']-.1)<1e-14
assert pins=={name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in pins}
assert 'torch' not in sys.modules
final_memory=guard()
output=Path(__file__).parent/'metrics_native01'/'result.json'
receipt=dict(status='PASS_SYNTHETIC_ACTUAL_EVALUATOR_NOT_MODEL_RESULT',manufactured_rows=5,supported_rows=4,
    unsupported_rows=1,reporting=result,source_before_after=pins,before_memory=before_memory,after_import=after_import,
    final_memory=final_memory,model_calls=0,solver_fits=0,real_data_reads=0,
    scope_vi='Chạy evaluator pandas/sklearn thật và helper mới trên số liệu tự dựng. AUC/Brier không phải kết quả AKT/CG-AKT hoặc evidence trả lời RQ.')
with output.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
print('PASS_SYNTHETIC_ACTUAL_CANONICAL_METRICS')
