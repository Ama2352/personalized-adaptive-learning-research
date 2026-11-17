"""Rút projection demo Grade10 từ CSV selected đã nghiệm thu, không model load."""
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'src'))
MODELS = ('A0','A1_EXPERT','A1_LEARNED','A2_EXPERT','A2_LEARNED','A3_EXPERT','A3_LEARNED')
IDENTITY = ('learner_id','item_id','timestamp','source_row','global_rank','history_sha256',
            'history_hash_scheme','origin_role','phase_scope','phase_sha256','encoding_sha256')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read_csv(raw):
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8'), newline='')))


def paired_rows(predictions, targets):
    if len(predictions)!=1260 or len(targets)!=1260:
        raise ValueError('Grade10 selection requires1260rows')
    result=[]
    seen=set()
    for prediction,target in zip(predictions,targets):
        identity=tuple(prediction[name] for name in IDENTITY)
        if (identity!=tuple(target[name] for name in IDENTITY) or identity in seen
                or prediction['phase_scope']!='raw_selection10' or prediction['origin_role']!='selection'
                or prediction['support_reason']!='supported' or target['correct'] not in ('0','1')):
            raise ValueError('Selected prediction/target identity or role mismatch')
        seen.add(identity)
        probability=float(prediction['probability'])
        if not math.isfinite(probability) or not 0<=probability<=1:
            raise ValueError('Selected probability invalid')
        result.append(dict(identity=identity,probability=probability,correct=int(target['correct']),
            history_available=int(prediction['history_available']),history_used=int(prediction['history_used'])))
    if result!=sorted(result,key=lambda r:(r['identity'][0],int(r['identity'][4]))):
        raise ValueError('Selected learners/ranks are not canonical')
    return result


def build():
    import pandas as pd
    from knowledge_tracing.gam_kt.evaluation import _metrics
    index_path=ROOT/'experiments/akt/results/model-export-20261112-01/MODEL_INDEX.json'
    index=json.loads(index_path.read_text())
    entries={row['model']:row for row in index['entries'] if row['dataset']=='Grade10'}
    if set(entries)!=set(MODELS):
        raise ValueError('Seven Grade10 selected checkpoints required')
    accepted_a0_path=ROOT/'research_tracking/runs/modal-akt-recovery-20261112-01/main60-a0-verification.json'
    accepted_graph_path=ROOT/'research_tracking/runs/modal-akt-graph-selected-20261112-01/batch-summary.json'
    accepted_a0=json.loads(accepted_a0_path.read_text())
    accepted_graph=json.loads(accepted_graph_path.read_text())
    accepted={'A0':accepted_a0,**{row['candidate_id']:row for row in accepted_graph['conditions']}}
    support=index_path.parent/'SUPPORT.zip'
    if sha(support)!=index['support_sha256']:
        raise ValueError('Portable support archive changed')
    with zipfile.ZipFile(support) as archive:
        bank=json.loads(archive.read('grade10_item_bank.json'))
    items={row['item_id']:dict(concept=row['concept_id'],difficulty=row['difficulty']) for row in bank['items']}
    if len(items)!=84 or len({row['concept'] for row in items.values()})!=28:
        raise ValueError('Grade10 bank84items/28concepts required')
    pins=[dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size)
          for path in (index_path,support,accepted_a0_path,accepted_graph_path)]
    model_rows={}
    reference=None
    for model in MODELS:
        entry=entries[model]
        if entry['phase']!='selected_fit80' or entry['final_research_evaluation_complete'] is not False:
            raise ValueError('Demo requires declared selected-only research scope')
        if model in ('A0','A1_EXPERT'):
            receipt_path=HERE/(model+'_RANGE_RECEIPT.json')
            receipt=json.loads(receipt_path.read_text())
            members={}
            for name in ('predictions.csv','targets.csv'):
                path=HERE/('source-'+model.lower().replace('_','-'))/name
                if sha(path)!=receipt['members'][name]['sha256']:
                    raise ValueError('Recovered A0 member changed')
                members[name]=path.read_bytes()
                pins.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size))
            pins.append(dict(path=str(receipt_path.relative_to(ROOT)),sha256=sha(receipt_path),bytes=receipt_path.stat().st_size))
        else:
            path=ROOT/entry['source_archive']
            if sha(path)!=accepted[model]['archive_sha256']:
                raise ValueError('Grade10 selected archive pin changed')
            pins.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size))
            with zipfile.ZipFile(path) as archive:
                certificate=json.loads(archive.read('SHA256.json'))
                members={}
                for name in ('predictions.csv','targets.csv'):
                    full=str(Path(entry['source_member']).parents[2]).replace('\\','/')+'/selection/'+name
                    raw=archive.read(full)
                    if len(raw)>1024**2 or hashlib.sha256(raw).hexdigest()!=certificate[full]['sha256']:
                        raise ValueError('Grade10 selected CSV pin changed')
                    members[name]=raw
        rows=paired_rows(read_csv(members['predictions.csv']),read_csv(members['targets.csv']))
        signatures=[(row['identity'],row['correct'],row['history_available'],row['history_used']) for row in rows]
        if reference is not None and signatures!=reference:
            raise ValueError('Models do not share target/history population')
        reference=signatures
        computed=_metrics(pd.DataFrame(dict(correct=[r['correct'] for r in rows],prediction=[r['probability'] for r in rows])))
        for key in ('log_loss','auc','brier','ece'):
            if not math.isclose(computed[key],accepted[model]['selection_metrics'][key],rel_tol=1e-10,abs_tol=1e-12):
                raise ValueError('Stored selection metric does not match shared evaluator')
        condition=entry['condition']
        if condition['recipe']!='cgakt-centered-parentmean-scalar-v1':
            raise ValueError('Unknown graph recipe')
        edges=[dict(parent=r['parent_id'],child=r['child_id'],weight=r['operational_weight'],
                    supported=r['supported']) for r in condition['edge_weights']]
        model_rows[model]=dict(variant=condition['variant'],graph_source='NONE' if model=='A0' else model.split('_')[1],
            selected_epoch=entry['epoch'],checkpoint_sha256=entry['sha256'],metrics=computed,
            probabilities=[r['probability'] for r in rows],edges=edges,
            confidence_kind=condition['confidence_kind'],confidence_semantics=condition['confidence_semantics'],
            gate_kind='learned' if model.startswith('A3') else 'disabled' if model=='A0' else 'fixed',
            gate_values_archived=False)
    ids=sorted({row['identity'][0] for row in rows})
    if len(ids)!=6:
        raise ValueError('Six selection learners required')
    learners=[]
    for number, learner in enumerate(ids,1):
        offsets=[index for index,row in enumerate(rows) if row['identity'][0]==learner]
        selected=[rows[index] for index in offsets]
        if [int(row['identity'][4]) for row in selected]!=list(range(210)):
            raise ValueError('Complete210step selection learner required')
        learners.append(dict(id=f'learner-{number}',events=[dict(item=row['identity'][1],timestamp=int(row['identity'][2]),
            correct=row['correct'],history_available=row['history_available'],history_used=row['history_used']) for row in selected]))
    for value in model_rows.values():
        probabilities=value.pop('probabilities')
        value['probabilities']={f'learner-{i+1}':probabilities[i*210:(i+1)*210] for i in range(6)}
    payload=dict(kind='GRADE10_SELECTED_MODEL_REPLAY_V1',phase='raw_selection10',dataset='Grade10',
        items=items,learners=learners,models=model_rows,cohort=dict(learners=6,targets=1260,steps=210,concepts=28,items=84),
        labels_are_synthetic=True,independent_evaluation=False,source_pins=pins)
    output=HERE/'selected-replay.json.gz'
    compressed=gzip.compress(json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode(),mtime=0)
    with output.open('xb') as stream:
        stream.write(compressed)
    manifest=dict(kind=payload['kind'],output_sha256=sha(output),output_bytes=len(compressed),
        source_pins=pins,models=list(MODELS),new_predictions_generated=False,shared_evaluator_parity=True)
    with (HERE/'REPLAY_MANIFEST.json').open('x',encoding='utf-8') as stream:
        json.dump(manifest,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status='SEVEN_SELECTED_REPLAYS_VERIFIED',models=7,targets_per_model=1260,bytes=len(compressed))))


if __name__=='__main__':
    build()
