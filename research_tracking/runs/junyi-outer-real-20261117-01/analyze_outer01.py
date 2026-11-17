"""Tổng hợp loss theo người học, bootstrap ghép cặp và Holm trên family24."""
import csv
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path

os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
CACHE=ROOT/'artifacts/akt/local-calibration/20261117/outer-export01'
MODELS=('A0','A1','A2','A3')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def bootstrap_losses(counts,losses,*,replicates=2000,seed=42):
    """Giữ response-weighted estimand, cùng draws cho toàn bộ model/metric."""
    models=tuple(sorted(losses))
    names=[];columns=[]
    for reference,candidate in combinations(models,2):
        for state in ('raw','calibrated'):
            for metric in ('log_loss','brier'):
                names.append((reference,candidate,state,metric))
                columns.append(losses[candidate][state][metric]-losses[reference][state][metric])
    deltas=np.column_stack(columns)
    assert deltas.shape==(len(counts),len(names)) and np.isfinite(deltas).all() and np.all(counts>0)
    point=deltas.sum(axis=0)/counts.sum()
    draws=np.empty((replicates,len(names)))
    rng=np.random.default_rng(seed)
    for index in range(replicates):
        sampled=rng.integers(0,len(counts),size=len(counts))
        weights=np.bincount(sampled,minlength=len(counts))
        draws[index]=(weights@deltas)/(weights@counts)
    probabilities=(1+np.count_nonzero(np.abs(draws-point)>=np.abs(point),axis=0))/(replicates+1)
    order=np.argsort(probabilities,kind='stable')
    adjusted=np.empty(len(names))
    adjusted[order]=np.minimum(1,np.maximum.accumulate(probabilities[order]*np.arange(len(names),0,-1)))
    intervals=np.quantile(draws,[.025,.975],axis=0)
    return [dict(reference=reference,candidate=candidate,probabilities=state,metric=metric,
        estimate=float(point[i]),ci95=[float(intervals[0,i]),float(intervals[1,i])],
        centered_bootstrap_p=float(probabilities[i]),holm_p=float(adjusted[i]))
        for i,(reference,candidate,state,metric) in enumerate(names)]

def main():
    import duckdb
    protocol=json.loads((B/'STATISTICAL_PLAN01.json').read_text())
    assert protocol['family_size']==24 and protocol['replicates']==2000
    con=duckdb.connect(config={'memory_limit':'384MB','threads':'1','temp_directory':''})
    losses={};metrics={};pins={};users=None;counts=None;positives=None;source_keys=None
    for model in MODELS:
        folder=CACHE/model
        complete=json.loads((folder/'COMPLETE.json').read_text())
        score=json.loads((folder/'METRICS.json').read_text())
        assert complete['status']=='COMPLETE_OUTER_NUMERIC_CPU_EXPORT'
        assert complete['targets']==4137050 and complete['fitted_targets']==4136906 and complete['oov_targets']==144
        if source_keys is None:
            source_keys=complete['source_keys_sha256']
        assert source_keys==complete['source_keys_sha256']
        files=[]
        for entry in complete['files']:
            path=folder/entry['path']
            assert sha(path)==entry['sha256']
            files.append(str(path))
        eps=float(np.finfo(np.float64).eps)
        frame=con.execute('SELECT user_id,count(*) n,sum(correct) positive_count,'
            'sum(-(correct*ln(greatest(raw_prediction,?))+(1-correct)*ln(greatest(1-raw_prediction,?)))) raw_ll,'
            'sum(pow(raw_prediction-correct,2)) raw_brier,'
            'sum(-(correct*ln(greatest(calibrated_prediction,?))+(1-correct)*ln(greatest(1-calibrated_prediction,?)))) cal_ll,'
            'sum(pow(calibrated_prediction-correct,2)) cal_brier '
            'FROM read_parquet(?) WHERE raw_prediction IS NOT NULL GROUP BY user_id ORDER BY user_id',
            [eps,eps,eps,eps,files]).fetchdf()
        if users is None:
            users=frame.user_id.to_numpy();counts=frame.n.to_numpy(dtype=np.int64);positives=frame.positive_count.to_numpy()
        assert np.array_equal(users,frame.user_id.to_numpy()) and np.array_equal(counts,frame.n.to_numpy())
        assert np.array_equal(positives,frame.positive_count.to_numpy()) and counts.sum()==4136906
        losses[model]={
            'raw':dict(log_loss=frame.raw_ll.to_numpy(),brier=frame.raw_brier.to_numpy()),
            'calibrated':dict(log_loss=frame.cal_ll.to_numpy(),brier=frame.cal_brier.to_numpy())}
        for state in ('raw','calibrated'):
            for metric in ('log_loss','brier'):
                assert abs(losses[model][state][metric].sum()/counts.sum()-score[state][metric])<1e-12
        metrics[model]=score
        pins[model]=dict(complete_sha256=sha(folder/'COMPLETE.json'),metrics_sha256=sha(folder/'METRICS.json'))
    con.close()
    comparisons=bootstrap_losses(counts,losses,replicates=protocol['replicates'],seed=protocol['seed'])
    result=dict(status='PAIRED_OUTER_STATISTICS_WITH_DOCUMENTED_LATE_PROTOCOL_FREEZE',
        protocol_sha256=sha(B/'STATISTICAL_PLAN01.json'),models=metrics,source_keys_sha256=source_keys,
        full_learners=39616,supported_learners=len(users),supported_targets=int(counts.sum()),oov_targets=144,
        input_pins=pins,comparisons=comparisons,helper_sha256=sha(__file__))
    with (B/'OUTER_COMPARISON01.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    rows=[]
    for model in MODELS:
        for state in ('raw','calibrated'):
            rows.append(dict(model=model,probabilities=state,**metrics[model][state]))
    with (B/'OUTER_METRICS01.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with (B/'OUTER_PAIRED_PRIMARY01.csv').open('x',encoding='utf-8',newline='') as stream:
        fields=['reference','candidate','probabilities','metric','estimate','ci95_low','ci95_high','centered_bootstrap_p','holm_p']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in comparisons:
            row=dict(row);low,high=row.pop('ci95');writer.writerow(dict(row,ci95_low=low,ci95_high=high))
    print('FOUR_MODELS_COMMON_COHORT_BOOTSTRAP2000_HOLM24_COMPLETE',flush=True)

if __name__=='__main__':
    main()
