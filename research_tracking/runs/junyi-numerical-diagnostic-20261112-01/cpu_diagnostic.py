"""Đọc checkpoint T4 trên CPU để chẩn đoán sai khác batch và padding.

Không optimizer update, thay kiến trúc hoặc thay tolerance. Mọi số liệu được
lưu trước kết luận; trạng thái hoàn tất chẩn đoán chưa cấp admission training.
"""
from collections import defaultdict
import csv
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
from itertools import zip_longest
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path('/opt/kltn')
RUN = 'junyi-numerical-diagnostic-20261112-01'
DEBUG = ROOT/'artifacts/akt/modal/junyi-debug-input-20261112-01'
OUTPUT = Path(os.environ.get('CPU_DIAG_OUTPUT','/cpu-evidence/'+RUN))
OUTPUT.mkdir(parents=True,exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
    OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(ROOT/'src'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write_json(name,value):
    with (OUTPUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def model_hash(adapter):
    digest = hashlib.sha256()
    for name,value in sorted(adapter.native.state_dict().items()):
        digest.update(name.encode())
        digest.update(str((value.shape,value.dtype)).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def metrics(records):
    import pandas as pd
    from knowledge_tracing.gam_kt.evaluation import _metrics
    supported = [row for row in records if row['prediction'] is not None]
    return dict(targets=len(records),supported=len(supported),oov=len(records)-len(supported),
                supported_metrics=_metrics(pd.DataFrame(supported)))


def delta_summary(values):
    import numpy as np
    if not values:
        return dict(count=0,max=None,mean=None,q99=None,over_1e6=0,over_1e5=0)
    array = np.asarray(values,dtype=np.float64)
    return dict(count=len(values),max=float(array.max()),mean=float(array.mean()),
                q99=float(np.quantile(array,.99)),over_1e6=int((array>1e-6).sum()),
                over_1e5=int((array>1e-5).sum()))


class SameLengthProxy:
    """Gom theo length trong từng batch đầu vào, giữ output đúng vị trí."""
    def __init__(self,adapter):
        self.adapter = adapter
        self.calls = []

    def __getattr__(self,name):
        return getattr(self.adapter,name)

    def predict_windows(self,windows):
        groups = defaultdict(list)
        for index,window in enumerate(windows):
            groups[len(window.inputs.item_ids)].append((index,window))
        output = [None]*len(windows)
        for length,group in groups.items():
            self.calls.append(dict(length=length,batch=len(group)))
            values = self.adapter.predict_windows(tuple(window for _,window in group))
            if len(values)!=len(group):
                raise ValueError('Same-length proxy output count mismatch')
            for (index,_),value in zip(group,values):
                output[index] = value
        return output


def run():
    import numpy as np
    import torch
    from knowledge_tracing.akt.config import AKTConfig
    from knowledge_tracing.akt.checkpoint import load_checkpoint
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.prediction import iter_predictions
    from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
    from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs
    from knowledge_tracing.akt.types import UnseenTarget
    from knowledge_tracing.akt.windows import iter_windows

    upstream = ROOT/'artifacts/akt/dependencies/upstream'
    count = int(os.environ.get('GIT_CONFIG_COUNT','0'))
    os.environ.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',
        GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    for key,value in (('safe.directory',str(upstream)),('core.autocrlf','false'),('core.fsmonitor','false')):
        os.environ[f'GIT_CONFIG_KEY_{count}'] = key
        os.environ[f'GIT_CONFIG_VALUE_{count}'] = value
        count += 1
    os.environ['GIT_CONFIG_COUNT'] = str(count)
    torch.set_num_threads(2)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True,warn_only=False)
    torch.manual_seed(42)
    views,encoding,learners,_ = prepare_inputs(
        ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01',
        ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json',
        cohort_sha256='3c706073f93fb02d5ecd673414a23494dc3301e06b3841378cd7c499c199dec2',
        roles_sha256='b0ca8f6949edd226e48d1cdb24e34ea34a042a385467e1650755994e96567ba3')
    checkpoint_path = DEBUG/'state.pt'
    metadata = json.loads((DEBUG/'metadata.json').read_text())
    checkpoint_sha = sha(checkpoint_path)
    if metadata['checkpoint_sha256']!=checkpoint_sha:
        raise ValueError('Debug checkpoint pin mismatch')
    payload = load_checkpoint(checkpoint_path,expected_identity=metadata['identity'],device='cpu')
    config = AKTConfig(phase='fold-readiness',device='cpu',execution_enabled=False,
        run_id=RUN,output_dir=ROOT/'experiments/akt/results'/RUN)
    adapter = AKTAdapter(config,encoding.native)
    adapter.native.load_state_dict(payload['model_state_dict'])
    del payload
    adapter.checkpoint_id = checkpoint_sha
    before = model_hash(adapter)
    timing = {}
    hashes = {'before':before}
    outputs = {}
    proxy = SameLengthProxy(adapter)
    for name,predictor in (('legacy',lambda:iter_predictions(adapter,learners['selection'])),
            ('batch4',lambda:iter_predictions_batched(adapter,learners['selection'])),
            ('same_length',lambda:iter_predictions_batched(proxy,learners['selection']))):
        started = time.perf_counter()
        outputs[name] = [asdict(record) for record in predictor()]
        timing[name] = time.perf_counter()-started
        hashes['after_'+name] = model_hash(adapter)
        with (OUTPUT/(name+'-predictions.jsonl')).open('x',encoding='utf-8') as stream:
            for row in outputs[name]:
                stream.write(json.dumps(row,allow_nan=False)+'\n')
    gpu = None
    if (DEBUG/'gpu-batch.jsonl').is_file():
        gpu = [json.loads(row) for row in (DEBUG/'gpu-batch.jsonl').read_text().splitlines()]
        outputs['gpu_batch4'] = gpu
    location = {}
    for learner in learners['selection']:
        for window in iter_windows(learner,encoding.native,training=False):
            if isinstance(window,UnseenTarget):
                location[window.event.source_row] = dict(global_rank=window.global_rank,window_length=0,local_position=None)
            else:
                for index in np.flatnonzero(window.target_mask):
                    location[int(window.inputs.source_rows[index])] = dict(
                        global_rank=int(window.global_ranks[index]),window_length=len(window.inputs.item_ids),
                        local_position=int(index))
    comparisons = [('legacy','batch4'),('legacy','same_length'),('batch4','same_length')]
    if gpu is not None:
        comparisons.extend([('legacy','gpu_batch4'),('batch4','gpu_batch4')])
    summary = {}
    for left_name,right_name in comparisons:
        name = left_name+'__'+right_name
        deltas = []
        details = []
        metadata_mismatches = null_mismatches = 0
        by_length = defaultdict(list)
        with (OUTPUT/(name+'-paired.jsonl')).open('x',encoding='utf-8') as stream:
            for index,(left,right) in enumerate(zip_longest(outputs[left_name],outputs[right_name])):
                p = None if left is None else left['prediction']
                q = None if right is None else right['prediction']
                left_meta = None if left is None else {k:v for k,v in left.items() if k!='prediction'}
                right_meta = None if right is None else {k:v for k,v in right.items() if k!='prediction'}
                metadata_mismatches += int(left_meta!=right_meta)
                null_mismatches += int((p is None)!=(q is None))
                delta = None if p is None or q is None else abs(p-q)
                source_row = (left or right)['source_row']
                geometry = location.get(source_row,{})
                detail = dict(index=index,source_row=source_row,**geometry,left_p=p,right_p=q,absolute_delta=delta)
                details.append(detail)
                if delta is not None:
                    deltas.append(delta)
                    by_length[geometry.get('window_length')].append(delta)
                stream.write(json.dumps(dict(**detail,left=left,right=right,
                    metadata_equal=left_meta==right_meta),allow_nan=False)+'\n')
        with (OUTPUT/(name+'-deltas.csv')).open('x',encoding='utf-8',newline='') as stream:
            columns = ['index','source_row','global_rank','window_length','local_position','left_p','right_p','absolute_delta']
            writer = csv.DictWriter(stream,fieldnames=columns)
            writer.writeheader()
            writer.writerows(details)
        summary[name] = dict(**delta_summary(deltas),metadata_mismatches=metadata_mismatches,
            null_mismatches=null_mismatches,
            by_window_length={str(length):delta_summary(values) for length,values in sorted(by_length.items())},
            top10=sorted((row for row in details if row['absolute_delta'] is not None),
                         key=lambda row:row['absolute_delta'],reverse=True)[:10])
    all_metrics = {name:metrics(records) for name,records in outputs.items()}
    metric_differences = {}
    for left_name,right_name in comparisons:
        left = all_metrics[left_name]['supported_metrics']
        right = all_metrics[right_name]['supported_metrics']
        metric_differences[left_name+'__'+right_name] = {key:None if left.get(key) is None or right.get(key) is None
            else float(right[key]-left[key]) for key in ('auc','log_loss','brier','ece','accuracy')}
    perturbations = []
    vocabulary = set(encoding.native.vocabulary.values)
    for learner in sorted(learners['selection'],key=lambda value:len(value.events),reverse=True)[:2]:
        candidates = [i for i,event in enumerate(learner.events)
                      if 0<i<len(learner.events)-1 and event.exercise in vocabulary]
        if not candidates:
            continue
        rank = min(candidates,key=lambda i:abs(i-len(learner.events)//2))
        target = learner.events[rank]
        baseline = {record.source_row:record.prediction for record in iter_predictions(adapter,[learner])}[target.source_row]
        for label,changed_rank in (('current',rank),('future',rank+1)):
            events = list(learner.events)
            events[changed_rank] = replace(events[changed_rank],correct=1-events[changed_rank].correct)
            changed = replace(learner,events=tuple(events))
            value = {record.source_row:record.prediction for record in iter_predictions(adapter,[changed])}[target.source_row]
            perturbations.append(dict(learner_id=learner.user_id,source_row=target.source_row,
                global_rank=rank,perturbation=label,changed_source_row=events[changed_rank].source_row,
                baseline_p=baseline,changed_p=value,absolute_delta=abs(baseline-value)))
    hashes['after_perturbations'] = model_hash(adapter)
    return dict(status='DIAGNOSTIC_COMPLETE_UNADMITTED',device='cpu',checkpoint_sha256=checkpoint_sha,
        torch=str(torch.__version__),model_hashes=hashes,model_state_unchanged=len(set(hashes.values()))==1,
        counts={name:len(records) for name,records in outputs.items()},timing_seconds=timing,
        metrics=all_metrics,metric_differences=metric_differences,comparisons=summary,
        same_length_native_calls=proxy.calls,causal_perturbations=perturbations,
        declared_thresholds=[1e-6,1e-5],tolerance_changed=False,optimizer_updates=0,
        interpretation='Chẩn đoán số học vàpadding bằngcheckpoint cốđịnh; chưaadmission batch4 hoặc training chính.')


started = time.monotonic()
result = dict(status='DIAGNOSTIC_FAILED_UNADMITTED',started_at_utc=datetime.now(timezone.utc).isoformat())
try:
    result.update(run())
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OUTPUT/'failure.log').write_text(traceback.format_exc())
finally:
    result.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-started)
    write_json('diagnostic-result.json',result)
print(json.dumps(result,ensure_ascii=False,allow_nan=False),flush=True)
raise SystemExit(0 if result['status']=='DIAGNOSTIC_COMPLETE_UNADMITTED' else 1)
