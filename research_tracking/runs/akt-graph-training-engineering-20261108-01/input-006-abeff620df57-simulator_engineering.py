"""Một epoch toy observable CPU, không là protocol hoặc fitted research artifact.

Không CLI/Junyi fold, collector, calibration/final/refit hay OnlineSession.
Approval/origin là khai báo của caller, không chứng thực nguồn dữ liệu độc lập.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import csv
from functools import wraps
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import re
import time
import traceback

import numpy as np
import torch

from knowledge_tracing.simulator_bridge import identity_hash
from .checkpoint import restore_checkpoint, save_checkpoint
from .config import AKTConfig, PROJECT_ROOT, SOURCE_COMMIT, validate_config
from .model import AKTAdapter
from .online import inference_recipe
from .provenance import verify_upstream
from .resources import memory_snapshot
from .simulator_data import (
    SimulatorEncoding, SimulatorShard, SimulatorUnseenQuery,
    fit_simulator_encoding, iter_simulator_windows, scoring_targets,
)
from .training import train_epoch

PURPOSE = "simulator_engineering_only_v1"
POLICY = "handcrafted-observable-fixture-v1"
GRAPH_PURPOSE = "simulator_graph_engineering_only_v1"
GRAPH_POLICY = "handmade-graph-engineering-only"
_GIB = 1024**3


def _cpu_only(function):
    @wraps(function)
    def guarded(*args, **kwargs):
        # Check before constructors, deserialization or Adam's lazy state allocation.
        if torch.cuda.is_available() or torch.cuda.is_initialized():
            raise RuntimeError("CPU engineering requires CUDA hidden/unavailable and uninitialized")
        with torch.device("cpu"):
            return function(*args, **kwargs)
    return guarded


@dataclass(frozen=True)
class SyntheticEngineeringBudget:
    approval_reference: str
    expected_train_sha256: str
    expected_selection_sha256: str
    approved: bool
    max_train_learners: int = 2
    max_selection_learners: int = 1
    max_events_per_learner: int = 12
    max_optimizer_steps: int = 4
    max_seconds: float = 60.0
    max_rss_bytes: int = 2 * _GIB
    min_available_ram_bytes: int = _GIB

    def __post_init__(self):
        if self.approved is not True or not isinstance(self.approval_reference, str) or not self.approval_reference.strip():
            raise PermissionError("explicit synthetic engineering approval required")
        if len(self.approval_reference) > 1000:
            raise ValueError("approval reference too long")
        for value in (self.expected_train_sha256, self.expected_selection_sha256):
            if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
                raise ValueError("explicit input SHA-256 required")
        for name, ceiling in (("max_train_learners", 2), ("max_selection_learners", 1),
                              ("max_events_per_learner", 12), ("max_optimizer_steps", 4),
                              ("max_rss_bytes", 2 * _GIB)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise ValueError("synthetic hard cap: " + name)
        if (type(self.max_seconds) not in (int, float) or not math.isfinite(self.max_seconds)
                or not 0 < self.max_seconds <= 60):
            raise ValueError("synthetic hard cap: max_seconds")
        if type(self.min_available_ram_bytes) is not int or self.min_available_ram_bytes < _GIB:
            raise ValueError("available RAM floor is at least 1 GiB")


@dataclass(frozen=True)
class EngineeringEpochResult:
    output_dir: Path
    checkpoint_sha256: str
    optimizer_steps: int
    train_targets: int
    selection_coverage: dict
    reload_max_abs_delta: float
    weight_role: str = "engineering_only"


class IncompleteEngineeringEpoch(RuntimeError):
    """Budget interrupted training: retain diagnostics, never publish checkpoint."""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_inventory():
    native = sorted(Path(__file__).parent.glob("*.py"))
    shared = [Path(__file__).parent.parent / name for name in
              ("simulator_data.py", "simulator_bridge.py", "shared_kt.py", "graph_context.py", "graph_augmentation.py")]
    return {p.relative_to(PROJECT_ROOT).as_posix(): _sha(p) for p in native + shared}


def _write(path, value):
    with Path(path).open("x", encoding="utf8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False, default=str)
        stream.write("\n")


def _guard(budget, deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("synthetic engineering wall budget exhausted")
    sample = memory_snapshot()
    if max(sample["process_rss_bytes"], sample["process_peak_rss_bytes"] or 0) > budget.max_rss_bytes:
        raise MemoryError("synthetic engineering RSS cap")
    if sample["system_available_ram_bytes"] < budget.min_available_ram_bytes:
        raise MemoryError("synthetic engineering available RAM floor")
    return sample


def _validate_scope(config, train, selection, budget, *, graph_setup=None):
    if graph_setup is not None:
        from .graph_training import GraphEngineeringSetup
        if type(graph_setup) is not GraphEngineeringSetup:
            raise ValueError("exact graph engineering setup required")
    if type(config) is not AKTConfig or type(budget) is not SyntheticEngineeringBudget:
        raise ValueError("exact config/budget types required")
    validate_config(config)
    if (config.execution_enabled is not True or config.phase != "smoke" or config.device != "cpu"
            or config.max_epochs != 1 or config.recovery is not None):
        raise PermissionError("enabled CPU smoke one-epoch engineering only; no recovery/refit")
    if type(config.threads) is not int or not 1 <= config.threads <= 2 or type(config.seed) is not int or not 0 <= config.seed < 2**32:
        raise ValueError("bounded CPU threads and NumPy-compatible explicit seed required")
    if config.source_root.resolve() != (PROJECT_ROOT / "artifacts/akt/dependencies/upstream").resolve():
        raise ValueError("only trusted pinned upstream path")
    for name, ceiling in (("max_train_users", budget.max_train_learners),
                          ("max_val_users", budget.max_selection_learners),
                          ("max_targets_per_side", budget.max_train_learners * budget.max_events_per_learner),
                          ("max_steps", budget.max_optimizer_steps), ("max_seconds", budget.max_seconds),
                          ("max_wall_seconds", budget.max_seconds), ("max_rss_bytes", budget.max_rss_bytes)):
        value = getattr(config, name)
        if value is None or value > ceiling:
            raise ValueError("config exceeds explicit engineering budget: " + name)
    if config.min_available_ram_bytes < budget.min_available_ram_bytes:
        raise ValueError("config RAM floor below engineering budget")
    if config.max_total_targets is None or config.max_total_targets > 3 * budget.max_events_per_learner:
        raise ValueError("explicit tiny total-target cap required")
    if type(train) is not SimulatorShard or type(selection) is not SimulatorShard:
        raise ValueError("exact observable shards required; oracle forbidden")
    if train.role != "train" or selection.role != "selection":
        raise ValueError("only train/selection roles; no calibration/final/refit")
    if train.plan != selection.plan or train.bank != selection.bank:
        raise ValueError("plan/domain mismatch")
    prefix = "synthetic-akt-engineering-" if graph_setup is None else "synthetic-akt-graph-engineering-"
    if not train.bank.environment_id.startswith(prefix):
        raise ValueError("explicit synthetic engineering domain required")
    if len(train.bank.items) > (36 if graph_setup is None else 8):
        raise ValueError("tiny handcrafted item bank cap exceeded")
    if graph_setup is not None:
        from .graph_prototype import _scope
        _scope(config, train, fit_simulator_encoding(train), graph_setup.graph)
    for shard, ceiling in ((train, budget.max_train_learners), (selection, budget.max_selection_learners)):
        shard.audit
        if len(shard.trajectories) > ceiling or shard.max_events_per_learner > budget.max_events_per_learner:
            raise ValueError("tiny learner/event cap exceeded")
        if any(t.collection_policy_id != (POLICY if graph_setup is None else GRAPH_POLICY) for t in shard.trajectories):
            raise ValueError("handcrafted observable fixture declaration required")
    if train.identity != budget.expected_train_sha256 or selection.identity != budget.expected_selection_sha256:
        raise ValueError("input SHA mismatch")
    train_count = sum(len(t.observations) for t in train.trajectories)
    selection_count = sum(len(t.observations) for t in selection.trajectories)
    if (len(train.trajectories) > config.max_train_users or len(selection.trajectories) > config.max_val_users
            or max(train_count, selection_count) > config.max_targets_per_side
            or train_count + selection_count > config.max_total_targets):
        raise ValueError("actual inputs exceed config caps")
    output = config.output_dir.absolute()
    roots = (PROJECT_ROOT / "artifacts/akt/synthetic", PROJECT_ROOT / "experiments/akt/results")
    if output.parent not in roots or output.name != config.run_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,47}", config.run_id):
        raise ValueError("fresh direct synthetic/results run directory required")
    if config.run_id.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1,10)), *(f"LPT{i}" for i in range(1,10))}:
        raise ValueError("Windows device run ID forbidden")
    for part in (output, *output.parents):
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise ValueError("symlink/junction output forbidden")
        if part == PROJECT_ROOT:
            break
    if output.exists():
        raise FileExistsError(output)
    return output


def _weights(adapter):
    return identity_hash({name: hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
                          for name, value in adapter.native.state_dict().items()})


def _evaluate(adapter, selection, encoding, budget, deadline):
    before, source_before = _weights(adapter), selection.identity
    expected = scoring_targets(selection, encoding)
    targets = {(t.learner_id, t.query.source_row, t.global_rank): t for t in expected}
    predictions = {}
    pending = []
    def flush():
        if not pending:
            return
        _guard(budget, deadline)
        values = adapter.predict_windows(pending)
        _guard(budget, deadline)
        for window, scores in zip(pending, values, strict=True):
            for local in np.flatnonzero(window.target_mask):
                key = (window.inputs.user_ids[local], int(window.inputs.source_rows[local]), int(window.global_ranks[local]))
                if key in predictions or key not in targets:
                    raise ValueError("duplicate/foreign selection target")
                predictions[key] = float(scores[local])
        pending.clear()
    for entry in iter_simulator_windows(selection, encoding, context=adapter.config.context,
                                        target_block=adapter.config.target_block, training=False):
        _guard(budget, deadline)
        if isinstance(entry, SimulatorUnseenQuery):
            key = (entry.learner_id, entry.query.source_row, entry.global_rank)
            if key in predictions or key not in targets:
                raise ValueError("duplicate/foreign unseen target")
            predictions[key] = None
        else:
            pending.append(entry)
            if len(pending) >= adapter.config.batch_size:
                flush()
    flush()
    if predictions.keys() != targets.keys():
        raise ValueError("selection target ledger mismatch")
    rows, loss_sum, known = [], 0.0, 0
    for key, target in targets.items():
        probability = predictions[key]
        if (probability is not None) != target.trained_item:
            raise ValueError("OOV support mismatch")
        if probability is not None:
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("invalid engineering prediction")
            p = min(1 - 1e-12, max(1e-12, probability))
            loss_sum -= target.correct * math.log(p) + (1-target.correct) * math.log1p(-p)
            known += 1
        rows.append({"learner_id": key[0], "source_row": key[1], "global_rank": key[2],
                     "item_id": target.query.item_id, "probability": probability,
                     "support_reason": "engineering_known_item" if probability is not None else "oov_item",
                     "weight_role": "engineering_only"})
        metadata = getattr(adapter, "prediction_metadata", None)
        if metadata is not None:
            fields = ("base_probability", "graph_applied", "gate_value", "confidence_mass", "normalizer",
                      "graph_residual", "window_id", "effective_start")
            if probability is None:
                rows[-1].update({f: None for f in fields})
            else:
                detail = metadata.get(key)
                if not isinstance(detail, dict) or set(detail) != set(fields):
                    raise ValueError("missing or unexpected graph selection metadata")
                base=detail["base_probability"];gate=detail["gate_value"];mass=detail["confidence_mass"]
                if (type(detail["graph_applied"]) is not bool
                        or type(base) not in (int,float) or not math.isfinite(base) or not 0<=base<=1
                        or type(mass) not in (int,float) or not math.isfinite(mass) or mass<0
                        or detail["normalizer"]!=max(1.,mass)
                        or type(detail["graph_residual"]) not in (int,float) or not math.isfinite(detail["graph_residual"])
                        or (gate is not None and (type(gate) not in (int,float) or not math.isfinite(gate) or not 0<=gate<=1))
                        or not isinstance(detail["window_id"],str) or not detail["window_id"]
                        or type(detail["effective_start"]) is not int or not 0<=detail["effective_start"]<=key[2]):
                    raise ValueError("invalid graph selection metadata values")
                if not detail["graph_applied"] and (probability!=base or detail["graph_residual"]!=0):
                    raise ValueError("inactive graph prediction must keep same-forward base probability")
                rows[-1].update(detail)
    if not known:
        raise ValueError("selection has no supported toy targets")
    if _weights(adapter) != before or selection.identity != source_before:
        raise ValueError("selection mutated weights or observable inputs")
    return {"expected_rows": len(rows), "known_rows": known, "unseen_rows": len(rows)-known,
            "engineering_mean_log_loss": loss_sum/known}, rows


def _graph_selection_exports(output, rows, selection, encoding):
    """Truth xuất riêng SAU prediction; không truyền labels CSV vào adapter."""
    targets=scoring_targets(selection,encoding)
    keys=lambda row:(row["learner_id"],row["source_row"],row["global_rank"])
    labels=[dict(learner_id=t.learner_id,source_row=t.query.source_row,global_rank=t.global_rank,
        item_id=t.query.item_id,timestamp=t.query.timestamp,correct=t.correct,role=selection.role,
        plan_sha256=selection.plan.identity,bank_sha256=identity_hash(selection.bank.identity)) for t in targets]
    if [keys(row) for row in rows]!=[keys(row) for row in labels]:
        raise ValueError("graph prediction/ground-truth export target keys or ordering mismatch")
    for name,data in (("selection.csv",rows),("selection_targets.csv",labels)):
        with (output/name).open("x",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(data[0]))
            writer.writeheader();writer.writerows(data);stream.flush();os.fsync(stream.fileno())


@_cpu_only
def load_engineering_checkpoint(path: Path, config: AKTConfig, encoding: SimulatorEncoding, *,
                                expected_sha256: str, expected_identity: dict):
    """Hash bounded actual deserialization bytes; never create a fitted backend."""
    if (expected_identity.get("purpose") != PURPOSE or expected_identity.get("weight_role") != "engineering_only"
            or "training_domain" in expected_identity or config.device != "cpu"
            or expected_identity.get("encoding_sha256") != encoding.identity
            or expected_identity.get("sources_sha256") != _source_inventory()
            or expected_identity.get("inference_recipe") != inference_recipe(config)):
        raise ValueError("engineering checkpoint scope/encoding/recipe mismatch")
    with Path(path).open("rb") as stream:
        payload_bytes = stream.read(8*1024**2 + 1)
    if len(payload_bytes) > 8*1024**2 or hashlib.sha256(payload_bytes).hexdigest() != expected_sha256:
        raise ValueError("engineering checkpoint payload SHA/size mismatch")
    payload = torch.load(io.BytesIO(payload_bytes), weights_only=True, map_location="cpu")
    if (payload.get("identity") != expected_identity or payload.get("progress", {}).get("complete") is not True
            or payload["progress"].get("role") != PURPOSE or payload["progress"].get("epoch") != 1):
        raise ValueError("not a complete engineering epoch checkpoint")
    adapter = AKTAdapter(config, encoding.exercise_encoding())
    optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
                                 eps=config.eps, weight_decay=config.weight_decay)
    restore_checkpoint(adapter, optimizer, payload)
    return adapter


@_cpu_only
def load_graph_engineering_checkpoint(path: Path, config: AKTConfig, encoding: SimulatorEncoding, *,
                                      train: SimulatorShard, selection: SimulatorShard, setup,
                                      expected_sha256: str, expected_identity: dict):
    """Chỉ restore toy graph recipe đã bind, không fitted backend hoặc resume."""
    from .graph_training import GraphEngineeringSetup, GraphTrainingAdapter, graph_checkpoint_identity
    if (type(setup) is not GraphEngineeringSetup or expected_identity.get("purpose") != GRAPH_PURPOSE
            or expected_identity.get("weight_role") != "engineering_only" or "training_domain" in expected_identity
            or config.device != "cpu" or expected_identity.get("encoding_sha256") != encoding.identity
            or expected_identity.get("train_sha256") != train.identity
            or expected_identity.get("selection_sha256") != selection.identity
            or expected_identity.get("sources_sha256") != _source_inventory()
            or expected_identity.get("config") != json.loads(json.dumps(asdict(config),default=str))
            or expected_identity.get("inference_recipe") != inference_recipe(config)):
        raise ValueError("graph engineering checkpoint scope/source/input/recipe mismatch")
    if graph_checkpoint_identity(config,train,selection,encoding,setup)!=expected_identity.get("graph_model"):
        raise ValueError("graph/confidence/module constructor recipe drift before deserialization")
    with Path(path).open("rb") as stream:
        raw=stream.read(8*1024**2+1)
    if len(raw)>8*1024**2 or hashlib.sha256(raw).hexdigest()!=expected_sha256:
        raise ValueError("graph engineering checkpoint payload SHA/size mismatch")
    payload=torch.load(io.BytesIO(raw),weights_only=True,map_location="cpu")
    if (payload.get("identity")!=expected_identity or payload.get("progress",{}).get("complete") is not True
            or payload["progress"].get("role")!=GRAPH_PURPOSE or payload["progress"].get("epoch")!=1):
        raise ValueError("not a complete graph engineering epoch checkpoint")
    adapter=GraphTrainingAdapter(config=config,train=train,selection=selection,encoding=encoding,setup=setup)
    if adapter.graph_checkpoint_identity()!=expected_identity.get("graph_model"):
        raise ValueError("graph/confidence/module constructor recipe drift")
    actual=payload.get("model_state_dict")
    expected=adapter.native.state_dict()
    if (not isinstance(actual,dict) or actual.keys()!=expected.keys()
            or any(not isinstance(actual[k],torch.Tensor) or actual[k].device.type!="cpu"
                   or actual[k].dtype!=v.dtype or actual[k].shape!=v.shape or not torch.isfinite(actual[k]).all()
                   for k,v in expected.items())):
        raise ValueError("graph checkpoint full module keys/shape/dtype/finiteness mismatch")
    optimizer=torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
                               eps=config.eps,weight_decay=config.weight_decay)
    restore_checkpoint(adapter,optimizer,payload)
    return adapter


@_cpu_only
def run_engineering_epoch(config: AKTConfig, *, train: SimulatorShard, selection: SimulatorShard,
                          budget: SyntheticEngineeringBudget) -> EngineeringEpochResult:
    return _run_engineering_epoch(config,train=train,selection=selection,budget=budget)


@_cpu_only
def run_graph_engineering_epoch(config: AKTConfig, *, train: SimulatorShard, selection: SimulatorShard,
                                budget: SyntheticEngineeringBudget, setup) -> EngineeringEpochResult:
    from .graph_training import GraphEngineeringSetup
    if type(setup) is not GraphEngineeringSetup:
        raise ValueError("exact graph engineering setup required")
    return _run_engineering_epoch(config,train=train,selection=selection,budget=budget,graph_setup=setup)


def _run_engineering_epoch(config, *, train, selection, budget, graph_setup=None):
    output = _validate_scope(config, train, selection, budget, graph_setup=graph_setup)
    purpose = PURPOSE if graph_setup is None else GRAPH_PURPOSE
    budget = replace(budget, max_rss_bytes=min(budget.max_rss_bytes, config.max_rss_bytes),
                     min_available_ram_bytes=max(budget.min_available_ram_bytes, config.min_available_ram_bytes))
    deadline = time.monotonic() + min(budget.max_seconds, config.max_wall_seconds)
    _guard(budget, deadline)
    output.mkdir(parents=True, exist_ok=False)
    source_before = {}; adapter = None
    previous_threads = torch.get_num_threads()
    try:
        source_before = _source_inventory()
        torch.set_num_threads(config.threads)
        upstream = verify_upstream(config.source_root, SOURCE_COMMIT)
        encoding = fit_simulator_encoding(train)
        identity = {"purpose": purpose, "weight_role": "engineering_only", "engineering_bank_identity": train.bank.identity,
                    "plan_sha256": train.plan.identity, "train_sha256": train.identity,
                    "selection_sha256": selection.identity, "encoding_sha256": encoding.identity,
                    "inference_recipe": inference_recipe(config), "config": json.loads(json.dumps(asdict(config), default=str)),
                    "budget": asdict(budget), "sources_sha256": source_before, "upstream": upstream,
                    "unused_legacy_fields": ["outer_fold", "inner_val_fraction", "patience", "min_delta"]}
        random.seed(config.seed)
        np.random.seed(config.seed)
        torch.manual_seed(config.seed)
        if graph_setup is None:
            adapter = AKTAdapter(config, encoding.exercise_encoding())
        else:
            from .graph_training import GraphTrainingAdapter
            def event_sink(event):
                with (output/"optimizer_events.jsonl").open("a",encoding="utf-8") as stream:
                    stream.write(json.dumps(event,allow_nan=False,sort_keys=True)+"\n")
                    stream.flush();os.fsync(stream.fileno())
            adapter=GraphTrainingAdapter(config=config,train=train,selection=selection,encoding=encoding,
                                         setup=graph_setup,event_sink=event_sink)
            identity["graph_model"]=adapter.graph_checkpoint_identity()
            identity["selection_policy"]="only_complete_epoch"
            identity["resume_supported"]=False
        _write(output/"invocation.json", identity)
        optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
                                     eps=config.eps, weight_decay=config.weight_decay)
        windows = tuple(iter_simulator_windows(train, encoding, context=config.context,
                                               target_block=config.target_block, training=True))
        ledger = [(w.window.inputs.user_ids[i], int(w.window.inputs.source_rows[i]), int(w.window.global_ranks[i]))
                  for w in windows for i in np.flatnonzero(w.window.target_mask)]
        if len(ledger) != len(set(ledger)) or len(ledger) != sum(len(t.observations) for t in train.trajectories):
            raise ValueError("train target ledger mismatch")
        before = _weights(adapter)
        extra = {} if graph_setup is None else {"batch_factory": adapter.collate}
        stats = train_epoch(adapter, lambda: iter(windows), optimizer=optimizer, epoch=1,
            budget={"max_steps": config.max_steps, "max_targets": config.max_targets_per_side,
                    "max_seconds": min(config.max_seconds, max(0.0, deadline-time.monotonic())),
                    "max_rss_bytes": config.max_rss_bytes, "min_available_ram_bytes": config.min_available_ram_bytes},**extra)
        _write(output/"training.json", {**asdict(stats), "target_ledger": ledger})
        if not stats.complete or stats.valid_targets != len(ledger):
            raise IncompleteEngineeringEpoch("no complete checkpoint for a partial engineering epoch")
        if before == _weights(adapter) or not stats.parameter_update_steps:
            raise ValueError("toy training did not update parameters")
        _guard(budget, deadline)
        coverage, rows = _evaluate(adapter, selection, encoding, budget, deadline)
        if train.identity != budget.expected_train_sha256 or _source_inventory() != source_before:
            raise ValueError("source/train input drift")
        checkpoint = output/"epoch1.pt"
        save_checkpoint(checkpoint, adapter, optimizer, identity=identity,
                        progress={"complete": True, "epoch": 1, "role": purpose})
        digest = _sha(checkpoint)
        _guard(budget, deadline)
        if graph_setup is None:
            reloaded = load_engineering_checkpoint(checkpoint, config, encoding,
                                                   expected_sha256=digest, expected_identity=identity)
        else:
            reloaded = load_graph_engineering_checkpoint(checkpoint, config, encoding,train=train,
                selection=selection,setup=graph_setup,expected_sha256=digest,expected_identity=identity)
        reload_coverage, reload_rows = _evaluate(reloaded, selection, encoding, budget, deadline)
        delta = max(abs(a["probability"]-b["probability"]) for a,b in zip(rows,reload_rows,strict=True)
                    if a["probability"] is not None)
        if coverage != reload_coverage or delta > 1e-7 or _weights(reloaded) != _weights(adapter):
            raise ValueError("engineering checkpoint reload parity failed")
        if graph_setup is not None and rows != reload_rows:
            raise ValueError("graph checkpoint telemetry/target ledger reload parity failed")
        if _source_inventory() != source_before or train.identity != budget.expected_train_sha256 or selection.identity != budget.expected_selection_sha256:
            raise ValueError("source/input drift before completion")
        _write(output/"selection.json", {"weight_role": "engineering_only", "coverage": coverage,
                                         "predictions": rows, "reload_max_abs_delta": delta})
        if graph_setup is not None:
            _graph_selection_exports(output,rows,selection,encoding)
            _guard(budget,deadline)
        _write(output/"result.json", {"status": "complete_engineering_only", "checkpoint_sha256": digest,
            "optimizer_steps": stats.optimizer_steps, "train_targets": stats.valid_targets,
            "selection_coverage": coverage, "reload_max_abs_delta": delta, "sources_post_sha256": _source_inventory(),
            "runtime": {"torch": torch.__version__, "device": "cpu", "memory": _guard(budget, deadline)},
            "not_adopted": ["research allocation", "mastery/calibration", "controller", "refit/final", "fitted OnlineSession"]})
        if graph_setup is not None:
            _guard(budget,deadline)
            with (output/"COMPLETE").open("x",encoding="ascii") as stream:
                stream.write("complete_graph_engineering_only\n");stream.flush();os.fsync(stream.fileno())
            # Marker alone is insufficient: a late publication failure retains failure.json.
            _guard(budget,deadline)
        return EngineeringEpochResult(output, digest, stats.optimizer_steps, stats.valid_targets, coverage, delta)
    except Exception as error:
        try:
            source_after = _source_inventory()
        except Exception as inventory_error:
            source_after = {"inventory_error": type(inventory_error).__name__}
        graph_failure = {} if graph_setup is None or adapter is None else {
            "graph_local_step_events": list(adapter.step_events),
            "graph_optimizer_start_reservations": adapter._started,
            "graph_optimizer_body_returns": adapter._body_returns,
            "optimizer_rollback_performed": False}
        _write(output/"failure.json", {"status": "failed_engineering_only", "error_type": type(error).__name__,
                                      "error": str(error), "sources_before_sha256": source_before,
                                      "sources_after_sha256": source_after,
                                      "complete_result_published": (output/"result.json").exists(),
                                      "complete_marker_published": (output/"COMPLETE").exists(),
                                      "run_accepted": False, **graph_failure})
        with (output/"failure.log").open("x",encoding="utf8") as stream:
            stream.write(traceback.format_exc())
        raise
    finally:
        torch.set_num_threads(previous_threads)
