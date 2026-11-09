"""GKT29 selected-only producer candidate, chưa apply hoặc execute.

Public entry tự kiểm actual GKT authorization trước lazy Torch. Tái dùng epoch,
predictor, checkpoint và stopper, không viết lại optimizer math. Không refit,
temperature fit, winner/freeze hoặc public resume. Caller chạy trong owned worker
có hard wall/Job-family guard; internal guard chỉ đo worker RSS/free RAM.
"""
from collections import Counter
from dataclasses import asdict
import csv
import hashlib
import io
import json
import math
import os
import random
import time
from types import SimpleNamespace

from knowledge_tracing.gkt.research_execution import (
    AuthorizedGKTSelectedExecution, GKTSelectedExecutionSpec, GKTSelectedEvidence,
    require_gkt_selected_authorization, need, canonical, OBJECTIVE, RECIPE_SHA256, ROOT,
)
from knowledge_tracing.akt.research_execution import _hash_file
from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus
from knowledge_tracing.simulator_bridge import identity_hash
from knowledge_tracing.research_admission import (
    ModelNeutralKey, RawSelectedRow, SelectedCandidateClaim, ArtifactClaim, TERMINAL_KIND,
    POPULATION_SCHEME, _canonical as population_bytes,
)


def _lazy():
    import torch
    import numpy as np
    import pandas as pd
    from knowledge_tracing.gkt import research_data as data, research_training as training
    from knowledge_tracing.gkt import research_checkpoint as cp
    from knowledge_tracing.gkt.config import GKTKernelConfig, GKTBinding
    from knowledge_tracing.gkt.research_model import GKTResearchModel, GKTResearchModelSpec, EVIDENCE_ROLE
    from knowledge_tracing.sakt.training import state_digest
    from knowledge_tracing.akt.training import EarlyStopping
    from knowledge_tracing.gam_kt.evaluation import _metrics
    return SimpleNamespace(torch=torch, np=np, pd=pd, data=data, training=training, cp=cp,
        config=GKTKernelConfig, binding=GKTBinding, model=GKTResearchModel, model_spec=GKTResearchModelSpec,
        model_role=EVIDENCE_ROLE, digest=state_digest, stopper=EarlyStopping, metrics=_metrics)


def selection_rows(result, truth, *, phase_sha256, encoding_sha256):
    """Loss/reporting join sau prediction; không tính hoặc đổi probability."""
    need(type(result) is dict and result['status'] == 'complete'
         and result['complete'] is True and result['stop_reason'] == 'raw_prediction_complete'
         and result['role'] == 'gkt_research_compute_only_no_fit_attestation'
         and result['resume_supported'] is False and result['fitted_research_model'] is False
         and result['pending_batch_keys'] == () and result['cleanup_errors'] == []
         and result['model_state_before'] == result['model_state_after']
         and result['normalization_before'] == result['normalization_after']
         and result['raw_predictions_sha256'] == identity_hash(result['predictions']),
         'complete frozen GKT selection prediction required')
    expected = {}
    for target in truth:
        key = (target.learner_id, target.query.source_row, target.global_rank)
        need(key not in expected, 'duplicate truth target')
        expected[key] = target
    need(len(expected) == len(result['predictions']) and len(expected)>0, 'full selection population required')
    rows, input_reasons, seen = [], {}, set()
    for prediction in result['predictions']:
        key = (prediction['learner_id'], prediction['query']['source_row'], prediction['global_rank'])
        need(key in expected and key not in seen, 'prediction/truth key mismatch')
        seen.add(key); target = expected[key]
        need((prediction['query'], prediction['origin_role'], prediction['history_hash_scheme'], prediction['history_sha256'])
             == (asdict(target.query), target.origin_role, target.history_hash_scheme, target.history_sha256)
             and target.origin_role == 'selection' and target.phase_scope == 'raw_selection10'
             and target.phase_sha256 == phase_sha256 and target.encoding_sha256 == encoding_sha256,
             'query/history/phase/encoding truth join mismatch')
        probability = prediction['probability']
        need(prediction['prediction_status'] == ('unsupported' if probability is None else 'scored'),
             'unprocessed target cannot be exported as unsupported')
        reason = prediction['support_reason']
        need((probability is None and reason in ('oov_item','unsupported_history'))
             or (probability is not None and reason in ('cold_query_only','known_history')),
             'GKT eligibility and null reason disagree')
        need(target.trained_item == (reason != 'oov_item'), 'registry support is not suffix eligibility')
        neutral = ModelNeutralKey(target.learner_id, target.query.item_id, target.query.timestamp,
            target.query.source_row, target.global_rank, target.history_hash_scheme, target.history_sha256, target.origin_role)
        rows.append(RawSelectedRow('GKT', neutral, target.correct, probability,
            prediction['support_reason'] if probability is None else 'supported', 'raw_selection10',
            target.phase_sha256, target.encoding_sha256))
        input_reasons[neutral] = prediction['support_reason']
    need(seen == set(expected), 'missing full selection keys')
    rows.sort(key=lambda row: row.key)
    return tuple(rows), input_reasons


def population(rows):
    full, labels = hashlib.sha256(), hashlib.sha256()
    for row in rows:
        full.update(population_bytes(row.key.values()))
        labels.update(population_bytes((row.key.values(), row.correct)))
    return dict(scheme=POPULATION_SCHEME, full_keys_sha256=full.hexdigest(), full_keys_labels_sha256=labels.hexdigest())


class _Run:
    def __init__(self, execution):
        need(type(execution) is AuthorizedGKTSelectedExecution, 'actual GKT execution token required')
        self.execution, self.spec = execution, execution.spec
        self.output, self.budget = self.spec.output, self.spec.budget
        self.reserved = self.returned = self.completed = 0
        self.reserved_targets = self.returned_targets = self.completed_targets = 0
        self.training_spent = 0.; self.training_started = None
        self.prediction_passes = self.prediction_targets = self.constructors = self.adam_constructors = 0
        self.output_bytes = 0
        self.model_calls = 0

    def train_seconds(self):
        if self.training_started is None:
            return self.training_spent
        return self.training_spent+max(time.perf_counter()-self.training_started[0], time.time()-self.training_started[1])

    def guard(self):
        self.execution.guard(self.train_seconds())
        need(self.output_bytes <= self.budget.max_output_bytes-self.budget.max_metadata_bytes, 'owned output/failure reserve')

    def boundary(self):
        self.guard(); self.execution.revalidate(self.train_seconds()); self.guard()

    def write(self, relative, value):
        self.guard()
        raw = (json.dumps(canonical(value), sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n').encode()
        need(len(raw) <= self.budget.max_metadata_bytes
             and self.output_bytes+len(raw) <= self.budget.max_output_bytes-self.budget.max_metadata_bytes,
             'metadata leaf/total cap before write')
        path = self.output/relative
        need(path.parent.is_dir(), 'existing owned output parent required')
        with path.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        self.output_bytes += len(raw); self.guard()
        return hashlib.sha256(raw).hexdigest()

    def event(self, kind, **extra):
        self.guard()
        raw = (json.dumps(dict(kind=kind, reserved=self.reserved, body_returned=self.returned,
            complete=self.completed, reserved_targets=self.reserved_targets, body_returned_targets=self.returned_targets,
            complete_targets=self.completed_targets, training_seconds=self.train_seconds(), **extra),
            sort_keys=True, allow_nan=False)+'\n').encode()
        need(self.output_bytes+len(raw) <= self.budget.max_output_bytes-self.budget.max_metadata_bytes, 'journal byte cap')
        with (self.output/'events.jsonl').open('ab') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        self.output_bytes += len(raw)


def _construct(run, tools, view):
    run.boundary()
    need(run.constructors < 2 and run.adam_constructors < 2, 'one fit model and one fresh best reload only')
    r, torch = run.spec.recipe, tools.torch
    with torch.random.fork_rng(devices=[]), torch.device('cpu'):
        torch.random.default_generator.manual_seed(r.seed)
        run.constructors += 1
        graph = view.graph
        vocabulary = identity_hash(list(view.encoding.exercise_encoding().vocabulary.values))
        config = tools.config(28,32,32,32,'static','concept',True,True)
        binding = tools.binding(graph.domain_sha256,vocabulary,graph.node_ids,'concept')
        spec = tools.model_spec(r.recipe_id,RECIPE_SHA256,view.phase.scope,view.phase.identity,
            view.encoding.identity,vocabulary,tools.training.model_source_identity(),42,tools.model_role)
        adjacency = torch.zeros((28,28),dtype=torch.float32,device='cpu')
        nodes = {node:index for index,node in enumerate(graph.node_ids)}
        for parent,child in graph.edges:
            adjacency[nodes[parent],nodes[child]] = 1.
        model = tools.model(config,binding,graph,adjacency,spec=spec)
        run.adam_constructors += 1
        optimizer = torch.optim.Adam(model.parameters(), lr=r.lr, betas=r.betas, eps=r.eps, weight_decay=r.weight_decay,
            amsgrad=False, foreach=False, fused=False, maximize=False, capturable=False, differentiable=False)
    need(all(p.device.type == 'cpu' and p.dtype == torch.float32 and p.requires_grad for p in model.parameters()), 'CPU FP32 owned model')
    run.guard()
    return model, optimizer


def _epoch_spec(tools, recipe, epoch):
    return tools.training.GKTResearchSpec(epoch,recipe.batch_size,recipe.max_grad_norm)


def _train_epoch(run, tools, model, optimizer, view, epoch, targets, budget, progress):
    r, b = run.spec.recipe, run.budget
    run.boundary(); before_steps, before_targets = run.returned, run.returned_targets
    lengths = [len(t.observations) for t in view.phase.trajectories]
    random.Random(42+epoch).shuffle(lengths)
    batch_targets = [sum(lengths[i:i+4]) for i in range(0,len(lengths),4)]
    need(sum(batch_targets)==targets,'complete trajectory batch sizes')
    need(run.model_calls+len(batch_targets)<=b.max_model_calls,'train model calls before allocation')
    local = [0, None]
    def reserve(owned, args, kwargs):
        need(owned is optimizer and local[1] is None, 'one pending owned Adam body')
        need(local[0]<len(batch_targets),'unexpected owned Adam body')
        count = batch_targets[local[0]]
        need(count > 0 and run.reserved+1 <= b.max_optimizer_steps
             and run.reserved_targets+count <= b.max_optimized_targets, 'cumulative optimizer/target quota')
        run.guard(); run.reserved += 1; run.reserved_targets += count; local[1] = count
        run.event('adam_reserved', epoch=epoch, targets=count)
    def returned(owned, args, kwargs):
        need(owned is optimizer and local[1] is not None, 'owned body returned without reservation')
        count = local[1]; run.returned += 1; run.returned_targets += count; local[0] += 1; local[1] = None
        run.event('adam_body_returned', epoch=epoch, targets=count)
    handles = [optimizer.register_step_pre_hook(reserve), optimizer.register_step_post_hook(returned)]
    run.training_started = (time.perf_counter(), time.time())
    try:
        result = tools.training.train_research_epoch(model, view, optimizer=optimizer,
            spec=_epoch_spec(tools,r,epoch),budget=budget,progress=progress)
    finally:
        run.training_spent = run.train_seconds(); run.training_started = None
        for handle in handles:
            handle.remove()
    before,ledger = result['counters_before'],result['counters']
    need(result['status']=='complete' and result['complete'] is True and result['stop_reason']=='epoch_complete'
         and result['pending_batch_keys']==() and not progress.poisoned
         and ledger['optimized_targets']-before['optimized_targets']==targets
         and ledger['adam_started']-before['adam_started']==ledger['adam_returned']-before['adam_returned']==local[0]
         and ledger['input_targets']-before['input_targets']==targets
         and ledger['complete_train_epochs']==epoch
         and run.returned-before_steps == local[0] and run.returned_targets-before_targets == targets
         and local[1] is None and run.reserved == run.returned, 'complete epoch/global durable accounting required')
    run.completed = run.returned; run.completed_targets = run.returned_targets
    run.model_calls += ledger['model_calls_started']-before['model_calls_started']
    need(run.model_calls<=b.max_model_calls,'whole producer physical model-call cap')
    run.boundary()
    return result


def _predict(run, tools, model, view, epoch, budget, progress):
    need(view.phase.scope == 'raw_selection10', 'selected producer predicts only selection10')
    run.boundary(); count = run.budget.selection_targets
    need(run.prediction_passes < run.spec.recipe.max_epochs+1
         and run.prediction_targets+count <= run.budget.max_prediction_targets, 'selection pass/full-row quota')
    maximum_calls=2*((len(view.phase.trajectories)+3)//4)
    need(run.model_calls+maximum_calls<=run.budget.max_model_calls,'prediction work reservation before model')
    rng_before=progress.rng_state.clone()
    result=tools.training.predict_research_gkt(model,view,spec=_epoch_spec(tools,run.spec.recipe,epoch),
        budget=budget,progress=progress)
    need(tools.torch.equal(rng_before,progress.rng_state) and not progress.poisoned,'eval owned RNG unchanged')
    scored=tools.training.score_raw_predictions(view,result)
    truth=tools.data.gkt_research_scoring_targets(view)
    rows,reasons=selection_rows(result,truth,phase_sha256=view.phase.identity,encoding_sha256=view.encoding.identity)
    need(len(rows) == count, 'declared full selection count')
    need(all(row.phase_sha256 == view.phase.identity and row.encoding_sha256 == view.encoding.identity for row in rows),
         'actual selected phase/encoding mismatch')
    run.prediction_passes += 1; run.prediction_targets += count
    run.model_calls += result['counters']['model_calls_started']-result['counters_before']['model_calls_started']
    supported = [row for row in rows if row.probability is not None]
    run.event('raw_selection_population',epoch=epoch,full_targets=len(rows),supported_targets=len(supported),
        unsupported_counts=dict(Counter(row.support_reason for row in rows if row.probability is None)))
    need(bool(supported), 'no supported selection population')
    objective=scored['raw_response_log_loss']
    need(type(objective) is float and math.isfinite(objective) and objective>=0
         and scored['full_targets']==count and scored['eligible_targets']==len(supported),
         'GKT29 finite response-pooled binary64 Log Loss')
    metrics = tools.metrics(tools.pd.DataFrame(dict(correct=[row.correct for row in supported],
        prediction=[row.probability for row in supported])))
    summary = dict(full_targets=len(rows), supported_targets=len(supported), unsupported_targets=len(rows)-len(supported),
        unsupported_counts=dict(Counter(row.support_reason for row in rows if row.probability is None)),
        raw_response_log_loss=objective, objective=OBJECTIVE, population=population(rows), supported_metrics=metrics,
        full_metrics=metrics if len(supported) == len(rows) else None,
        reporting='knowledge_tracing.gam_kt.evaluation._metrics', prediction_sha256=identity_hash([asdict(row) for row in rows]))
    run.boundary()
    return summary, rows, reasons


def _budget(run, tools, view, *, training):
    """One immutable whole-wall origin; separate actual train clock in run."""
    b,r=run.budget,run.spec.recipe
    trajectories=view.phase.trajectories
    targets=sum(len(t.observations) for t in trajectories)
    prefixes=sum(len(t.observations)*(len(t.observations)-1)//2 for t in trajectories)
    passes=r.max_epochs if training else r.max_epochs+1
    calls=passes*((len(trajectories)+3)//4)*(1 if training else 2)
    need(all(0<len(t.observations)<=210 for t in trajectories),'whole trajectories1..210')
    need(passes*prefixes <= (b.max_training_prefix_events if training else b.max_prediction_prefix_events),
         'expanded-prefix work reserved before model')
    return tools.training.GKTResearchBudget(run.execution.started[0],b.max_wall_seconds,
        b.max_worker_rss_bytes,b.min_available_ram_bytes,passes*targets,passes*prefixes,calls,
        b.max_optimizer_steps if training else 0,b.max_optimized_targets if training else 0,
        0 if training else b.max_prediction_targets)


def _exports(run, rows, reasons):
    directory = run.output/'selection'; directory.mkdir()
    keys = list(asdict(rows[0].key))
    for name, fields, payloads in (
        ('predictions.csv', keys+['probability','support_reason','input_support_reason','phase_scope','phase_sha256','encoding_sha256'],
         (dict(**asdict(row.key), probability=row.probability, support_reason=row.support_reason,
               input_support_reason=reasons[row.key], phase_scope=row.phase_scope, phase_sha256=row.phase_sha256,
               encoding_sha256=row.encoding_sha256) for row in rows)),
        ('targets.csv', keys+['correct'], (dict(**asdict(row.key), correct=row.correct) for row in rows))):
        path = directory/name
        buffer = io.StringIO(newline='')
        writer = csv.DictWriter(buffer, fieldnames=fields)
        with path.open('xb') as stream:
            writer.writeheader()
            raw = buffer.getvalue().encode('utf-8')
            need(run.output_bytes+len(raw) <= run.budget.max_output_bytes-run.budget.max_metadata_bytes, 'CSV header budget')
            stream.write(raw); run.output_bytes += len(raw)
            for payload in payloads:
                run.guard(); buffer.seek(0); buffer.truncate(0); writer.writerow(payload)
                raw = buffer.getvalue().encode('utf-8')
                need(run.output_bytes+len(raw) <= run.budget.max_output_bytes-run.budget.max_metadata_bytes, 'CSV row budget before write')
                stream.write(raw); run.output_bytes += len(raw)
            stream.flush(); os.fsync(stream.fileno())
        run.guard()


def _claim(run, summary, rows, reference, epoch, completed_epochs, initial, encoding, selection, terminal):
    def artifact(path):
        digest, size = _hash_file(path, cap=run.budget.max_output_bytes)
        return ArtifactClaim(digest, size)
    return SelectedCandidateClaim(candidate_id='GKT', context=run.spec.context, terminal_kind=TERMINAL_KIND,
        status='SELECTED_ONLY_COMPLETE', weights_phase='selected_fit80', prediction_phase='raw_selection10',
        encoding_fit_scope='select_train80', selected_epoch=epoch, complete_fit_epochs=completed_epochs,
        terminal=artifact(terminal), checkpoint=artifact(reference['directory']/'state.pt'),
        raw_predictions=artifact(run.output/'selection/predictions.csv'), targets=artifact(run.output/'selection/targets.csv'),
        coverage=artifact(run.output/'selection/coverage.json'), stage_journal_sha256=hashlib.sha256((run.output/'events.jsonl').read_bytes()).hexdigest(),
        config_sha256=run.spec.identity, sources_sha256=json.loads(run.execution.identity_json)['sources_sha256'],
        runtime_sha256=run.execution.evidence.runtime.sha256, phase_sha256=selection.phase.identity,
        encoding_sha256=encoding.identity, vocabulary_sha256=identity_hash(encoding.exercise_encoding().vocabulary.values),
        initial_model_sha256=initial, initial_backbone_sha256=None, graph_condition_sha256=selection.graph.identity,
        graph_train_role_sha256=run.spec.context.train_role_sha256, estimator_graph='expert', epoch_objective_id=OBJECTIVE,
        full_targets=summary['full_targets'], supported_targets=summary['supported_targets'],
        unsupported_counts=tuple(sorted(summary['unsupported_counts'].items())), refit_started=False, calibration_used_for_selection=False)


def run_gkt_selected_fit(spec, evidence, *, authorization_file, expected_authorization_sha256):
    """Normal entry; Root review và owned process allocation là prerequisites."""
    need(type(spec) is GKTSelectedExecutionSpec and type(evidence) is GKTSelectedEvidence, 'typed GKT entry required')
    actual = require_gkt_selected_authorization(spec, evidence, authorization_file=authorization_file,
                                               expected_authorization_sha256=expected_authorization_sha256)
    corpus = read_public_research_corpus(spec.corpus_id, expected_corpus_sha256=spec.corpus_sha256,
        expected_done_sha256=spec.done_sha256, limits=CorpusReadLimits(**json.loads(spec.read_limits_json)))
    for role in ('train', 'selection', 'calibration'):
        data = corpus.role_data(role)
        need(len(data.trajectories) == getattr(spec.budget, role+'_learners')
             and data.audit['audit']['targets'] == getattr(spec.budget, role+'_targets'), 'actual role count/allocation mismatch')
    need(corpus.plan.protocol_sha256 == spec.context.protocol21_sha256
         and corpus.plan.identity == spec.context.split_sha256
         and identity_hash(corpus.bank.identity) == spec.context.domain_sha256
         and corpus.role_data('train').audit['audit']['shard_sha256'] == spec.context.train_role_sha256
         and corpus.role_data('selection').audit['audit']['shard_sha256'] == spec.context.selection_role_sha256,
         'actual public split/domain/role audit bindings')
    concepts = {item.concept_id for item in corpus.bank.items}
    need(len(corpus.bank.items) == 84 and len(concepts) == 28
         and all(tuple(sorted(item.difficulty for item in corpus.bank.items if item.concept_id == concept))
                 == (1050, 1200, 1350) for concept in concepts), 'public Grade10 registry84/28/three difficulties required')
    from knowledge_tracing.gkt import research_data as data
    topology_path=ROOT/spec.topology.path
    topology=json.loads(topology_path.read_bytes())
    need(hashlib.sha256(topology_path.read_bytes()).hexdigest()==spec.topology.sha256,'topology bytes before view')
    graph=data.GKTResearchGraphBinding(spec.context.domain_sha256,tuple(topology['nodes']),
        tuple(tuple(e) for e in topology['edges']),spec.topology.sha256,spec.context.train_role_sha256,'declared_static_expert')
    recipe=data.GKTResearchDataRecipe('concept','full_prefix','query_only','unsupported_history')
    train=data.prepare_gkt_research_view(corpus,scope='select_train80',recipe=recipe,graph_binding=graph)
    selection=data.prepare_gkt_research_view(corpus,scope='raw_selection10',recipe=recipe,graph_binding=graph,encoding=train.encoding)
    run = _Run(actual); run.boundary()
    need(spec.budget.max_optimizer_steps >= spec.recipe.max_epochs*((spec.budget.train_learners+3)//4)
         and spec.budget.max_optimized_targets >= spec.recipe.max_epochs*spec.budget.train_targets
         and spec.budget.max_prediction_targets >= (spec.recipe.max_epochs+1)*spec.budget.selection_targets,
         'reserve full declared selected workload before model')
    # Corpus chỉ nằm ở orchestrator; run/optimizer callbacks giữ metadata.
    spec.output.mkdir(exist_ok=False)
    tools = None; old_threads = old_dtype = None; original_error = None
    progress = evaluation_progress = final_progress = None
    try:
        run.write('invocation.json', dict(scope='gkt_main_selected_only_v1', candidate_id='GKT', spec=asdict(spec),
            authorization_sha256=actual.authorization_sha256, identity=json.loads(actual.identity_json)))
        tools = _lazy(); torch = tools.torch
        runtime = json.loads((ROOT/evidence.runtime.path).read_bytes())
        need(torch.__version__ == runtime['torch_version'] and tools.np.__version__ == runtime['numpy_version']
             and str(torch.__file__) == runtime['torch_origin'] and str(tools.np.__file__) == runtime['numpy_origin']
             and torch.cuda.is_available() is False and torch.cuda.is_initialized() is False,
             'actual CPU Torch version/origin before constructor')
        old_threads, old_dtype = torch.get_num_threads(), torch.get_default_dtype()
        need(old_dtype == torch.float32, 'ambient FP32 required'); torch.set_num_threads(spec.budget.cpu_threads)
        training_budget=_budget(run,tools,train,training=True)
        evaluation_budget=_budget(run,tools,selection,training=False)
        run.guard(); model, optimizer = _construct(run, tools, train)
        initial = tools.digest(model)
        profile = tools.cp.GKTCheckpointProfile(spec.context.protocol21_sha256,evidence.runtime.sha256,spec.identity,initial,spec.run_id)
        limits = tools.cp.GKTCheckpointLimits(spec.budget.max_checkpoint_bytes, spec.budget.max_metadata_bytes, spec.budget.max_tensor_bytes)
        progress=tools.training.GKTResearchProgress(model.model_binding_sha256,model.initial_dropout_rng_state)
        evaluation_progress=tools.training.GKTResearchProgress(model.model_binding_sha256,model.initial_dropout_rng_state)
        stopper = tools.stopper(spec.recipe.patience, spec.recipe.min_delta)
        history = []; best = None
        for epoch in range(1, spec.recipe.max_epochs+1):
            result=_train_epoch(run,tools,model,optimizer,train,epoch,spec.budget.train_targets,training_budget,progress)
            train_counters=dict(progress.counters);train_rng=progress.rng_state.clone()
            summary,rows,reasons=_predict(run,tools,model,selection,epoch,evaluation_budget,evaluation_progress)
            need(progress.counters==train_counters and tools.torch.equal(progress.rng_state,train_rng)
                 and result['model_state_after']==tools.digest(model),'eval cannot invalidate complete training checkpoint receipt')
            prior_best=stopper.best_epoch;stop=stopper.observe(epoch,summary['raw_response_log_loss'])
            reference = None
            if stopper.best_epoch != prior_best:
                run.guard()
                need(run.output_bytes+spec.budget.max_checkpoint_bytes+2*spec.budget.max_metadata_bytes
                     <= spec.budget.max_output_bytes-spec.budget.max_metadata_bytes, 'checkpoint/output reservation')
                identity=tools.cp.research_checkpoint_identity(model,train,_epoch_spec(tools,spec.recipe,epoch),optimizer,
                    budget=training_budget,profile=profile)
                reference=tools.cp.save_epoch_state(run.output/('epoch-'+str(epoch)),model,train,
                    _epoch_spec(tools,spec.recipe,epoch),optimizer,budget=training_budget,progress=progress,
                    epoch_result=result,profile=profile,expected_identity=identity,limits=limits)
                run.output_bytes += sum((reference['directory']/name).stat().st_size for name in ('state.pt','metadata.json','COMPLETE.json'))
                best = (reference, identity)
            history.append(dict(epoch=epoch,seed=42+epoch,progress=dict(progress.counters),selection=summary,
                checkpoint_sha256=None if reference is None else reference['checkpoint_sha256']))
            run.write('epoch-'+str(epoch)+'.json', history[-1]); run.boundary()
            if stop:
                break
        need(best is not None, 'no completed best epoch')
        del optimizer, model, result
        reference, identity = best; selected_epoch = stopper.best_epoch
        need(reference['directory'].is_relative_to(run.output), 'only current owned selected checkpoint')
        for name, pin, cap in (('COMPLETE.json', reference['complete_sha256'], spec.budget.max_metadata_bytes),
                               ('metadata.json', reference['metadata_sha256'], spec.budget.max_metadata_bytes),
                               ('state.pt', reference['checkpoint_sha256'], spec.budget.max_checkpoint_bytes)):
            need(_hash_file(reference['directory']/name, cap=cap)[0] == pin, 'best checkpoint size/SHA before fresh constructor')
        run.boundary(); fresh, fresh_optimizer = _construct(run, tools, train)
        need(tools.digest(fresh)==initial,'same fresh initial model/BN before restore')
        fresh_progress=tools.training.GKTResearchProgress(fresh.model_binding_sha256,fresh.initial_dropout_rng_state)
        restored=tools.cp.restore_epoch_state(reference['directory'],fresh,train,_epoch_spec(tools,spec.recipe,selected_epoch),
            fresh_optimizer,budget=training_budget,fresh_progress=fresh_progress,profile=profile,expected_identity=identity,
            expected_complete_sha256=reference['complete_sha256'],limits=limits)
        del fresh_optimizer, restored
        final_progress=tools.training.GKTResearchProgress(fresh.model_binding_sha256,fresh.initial_dropout_rng_state)
        summary,rows,reasons=_predict(run,tools,fresh,selection,selected_epoch,evaluation_budget,final_progress)
        need(summary['prediction_sha256'] == history[selected_epoch-1]['selection']['prediction_sha256'], 'best reload/full selection parity')
        del fresh
        _exports(run, rows, reasons); run.write('selection/coverage.json', summary)
        run.write('epochs.json', history); run.boundary()
        torch.set_num_threads(old_threads); old_threads = None
        need(torch.get_default_dtype() == old_dtype, 'caller dtype changed')
        run.event('selected_only_exports_complete', selected_epoch=selected_epoch)
        terminal = dict(kind=TERMINAL_KIND, status='SELECTED_ONLY_COMPLETE', candidate_id='GKT', selected_epoch=selected_epoch,
            complete_fit_epochs=len(history), counters=dict(reserved=run.reserved, returned=run.returned, completed=run.completed,
                reserved_targets=run.reserved_targets, returned_targets=run.returned_targets, completed_targets=run.completed_targets,
                model_constructors=run.constructors, adam_constructors=run.adam_constructors,
                prediction_passes=run.prediction_passes, prediction_full_targets=run.prediction_targets),
            physical_model_calls=run.model_calls,epoch_objective=OBJECTIVE,
            checkpoint_sha256=reference['checkpoint_sha256'], complete_sha256=reference['complete_sha256'],
            source_sha256=json.loads(actual.identity_json)['sources_sha256'], runtime_sha256=evidence.runtime.sha256,
            external_freeze_authority=False, refit_started=False, calibration_used_for_selection=False)
        run.write('selected-terminal.json', terminal)
        claim = _claim(run, summary, rows, reference, selected_epoch, len(history), initial, train.encoding, selection,
                       run.output/'selected-terminal.json')
        run.write('selected-claim.json', asdict(claim)); run.boundary()
        run.write('COMPLETE.json', dict(status='COMPLETE_GKT_MAIN_SELECTED_ONLY', terminal_sha256=hashlib.sha256(
            (run.output/'selected-terminal.json').read_bytes()).hexdigest(), claim_sha256=hashlib.sha256(
            (run.output/'selected-claim.json').read_bytes()).hexdigest(), system_freeze_performed=False))
        run.boundary()
        return claim
    except BaseException as error:
        original_error = error
        failure = dict(status='FAILED_GKT_SELECTED_ONLY_KEEP_ALL', error_type=type(error).__name__, error=str(error),
            reserved_steps=run.reserved, body_returned_steps=run.returned, complete_steps=run.completed,
            reserved_targets=run.reserved_targets, body_returned_targets=run.returned_targets, complete_targets=run.completed_targets,
            training_seconds=run.train_seconds(), rollback=False, public_resume_supported=False)
        primitive_result=getattr(error,'result',None)
        if type(primitive_result) is dict:
            failure['primitive_partial']={key:primitive_result.get(key) for key in ('status','stop_reason','counters',
                'counters_before','pending_batch_keys','unreturned_sequence_work','optimized_target_semantics')}
        failure['progress']={name:dict(counters=dict(value.counters),poisoned=value.poisoned)
            for name,value in (('train',progress),('eval',evaluation_progress),('fresh_best_eval',final_progress))
            if value is not None}
        try:
            with (run.output/'failure.json').open('x', encoding='utf-8') as stream:
                json.dump(failure, stream, sort_keys=True, allow_nan=False); stream.flush(); os.fsync(stream.fileno())
        except BaseException as secondary:
            error.add_note('Failure receipt publication: '+type(secondary).__name__)
        raise
    finally:
        if tools is not None and old_threads is not None:
            try:
                tools.torch.set_num_threads(old_threads)
            except BaseException as cleanup_error:
                if original_error is None:
                    raise
                original_error.add_note('Thread restoration failed: '+type(cleanup_error).__name__)
