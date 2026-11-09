"""Actual conditional selected-only A0-A3 producer; no CLI or automatic execution.

Entry constructs the real disk guard itself. Metadata stages never authorize fit.
Old A0 lifecycle remains unchanged. No refit, system winner, calibration or resume.
"""
from dataclasses import asdict
from collections import Counter
import json
from pathlib import Path
import random
import time

from .research_main_execution import (MainSelectedExecutionSpec,require_main_selected_authorization,
                                     canonical,need)
from .research_main_stage import prepare_main_selected_stage
from . import research_runner as primitive
from ..research_admission import SelectedCandidateClaim,ArtifactClaim,TERMINAL_KIND
from ..simulator_bridge import identity_hash


def _tools():
    tools=primitive._lazy()
    from .research_graph_model import ResearchGraphAKTAdapter
    from . import research_graph_checkpoint as cp
    from .research_graph_context import ResearchGraphContextLimits,prepare_research_graph_context
    tools.graph_adapter=ResearchGraphAKTAdapter;tools.cp=cp
    tools.context_limits_type=ResearchGraphContextLimits;tools.context_index=prepare_research_graph_context
    return tools


class _Run:
    def __init__(self,execution):
        self.execution=execution;self.spec=execution.spec
        self.config=self.spec.research.native_config;self.budget=self.spec.research.budget
        self.output=self.config.output_dir;self.bank=execution._corpus.bank;self.plan=execution._corpus.plan
        self.stage=prepare_main_selected_stage(self.spec.stage)
        self.training_spent=0.;self.training_started=None
        self.reserved_steps=self.returned_steps=self.completed_steps=0
        self.reserved_targets=self.returned_targets=self.completed_targets=0
        self.batch_targets=None;self.constructors=0;self.optimizer_constructors=0
        self.output_bytes=0;self.events=[]

    def clocks(self):
        training=self.training_spent
        if self.training_started is not None:
            training+=max(time.perf_counter()-self.training_started[0],time.time()-self.training_started[1])
        return dict(wall_seconds=max(time.perf_counter()-self.execution.started[0],time.time()-self.execution.started[1]),
                    training_seconds=training)

    def guard(self):
        from .research_main_execution import _resource
        _resource(self.spec,self.execution.started,self.clocks()['training_seconds'])
        need(self.output_bytes<=self.spec.max_output_bytes,'cumulative selected output bytes cap')

    def boundary(self):
        self.guard();self.execution.revalidate(self.clocks()['training_seconds']);self.guard()

    def json(self,name,value):
        self.guard();path=self.output/name
        need(path.parent.is_dir() and not path.exists(),'exclusive owned JSON output')
        raw=(json.dumps(canonical(value),ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
        need(len(raw)<=self.budget.max_prediction_bytes and self.output_bytes+len(raw)<=self.spec.max_output_bytes,'metadata/output quota before write')
        pin=primitive._write_json(path,value,self.budget.max_prediction_bytes);self.output_bytes+=len(raw);self.guard()
        return pin

    def event(self,kind,**fields):
        import os
        self.guard()
        value=dict(kind=kind,**self.clocks(),reserved_steps=self.reserved_steps,body_returned_steps=self.returned_steps,
                   completed_steps=self.completed_steps,reserved_targets=self.reserved_targets,body_returned_targets=self.returned_targets,
                   completed_targets=self.completed_targets,**fields)
        raw=(json.dumps(canonical(value),ensure_ascii=False,sort_keys=True)+'\n').encode()
        need(self.output_bytes+len(raw)<=self.spec.max_output_bytes,'event/output quota before durable append')
        with (self.output/'events.jsonl').open('ab') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        self.output_bytes+=len(raw);self.events.append(kind)

    def optimizer_event(self,event):
        kind=event['kind']
        if kind=='optimizer_started':
            need(type(self.batch_targets) is int and self.batch_targets>0,'tracked batch before Adam reservation')
            need(self.reserved_steps+1<=self.budget.max_optimizer_steps
                 and self.reserved_targets+self.batch_targets<=self.budget.max_optimized_targets,'cumulative selected optimizer/target cap')
            self.reserved_steps+=1;self.reserved_targets+=self.batch_targets
        elif kind=='optimizer_body_returned':
            need(self.returned_steps+1==self.reserved_steps,'one durable reservation per actual Adam body')
            self.returned_steps+=1;self.returned_targets+=self.batch_targets
        need(type(event['started']) is type(event['body_returned']) is int
             and event['started']==self.reserved_steps and event['body_returned']==self.returned_steps,
             'actual tracker/global Adam body accounting mismatch')
        self.event('tracker_'+kind,tracker=event)


def _construct(run,tools,encoding,index,condition):
    run.boundary();need(run.constructors<2 and run.optimizer_constructors<2,'one fresh fit plus one fresh best reload only')
    random.seed(run.config.seed);tools.np.random.seed(run.config.seed)
    tools.torch.random.default_generator.manual_seed(run.config.seed)
    with tools.torch.device('cpu'):
        adapter=tools.graph_adapter(config=run.config,encoding=encoding,index=index,condition=condition)
        run.constructors+=1
        optimizer=tools.torch.optim.Adam(adapter.native.parameters(),lr=run.config.lr,betas=run.config.betas,
            eps=run.config.eps,weight_decay=run.config.weight_decay)
        run.optimizer_constructors+=1
    run.boundary()
    return adapter,optimizer


def _predict(run,tools,data,adapter,phase,encoding,index):
    entitlement=run.stage.epoch_validation_inputs() if run.stage.phase=='selected_fit80' else run.stage.phase_inputs()
    need(entitlement[0]==phase.scope=='raw_selection10','selected producer predicts only raw selection10')
    run.boundary();adapter.set_context_index(index);adapter.audit_context_boundary()
    result=primitive._predict(run,tools,data,adapter,phase,encoding)
    adapter.audit_context_boundary();run.boundary()
    return result


def _epoch(run,tools,data,adapter,optimizer,tracker,phase,encoding,index,epoch):
    need(run.stage.phase_inputs()[0]=='select_train80' and phase.scope=='select_train80','optimization train80 only')
    adapter.set_context_index(index);adapter.audit_context_boundary();run.boundary();tracker.begin_epoch(epoch)
    def collate(entries):
        need(run.batch_targets is None,'one pending optimizer batch')
        batch=tracker.collate(entries)
        run.batch_targets=sum(1 for contexts in tracker.adapter._ticket.context for value in contexts if value is not None)
        return batch
    def progress(event):
        tracker.progress(event)
        if tracker.pending is None and run.batch_targets is not None:
            need(run.returned_steps==run.reserved_steps,'progress before all Adam body returns')
            run.completed_steps=run.returned_steps;run.completed_targets=run.returned_targets
            run.batch_targets=None;run.event('step_committed')
        run.guard()
    run.training_started=(time.perf_counter(),time.time())
    try:
        clock=run.clocks()
        budget=dict(max_steps=run.budget.max_optimizer_steps-run.reserved_steps,
            max_targets=run.budget.max_optimized_targets-run.reserved_targets,
            max_seconds=min(run.budget.max_training_seconds-clock['training_seconds'],run.budget.max_wall_seconds-clock['wall_seconds']),
            max_rss_bytes=run.budget.max_rss_bytes,min_available_ram_bytes=run.budget.min_available_ram_bytes)
        need(all(budget[n]>0 for n in ('max_steps','max_targets','max_seconds')),'no remaining selected optimization budget')
        # Adam lazy scalar state must also allocate on CPU, even if a caller's
        # ambient default device differs; numerical/model config is unchanged.
        with tools.torch.device('cpu'):
            stats=tools.train_epoch(adapter,lambda:data.iter_research_windows(phase,encoding,context=run.config.context,
                target_block=run.config.target_block,training=True),optimizer=optimizer,epoch=epoch,budget=budget,
                batch_factory=collate,progress_callback=progress,resource_callback=lambda _:run.guard(),recovery=None)
        receipt=tracker.finish_epoch(stats)
        need(stats.complete and stats.valid_targets==run.budget.train_targets and run.batch_targets is None,'actual complete full train80 epoch required')
    finally:
        run.training_spent=run.clocks()['training_seconds'];run.training_started=None
    run.guard()
    return stats,receipt


def _profile(run,tools,initial_backbone):
    return tools.cp.GraphCheckpointProfile(run.spec.stage.context.protocol21_sha256,run.spec.stage.context.recipe26_sha256,
        run.execution.evidence.runtime_report_sha256,identity_hash(dict(lock=run.execution.evidence.lock_sha256,cpu_threads=run.spec.cpu_threads)),
        initial_backbone,run.spec.stage.context.allocation_sha256,'selected_fit_candidate',None)


def _save(run,tools,adapter,optimizer,tracker,receipt,profile,identity,epoch,limits):
    run.boundary()
    # Reserve an upper bound before serializing/writing, not after quota exhaustion.
    need(run.output_bytes+limits.max_checkpoint_bytes+2*limits.max_metadata_bytes<=run.spec.max_output_bytes,'checkpoint publication quota')
    directory=run.output/'checkpoints'/f'epoch-{epoch}'
    reference=tools.cp.save_graph_epoch_state(directory,adapter=adapter,optimizer=optimizer,participation=tracker,
        epoch_receipt=receipt,expected_identity=identity,profile=profile,limits=limits)
    run.output_bytes+=sum(p.stat().st_size for p in directory.iterdir() if p.is_file())
    run.boundary();return reference


def _claim(run,summary,rows,reference,best_epoch,completed_epochs,initial_model,initial_backbone,encoding,selection,terminal_file):
    def artifact(path):return ArtifactClaim(primitive._sha(path),path.stat().st_size)
    counts=Counter(row['support_reason'] for row in rows if row['probability'] is None)
    need(sum(counts.values())==summary['unsupported_targets'],'actual raw unsupported-reason coverage')
    return SelectedCandidateClaim(candidate_id=run.spec.stage.candidate_id,context=run.spec.stage.context,
        terminal_kind=TERMINAL_KIND,status='SELECTED_ONLY_COMPLETE',weights_phase='selected_fit80',prediction_phase='raw_selection10',
        encoding_fit_scope=encoding.optimization_scope,selected_epoch=best_epoch,complete_fit_epochs=completed_epochs,
        terminal=artifact(terminal_file),checkpoint=artifact(reference.directory/'state.pt'),raw_predictions=artifact(run.output/'selection/predictions.csv'),
        targets=artifact(run.output/'selection/targets.csv'),coverage=artifact(run.output/'selection/coverage.json'),
        stage_journal_sha256=primitive._sha(run.output/'events.jsonl'),config_sha256=run.spec.stage.config_sha256,
        sources_sha256=run.spec.stage.sources_sha256,runtime_sha256=run.spec.stage.runtime_sha256,phase_sha256=selection.identity,
        encoding_sha256=encoding.identity,vocabulary_sha256=identity_hash(encoding.exercise_encoding().vocabulary.values),
        initial_model_sha256=initial_model,initial_backbone_sha256=initial_backbone,
        graph_condition_sha256=run.spec.stage.graph_condition_sha256,graph_train_role_sha256=run.spec.stage.graph_train_role_sha256,
        estimator_graph=run.spec.stage.estimator_graph,epoch_objective_id=primitive.OBJECTIVE,full_targets=summary['full_targets'],
        supported_targets=summary['supported_targets'],unsupported_counts=tuple(sorted(counts.items())),
        refit_started=False,calibration_used_for_selection=False)


def run_main_selected_candidate(spec,evidence,*,authorization_file,expected_authorization_sha256):
    """Spec is an input, never permission; actual factory runs ONCE inside entry.

    No caller-provided guard/callback/corpus/model factory or arbitrary token.
    Final guard/writes are charged to the same start, including fresh best reload.
    """
    need(type(spec) is MainSelectedExecutionSpec,'main metadata/callable/NOAUTH stage cannot execute')
    # The factory rejects wrong environment/family before source/data/model work.
    actual=require_main_selected_authorization(spec,evidence,authorization_file=authorization_file,
        expected_authorization_sha256=expected_authorization_sha256)
    run=_Run(actual);run.boundary();run.output.mkdir()
    for name in ('fit80','selection','checkpoints'):(run.output/name).mkdir()
    tools=torch=None;old_dtype=old_threads=None;tracker=restored=None;threads_restored=False
    try:
        run.json('invocation.json',dict(scope='MAIN_SELECTED_ONLY_NO_REFIT',spec=asdict(spec),identity=json.loads(actual.identity_json),
            authorization_sha256=actual.authorization_sha256,required_matrix_candidates=9,
            cpu_threads=spec.cpu_threads,initialization_seed=run.config.seed,resume_supported=False))
        data=primitive._data();corpus=actual._corpus
        train=primitive._phase(data,corpus,'select_train80');selection=primitive._phase(data,corpus,'raw_selection10')
        encoding=data.fit_research_encoding(train);run.guard()
        tools=_tools();run.guard();torch=tools.torch
        old_dtype,old_threads=torch.get_default_dtype(),torch.get_num_threads()
        need(old_dtype==torch.float32,'runtime must start FP32');torch.set_num_threads(spec.cpu_threads)
        from .research_main_execution import decode
        context_limits=tools.context_limits_type(**decode(spec.context_limits_json))
        checkpoint_limits=tools.cp.GraphCheckpointLimits(**decode(spec.checkpoint_limits_json))
        need(context_limits.max_seconds<=run.budget.max_wall_seconds and checkpoint_limits.max_checkpoint_bytes<=run.budget.max_checkpoint_bytes,
             'subcomponent caps exceed authorization')
        condition=actual._condition
        train_index=tools.context_index(train,encoding,condition,limits=context_limits,fit80_encoding_sha256=encoding.identity,
            context=run.config.context,target_block=run.config.target_block)
        run.guard()
        selection_index=tools.context_index(selection,encoding,condition,limits=context_limits,fit80_encoding_sha256=encoding.identity,
            context=run.config.context,target_block=run.config.target_block)
        run.boundary()
        run.stage=run.stage.begin_selected_fit();run.event('selected_fit_started')
        adapter,optimizer=_construct(run,tools,encoding,train_index,condition)
        initial_backbone=tools.cp._state_sha(adapter.native.backbone.state_dict());initial_model=tools.cp._state_sha(adapter.native.state_dict())
        tracker=tools.cp.GraphAdamParticipation(adapter,optimizer,event_sink=run.optimizer_event)
        profile=_profile(run,tools,initial_backbone)
        identity=tools.cp.graph_checkpoint_identity(config=run.config,encoding=encoding,condition=condition,index=train_index,profile=profile)
        stopper=tools.EarlyStopping(run.config.patience,run.config.min_delta);history=[];best=None
        run.json('fit80/encoding.json',asdict(encoding))
        for epoch in range(1,run.config.max_epochs+1):
            run.boundary();stats,receipt=_epoch(run,tools,data,adapter,optimizer,tracker,train,encoding,train_index,epoch)
            need(run.stage.epoch_validation_inputs()[0]=='raw_selection10','per-epoch raw validation while fit state')
            summary,rows,truth=_predict(run,tools,data,adapter,selection,encoding,selection_index)
            old_best=stopper.best_epoch;stop=stopper.observe(epoch,summary['native_bce_mean'])
            # Receipt is a TRAIN index boundary even though selection just ran.
            adapter.set_context_index(train_index);adapter.audit_context_boundary()
            reference=None
            if stopper.best_epoch!=old_best:
                reference=best=_save(run,tools,adapter,optimizer,tracker,receipt,profile,identity,epoch,checkpoint_limits)
            record=dict(epoch=epoch,training=asdict(stats),receipt=asdict(receipt),raw_selection=summary,
                raw_prediction_semantic_sha256=identity_hash(rows),checkpoint=None if reference is None else asdict(reference),
                selected_epoch=stopper.best_epoch,epoch_objective=primitive.OBJECTIVE)
            history.append(record);run.json(f'fit80/epoch-{epoch}.json',record)
            if stop:break
        need(best is not None and stopper.best_epoch is not None,'no complete selected checkpoint')
        run.json('fit80/epochs.json',history);tracker.close();tracker=None
        # Fresh containers for verified best reload, never a continuation/refit.
        fresh,fresh_optimizer=_construct(run,tools,encoding,train_index,condition)
        need(tools.cp._state_sha(fresh.native.backbone.state_dict())==initial_backbone,'independent same initial backbone')
        inspected=tools.cp.inspect_graph_epoch_state(best.directory,expected_identity=identity,expected_complete_sha256=best.complete_sha256,limits=checkpoint_limits)
        restored=tools.cp.restore_graph_epoch_state(inspected,fresh_adapter=fresh,fresh_owned_optimizer=fresh_optimizer,
            expected_identity=identity,profile=profile,limits=checkpoint_limits,event_sink=lambda event:run.event('best_reload',checkpoint_event=event))
        restored.close();restored=None;run.boundary()
        run.stage=run.stage.begin_raw_best_selection()
        summary,rows,truth=_predict(run,tools,data,fresh,selection,encoding,selection_index)
        chosen=history[stopper.best_epoch-1]
        need(identity_hash(rows)==chosen['raw_prediction_semantic_sha256'],'best checkpoint/full raw prediction parity')
        need(summary['full_targets']==run.budget.selection_targets and run.reserved_steps==run.returned_steps==run.completed_steps
             and run.reserved_targets==run.returned_targets==run.completed_targets,'full selection and cumulative optimizer accounting')
        need(run.output_bytes+3*run.budget.max_prediction_bytes<=spec.max_output_bytes,'selection export quota')
        primitive._exports(run,'selection',summary,rows,truth)
        # _exports charges coverage.json via run.json; account the two CSVs here.
        run.output_bytes+=sum((run.output/'selection'/n).stat().st_size for n in ('predictions.csv','targets.csv'));run.boundary()
        # Cleanup occurs before terminal publication; cleanup failure cannot leave
        # an apparently accepted COMPLETE without a failure override.
        torch.set_num_threads(old_threads);need(torch.get_default_dtype()==old_dtype,'caller dtype changed unexpectedly')
        threads_restored=True;run.boundary()
        run.event('raw_best_exports_complete',selected_epoch=stopper.best_epoch,completed_fit_epochs=len(history))
        evidence_record=dict(schema_version=1,kind=TERMINAL_KIND,status='SELECTED_ONLY_COMPLETE',candidate_id=spec.stage.candidate_id,
            authorization_sha256=actual.authorization_sha256,stage_spec_sha256=spec.stage.identity,weights_phase='selected_fit80',
            prediction_phase='raw_selection10',selected_epoch=stopper.best_epoch,complete_fit_epochs=len(history),
            internal_condition_sha256=condition.identity,external_graph_condition_sha256=spec.stage.graph_condition_sha256,
            checkpoint=asdict(best),complete_epoch_receipts=[row['receipt'] for row in history],
            full_selection=summary,raw_prediction_sha256=primitive._sha(run.output/'selection/predictions.csv'),
            target_sha256=primitive._sha(run.output/'selection/targets.csv'),journal_sha256=primitive._sha(run.output/'events.jsonl'),
            counters=dict(reserved=run.reserved_steps,body_returned=run.returned_steps,complete=run.completed_steps,
                reserved_targets=run.reserved_targets,body_returned_targets=run.returned_targets,complete_targets=run.completed_targets,
                model_constructors=run.constructors,adam_constructors=run.optimizer_constructors),
            fresh_best_reload=True,system_selection_performed=False,external_freeze_authority=False,refit_started=False,calibration_used_for_selection=False)
        run.json('selected-terminal.json',evidence_record)
        claim=_claim(run,summary,rows,best,stopper.best_epoch,len(history),initial_model,initial_backbone,encoding,selection,run.output/'selected-terminal.json')
        run.stage=run.stage.finish_selected(claim);run.json('selected-claim.json',asdict(claim))
        run.json('stage-completion.json',dict(status=run.stage.status,stage_sha256=run.stage.identity,phase=run.stage.phase,
            spec_sha256=spec.stage.identity,external_freeze_authority=False))
        run.boundary()
        outputs={p.relative_to(run.output).as_posix():primitive._sha(p) for p in run.output.rglob('*') if p.is_file()}
        run.json('COMPLETE.json',dict(status='COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE',terminal_sha256=primitive._sha(run.output/'selected-terminal.json'),
            claim_sha256=primitive._sha(run.output/'selected-claim.json'),stage_sha256=run.stage.identity,outputs_sha256=outputs,
            main_matrix_complete=False,system_winner=None,refit_calibration_performed=False))
        run.boundary();return claim
    except BaseException as error:
        if run.output.exists():
            # Failure survives even when normal deadline/output writer would refuse.
            failure=dict(status='FAILED_NO_ACCEPTED_MAIN_SELECTED_TERMINAL',error_type=type(error).__name__,error=str(error),
                phase=run.stage.phase,counters=dict(reserved=run.reserved_steps,body_returned=run.returned_steps,complete=run.completed_steps),
                clocks=run.clocks(),rollback=False,automatic_retry=False)
            try:primitive._write_json(run.output/'failure.json',failure,run.budget.max_prediction_bytes)
            except BaseException as secondary:error.add_note('failure receipt unavailable:'+type(secondary).__name__)
        raise
    finally:
        if tracker is not None:tracker.close()
        if restored is not None:restored.close()
        if torch is not None and old_threads is not None and not threads_restored:
            try:torch.set_num_threads(old_threads)
            except BaseException as cleanup_error:
                import sys
                active=sys.exception()
                if active is not None:active.add_note('thread cleanup failure:'+str(cleanup_error))
                raise
