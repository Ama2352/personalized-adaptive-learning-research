"""Đối chiếu độc lập số học Decimal trên output cached, không gọi analyzer."""
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import time

WORK=Path(__file__).resolve().parent
INPUT=WORK/'reference-mixture-cached-attempt01'
START=time.perf_counter()

def check(ok, message):
    if not ok:
        raise ValueError(message)
    if time.perf_counter()-START>=5:
        raise TimeoutError('independent numeric cap5seconds')

def compare(actual, expected):
    if expected is None:
        check(actual is None, 'empty cell must remain null')
    else:
        check(type(actual) in (int,float) and math.isfinite(actual)
              and math.isclose(actual,float(expected),rel_tol=1e-13,abs_tol=1e-14), 'numeric mismatch')

def cell(rows):
    if not rows:
        return None,None,None
    n=Decimal(len(rows))
    p=sum((Decimal.from_float(r['prediction']) for r in rows),Decimal(0))/n
    y=sum((Decimal(r['y']) for r in rows),Decimal(0))/n
    return p,y,p-y

if __name__=='__main__':
    files=[INPUT/'summary.json',INPUT/'joined_rows.jsonl']
    pins={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    check(all(f.stat().st_size<=4*1024**2 for f in files),'bounded inputs')
    summary=json.loads(files[0].read_bytes());rows=[json.loads(line) for line in files[1].read_bytes().splitlines()]
    check(len(rows)==2160,'all2160 rows')
    keys={(r['variant'],r['seed'],r['profile'],r['event_id']) for r in rows}
    expected_keys={(v,s,p,str(t)) for v in ('graph_package','empty_graph_package')
                   for s in (20000,20001,20002) for p in ('PG','PY','PYH') for t in range(120)}
    check(keys==expected_keys,'all unique expected keys')
    expected_groups={(level,s,p,v) for level,s,p in [('pooled',None,None)]
        +[('profile',None,p) for p in ('PG','PY','PYH')]
        +[('seed',s,None) for s in (20000,20001,20002)]
        +[('trajectory',s,p) for s in (20000,20001,20002) for p in ('PG','PY','PYH')]
        for v in ('graph_package','empty_graph_package')}
    seen=set();bin_count=strata_count=0
    with localcontext() as context:
        context.prec=50
        for group in summary['groups']:
            key=(group['level'],group['seed'],group['profile'],group['variant'])
            check(key in expected_groups and key not in seen,'unique expected group');seen.add(key)
            selected=[r for r in rows if r['variant']==group['variant']
                and (group['seed'] is None or r['seed']==group['seed'])
                and (group['profile'] is None or r['profile']==group['profile'])]
            check(group['rows']==len(selected),'group population')
            ece=Decimal(0)
            check(len(group['bins'])==15 and len(group['threshold_strata'])==2,'fixed cells')
            for i,b in enumerate(group['bins']):
                subset=[r for r in selected if min(int(r['prediction']*15),14)==i]
                check(b['bin_index']==i and b['rows']==len(subset),'bin counts')
                expected=cell(subset)
                for field,value in zip(('mean_prediction','mean_correct','empirical_signed_gap'),expected):compare(b[field],value)
                if subset:ece+=Decimal(len(subset))/Decimal(len(selected))*abs(expected[2])
                bin_count+=1
            compare(group['ordinary_ece15'],ece)
            for i,s in enumerate(group['threshold_strata']):
                check(s['threshold']==.5637150147511514 and s['at_or_above_tau']==bool(i),'frozen threshold')
                subset=[r for r in selected if (r['prediction']>=s['threshold'])==bool(i)]
                check(s['rows']==len(subset),'stratum count')
                for field,value in zip(('mean_prediction','mean_correct','empirical_signed_gap'),cell(subset)):compare(s[field],value)
                strata_count+=1
    check(seen==expected_groups and bin_count==480 and strata_count==64,'all output cells')
    check(all(hashlib.sha256(f.read_bytes()).hexdigest()==pins[f.name] for f in files),'inputs unchanged')
    result=dict(status='ACCEPTED_INDEPENDENT_DECIMAL_NUMERIC_CHECK',groups=32,bins=480,strata=64,
        decimal_precision=50,rel_tol=1e-13,abs_tol=1e-14,elapsed_seconds=time.perf_counter()-START,
        cap_seconds=5,input_sha256=pins,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope_vi='Chỉ đối chiếu số học output cached. Không tăng mẫu hoặc chứng minh mastery truth.')
    with (WORK/'reference_mixture_numeric_check01.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(result,ensure_ascii=False))
