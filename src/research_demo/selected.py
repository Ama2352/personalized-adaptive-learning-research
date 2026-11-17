"""Replay hữu hạn của xác suất Grade10 selected-fit đã lưu, không gọi model."""
import gzip
import hashlib
import io
import math
import zlib

from .evidence import EvidenceError, ROOT, bounded_read, parse_json

RUN = 'demo-grade10-selected-replay-20261117-01'
MANIFEST_SHA256 = '0704604b248a429304cdea2e0bcbe09fa59bbe0692f1f9d151e69a61551f9606'
MODELS = (
    'A0', 'A1_EXPERT', 'A1_LEARNED', 'A2_EXPERT', 'A2_LEARNED',
    'A3_EXPERT', 'A3_LEARNED',
)


def _need(value, message):
    if not value:
        raise EvidenceError(message)


def _probability(value):
    return type(value) in (int,float) and math.isfinite(value) and 0 <= value <= 1


class SelectedReplay:
    def __init__(self):
        folder = ROOT/'research_tracking/runs'/RUN
        manifest_raw = bounded_read(folder/'REPLAY_MANIFEST.json', 32*1024)
        _need(hashlib.sha256(manifest_raw).hexdigest() == MANIFEST_SHA256, 'SHA manifest selected không khớp')
        manifest = parse_json(manifest_raw)
        _need(manifest['kind'] == 'GRADE10_SELECTED_MODEL_REPLAY_V1'
              and manifest['new_predictions_generated'] is False and manifest['shared_evaluator_parity'] is True,
              'Phạm vi selected replay không hợp lệ')
        raw = bounded_read(folder/'selected-replay.json.gz', 256*1024)
        _need(len(raw) == manifest['output_bytes'] and hashlib.sha256(raw).hexdigest() == manifest['output_sha256'],
              'SHA projection selected không khớp')
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                expanded = stream.read(2*1024**2+1)
        except (OSError, EOFError, zlib.error) as exc:
            raise EvidenceError('Projection selected gzip không hợp lệ') from exc
        _need(len(expanded) <= 2*1024**2, 'Projection selected giải nén vượt giới hạn')
        self.data = parse_json(expanded)
        self.validate(self.data)
        self.learners = {row['id']: row['events'] for row in self.data['learners']}
        self.items = self.data['items']
        self.models = self.data['models']
        self.provenance = dict(run=RUN, manifest_sha256=MANIFEST_SHA256,
                               output_sha256=manifest['output_sha256'])

    @staticmethod
    def validate(data):
        _need(data['kind'] == 'GRADE10_SELECTED_MODEL_REPLAY_V1' and data['dataset'] == 'Grade10'
              and data['phase'] == 'raw_selection10' and data['labels_are_synthetic'] is True
              and data['independent_evaluation'] is False, 'Dataset/phase selected replay không hợp lệ')
        _need(data['cohort'] == dict(learners=6,targets=1260,steps=210,concepts=28,items=84), 'Cohort selected không khớp')
        items, models = data['items'], data['models']
        _need(len(items) == 84 and len({row['concept'] for row in items.values()}) == 28
              and set(models) == set(MODELS), 'Danh mục Grade10/model không khớp')
        concepts = {row['concept'] for row in items.values()}
        for item, metadata in items.items():
            _need(type(item) is str and item and type(metadata['concept']) is str
                  and metadata['difficulty'] in (1050,1200,1350), 'Item Grade10 không hợp lệ')
        learner_ids = {f'learner-{i}' for i in range(1,7)}
        _need(len(data['learners']) == 6 and {row['id'] for row in data['learners']} == learner_ids,
              'Lựa chọn người học selected không khớp')
        labels = []
        for learner in data['learners']:
            events = learner['events']
            _need(len(events) == 210, 'Lịch sử selected phải đủ210bước')
            for index, event in enumerate(events):
                _need(event['item'] in items and type(event['timestamp']) is int
                      and type(event['correct']) is int and event['correct'] in (0,1)
                      and type(event['history_available']) is int and event['history_available'] >= 0
                      and type(event['history_used']) is int and 0 <= event['history_used'] <= event['history_available'],
                      'Event selected không hợp lệ')
                _need(index == 0 or events[index-1]['timestamp'] < event['timestamp'], 'Thứ tự selected không hợp lệ')
                labels.append(event['correct'])
        for model, row in models.items():
            _need(row['variant'] == model[:2] and row['graph_source'] == ('NONE' if model == 'A0' else model.split('_')[1])
                  and row['selected_epoch'] in (4,5) and row['gate_values_archived'] is False,
                  'Model selected/graph/gate không khớp')
            _need(set(row['probabilities']) == learner_ids, 'Probability learner coverage không khớp')
            probabilities = []
            for learner in data['learners']:
                values = row['probabilities'][learner['id']]
                _need(len(values) == 210 and all(_probability(value) for value in values), 'Selected probabilities không hợp lệ')
                probabilities.extend(values)
            expected_brier = sum((p-y)**2 for p,y in zip(probabilities,labels))/1260
            _need(abs(expected_brier-row['metrics']['brier']) < 1e-12, 'Metric Brier không khớp projection')
            _need(all(type(row['metrics'][name]) in (int,float) and math.isfinite(row['metrics'][name])
                      for name in ('log_loss','auc','brier','ece')), 'Metrics selected không hữu hạn')
            edges = row['edges']
            _need(len(edges) == (0 if model == 'A0' else 31)
                  and len({(edge['parent'],edge['child']) for edge in edges}) == len(edges), 'Edge coverage không khớp')
            for edge in edges:
                _need(edge['parent'] in concepts and edge['child'] in concepts and edge['parent'] != edge['child']
                      and _probability(edge['weight']) and type(edge['supported']) is bool
                      and (edge['supported'] or edge['weight'] == 0), 'Edge confidence không hợp lệ')

    def catalog(self):
        return dict(
            dataset='Grade10', phase='raw_selection10', cohort=self.data['cohort'],
            learners=[
                dict(id=name, label='Người học mô phỏng '+name.split('-')[1])
                for name in self.learners
            ],
            models=[
                dict(
                    id=name, variant=self.models[name]['variant'],
                    graph_source=self.models[name]['graph_source'],
                    selected_epoch=self.models[name]['selected_epoch'],
                    metrics=self.models[name]['metrics'],
                )
                for name in MODELS
            ],
            independent_evaluation=False, model_loaded=False,
            provenance=self.provenance,
            scope_vi='Dự báo development đã dùng chọn vòng. Cùng lịch sử Grade10 mô phỏng, chưa là kết quả vòng kín của AKT.',
        )

    def snapshot(self, model, learner, step):
        if (model not in MODELS or learner not in self.learners
                or type(step) is not int or not 0 <= step < 210):
            raise EvidenceError('Model/người học/bước selected phải thuộc allowlist')
        row, events = self.models[model], self.learners[learner]
        current = events[step]
        concepts = {metadata['concept']: dict(observed=0,correct=0,last_probability=None)
                    for metadata in self.items.values()}
        history = []
        for index, event in enumerate(events[:step]):
            concept = self.items[event['item']]['concept']
            concepts[concept]['observed'] += 1
            concepts[concept]['correct'] += event['correct']
            concepts[concept]['last_probability'] = row['probabilities'][learner][index]
            history.append(dict(step=index,item=event['item'],correct=event['correct']))
        return dict(
            dataset='Grade10', phase='raw_selection10', model=model,
            learner=learner, step=step,
            item=dict(id=current['item'], **self.items[current['item']]),
            timestamp=current['timestamp'],
            probability=row['probabilities'][learner][step],
            reference_probability=self.models['A0']['probabilities'][learner][step],
            history_available=current['history_available'],
            history_used=current['history_used'],
            observed_concepts=concepts, observed_history=history,
            query_route=[
                dict(step=index, item=event['item'])
                for index, event in enumerate(events[:step+1])
            ],
            graph=dict(
                source=row['graph_source'], edges=row['edges'],
                confidence_kind=row['confidence_kind'],
                confidence_semantics=row['confidence_semantics'],
                gate_kind=row['gate_kind'], gate_value=None,
            ),
            checkpoint_sha256=row['checkpoint_sha256'],
            selected_epoch=row['selected_epoch'], independent_evaluation=False,
            recommendation_available=False, calibrated_mastery_available=False,
            scope_vi='Xác suất của câu đã ghi, trước dùng đáp án hiện tại. Lịch sử chỉ gồm các đáp án ở bước trước.',
        )
