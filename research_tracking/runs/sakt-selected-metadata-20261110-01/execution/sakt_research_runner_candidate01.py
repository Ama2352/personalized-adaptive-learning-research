"""SAKT30 selected-only producer candidate, chưa apply hoặc execute.

Public entry tự kiểm actual SAKT authorization trước lazy Torch. Tái dùng epoch,
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
import time
from types import SimpleNamespace

from knowledge_tracing.sakt.research_execution import (
    AuthorizedSAKTSelectedExecution, SAKTSelectedExecutionSpec, SAKTSelectedEvidence,
    require_sakt_selected_authorization, need, canonical, OBJECTIVE, RECIPE_SHA256, ROOT,
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
    from knowledge_tracing.sakt import research_data as data, research_training as training
    from knowledge_tracing.sakt import research_checkpoint as cp
    from knowledge_tracing.sakt.config import SAKTConfig
    from knowledge_tracing.sakt.model import SAKTCore
    from knowledge_tracing.sakt.training import state_digest
    from knowledge_tracing.akt.training import EarlyStopping
    from knowledge_tracing.gam_kt.evaluation import _metrics
    return SimpleNamespace(torch=torch, np=np, pd=pd, data=data, training=training, cp=cp,
        config=SAKTConfig, model=SAKTCore, digest=state_digest, stopper=EarlyStopping, metrics=_metrics)


def selection_rows(result):
    """Loss/reporting join sau prediction; không tính hoặc đổi probability."""
    need(type(result) is dict and result['status'] == 'complete'
         and result['stop_reason'] == 'prediction_complete' and result['truth_sidecar_complete'] is True
         and result['role'] == 'research_computation_only_no_selected_fit_attestation'
         and result['resume_supported'] is False and result['fitted_research_model'] is False
         and result['binding']['phase_scope'] == 'raw_selection10'
         and result['ledger']['complete'] is True and result['ledger']['input_population_complete'] is True
         and result['model_state_before'] == result['model_state_after'], 'complete frozen selection prediction required')
    expected = {}
    for target in result['truth_sidecar']:
        key = (target.learner_id, target.query.source_row, target.global_rank)
        need(key not in expected, 'duplicate truth target')
        expected[key] = target
    need(len(expected) == result['ledger']['expected_targets'] == len(result['predictions']), 'full selection population required')
    rows, input_reasons, seen = [], {}, set()
    for prediction in result['predictions']:
        key = (prediction['learner_id'], prediction['source_row'], prediction['global_rank'])
        need(key in expected and key not in seen, 'prediction/truth key mismatch')
        seen.add(key); target = expected[key]
        need((prediction['item_id'], prediction['timestamp'], prediction['origin_role'],
              prediction['history_hash_scheme'], prediction['history_sha256'], prediction['phase_sha256'], prediction['encoding_sha256'])
             == (target.query.item_id, target.query.timestamp, target.origin_role,
                 target.history_hash_scheme, target.history_sha256, target.phase_sha256, target.encoding_sha256),
             'query/history/phase/encoding truth join mismatch')
        need(target.encoding_sha256 == result['binding']['encoding_sha256'], 'prediction binding encoding mismatch')
        probability = prediction['probability']
        need(prediction['prediction_status'] == ('unsupported' if probability is None else 'scored'),
             'unprocessed target cannot be exported as unsupported')
        neutral = ModelNeutralKey(target.learner_id, target.query.item_id, target.query.timestamp,
            target.query.source_row, target.global_rank, target.history_hash_scheme, target.history_sha256, target.origin_role)
        rows.append(RawSelectedRow('SAKT', neutral, target.correct, probability,
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
        need(type(execution) is AuthorizedSAKTSelectedExecution, 'actual SAKT execution token required')
        self.execution, self.spec = execution, execution.spec
        self.output, self.budget = self.spec.output, self.spec.budget
        self.reserved = self.returned = self.completed = 0
        self.reserved_targets = self.returned_targets = self.completed_targets = 0
        self.training_spent = 0.; self.training_started = None
        self.prediction_passes = self.prediction_targets = self.constructors = self.adam_constructors = 0
        self.output_bytes = 0

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


def _construct(run, tools, num_items):
    run.boundary()
    need(run.constructors < 2 and run.adam_constructors < 2, 'one fit model and one fresh best reload only')
    r, torch = run.spec.recipe, tools.torch
    with torch.random.fork_rng(devices=[]), torch.device('cpu'):
        torch.random.default_generator.manual_seed(r.seed)
        run.constructors += 1
        model = tools.model(tools.config(num_items, r.max_length, r.d_model, r.num_heads, r.head_dim, r.dropout, r.layer_norm_eps))
        run.adam_constructors += 1
        optimizer = torch.optim.Adam(model.parameters(), lr=r.lr, betas=r.betas, eps=r.eps, weight_decay=r.weight_decay,
            amsgrad=False, foreach=False, fused=False, maximize=False, capturable=False, differentiable=False)
    need(all(p.device.type == 'cpu' and p.dtype == torch.float32 and p.requires_grad for p in model.parameters()), 'CPU FP32 owned model')
    run.guard()
    return model, optimizer


def _epoch_spec(tools, recipe, epoch):
    return tools.training.SAKTResearchSpec(recipe.batch_size, recipe.max_grad_norm,
        recipe.seed+epoch-1, 'seeded_permutation', 'cpu', 'float32', 'mean_bce_on_eligible_targets')


def _train_epoch(run, tools, model, optimizer, view, epoch, targets):
    r, b = run.spec.recipe, run.budget
    run.boundary(); before_steps, before_targets = run.returned, run.returned_targets
    local = [0, None]
    def reserve(owned, args, kwargs):
        need(owned is optimizer and local[1] is None, 'one pending owned Adam body')
        count = min(r.batch_size, targets-local[0]*r.batch_size)
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
            spec=_epoch_spec(tools, r, epoch), budget=tools.training.SAKTResearchBudget(
                b.max_training_seconds-run.training_spent, targets, targets, b.max_optimizer_steps-run.completed))
    finally:
        run.training_spent = run.train_seconds(); run.training_started = None
        for handle in handles:
            handle.remove()
    ledger = result['ledger']
    need(result['status'] == 'complete' and result['stop_reason'] == 'epoch_complete' and ledger['complete'] is True
         and ledger['input_population_complete'] is True and ledger['expected_targets'] == ledger['seen_targets'] == targets
         and ledger['optimized_targets'] == targets and ledger['possibly_updated_source_rows'] == []
         and ledger['optimizer_steps_started'] == ledger['optimizer_steps_body_returned'] == local[0]
         and run.returned-before_steps == local[0] and run.returned_targets-before_targets == targets
         and local[1] is None and run.reserved == run.returned, 'complete epoch/global durable accounting required')
    run.completed = run.returned; run.completed_targets = run.returned_targets
    run.boundary()
    return result


def _predict(run, tools, model, view, epoch):
    need(view.phase.scope == 'raw_selection10', 'selected producer predicts only selection10')
    run.boundary(); count = run.budget.selection_targets
    need(run.prediction_passes < run.spec.recipe.max_epochs+1
         and run.prediction_targets+count <= run.budget.max_prediction_targets, 'selection pass/full-row quota')
    result = tools.training.predict_research_sakt(model, view,
        spec=_epoch_spec(tools, run.spec.recipe, epoch),
        budget=tools.training.SAKTResearchBudget(run.budget.max_wall_seconds-max(
            time.perf_counter()-run.execution.started[0], time.time()-run.execution.started[1]), count, count, 0))
    rows, reasons = selection_rows(result)
    need(len(rows) == count, 'declared full selection count')
    need(all(row.phase_sha256 == view.phase.identity and row.encoding_sha256 == view.encoding.identity for row in rows),
         'actual selected phase/encoding mismatch')
    run.prediction_passes += 1; run.prediction_targets += count
    supported = [row for row in rows if row.probability is not None]
    need(bool(supported), 'no supported selection population')
    torch = tools.torch
    with torch.device('cpu'):
        p = torch.tensor([row.probability for row in supported], dtype=torch.float32, device='cpu')
        y = torch.tensor([row.correct for row in supported], dtype=torch.float32, device='cpu')
        objective = float(torch.nn.functional.binary_cross_entropy(p, y, reduction='mean'))
    need(math.isfinite(objective) and objective >= 0, 'finite raw native BCE criterion')
    metrics = tools.metrics(tools.pd.DataFrame(dict(correct=[row.correct for row in supported],
        prediction=[row.probability for row in supported])))
    summary = dict(full_targets=len(rows), supported_targets=len(supported), unsupported_targets=len(rows)-len(supported),
        unsupported_counts=dict(Counter(row.support_reason for row in rows if row.probability is None)),
        native_bce_mean=objective, objective=OBJECTIVE, population=population(rows), supported_metrics=metrics,
        full_metrics=metrics if len(supported) == len(rows) else None,
        reporting='knowledge_tracing.gam_kt.evaluation._metrics', prediction_sha256=identity_hash([asdict(row) for row in rows]))
    run.boundary()
    return summary, rows, reasons


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
    return SelectedCandidateClaim(candidate_id='SAKT', context=run.spec.context, terminal_kind=TERMINAL_KIND,
        status='SELECTED_ONLY_COMPLETE', weights_phase='selected_fit80', prediction_phase='raw_selection10',
        encoding_fit_scope='select_train80', selected_epoch=epoch, complete_fit_epochs=completed_epochs,
        terminal=artifact(terminal), checkpoint=artifact(reference['directory']/'state.pt'),
        raw_predictions=artifact(run.output/'selection/predictions.csv'), targets=artifact(run.output/'selection/targets.csv'),
        coverage=artifact(run.output/'selection/coverage.json'), stage_journal_sha256=hashlib.sha256((run.output/'events.jsonl').read_bytes()).hexdigest(),
        config_sha256=run.spec.identity, sources_sha256=json.loads(run.execution.identity_json)['sources_sha256'],
        runtime_sha256=run.execution.evidence.runtime.sha256, phase_sha256=selection.phase.identity,
        encoding_sha256=encoding.identity, vocabulary_sha256=identity_hash(encoding.exercise_encoding().vocabulary.values),
        initial_model_sha256=initial, initial_backbone_sha256=None, graph_condition_sha256=None,
        graph_train_role_sha256=None, estimator_graph='disabled', epoch_objective_id=OBJECTIVE,
        full_targets=summary['full_targets'], supported_targets=summary['supported_targets'],
        unsupported_counts=tuple(sorted(summary['unsupported_counts'].items())), refit_started=False, calibration_used_for_selection=False)


def run_sakt_selected_fit(spec, evidence, *, authorization_file, expected_authorization_sha256):
    """Normal entry; Root review và owned process allocation là prerequisites."""
    need(type(spec) is SAKTSelectedExecutionSpec and type(evidence) is SAKTSelectedEvidence, 'typed SAKT entry required')
    actual = require_sakt_selected_authorization(spec, evidence, authorization_file=authorization_file,
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
    from knowledge_tracing.sakt import research_data as data
    recipe = data.SAKTDataRecipe(100, 'left', 'query_only', 'sliding_last_context', 'window_relative_interaction_rank')
    train = data.prepare_sakt_research_view(corpus, scope='select_train80', recipe=recipe)
    selection = data.prepare_sakt_research_view(corpus, scope='raw_selection10', recipe=recipe, encoding=train.encoding)
    run = _Run(actual); run.boundary()
    need(spec.budget.max_optimizer_steps >= spec.recipe.max_epochs*((spec.budget.train_targets+127)//128)
         and spec.budget.max_optimized_targets >= spec.recipe.max_epochs*spec.budget.train_targets
         and spec.budget.max_prediction_targets >= (spec.recipe.max_epochs+1)*spec.budget.selection_targets,
         'reserve full declared selected workload before model')
    # Corpus chỉ nằm ở orchestrator; run/optimizer callbacks giữ metadata.
    spec.output.mkdir(exist_ok=False)
    tools = None; old_threads = old_dtype = None; original_error = None
    try:
        run.write('invocation.json', dict(scope='sakt_main_selected_only_v1', candidate_id='SAKT', spec=asdict(spec),
            authorization_sha256=actual.authorization_sha256, identity=json.loads(actual.identity_json)))
        tools = _lazy(); torch = tools.torch
        runtime = json.loads((ROOT/evidence.runtime.path).read_bytes())
        need(torch.__version__ == runtime['torch_version'] and tools.np.__version__ == runtime['numpy_version']
             and str(torch.__file__) == runtime['torch_origin'] and str(tools.np.__file__) == runtime['numpy_origin']
             and torch.cuda.is_available() is False and torch.cuda.is_initialized() is False,
             'actual CPU Torch version/origin before constructor')
        old_threads, old_dtype = torch.get_num_threads(), torch.get_default_dtype()
        need(old_dtype == torch.float32, 'ambient FP32 required'); torch.set_num_threads(spec.budget.cpu_threads)
        run.guard(); model, optimizer = _construct(run, tools, len(train.vocabulary.values))
        initial = tools.digest(model)
        profile = tools.cp.SAKTCheckpointProfile(spec.context.protocol21_sha256, evidence.runtime.sha256, spec.identity, spec.run_id)
        limits = tools.cp.SAKTCheckpointLimits(spec.budget.max_checkpoint_bytes, spec.budget.max_metadata_bytes, spec.budget.max_tensor_bytes)
        progress = tools.cp.SAKTEpochProgress(0, 0, 0)
        stopper = tools.stopper(spec.recipe.patience, spec.recipe.min_delta)
        history = []; best = None
        for epoch in range(1, spec.recipe.max_epochs+1):
            result = _train_epoch(run, tools, model, optimizer, train, epoch, spec.budget.train_targets)
            summary, rows, reasons = _predict(run, tools, model, selection, epoch)
            previous, progress = progress, tools.cp._epoch_progress(model, train, _epoch_spec(tools, spec.recipe, epoch), optimizer, result, progress)
            prior_best = stopper.best_epoch; stop = stopper.observe(epoch, summary['native_bce_mean'])
            reference = None
            if stopper.best_epoch != prior_best:
                run.guard()
                need(run.output_bytes+spec.budget.max_checkpoint_bytes+2*spec.budget.max_metadata_bytes
                     <= spec.budget.max_output_bytes-spec.budget.max_metadata_bytes, 'checkpoint/output reservation')
                identity = tools.cp.research_checkpoint_identity(model, train, _epoch_spec(tools, spec.recipe, epoch), optimizer, profile=profile)
                reference = tools.cp.save_research_training_state(run.output/('epoch-'+str(epoch)), model, train,
                    _epoch_spec(tools, spec.recipe, epoch), optimizer, profile=profile, epoch_result=result,
                    previous_progress=previous, expected_identity=identity, limits=limits)
                run.output_bytes += sum((reference['directory']/name).stat().st_size for name in ('state.pt','metadata.json','COMPLETE.json'))
                best = (reference, identity)
            history.append(dict(epoch=epoch, seed=spec.recipe.seed+epoch-1, progress=asdict(progress), selection=summary,
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
        run.boundary(); fresh, fresh_optimizer = _construct(run, tools, len(train.vocabulary.values))
        need(tools.digest(fresh) == initial, 'independent same initialization before reload')
        restored = tools.cp.restore_research_training_state(reference['directory'], fresh, train,
            _epoch_spec(tools, spec.recipe, selected_epoch), fresh_optimizer, profile=profile, expected_identity=identity,
            expected_complete_sha256=reference['complete_sha256'], limits=limits)
        del fresh_optimizer, restored
        summary, rows, reasons = _predict(run, tools, fresh, selection, selected_epoch)
        need(summary['prediction_sha256'] == history[selected_epoch-1]['selection']['prediction_sha256'], 'best reload/full selection parity')
        del fresh
        _exports(run, rows, reasons); run.write('selection/coverage.json', summary)
        run.write('epochs.json', history); run.boundary()
        torch.set_num_threads(old_threads); old_threads = None
        need(torch.get_default_dtype() == old_dtype, 'caller dtype changed')
        run.event('selected_only_exports_complete', selected_epoch=selected_epoch)
        terminal = dict(kind=TERMINAL_KIND, status='SELECTED_ONLY_COMPLETE', candidate_id='SAKT', selected_epoch=selected_epoch,
            complete_fit_epochs=len(history), counters=dict(reserved=run.reserved, returned=run.returned, completed=run.completed,
                reserved_targets=run.reserved_targets, returned_targets=run.returned_targets, completed_targets=run.completed_targets,
                model_constructors=run.constructors, adam_constructors=run.adam_constructors,
                prediction_passes=run.prediction_passes, prediction_full_targets=run.prediction_targets),
            checkpoint_sha256=reference['checkpoint_sha256'], complete_sha256=reference['complete_sha256'],
            source_sha256=json.loads(actual.identity_json)['sources_sha256'], runtime_sha256=evidence.runtime.sha256,
            external_freeze_authority=False, refit_started=False, calibration_used_for_selection=False)
        run.write('selected-terminal.json', terminal)
        claim = _claim(run, summary, rows, reference, selected_epoch, len(history), initial, train.encoding, selection,
                       run.output/'selected-terminal.json')
        run.write('selected-claim.json', asdict(claim)); run.boundary()
        run.write('COMPLETE.json', dict(status='COMPLETE_SAKT_MAIN_SELECTED_ONLY', terminal_sha256=hashlib.sha256(
            (run.output/'selected-terminal.json').read_bytes()).hexdigest(), claim_sha256=hashlib.sha256(
            (run.output/'selected-claim.json').read_bytes()).hexdigest(), system_freeze_performed=False))
        run.boundary()
        return claim
    except BaseException as error:
        original_error = error
        failure = dict(status='FAILED_SAKT_SELECTED_ONLY_KEEP_ALL', error_type=type(error).__name__, error=str(error),
            reserved_steps=run.reserved, body_returned_steps=run.returned, complete_steps=run.completed,
            reserved_targets=run.reserved_targets, body_returned_targets=run.returned_targets, complete_targets=run.completed_targets,
            training_seconds=run.train_seconds(), rollback=False, public_resume_supported=False)
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
