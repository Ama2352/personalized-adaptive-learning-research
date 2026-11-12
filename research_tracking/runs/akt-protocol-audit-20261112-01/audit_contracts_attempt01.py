"""Audit cấu hình, split và dự báo đã chạy. Chỉ stdlib, không training/cloud."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
GRAPH_BUNDLE = ROOT / 'research_tracking/runs/modal-akt-graph-selected-20261112-01'
CORPUS = ROOT / 'artifacts/simulator/corpora/grade10-development-lifecycle01-20261108'
FROZEN = dict(device='cuda', seed=42, context=100, target_block=100, max_length=200,
    d_model=256, heads=8, blocks=1, d_ff=1024, final_fc=512, dropout=0.05,
    kq_same=1, separate_qa=False, n_pid=0, graph=False, batch_size=4, lr=1e-4,
    betas=[0.9,0.999], eps=1e-8, weight_decay=0.0, max_grad_norm=1.0,
    max_epochs=20, patience=3, min_delta=0.0001,
    source_commit='01b7e8d7d7c862cabc9467108e3e7f2555653a88', phase='simulator-research')


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check_recipe(config):
    for name, expected in FROZEN.items():
        need(type(config[name]) is type(expected) and config[name] == expected, 'recipe:' + name)


def replay_stopping(epochs, config):
    best, best_epoch, stale, saved = math.inf, None, 0, []
    for position, row in enumerate(epochs, 1):
        need(row['epoch'] == position and stale < config['patience'], 'epoch ordering/continuation after stop')
        value = row['raw_selection']['native_bce_mean']
        need(math.isfinite(value), 'nonfinite epoch objective')
        if value < best - config['min_delta']:
            best, best_epoch, stale = value, position, 0
            saved.append(position)
        else:
            stale += 1
        need(row['selected_epoch'] == best_epoch, 'epoch selected-state mismatch')
    need(stale >= config['patience'] or len(epochs) == config['max_epochs'], 'premature training terminal')
    return best_epoch, saved


def check_population(predictions, targets, expected):
    need(len(predictions) == len(targets) == len(expected), 'target count')
    seen = set()
    for prediction, target in zip(predictions, targets):
        key = prediction['learner_id'], int(prediction['global_rank'])
        need(key not in seen and key in expected, 'duplicate/foreign target')
        seen.add(key)
        query, label = expected[key]
        for row in (prediction, target):
            need(row['learner_id'] == key[0] and int(row['global_rank']) == key[1], 'prediction/truth join')
            need(row['item_id'] == query['item_id'] and int(row['timestamp']) == query['timestamp']
                 and int(row['source_row']) == query['source_row'], 'target identity/order')
            need(row['origin_role'] == 'selection' and row['phase_scope'] == 'raw_selection10', 'scored role')
        need(int(target['correct']) == label, 'truth differs from observable corpus')
        effective_start = max(0, (key[1] // 100)*100 - 100)
        history = key[1] - effective_start
        need(int(prediction['history_used']) == int(prediction['history_available']) == history, 'causal window geometry')
        need(prediction['context_reset'] == 'False' and prediction['support_reason'] == 'supported', 'unexpected support/reset')
    need(seen == set(expected), 'missing target')


def recompute_metrics(predictions, targets):
    pairs = [(float(row['probability']), int(truth['correct'])) for row, truth in zip(predictions, targets)]
    need(all(math.isfinite(p) and 0 < p < 1 and y in (0,1) for p,y in pairs), 'invalid probability/label')
    n = len(pairs)
    loss = sum(-y*math.log(p)-(1-y)*math.log1p(-p) for p,y in pairs)/n
    brier = sum((p-y)**2 for p,y in pairs)/n
    accuracy = sum((p>=0.5)==bool(y) for p,y in pairs)/n
    bins = [[(p,y) for p,y in pairs if min(int(p*15),14)==index] for index in range(15)]
    ece = sum(abs(sum(y-p for p,y in group))/n for group in bins if group)
    ties = {}
    for p,y in pairs:
        counts = ties.setdefault(p, [0,0]); counts[y] += 1
    negative_before, concordance = 0, 0.0
    for p in sorted(ties):
        negative, positive = ties[p]
        concordance += positive*(negative_before+0.5*negative)
        negative_before += negative
    positives = sum(y for _,y in pairs)
    auc = concordance/(positives*(n-positives))
    return dict(log_loss=loss,brier=brier,accuracy=accuracy,ece=ece,auc=auc)


def main():
    corpus = json.loads((CORPUS/'corpus.json').read_text())
    plan = json.loads((CORPUS/'plan.json').read_text())['manifest']
    need(corpus['no_junyi_fold'] is True and corpus['domain']=='simulator', 'environment')
    need(corpus['protocol_sha256'] == sha(ROOT/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md'), 'protocol source drift')
    role_ids, source_refs, trajectories = {}, {}, {}
    for role in ('train','selection','calibration'):
        role_meta = corpus['roles'][role]
        manifest_path = CORPUS/role_meta['manifest_file']
        observable = CORPUS/role_meta['observable_file']
        need(sha(manifest_path)==role_meta['manifest_sha256'] and sha(observable)==role_meta['observable_sha256'], 'corpus bytes')
        manifest = json.loads(manifest_path.read_text())
        role_ids[role] = set(manifest['learner_ids'])
        need(len(role_ids[role])==role_meta['learners'], 'role learner count')
        source_refs[str(manifest_path.relative_to(ROOT))] = sha(manifest_path)
        if role != 'calibration':
            with observable.open() as stream:
                trajectories[role] = [json.loads(line) for line in stream]
    need(sum(map(len,role_ids.values())) == len(set.union(*role_ids.values())) == 60, 'learner overlap')
    assignments = plan['assignments']
    need(len({row['seed_family'] for row in assignments}) == 60, 'seed-family reuse')
    seeds = [seed for row in assignments for _,seed in row['stream_seeds']]
    need(len(set(seeds))==len(seeds)==180, 'stream seed reuse')
    expected, support = {}, {}
    for role, learners in trajectories.items():
        need({row['learner_id'] for row in learners}==role_ids[role], 'observable/role learner mismatch')
        for learner in learners:
            observations=learner['observations']
            need(len(observations)==210, 'learner target count')
            clocks=[(row['query']['timestamp'],row['query']['source_row']) for row in observations]
            need(clocks==sorted(clocks) and len(set(clocks))==210, 'learner chronology')
            if role=='train':
                for item in {row['query']['item_id'] for row in observations}:
                    support[item]=support.get(item,0)+1
            else:
                for rank,row in enumerate(observations):
                    expected[learner['learner_id'],rank]=(row['query'],row['correct'])
    need(len(support)==84 and len(expected)==1260, 'train vocabulary/selection targets')
    index=json.loads((GRAPH_BUNDLE/'checkpoint-index.json').read_text())
    results, common = [], None
    for entry in index['entries']:
        run_id=entry['run_id'];native=ROOT/'experiments/akt/results'/run_id
        receipt=json.loads((native/'receipt.json').read_text())
        archive=native/'artifacts.zip';need(sha(archive)==receipt['archive_sha256'], 'archive bytes')
        prefix=f'experiments/akt/results/{run_id}/'
        with zipfile.ZipFile(archive) as saved:
            def read(name): return saved.read(prefix+name)
            def document(name): return json.loads(read(name))
            config=json.loads(saved.read(f'experiments/akt/results/{run_id}-operation/config.json'))
            check_recipe(config)
            invocation=document('invocation.json');claim=document('selected-claim.json')
            encoding=document('fit80/encoding.json');epochs=document('fit80/epochs.json')
            coverage=document('selection/coverage.json');terminal=document('selected-terminal.json')
            need(dict(encoding['support'])==support and encoding['learners']==48, 'vocabulary/support was not fit on TRAIN48')
            need(encoding['optimization_scope']=='select_train80' and encoding['selection_freeze_sha256'] is None, 'encoding phase')
            need(claim['context']['environment_id']=='grade10_simulator', 'false Junyi fold interpretation')
            shared=dict(config={key:config[key] for key in FROZEN},
                context=claim['context'],encoding=claim['encoding_sha256'],
                initialization=claim['initial_backbone_sha256'],cuda=invocation['spec']['cuda_profile'],
                objective=claim['epoch_objective_id'])
            if common is None: common=shared
            need(shared==common, 'cross-model recipe/split/init/backend mismatch')
            selected,saved_epochs=replay_stopping(epochs,config)
            need(selected==claim['selected_epoch']==terminal['selected_epoch'], 'best checkpoint selection')
            need(sorted(int(name.split('-')[1]) for name in receipt['checkpoint_transfers'])==saved_epochs, 'saved best epoch inventory')
            need(not claim['refit_started'] and not claim['calibration_used_for_selection'], 'selection/refit/calibration ordering')
            need(invocation['required_matrix_candidates']==9 and not terminal['system_selection_performed'], 'premature system winner')
            predictions=list(csv.DictReader(io.StringIO(read('selection/predictions.csv').decode())))
            targets=list(csv.DictReader(io.StringIO(read('selection/targets.csv').decode())))
            check_population(predictions,targets,expected)
            metrics=recompute_metrics(predictions,targets)
            for key,value in metrics.items():need(abs(value-coverage['full_metrics'][key])<1e-12,'reported metric:'+key)
            need(terminal['counters']['complete']==36*len(epochs) and terminal['counters']['complete_targets']==10080*len(epochs),'optimizer target accounting')
            need(all(row['receipt']['epoch_steps']==36 and row['receipt']['epoch_targets']==10080 for row in epochs),'full epoch')
            results.append(dict(candidate_id=entry['candidate_id'],status='PASS_SELECTED_ONLY',
                epochs=len(epochs),selected_epoch=selected,calibration_leak_evidence=False,
                reused_for='Đánh giá selected-fit80 của Grade10 theo recipe26',
                config_outer_fold_ignored_for_simulator=config['outer_fold'],metrics_recomputed=metrics))
    output=dict(status='PAST_SELECTED_RUNS_PASS_FUTURE_FULL_EXPERIMENT_NOT_READY',
        frozen_recipe=FROZEN,roles={key:len(ids) for key,ids in role_ids.items()},
        seed_families_disjoint=True,stream_seeds_disjoint=True,
        train_vocabulary_recomputed=84,selection_queries_checked_per_model=1260,
        actual_effective_history_range=[0,199],results=results,source_refs=source_refs,
        pending=['Junyi typed producer và role views chưa nối','Full Gate cho nguồn Junyi mới chưa nghiệm thu',
                 'SAKT/GKT Main selected và external-freeze/refit/calibration còn thiếu',
                 'Matched Junyi GAM/Graph-GAM khác phạm vi train của historical5fold',
                 'Chưa có đánh giá độc lập/closed-loop để kết luận hiệu quả'],
        gpu_allocated=False,training_performed=False,holdout_events_read=False)
    with (BUNDLE/'audit-result.json').open('x',encoding='utf-8') as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(status=output['status'],selected_runs_verified=len(results),queries_verified=1260*len(results),effective_history=[0,199]),ensure_ascii=False))


if __name__=='__main__':
    main()
