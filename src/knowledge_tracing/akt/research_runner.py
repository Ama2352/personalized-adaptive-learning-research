"""A0 selected-fit/refit/calibration, chưa có CLI hay quyền tự chạy.

Entry consume closed authorization thật trước lazy Torch; reuse native trainer,
EarlyStopping/checkpoint và shared data/calibration. Không fake Junyi fold,
không resume/main-matrix selector. Caller phải chạy trong owned worker đã duyệt;
guards/cooperative receipts không là sandbox hoặc chứng nhận nghiên cứu fitted.
"""
from dataclasses import asdict
import csv
import hashlib
import io
from itertools import islice
import json
import math
from pathlib import Path
import random
import time
from types import SimpleNamespace

from .research_execution import AuthorizedResearchExecution, require_research_authorization
from .research_lifecycle import (LifecycleInvocation, LifecycleLedger, LifecycleBudgetExceeded,
                                 EpochRecord, PURPOSE)
from ..simulator_bridge import identity_hash
from ..simulator_research_data import SelectionFreeze
from ..simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus

OBJECTIVE = 'native_torch_bce_float32_exported_supported_mean_v1'
METRICS = 'knowledge_tracing.gam_kt.evaluation._metrics; canonical sklearn log_loss clip'
POPULATION_SCHEME = 'full-query-keys-and-observable-shard-bindings-v1'


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _canonical(value):
    return json.loads(json.dumps(value, default=str, sort_keys=True, allow_nan=False))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path, value, cap):
    raw = (json.dumps(_canonical(value), sort_keys=True, ensure_ascii=False, indent=2)+'\n').encode()
    _require(len(raw) <= cap, 'metadata/export byte cap exceeded')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush()
        import os
        os.fsync(stream.fileno())
    _require(path.read_bytes() == raw, 'metadata publication readback mismatch')
    return hashlib.sha256(raw).hexdigest()


def _write_csv(path, rows, cap):
    _require(bool(rows), 'empty full target export')
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    raw = buffer.getvalue().encode('utf-8')
    _require(len(raw) <= cap, 'prediction/target export byte cap exceeded')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush()
        import os
        os.fsync(stream.fileno())
    _require(_sha(path) == hashlib.sha256(raw).hexdigest(), 'CSV readback mismatch')
    return _sha(path)


def _memory():
    from .resources import memory_snapshot
    return memory_snapshot()


def _lazy():
    """Chỉ gọi sau actual guard + public reader/count/support/RAM admission."""
    import numpy as np
    import pandas as pd
    import torch
    from .model import AKTAdapter
    from .training import train_epoch, EarlyStopping
    from .checkpoint import save_checkpoint, load_checkpoint, restore_checkpoint
    from .tensors import collate_windows
    from .online import simulator_model_identity
    from ..gam_kt.evaluation import _metrics
    return SimpleNamespace(**locals())


def _data():
    # Data-only module imports NumPy, không Torch/model.
    from .research_simulator_data import (ResearchAKTShard, prepare_research_phase,
        fit_research_encoding, iter_research_windows, research_scoring_targets, ResearchUnseenTarget)
    return SimpleNamespace(**locals())


def _admit(execution, read_limits):
    _require(type(execution) is AuthorizedResearchExecution, 'actual typed research authorization required')
    _require(type(read_limits) is CorpusReadLimits, 'explicit typed public read limits required')
    # Không tin caller tự instantiate token hoặc approval_reference.
    actual = require_research_authorization(execution.spec, execution.evidence,
        authorization_file=execution.authorization_file, expected_authorization_sha256=execution.authorization_sha256)
    _require(actual == execution, 'authorization token differs from actual closed disk artifact')
    identity = actual.revalidate()
    b = actual.spec.budget
    _require(read_limits.max_total_bytes <= b.max_input_bytes
             and read_limits.max_events_per_learner <= b.max_events_per_learner
             and read_limits.max_total_events <= b.train_targets+b.selection_targets+b.calibration_targets
             and read_limits.max_trajectories_per_role <= b.train_learners
             and read_limits.max_wall_seconds <= b.max_wall_seconds, 'read limits exceed authorized caps')
    corpus = read_public_research_corpus(actual.spec.corpus_id,
        expected_corpus_sha256=actual.spec.expected_corpus_sha256,
        expected_done_sha256=identity['corpus']['done_sha256'], limits=read_limits)
    corpus.assert_integrity()
    _require(dict((name, digest) for name,digest,_ in corpus.files_sha256) == identity['corpus']['files_sha256']
             and corpus.plan.identity == identity['corpus']['research_plan_sha256']
             and identity_hash(corpus.bank.identity) == identity['corpus']['domain_sha256'], 'reader/authorization corpus identity drift')
    from ..response_calibration import reference_bank_v1
    reference_bank_v1(corpus.bank)
    for role in ('train','selection','calibration'):
        value = corpus.role_data(role)
        _require(len(value.trajectories) == getattr(b,role+'_learners')
                 and value.audit['audit']['targets'] == getattr(b,role+'_targets')
                 and value.reference_complete, 'role counts/full84reference support admission failed')
    _require(corpus.role_data('calibration').two_class_support, 'calibration requires two-class observed support')
    return actual, identity, corpus


class _Run:
    """Một head và journal owned; không generic trainer hay resume framework."""
    def __init__(self, execution, identity, corpus, started, wall_started):
        self.execution, self.identity = execution, identity
        # Optimization callbacks chỉ giữ metadata, không giữ role trajectories.
        self.bank, self.plan = corpus.bank, corpus.plan
        self.config, self.budget = execution.spec.native_config, execution.spec.budget
        self.output = self.config.output_dir
        self.started, self.wall_started = started, wall_started
        self.training_spent = 0.; self.training_started = None
        self.head = None; self.batch_targets = None

    def clocks(self):
        wall = max(time.perf_counter()-self.started, time.time()-self.wall_started)
        training = self.training_spent
        if self.training_started is not None:
            training += max(time.perf_counter()-self.training_started[0], time.time()-self.training_started[1])
        return dict(wall_seconds=wall, training_seconds=training)

    def guard(self):
        clocks = self.clocks(); memory = _memory()
        _require(clocks['wall_seconds'] <= self.budget.max_wall_seconds
                 and clocks['training_seconds'] <= self.budget.max_training_seconds, 'global lifecycle deadline exceeded')
        if (max(memory['process_rss_bytes'],memory.get('process_peak_rss_bytes') or 0) > self.budget.max_rss_bytes
                or memory['system_available_ram_bytes'] < self.budget.min_available_ram_bytes):
            raise MemoryError('research RAM cap/floor')
        return memory

    def transition(self, method, *args, **kwargs):
        old = self.head
        try:
            self.head = getattr(old,method)(*args,**kwargs,**self.clocks())
        except LifecycleBudgetExceeded as error:
            self.head = error.ledger
            self.flush_events(len(old.events))
            raise
        self.flush_events(len(old.events))

    def flush_events(self, start):
        import os
        with (self.output/'events.jsonl').open('a',encoding='utf-8') as stream:
            for event in self.head.events[start:]:
                stream.write(event+'\n')
            stream.flush(); os.fsync(stream.fileno())

    def json(self, relative, value):
        return _write_json(self.output/relative,value,self.budget.max_prediction_bytes)


def _phase(data, corpus, scope, freeze=None):
    roles = {'select_train80':('train',),'raw_selection10':('selection',),
             'refit_union90':('train','selection'),'calibration_predict':('calibration',)}[scope]
    shards = tuple(data.ResearchAKTShard(corpus.plan,corpus.bank,role,corpus.role_data(role).trajectories,
        corpus.role_data(role).provenance,corpus.role_data(role).provenance.identity,corpus.limits.shard_limits) for role in roles)
    return data.prepare_research_phase(scope,shards=shards,selection_freeze=freeze)


def _population(data, phase, encoding):
    # Full stream shard SHA binds strictly ordered observations, hence every past;
    # prefix-chain arithmetic remains solely in research_simulator_data.
    phase.assert_integrity(); encoding.assert_integrity()
    return _public_population(phase.trajectories,
        tuple((s.role,s.audit['audit']['shard_sha256']) for s in phase.shards))


def _public_population(trajectories, role_shards):
    return identity_hash(dict(scheme=POPULATION_SCHEME,role_shards=role_shards,
        query_keys=[(t.learner_id,o.query.item_id,o.query.timestamp,o.query.source_row,rank)
                    for t in sorted(trajectories,key=lambda row:row.learner_id)
                    for rank,o in enumerate(t.observations)]))


def _state_hash(adapter):
    digest = hashlib.sha256()
    for name,value in sorted(adapter.native.state_dict().items()):
        digest.update(name.encode()); digest.update(str((value.shape,value.dtype)).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _native_bce(tools, probabilities, labels):
    return float(tools.torch.nn.functional.binary_cross_entropy(
        tools.torch.tensor(probabilities,dtype=tools.torch.float32,device='cpu'),
        tools.torch.tensor(labels,dtype=tools.torch.float32,device='cpu'),reduction='mean').item())


def _reload_probe(run, tools, data, adapter, phase, encoding):
    """Tối đa4window đầu theo native order; không chọn theo outcome/không calibration."""
    _require(phase.scope == 'refit_union90', 'reload probe must not use calibration')
    phase.assert_integrity(); encoding.assert_integrity(); run.guard()
    windows = tuple(islice(data.iter_research_windows(phase,encoding,context=run.config.context,
        target_block=run.config.target_block,training=False),min(4,run.config.batch_size)))
    _require(windows and not any(type(w) is data.ResearchUnseenTarget for w in windows), 'invalid refit reload probe')
    payload=[]
    for w in windows:
        payload.append(dict(window_id=w.window_id,
            inputs={key:None if value is None else value.tolist() if hasattr(value,'tolist') else list(value)
                    for key,value in vars(w.inputs).items()},
            target_mask=w.target_mask.tolist(),global_ranks=w.global_ranks.tolist(),
            history_available=w.history_available.tolist(),history_used=w.history_used.tolist(),context_reset=w.context_reset.tolist()))
    before=_state_hash(adapter)
    predicted=adapter.predict_windows(windows)
    _require(len(predicted)==len(windows),'reload probe output count')
    truth={(t.learner_id,o.query.source_row,rank):o.correct
           for t in phase.trajectories for rank,o in enumerate(t.observations)}
    probabilities=[];labels=[];keys=[]
    for w,p in zip(windows,predicted):
        _require(len(p)==len(w.inputs.item_ids),'reload probe vector shape')
        for index in tools.np.flatnonzero(w.target_mask):
            key=(w.inputs.user_ids[index],int(w.inputs.source_rows[index]),int(w.global_ranks[index]))
            value=float(p[index])
            _require(key in truth and key not in keys and math.isfinite(value) and 0<=value<=1
                     and float(tools.np.float32(value))==value,'invalid reload probe target/value')
            keys.append(key);probabilities.append(value);labels.append(truth[key])
    _require(probabilities and _state_hash(adapter)==before,'reload probe empty/mutated weights')
    loss=_native_bce(tools,probabilities,labels)
    _require(math.isfinite(loss),'nonfinite reload probe loss')
    phase.assert_integrity(); encoding.assert_integrity(); run.guard()
    return dict(scope='BOUNDED_FIRST_NATIVE_WINDOWS_NOT_FULL_REFIT',windows=len(windows),targets=len(keys),
        population_sha256=identity_hash(dict(phase_sha256=phase.identity,encoding_sha256=encoding.identity,
                                             windows=payload,keys=keys)),
        predictions_sha256=identity_hash(probabilities),native_bce_mean=loss,objective=OBJECTIVE)


def _predict(run, tools, data, adapter, phase, encoding):
    """Predictor chỉ thấy WindowInputs; join truth sau toàn prediction pass."""
    run.guard(); phase.assert_integrity(); encoding.assert_integrity()
    before = _state_hash(adapter); predictions = {}; pending = []
    def flush():
        if not pending:
            return
        run.guard()
        values = adapter.predict_windows(tuple(pending))
        _require(len(values) == len(pending), 'prediction window count mismatch')
        for window, probabilities in zip(pending,values):
            _require(len(probabilities) == len(window.inputs.item_ids), 'prediction vector shape mismatch')
            for index in tools.np.flatnonzero(window.target_mask):
                key = (window.inputs.user_ids[index],int(window.inputs.source_rows[index]),int(window.global_ranks[index]))
                p = float(probabilities[index])
                _require(key not in predictions and math.isfinite(p) and 0 <= p <= 1, 'duplicate/nonfinite prediction')
                _require(float(tools.np.float32(p)) == p, 'export must preserve exact native float32 probability')
                predictions[key] = (p,dict(window_id=window.window_id,
                    history_available=int(window.history_available[index]),history_used=int(window.history_used[index]),
                    context_reset=bool(window.context_reset[index])))
        pending.clear(); run.guard()
    for window in data.iter_research_windows(phase,encoding,context=run.config.context,
                                             target_block=run.config.target_block,training=False):
        if type(window) is data.ResearchUnseenTarget:
            key = (window.learner_id,window.query.source_row,window.global_rank)
            _require(key not in predictions, 'duplicate unsupported target')
            predictions[key] = (None,dict(window_id=None,history_available=None,history_used=None,context_reset=None))
        else:
            pending.append(window)
            if len(pending) >= run.config.batch_size:
                flush()
    flush()
    truth = data.research_scoring_targets(phase,encoding)
    expected = {(t.learner_id,t.query.source_row,t.global_rank) for t in truth}
    _require(len(expected) == len(truth) and set(predictions) == expected, 'missing/extra full prediction targets')
    rows = []; labels = []; supported_p = []; supported_y = []
    for t in truth:
        p,geometry = predictions[(t.learner_id,t.query.source_row,t.global_rank)]
        _require((p is not None) == t.trained_item, 'OOV must remain null; no graph/fallback rescue')
        key = dict(learner_id=t.learner_id,item_id=t.query.item_id,timestamp=t.query.timestamp,
                   source_row=t.query.source_row,global_rank=t.global_rank,history_sha256=t.history_sha256,
                   history_hash_scheme=t.history_hash_scheme,origin_role=t.origin_role,
                   phase_scope=t.phase_scope,phase_sha256=t.phase_sha256,encoding_sha256=t.encoding_sha256)
        rows.append(dict(**key,**geometry,probability=p,support_reason='supported' if p is not None else 'oov_item'))
        labels.append(dict(**key,correct=t.correct))
        if p is not None:
            supported_p.append(p); supported_y.append(t.correct)
    _require(bool(supported_p), 'no supported prediction population')
    # Exact native BCE primitive on SAME exported float32 p; labels joined afterwards.
    loss = _native_bce(tools,supported_p,supported_y)
    _require(math.isfinite(loss) and loss >= 0 and _state_hash(adapter) == before, 'prediction mutated weights/nonfinite BCE')
    phase.assert_integrity(); encoding.assert_integrity(); run.guard()
    metrics = tools._metrics(tools.pd.DataFrame(dict(correct=supported_y,prediction=supported_p)))
    summary = dict(full_targets=len(truth),supported_targets=len(supported_p),unsupported_targets=len(truth)-len(supported_p),
        population_sha256=_population(data,phase,encoding),population_scheme=POPULATION_SCHEME,
        native_bce_mean=loss,objective=OBJECTIVE,
        reporting_evaluator=METRICS,supported_metrics=metrics,
        full_metrics=metrics if len(supported_p)==len(truth) else None)
    return summary, rows, labels


def _new_model(run, tools, encoding):
    run.guard()
    random.seed(run.config.seed); tools.np.random.seed(run.config.seed)
    tools.torch.random.default_generator.manual_seed(run.config.seed)
    adapter = tools.AKTAdapter(run.config,encoding.exercise_encoding())
    optimizer = tools.torch.optim.Adam(adapter.native.parameters(),lr=run.config.lr,betas=run.config.betas,
        eps=run.config.eps,weight_decay=run.config.weight_decay)
    run.guard()
    return adapter, optimizer


def _train_epoch(run, tools, data, adapter, optimizer, phase, encoding, epoch):
    run.head.inputs(phase.scope); run.transition('start_epoch')
    parameters = {id(p) for p in adapter.native.parameters()}
    owned = [id(p) for g in optimizer.param_groups for p in g['params']]
    _require(parameters and len(owned) == len(set(owned)) and parameters == set(owned), 'Adam parameter ownership mismatch')
    start_steps,start_targets = run.head.completed_steps,run.head.completed_targets
    def collate(entries):
        _require(run.batch_targets is None and run.head.pending is None, 'batch already pending')
        batch = tools.collate_windows([x.window for x in entries],n_items=len(adapter.encoding.vocabulary.values),
                                     device='cpu',targets=[x.targets for x in entries])
        run.batch_targets = sum(int(x.window.target_mask.sum()) for x in entries)
        return batch
    def before_step(actual,*args):
        _require(actual is optimizer and run.batch_targets is not None
                 and parameters == {id(p) for g in actual.param_groups for p in g['params']}, 'foreign Adam/batch')
        run.guard(); run.transition('reserve_step',run.batch_targets)
    def after_step(actual,*args):
        _require(actual is optimizer, 'foreign optimizer posthook')
        run.transition('body_returned',run.head.pending)
    def progress(payload):
        if run.head.pending is not None:
            _require(run.head.pending_body_returned, 'progress before optimizer return')
            run.transition('complete_step',run.head.pending); run.batch_targets = None
        run.guard()
    pre = optimizer.register_step_pre_hook(before_step); post = optimizer.register_step_post_hook(after_step)
    run.training_started = (time.perf_counter(),time.time())
    try:
        remaining = run.clocks()
        budget = dict(max_steps=run.budget.max_optimizer_steps-run.head.reserved_steps,
            max_targets=run.budget.max_optimized_targets-run.head.reserved_targets,
            max_seconds=min(run.budget.max_training_seconds-remaining['training_seconds'],
                            run.budget.max_wall_seconds-remaining['wall_seconds']),
            max_rss_bytes=run.budget.max_rss_bytes,min_available_ram_bytes=run.budget.min_available_ram_bytes)
        _require(all(budget[k] > 0 for k in ('max_steps','max_targets','max_seconds')), 'no remaining optimization budget')
        stats = tools.train_epoch(adapter,lambda:data.iter_research_windows(phase,encoding,
            context=run.config.context,target_block=run.config.target_block,training=True),optimizer=optimizer,
            epoch=epoch,budget=budget,progress_callback=progress,resource_callback=lambda _:run.guard(),
            batch_factory=collate,recovery=None)
        _require(stats.complete and stats.valid_targets == sum(s.audit['audit']['targets'] for s in phase.shards)
                 and run.head.pending is None and run.head.completed_steps-start_steps == stats.optimizer_steps
                 and run.head.completed_targets-start_targets == stats.valid_targets,
                 'partial optimization epoch or native/global counter mismatch')
        return stats
    finally:
        run.training_spent = run.clocks()['training_seconds']; run.training_started = None
        pre.remove(); post.remove()


def _checkpoint_identity(run, tools, adapter, encoding, role):
    return _canonical(dict(schema_version=1,purpose=PURPOSE,weight_role=role,authorization_sha256=run.execution.authorization_sha256,
        authorized_identity=run.identity,encoding=asdict(encoding),encoding_sha256=encoding.identity,
        objective=OBJECTIVE,resume_supported=False,
        **tools.simulator_model_identity(run.config,run.bank,adapter.encoding)))


def _save(run, tools, path, adapter, optimizer, identity, epoch):
    run.guard()
    tools.save_checkpoint(path,adapter,optimizer,identity=identity,
        progress=dict(complete=True,epoch=epoch,role=identity['weight_role']))
    size = path.stat().st_size
    _require(size <= run.budget.max_checkpoint_bytes, 'checkpoint write exceeded cooperative byte cap')
    digest = _sha(path)
    metadata = dict(checkpoint_sha256=digest,bytes=size,identity=identity,epoch=epoch)
    meta_sha = _write_json(path.with_suffix('.json'),metadata,run.budget.max_prediction_bytes)
    run.guard()
    return dict(path=path.relative_to(run.output).as_posix(),**metadata,metadata_sha256=meta_sha)


def _read_owned(run, tools, reference, expected_identity):
    """Bound metadata+bytes trước weights_only load và trước reload constructor."""
    run.guard()
    _require(reference['identity'] == expected_identity, 'checkpoint expected identity mismatch before load')
    path = run.output/reference['path']
    _require(path.parent == run.output/'fit80' or path.parent == run.output/'refit90', 'unowned checkpoint')
    with path.with_suffix('.json').open('rb') as stream:
        meta_raw = stream.read(run.budget.max_prediction_bytes+1)
    _require(len(meta_raw) <= run.budget.max_prediction_bytes
             and hashlib.sha256(meta_raw).hexdigest() == reference['metadata_sha256'], 'checkpoint metadata drift before load')
    meta = json.loads(meta_raw)
    _require(meta['identity'] == expected_identity and meta['checkpoint_sha256'] == reference['checkpoint_sha256'], 'checkpoint metadata identity drift')
    _require(type(meta['bytes']) is int and 0 < meta['bytes'] <= run.budget.max_checkpoint_bytes, 'checkpoint declared byte cap')
    with path.open('rb') as stream:
        raw = stream.read(run.budget.max_checkpoint_bytes+1)
    _require(len(raw) == meta['bytes'] and hashlib.sha256(raw).hexdigest() == meta['checkpoint_sha256'], 'checkpoint payload SHA/size before load')
    payload = tools.load_checkpoint(io.BytesIO(raw),expected_identity=expected_identity,device='cpu')
    _require(payload.get('progress',{}).get('epoch') == reference['epoch']
             and payload['progress'].get('role') == expected_identity['weight_role'], 'checkpoint epoch/role mismatch')
    return payload


def _restore_loaded(run, tools, payload, adapter, optimizer):
    actual = payload.get('model_state_dict'); expected = adapter.native.state_dict()
    _require(isinstance(actual,dict) and actual.keys() == expected.keys()
             and all(isinstance(actual[k],tools.torch.Tensor) and actual[k].device.type == 'cpu'
                     and actual[k].shape == v.shape and actual[k].dtype == v.dtype
                     and bool(tools.torch.isfinite(actual[k]).all()) for k,v in expected.items()), 'checkpoint tensor contract')
    tools.restore_checkpoint(adapter,optimizer,payload)
    restored=adapter.native.state_dict()
    _require(all(tools.torch.equal(actual[k],restored[k]) for k in actual),'checkpoint exact tensor restore parity')
    run.guard()


def _restore_owned(run, tools, reference, adapter, optimizer, expected_identity):
    payload=_read_owned(run,tools,reference,expected_identity)
    _restore_loaded(run,tools,payload,adapter,optimizer)


def _exports(run, prefix, summary, rows, truth):
    psha = _write_csv(run.output/(prefix+'/predictions.csv'),rows,run.budget.max_prediction_bytes)
    tsha = _write_csv(run.output/(prefix+'/targets.csv'),truth,run.budget.max_prediction_bytes)
    run.json(prefix+'/coverage.json',summary)
    return psha,tsha


def _calibrated_reporting_metrics(tools, raw_summary, raw_rows, calibrated_rows, truth):
    """Cùng full population/nhãn; canonical evaluator, không dùng Tfit loss làm reportLL."""
    keys=('learner_id','item_id','timestamp','source_row','global_rank','history_sha256',
          'history_hash_scheme','origin_role','phase_scope','phase_sha256','encoding_sha256')
    def index(rows):
        result={}
        for row in rows:
            _require(all(name in row for name in keys),'reporting row missing target identity')
            _require(row['phase_scope']=='calibration_predict' and row['origin_role']=='calibration',
                     'calibrated reporting requires calibration-only target role')
            key=tuple(row[name] for name in keys)
            _require(key not in result,'duplicate reporting target identity')
            result[key]=row
        return result
    raw_index=index(raw_rows); calibrated_index=index(calibrated_rows); truth_index=index(truth)
    _require(raw_index and raw_index.keys()==calibrated_index.keys()==truth_index.keys()
             and len(raw_index)==raw_summary['full_targets'],'calibrated reporting full population mismatch')
    probabilities=[];labels=[];unsupported={}
    for key,raw in raw_index.items():
        calibrated=calibrated_index[key];target=truth_index[key]
        _require(set(calibrated)==set(raw)|{'calibrated_probability'}
                 and {name:calibrated[name] for name in raw}==raw,'calibration changed original prediction row')
        _require(type(target['correct']) is int and target['correct'] in (0,1),'binary reporting label required')
        p=calibrated['calibrated_probability']
        if raw['probability'] is None:
            _require(p is None and raw['support_reason']!='supported','unsupported target must remain null')
            reason=raw['support_reason'];unsupported[reason]=unsupported.get(reason,0)+1
        else:
            _require(type(raw['probability']) in (int,float) and not isinstance(raw['probability'],bool)
                     and math.isfinite(raw['probability']) and 0<=raw['probability']<=1
                     and raw['support_reason']=='supported'
                     and type(p) in (int,float) and not isinstance(p,bool) and math.isfinite(p) and 0<=p<=1,
                     'invalid supported raw/calibrated reporting probability')
            probabilities.append(p);labels.append(target['correct'])
    _require(len(probabilities)==raw_summary['supported_targets'],'calibrated reporting support population changed')
    metrics=tools._metrics(tools.pd.DataFrame(dict(correct=labels,prediction=probabilities)))
    return dict(reporting_evaluator=METRICS,evaluation_scope='in_sample_calibration_partition_not_external_quality',
        population_sha256=raw_summary['population_sha256'],population_scheme=raw_summary['population_scheme'],
        target_identity_sha256=identity_hash(list(raw_index)),full_targets=len(raw_index),
        supported_targets=len(probabilities),unsupported_targets=len(raw_index)-len(probabilities),
        unsupported_counts=unsupported,supported_metrics=metrics,
        full_metrics=metrics if len(probabilities)==len(raw_index) else None)


def _execute(run, tools, data, train, selection, encoding80, corpus):
    config = run.config
    _require(not tools.torch.cuda.is_available() and not tools.torch.cuda.is_initialized(), 'CPU research requires CUDA hidden/unavailable')
    previous_threads = tools.torch.get_num_threads(); previous_dtype = tools.torch.get_default_dtype()
    try:
        tools.torch.set_num_threads(config.threads); tools.torch.set_default_dtype(tools.torch.float32)
        with tools.torch.device('cpu'):
            return _execute_cpu(run,tools,data,train,selection,encoding80,corpus)
    finally:
        tools.torch.set_default_dtype(previous_dtype); tools.torch.set_num_threads(previous_threads)


def _execute_cpu(run, tools, data, train, selection, encoding80, corpus):
    config = run.config
    fit,opt80 = _new_model(run,tools,encoding80)
    identity80 = _checkpoint_identity(run,tools,fit,encoding80,'simulator_research_selected_fit80')
    stopper = tools.EarlyStopping(config.patience,config.min_delta)
    history = []; best = None
    run.json('fit80/encoding.json',asdict(encoding80))
    for epoch in range(1,config.max_epochs+1):
        run.execution.revalidate(); corpus.assert_integrity()
        stats = _train_epoch(run,tools,data,fit,opt80,train,encoding80,epoch)
        summary,rows,truth = _predict(run,tools,data,fit,selection,encoding80)
        old_best = stopper.best_epoch
        stopped = stopper.observe(epoch,summary['native_bce_mean'])
        reference = None
        if stopper.best_epoch != old_best:
            best = reference = _save(run,tools,run.output/f'fit80/e{epoch}.pt',fit,opt80,identity80,epoch)
        record = EpochRecord(epoch,None if reference is None else reference['checkpoint_sha256'],identity_hash(rows),
            summary['population_sha256'],summary['full_targets'],summary['supported_targets'],summary['native_bce_mean'])
        run.transition('complete_fit_epoch',record)
        entry = dict(epoch=epoch,complete_epoch=True,training=asdict(stats),raw_selection=summary,
                     checkpoint=reference,selected_epoch=stopper.best_epoch,objective=OBJECTIVE)
        history.append(entry); run.json(f'fit80/epoch{epoch}.json',entry)
        if stopped:
            break
    _require(best is not None and stopper.best_epoch is not None, 'no selected complete checkpoint')
    run.json('fit80/epochs.json',history)
    _restore_owned(run,tools,best,fit,opt80,identity80)
    summary,rows,truth = _predict(run,tools,data,fit,selection,encoding80)
    psha,tsha = _exports(run,'selection',summary,rows,truth)
    selected_record = run.head.fit_epochs[stopper.best_epoch-1]
    _require(identity_hash(rows) == selected_record.predictions_sha256
             and best['epoch'] == stopper.best_epoch
             and best['checkpoint_sha256'] == selected_record.checkpoint_sha256,
             'best checkpoint epoch/bytes/prediction parity')
    selector = dict(kind='single_candidate_A0_epoch_selection',objective=OBJECTIVE,selected_epoch=stopper.best_epoch,
        checkpoint=best,predictions_sha256=psha,targets_sha256=tsha,coverage=summary,
        system_selector='DEFERRED_MAIN_MATRIX_NOT_RUN',history_sha256=identity_hash(history))
    selector_sha = run.json('selection/result.json',selector)
    freeze = SelectionFreeze(run.plan.identity,identity_hash(run.bank.identity),
        train.shards[0].audit['audit']['shard_sha256'],selection.shards[0].audit['audit']['shard_sha256'],
        selector_sha,stopper.best_epoch,'raw_selection_before_refit')
    run.transition('freeze_selection',freeze); run.json('selection/freeze.json',asdict(freeze))
    refit = _phase(data,corpus,'refit_union90',freeze)
    encoding90 = data.fit_research_encoding(refit)
    run.json('refit90/encoding.json',asdict(encoding90))
    refit_adapter,opt90 = _new_model(run,tools,encoding90)
    _require(refit_adapter is not fit and opt90 is not opt80
             and not ({id(p) for p in refit_adapter.native.parameters()} & {id(p) for p in fit.native.parameters()}),
             'refit must construct fresh parameters and Adam')
    del fit,opt80
    identity90 = _checkpoint_identity(run,tools,refit_adapter,encoding90,'simulator_research_refit90')
    for epoch in range(1,freeze.selected_epoch+1):
        run.execution.revalidate()
        stats = _train_epoch(run,tools,data,refit_adapter,opt90,refit,encoding90,epoch)
        run.transition('complete_refit_epoch'); run.json(f'refit90/epoch{epoch}.json',asdict(stats))
    final = _save(run,tools,run.output/'refit90/checkpoint.pt',refit_adapter,opt90,identity90,freeze.selected_epoch)
    # Bounded deterministic probe, không2full-refit passes hoặc calibration labels.
    baseline = _reload_probe(run,tools,data,refit_adapter,refit,encoding90)
    del refit_adapter,opt90  # Chỉ còn metadata của baseline; không cần giữ model/Adam cũ khi reload.
    payload = _read_owned(run,tools,final,identity90)
    reloaded,reload_opt = _new_model(run,tools,encoding90)
    _restore_loaded(run,tools,payload,reloaded,reload_opt)
    del payload,reload_opt  # Restore/RNG đã hoàn tất; prediction không dùng optimizer.
    parity = _reload_probe(run,tools,data,reloaded,refit,encoding90)
    _require(parity == baseline, 'refit reload exact prediction/loss/count parity')
    reload_sha = run.json('refit90/reload.json',dict(checkpoint_sha256=final['checkpoint_sha256'],
        max_probability_delta=0.,exact_population=True,exact_native_bce=True,
        parity=parity,resume_supported=False))
    run.transition('seal_refit',final['checkpoint_sha256'],reload_sha)
    run.head.inputs('calibration_predict')
    calibration = _phase(data,corpus,'calibration_predict',freeze)
    summary,rows,truth = _predict(run,tools,data,reloaded,calibration,encoding90)
    del reloaded  # Tfit/export chỉ dùng scalar predictions; không bảo đảm RSS trả về OS ngay.
    psha,tsha = _exports(run,'calibration',summary,rows,truth)
    run.transition('predictions_complete',checkpoint_sha256=final['checkpoint_sha256'],predictions_sha256=psha,
        population_sha256=summary['population_sha256'],full_targets=summary['full_targets'],supported_targets=summary['supported_targets'])
    from ..response_calibration import (PredictionBinding,CalibrationPartition,CalibrationTarget,fit_temperature,
        calibrate_probability,reference_bank_v1,reference_identity,CLIP,RECIPE)
    assignments = run.plan.split_plan.assignments()
    excluded = tuple(a.learner_id for a in assignments if a.role in ('train','selection'))
    learners = tuple(a.learner_id for a in assignments if a.role == 'calibration')
    families = tuple((a.learner_id,a.seed_family) for a in assignments if a.role != 'final')
    partition = CalibrationPartition(run.plan.identity,learners,excluded,families)
    binding = PredictionBinding(final['checkpoint_sha256'],final['checkpoint_sha256'],
        identity90['vocabulary_sha256'],run.plan.identity,run.bank.identity['item_bank_sha256'],
        reference_identity(reference_bank_v1(run.bank)),identity_hash(run.identity['native_evidence']['build_hashes']),
        identity_hash(run.bank.identity))
    targets = tuple(CalibrationTarget(p['learner_id'],str(p['source_row']),p['item_id'],p['history_sha256'],
        t['correct'],p['probability'],p['support_reason']) for p,t in zip(rows,truth))
    expected = tuple((t.learner_id,t.event_id,t.item_id,t.history_sha256) for t in targets)
    calibrator = fit_temperature(targets,binding=binding,partition=partition,expected_target_keys=expected,max_evaluations=200)
    csha = run.json('calibration/calibrator.json',calibrator.to_payload())
    _require(calibrator.status == 'fitted_response_temperature', 'unsupported temperature; calibrated lifecycle cannot complete')
    calibrated = [dict(p,calibrated_probability=None if p['probability'] is None else
        calibrate_probability(p['probability'],calibration=calibrator,binding=binding)) for p in rows]
    reporting=_calibrated_reporting_metrics(tools,summary,rows,calibrated,truth)
    calibrated_sha = _write_csv(run.output/'calibration/calibrated.csv',calibrated,run.budget.max_prediction_bytes)
    esha = run.json('calibration/export.json',dict(binding=asdict(binding),partition=asdict(partition),
        raw_predictions_sha256=psha,targets_sha256=tsha,calibrated_predictions_sha256=calibrated_sha,
        calibrator_sha256=csha,coverage=summary,calibrated_reporting=reporting,
        temperature_fit_objective=dict(recipe=RECIPE,logit_clip=CLIP,raw_log_loss=calibrator.raw_log_loss,
            calibrated_log_loss=calibrator.calibrated_log_loss,scope='Tfit optimization objective; not canonical reportingLL'),
        calibration_quality='in-sample response fit, not external/latent mastery calibration'))
    run.transition('finish',csha,esha)
    return dict(selected_epoch=freeze.selected_epoch,freeze_sha256=freeze.identity,refit_checkpoint=final,
                calibrator_sha256=csha,calibration_export_sha256=esha)


def run_a0_research_lifecycle(execution, *, read_limits):
    """Actual research entry; source implementation chưa chứng minh một fit đã chạy."""
    started,wall_started = time.perf_counter(),time.time()
    actual,identity,corpus = _admit(execution,read_limits)
    run = _Run(actual,identity,corpus,started,wall_started)
    run.guard()  # Trước output mkdir, NumPy preprocessing và lazy Torch/model.
    data = _data()
    train = _phase(data,corpus,'select_train80'); selection = _phase(data,corpus,'raw_selection10')
    encoding80 = data.fit_research_encoding(train)
    # Population hashes dùng public observables; không gửi truth/calibration vào fit.
    selection_population = _population(data,selection,encoding80)
    calibration_role = corpus.role_data('calibration')
    calibration_population = _public_population(calibration_role.trajectories,
        (('calibration',calibration_role.audit['audit']['shard_sha256']),))
    invocation = LifecycleInvocation(actual.spec,actual.authorization_sha256,corpus.done_sha256,corpus.plan.identity,
        identity_hash(corpus.bank.identity),tuple((r,corpus.role_data(r).audit['audit']['shard_sha256']) for r in ('train','selection','calibration')),
        selection_population,calibration_population,identity_hash(identity['native_evidence']['build_hashes']),PURPOSE)
    run.head = LifecycleLedger.begin(invocation)
    run.guard(); actual.revalidate()
    run.output.mkdir()  # Fresh path already bound by actual closed authorization.
    try:
        for name in ('fit80','selection','refit90','calibration'):
            (run.output/name).mkdir()
        run.json('invocation.json',dict(invocation=asdict(invocation),authorized_identity=identity,
            read_limits=asdict(read_limits),reader_sha256=corpus.identity,objective=OBJECTIVE,reporting_evaluator=METRICS,
            cpu_rng_scope='owned process seeds Python/NumPy/Torch; no caller RNG preservation',resume_supported=False))
        tools = _lazy(); run.guard()
        result = _execute(run,tools,data,train,selection,encoding80,corpus)
        actual.revalidate(); corpus.assert_integrity(); run.guard()
        outputs = {p.relative_to(run.output).as_posix():_sha(p) for p in run.output.rglob('*') if p.is_file()}
        run.json('run.json',dict(status='A0_SINGLE_CANDIDATE_LIFECYCLE_COMPLETE',result=result,
            counts=dict(reserved=run.head.reserved_steps,body_returned=run.head.body_returned_steps,complete=run.head.completed_steps),
            clocks=run.clocks(),main_matrix_complete=False,resume_supported=False,outputs_sha256=outputs))
        run.guard()
        run.json('COMPLETE.json',dict(status='COMPLETE_A0_RESEARCH_LIFECYCLE',run_sha256=_sha(run.output/'run.json')))
        run.guard()  # Late publication errors must leave failure, not acceptance.
        return result
    except BaseException as error:
        failure = dict(status='FAILED_NO_ACCEPTED_LIFECYCLE',error_type=type(error).__name__,error=str(error),
            phase=run.head.phase,clocks=run.clocks(),reserved_steps=run.head.reserved_steps,
            body_returned_steps=run.head.body_returned_steps,complete_steps=run.head.completed_steps,
            pending=None if run.head.pending is None else asdict(run.head.pending),rollback=False,resume_supported=False)
        try:
            run.json('failure.json',failure)
        except BaseException:
            pass  # Original exception kept; outer owned controller must reject unknown durability.
        raise
