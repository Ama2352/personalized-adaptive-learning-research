"""Đánh giá CSV selected-only SAKT/GKT trên target population đã ghim.

Tái dùng parser, khóa và metrics hiện hành. Kết quả chỉ nghiệm thu cached rows,
không thay admission đủ chín candidate hoặc xác nhận weights/causality của model.
"""
from collections import Counter, defaultdict
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
import hashlib

from .research_admission import _canonical, POPULATION_SCHEME
from .research_population import SelectionPopulation
from .research_selected_rows import decode_selected_claim, normalize_selected_row
from .research_selection_io import BoundedArtifactReader, need
from .simulator_research_data import ResearchSplitPlan


def _timeline(keys):
    grouped = defaultdict(list)
    for key in keys:
        grouped[key.learner_id].append(key)
    for learner, values in grouped.items():
        ordered = sorted(values, key=lambda key: key.global_rank)
        need([key.global_rank for key in ordered] == list(range(len(ordered))),
             'Full contiguous learner target ranks required')
        chronology = [(key.timestamp, key.source_row) for key in ordered]
        need(all(left < right for left, right in zip(chronology, chronology[1:]))
             and len({key.source_row for key in ordered}) == len(ordered),
             'Target chronology/source-row identity mismatch')
    return {learner: len(values) for learner, values in grouped.items()}


def evaluate_cached_selected_baseline(root, *, claim_ref, predictions_ref, targets_ref,
        coverage_ref, population, plan, io_limits):
    """Public CPU entry, đọc exact refs và trả metric/coverage JSON nhỏ."""
    need(type(population) is SelectionPopulation and type(plan) is ResearchSplitPlan,
         'Independent audited selection population and split plan required')
    expected = population.expectation
    expected.context.validate()
    need(expected.context.environment_id == 'grade10_simulator'
         and expected.context.split_sha256 == plan.identity,
         'Frozen Grade10 plan required; Junyi baseline domain not qualified')
    assignments = plan.split_plan.assignments()
    selected = {entry.learner_id for entry in assignments if entry.role == 'selection'}
    excluded = {entry.learner_id for entry in assignments if entry.role != 'selection'}
    learner_counts = dict(population.learner_target_counts)
    need(len(learner_counts) == len(population.learner_target_counts)
         and set(learner_counts) == selected and not selected & excluded
         and population.role_shard_sha256 == expected.context.selection_role_sha256,
         'Learner-disjoint selection population/role binding mismatch')
    with BoundedArtifactReader(root, io_limits) as reader:
        claim = decode_selected_claim(reader.read_json(claim_ref))
        need(claim.candidate_id in ('SAKT', 'GKT') and claim.context == expected.context,
             'Matched SAKT/GKT selected-only candidate required')
        for ref, artifact in ((predictions_ref, claim.raw_predictions),
                              (targets_ref, claim.targets), (coverage_ref, claim.coverage)):
            need((ref.sha256, ref.size_bytes) == (artifact.sha256, artifact.size_bytes),
                 'CSV/coverage file pin differs from selected claim')
        coverage = reader.read_json(coverage_ref)
        predictions = reader.index_csv(predictions_ref, candidate_id=claim.candidate_id, kind='predictions')
        targets = reader.index_csv(targets_ref, candidate_id=claim.candidate_id, kind='targets')
        need(predictions.keys == targets.keys and len(targets.keys) == expected.full_targets == claim.full_targets,
             'Exact full prediction/target key population required')
        need(_timeline(targets.keys) == learner_counts, 'Selection learner target counts mismatch')
        keys_hash, labels_hash = hashlib.sha256(), hashlib.sha256()
        unsupported, input_support = Counter(), Counter()
        scored_labels, probabilities = [], []
        full_classes = [0, 0]
        rows_digest = hashlib.sha256()
        # Giữ hai handles qua vòng join, tránh mở lại CSV theo từng target.
        with predictions.open_rows() as prediction_rows, targets.open_rows() as target_rows:
            for key in targets.keys:
                raw_prediction = prediction_rows.row(key)
                row = normalize_selected_row(raw_prediction, target_rows.row(key), claim)
                keys_hash.update(_canonical(row.key.values()))
                labels_hash.update(_canonical((row.key.values(), row.correct)))
                rows_digest.update(_canonical(asdict(row)))
                full_classes[row.correct] += 1
                input_support[raw_prediction['input_support_reason']] += 1
                if row.probability is None:
                    unsupported[row.support_reason] += 1
                else:
                    scored_labels.append(row.correct)
                    probabilities.append(row.probability)
        actual_population = dict(scheme=POPULATION_SCHEME, full_keys_sha256=keys_hash.hexdigest(),
                                 full_keys_labels_sha256=labels_hash.hexdigest())
        need(actual_population == dict(scheme=expected.scheme,
            full_keys_sha256=expected.full_keys_sha256, full_keys_labels_sha256=expected.full_keys_labels_sha256)
             and tuple(full_classes) == population.class_counts,
             'Independent full target/label/prefix population mismatch')
        need(len(probabilities) == claim.supported_targets
             and dict(unsupported) == dict(claim.unsupported_counts)
             and coverage['full_targets'] == claim.full_targets
             and coverage['supported_targets'] == claim.supported_targets
             and coverage['unsupported_targets'] == sum(unsupported.values())
             and coverage['unsupported_counts'] == dict(unsupported)
             and coverage['population'] == actual_population
             and coverage['objective'] == claim.epoch_objective_id,
             'Actual coverage/population differs from selected producer')
        from .gam_kt.evaluation import _metrics
        import pandas as pd
        metrics = _metrics(pd.DataFrame(dict(correct=scored_labels, prediction=probabilities)))
        need(set(metrics) == set(coverage['supported_metrics'])
             and all((value is None and coverage['supported_metrics'][name] is None)
                     or (value is not None and coverage['supported_metrics'][name] is not None
                         and abs(value-coverage['supported_metrics'][name]) <= 1e-12)
                     for name, value in metrics.items()), 'Cached reporting metrics mismatch')
        inputs = reader.verify_unchanged()
    return dict(status='CACHED_SELECTED_BASELINE_METRICS_VERIFIED', candidate_id=claim.candidate_id,
        context=asdict(claim.context), selected_epoch=claim.selected_epoch,
        declared_checkpoint_sha256=claim.checkpoint.sha256,
        input_artifacts={name: asdict(ref) for name, ref in (('claim',claim_ref),
            ('predictions',predictions_ref),('targets',targets_ref),('coverage',coverage_ref))},
        weights_phase=claim.weights_phase, prediction_phase=claim.prediction_phase,
        population=actual_population, normalized_rows_sha256=rows_digest.hexdigest(),
        full_targets=claim.full_targets, supported_targets=len(probabilities),
        coverage=len(probabilities)/claim.full_targets, unsupported_counts=dict(unsupported),
        input_support_counts=dict(input_support), learner_target_counts=learner_counts,
        full_class_counts=dict(negative=full_classes[0], positive=full_classes[1]),
        supported_class_counts=dict(negative=scored_labels.count(0),positive=scored_labels.count(1)),
        supported_metrics=metrics, full_metrics=metrics if not unsupported else None,
        epoch_objective=dict(id=claim.epoch_objective_id,
            native_bce_mean=coverage.get('native_bce_mean'),
            raw_response_log_loss=coverage.get('raw_response_log_loss')),
        metric_contract=dict(implementation='knowledge_tracing.gam_kt.evaluation._metrics',
            source_sha256=hashlib.sha256((Path(__file__).parent/'gam_kt/evaluation.py').read_bytes()).hexdigest(),
            runtime={name: version(name) for name in ('numpy','pandas','scikit-learn')},
            ece_bins=15, ece_edges='equal width [k/15,(k+1)/15), p=1 in last bin',
            accuracy_threshold=.5, probability_precision='exact CSV binary64',
            aggregation='response pooled on supported targets',
            auc_undefined='null for one class or no supported targets'),
        input_verification=inputs, all_nine_candidates_admitted=False,
        external_freeze_authority=False, main_refit_authorized=False,
        checkpoint_weights_loaded=False)
