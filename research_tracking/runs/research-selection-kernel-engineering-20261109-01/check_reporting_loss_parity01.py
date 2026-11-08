"""Fixture LL theo contract đối chiếu evaluator hiện hành; không fit/data thật."""
import time
START=time.perf_counter()
from pathlib import Path
import hashlib
import json
import math
import os
import sys
ROOT=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
assert Path(sys.prefix).resolve()==ROOT/'.venv'
os.environ.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
sys.path.insert(0,str(ROOT/'src'))
source=ROOT/'src/knowledge_tracing/gam_kt/evaluation.py'
before=hashlib.sha256(source.read_bytes()).hexdigest()
from knowledge_tracing.gam_kt.evaluation import _metrics
import numpy as np
import pandas as pd
import sklearn
EPS=2**-52
def proposed(y,p):
    two=(1.-p,p)
    return -math.log(min(1.-EPS,max(EPS,two[y])))
cases=[
 ('perfect_boundaries', [0,1,0,1],[0.,1.,0.,1.]),
 ('wrong_boundaries',[0,1,0,1],[1.,0.,1.,0.]),
 ('ordinary',[0,1,1,0,1,0],[.1,.7,.4,.8,.9,.3]),
 ('near_clip',[0,1,0,1,0,1],[1e-300,1e-300,1.-2**-53,1.-2**-53,EPS,1.-EPS]),
 ('float32_exports',[0,1,1,0,0,1],[float(np.float32(x)) for x in (.000001,.999999,.33333334,.6666667,0.,1.)]),
 ('unequal_cluster_rows',[0,1]+[1]*18,[.4,.6]+[.8]*18),
]
rows=[]
for name,y,p in cases:
    actual=_metrics(pd.DataFrame({'correct':y,'prediction':p}))['log_loss']
    expected=math.fsum(proposed(label,probability) for label,probability in zip(y,p))/len(y)
    rows.append(dict(fixture=name,labels=y,probabilities=p,canonical_log_loss=actual,
        contract_log_loss=expected,absolute_difference=abs(actual-expected)))
    assert math.isclose(actual,expected,rel_tol=0.,abs_tol=1e-12)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
assert 'torch' not in sys.modules
assert time.perf_counter()-START<8
out=P/'reporting-loss-parity01.json'
value=dict(status='ACCEPTED_SIX_MANUFACTURED_REPORTING_LL_PARITY_FIXTURES_NOT_SELECTOR',
    fixtures=rows,source_sha256=before,scikit_learn=sklearn.__version__,numpy=np.__version__,pandas=pd.__version__,
    epsilon=EPS,absolute_tolerance=1e-12,relative_tolerance=0.,seconds=time.perf_counter()-START,
    scope_vi='Currentevaluator vs proposedbinary64formula; không kernelimplementation/bitwiseidentity/realdata/model/selection/CUDA claim.')
with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(status=value['status'],fixtures=len(rows),max_abs_difference=max(r['absolute_difference'] for r in rows),seconds=time.perf_counter()-START)))
