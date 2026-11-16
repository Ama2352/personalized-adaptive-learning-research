"""Builder CPU cho export refit Junyi thật, tách probe khỏi calibration dữ liệu."""
from dataclasses import asdict,dataclass
import hashlib
import json
import math
from pathlib import Path
import sys
import time

from .config import PROJECT_ROOT,config_from_payload
from .encoding import encoding_from_payload
from .research_junyi_roles import JunyiResearchRoles
from .research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
from .research_junyi_calibration import read_refit_export_package,attach_refit_export,inference_source_identity
from .resources import memory_snapshot
from .types import KTEvent,LearnerEvents,WindowInputs
from .windows import iter_windows
from knowledge_tracing.response_calibration import PredictionBinding
from knowledge_tracing.shared_kt import PrerequisiteGraph


def _need(ok,message):
    if not ok:
        raise ValueError(message)


def _identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


@dataclass(frozen=True)
class JunyiCPUInferenceBudget:
    max_targets: int
    max_learner_events: int
    max_users: int
    max_seconds: float
    max_rss_bytes: int
    min_available_ram_bytes: int
    prediction_batch_size: int
    max_checkpoint_bytes: int=64*1024**2
    min_available_before_model_bytes: int=1024**3

    def __post_init__(self):
        for name,value in asdict(self).items():
            valid=(type(value) in (int,float) and math.isfinite(value) and value>0
                   if name=='max_seconds' else type(value) is int and value>0)
            _need(valid,'positive CPU inference budget required: '+name)
        _need(type(self.prediction_batch_size) is int and self.prediction_batch_size<=128,
              'explicit prediction batch1..128 required')

    def check(self,started):
        snapshot=memory_snapshot()
        _need(time.monotonic()-started<=self.max_seconds,'CPU inference wall-time cap exceeded')
        if (max(snapshot['process_rss_bytes'],snapshot['process_peak_rss_bytes'] or 0)>self.max_rss_bytes
                or snapshot['system_available_ram_bytes']<self.min_available_ram_bytes):
            raise MemoryError('CPU inference RAM budget exceeded')
        return snapshot


def inspect_cpu_refit_export(export, *, expected_index_sha256, output, run_id, budget):
    """Đọc metadata nhỏ, dựng lineage và config, chưa import Torch/nạp weights."""
    _need(type(budget) is JunyiCPUInferenceBudget,'typed CPU inference budget required')
    index,members=read_refit_export_package(export,expected_index_sha256=expected_index_sha256)
    values=dict(members['inputs/roles.json'])
    for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
        values[name]=tuple(values[name])
    roles=JunyiResearchRoles(**values)
    train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    refit=JunyiPhaseView(roles,'refit_union90',tuple(sorted((*roles.train_users,*roles.selection_users))),roles.identity)
    calibration=JunyiPhaseView(roles,'calibration_predict',roles.calibration_users,roles.identity)
    def encoding_for(scope,view):
        name='inputs/encoding'+scope+'.json'
        encoding=JunyiResearchEncoding(encoding_from_payload(members[name]),view)
        receipt=members['inputs/encoding'+scope+'_receipt.json']
        _need(receipt['status']=='JUNYI_TRAIN_ENCODING_FITTED'
              and receipt['fit_view_identity']==view.identity and receipt['phase_scope']==view.scope
              and receipt['encoding_identity']==encoding.identity
              and receipt['encoding_file_sha256']==members['INVENTORY.json'][name]['sha256'],
              'portable encoding lineage mismatch')
        return encoding
    encoding=encoding_for('90',refit)
    origin=encoding_for('80',train)
    plan=members['inputs/epoch_plan.json']
    _need(plan['roles_identity']==roles.identity and plan['identity']==index['identity']['plan_sha256']
          and encoding.identity==index['identity']['encoding'],
          'portable refit plan/role/encoding mismatch')
    config_data=dict(members['inputs/config.json'])
    config_data.update(project_root=str(PROJECT_ROOT),source_root=str(PROJECT_ROOT/'artifacts/akt/dependencies/upstream'),
        output_dir=str(Path(output)),run_id=run_id,phase='junyi-inference',device='cpu',
        max_train_users=1,max_val_users=budget.max_users,max_targets_per_side=budget.max_targets,
        max_total_targets=budget.max_targets,max_steps=max(1,(budget.max_targets+99)//100),
        max_seconds=budget.max_seconds,max_wall_seconds=budget.max_seconds,
        max_rss_bytes=budget.max_rss_bytes,min_available_ram_bytes=budget.min_available_ram_bytes,
        threads=1,execution_enabled=True)
    config=config_from_payload(config_data)
    variant=index['identity']['variant']
    _need(variant in ('A0','A1','A2','A3') and index['model']==variant+'_JUNYI_REFIT',
          'portable A0-A3 model identity required')
    condition=None
    if variant!='A0':
        from .research_junyi_graph import JunyiGraphCondition
        from .research_junyi_confidence_binding import binding_from_payload
        topology=members['inputs/graph.json']
        confidence=None if variant=='A1' else binding_from_payload(members['inputs/confidence.json'])
        condition=JunyiGraphCondition(encoding,
            PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges']),
            members['INVENTORY.json']['inputs/graph.json']['sha256'],variant=variant,
            confidence=confidence,train80_origin=origin)
        _need(condition.identity==index['identity']['condition'],'portable graph/confidence condition changed')
    else:
        _need(index['identity']['condition'] is None,'graph-free export has unexpected condition')
    return dict(export=Path(export),expected_index_sha256=expected_index_sha256,index=index,config=config,
                encoding=encoding,origin=origin,calibration=calibration,condition=condition,budget=budget)


def build_cpu_refit_predictor(assets, *, domain_sha256):
    """Dựng backbone chuẩn, nạp weights thật bằng attach API đã kiểm."""
    budget=assets['budget']
    started=time.monotonic()
    before=budget.check(started)
    if 'torch' not in sys.modules and before['system_available_ram_bytes']<budget.min_available_before_model_bytes:
        raise MemoryError('CPU model import headroom below declared startup budget')
    import torch
    torch.set_num_threads(assets['config'].threads)
    _need(torch.get_default_dtype()==torch.float32,'FP32 CPU inference required')
    if assets['condition'] is None:
        from .model import AKTAdapter
        adapter=AKTAdapter(assets['config'],assets['encoding'].native)
    else:
        from .research_junyi_graph import JunyiGraphPhaseSession
        from .research_junyi_graph_model import JunyiGraphAKTAdapter
        adapter=JunyiGraphAKTAdapter(config=assets['config'],encoding=assets['encoding'],
            condition=assets['condition'],phase=JunyiGraphPhaseSession(assets['condition'],assets['calibration']),
            compact_context=True)
    budget.check(started)
    index=assets['index']
    vocabulary=assets['encoding'].native.vocabulary.values
    binding=PredictionBinding(index['model'],index['checkpoint_sha256'],assets['encoding'].identity,
        assets['encoding'].fit_view.roles.identity,
        _identity(dict(domain='junyi_exercises',values=vocabulary)),
        _identity(dict(domain='junyi_logged_response',reference_bank='not_applicable')),
        inference_source_identity(),domain_sha256)
    result=attach_refit_export(adapter,assets['encoding'],assets['export'],
        expected_index_sha256=assets['expected_index_sha256'],binding=binding,
        max_checkpoint_bytes=budget.max_checkpoint_bytes)
    budget.check(started)
    return result


def probe_real_weights(assets, *, targets=110):
    """Weights thật + events tổng hợp; không đọc event Junyi hoặc fit temperature."""
    budget=assets['budget']
    _need(type(targets) is int and 1<=targets<=min(128,budget.max_targets,budget.max_learner_events)
          and budget.max_users==1,'technical probe limited to one synthetic learner and128 targets')
    started=time.monotonic()
    memory=[budget.check(started)]
    predictor=build_cpu_refit_predictor(assets,domain_sha256=_identity(dict(
        scope='synthetic_events_real_refit_weights',recipe='alternating_labels_known_items_v1')))
    memory.append(budget.check(started))
    user=assets['calibration'].users[0]
    values=assets['encoding'].native.vocabulary.values[:3]
    learner=LearnerEvents(user,0,tuple(KTEvent(user,values[i%len(values)],i+1,i+1,i%2,0,0)
        for i in range(targets)))
    windows=tuple(iter_windows(learner,assets['encoding'].native,context=100,target_block=100,training=False))
    _need(1<=len(windows)<=2 and all(type(row) is WindowInputs for row in windows),
          'technical probe must contain at most two known-item windows')
    probabilities=predictor.adapter.predict_windows(windows)
    import numpy as np
    _need(len(probabilities)==len(windows) and all(np.isfinite(row).all() and ((row>=0)&(row<=1)).all()
          for row in probabilities),'invalid real-checkpoint technical predictions')
    predictor.assert_boundary()
    memory.append(budget.check(started))
    return dict(status='REAL_REFIT_WEIGHTS_SYNTHETIC_CPU_PROBE_PASS',model=assets['index']['model'],
        checkpoint_sha256=predictor.binding.checkpoint_sha256,encoding_identity=assets['encoding'].identity,
        training_identity=assets['index']['identity'],inference_source_sha256=predictor.binding.model_source_sha256,
        domain='synthetic_events_only',synthetic_targets=targets,windows=len(windows),
        probabilities_sha256=_identity([row.tolist() for row in probabilities]),
        wall_seconds=time.monotonic()-started,memory_samples=memory,
        calibration_completed=False,real_junyi_events_read=False,full_junyi_benchmark=False)
