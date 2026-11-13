"""Chuẩn bị mẫu throughput Junyi, giữ membership và đổi mã learner khi xuất.

Chỉ đọc TRAIN80 và selection10 đã ghim. Không chọn mẫu theo correctness.
Gói phái sinh giữ ngoài Git, không sửa cache hoặc dataset nguồn.
"""
from dataclasses import asdict,replace
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
os.environ.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    import duckdb
    import numpy as np
    from knowledge_tracing.akt.encoding import load_encoding
    from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
    from knowledge_tracing.akt.research_junyi_window_cache import _load_shard,_save_shard,_parts
    from knowledge_tracing.akt.types import LearnerEvents,KTEvent,TrainingWindow
    from knowledge_tracing.akt.windows import iter_windows
    started=time.perf_counter()
    output=ROOT/'artifacts/akt/colab/junyi-real-t4-cohort-20261113-01'
    output.mkdir(exist_ok=False)
    request=json.loads((ROOT/'research_tracking/runs/junyi-a1-selected-20261113-01/request05.json').read_text())
    inputs=request['inputs']
    pins={}
    for key,pin in [('roles_path','roles_sha256'),('encoding_file','encoding_sha256'),
                    ('encoding_receipt','encoding_receipt_sha256')]:
        pins[inputs[key]]=sha(ROOT/inputs[key])
        assert pins[inputs[key]]==inputs[pin]
    raw_roles=json.loads((ROOT/inputs['roles_path']).read_text())
    groups=('train_users','selection_users','calibration_users','outer_validation_users')
    for name in groups:raw_roles[name]=tuple(raw_roles[name])
    roles=JunyiResearchRoles(**raw_roles)
    train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    selection=JunyiPhaseView(roles,'raw_selection10',roles.selection_users,roles.identity)
    native=load_encoding(ROOT/inputs['encoding_file'])
    encoding=JunyiResearchEncoding(native,train)
    receipt=json.loads((ROOT/inputs['encoding_receipt']).read_text())
    assert encoding.identity==receipt['encoding_identity'] and train.identity==receipt['fit_view_identity']
    aliases={}
    mapped=asdict(roles)
    for prefix,name in zip(('tr','se','ca','ov'),groups):
        mapped[name]=tuple(f'{prefix}{index:06d}' for index,_ in enumerate(getattr(roles,name)))
        aliases.update(zip(getattr(roles,name),mapped[name]))
    exported_roles=JunyiResearchRoles(**mapped)
    exported_train=JunyiPhaseView(exported_roles,'select_train80',exported_roles.train_users,exported_roles.identity)
    exported_selection=JunyiPhaseView(exported_roles,'raw_selection10',exported_roles.selection_users,exported_roles.identity)
    exported_encoding=JunyiResearchEncoding(native,exported_train)
    # Ánh xạ dựa trên thứ tự role đã đóng, không chạy lại phép chia trên alias.
    def alias_window(window):
        users=tuple(aliases[user] for user in window.inputs.user_ids)
        result=replace(window,inputs=replace(window.inputs,user_ids=users))
        assert all(np.array_equal(getattr(result.inputs,name),getattr(window.inputs,name))
                   for name in ('item_ids','timestamps','prior_responses','source_rows'))
        return result
    cache=ROOT/inputs['train_window_cache']
    manifest_path=cache/'manifest.json'
    pins[manifest_path.relative_to(ROOT).as_posix()]=sha(manifest_path)
    assert sha(manifest_path)==inputs['train_window_manifest_sha256']
    manifest=json.loads(manifest_path.read_text())
    assert manifest['status']=='COMPLETE' and manifest['summary']['target_rows']==13347331
    chosen=sorted(random.Random(43).sample(range(len(manifest['shards'])),8))
    training=[]
    for index in chosen:
        entry=manifest['shards'][index]
        path=cache/entry['name']
        records=list(_load_shard(path,entry,manifest))
        pins[path.relative_to(ROOT).as_posix()]=entry['sha256']
        for record in random.Random(4300+index).sample(records,32):
            assert type(record) is TrainingWindow
            _parts(record,train,encoding,frozenset(train.users))
            mapped_record=replace(record,window=alias_window(record.window))
            assert np.array_equal(mapped_record.targets,record.targets)
            training.append(mapped_record)
    random.Random(45).shuffle(training)
    cohort_root=ROOT/inputs['selected_cache_root']
    cohort_manifest=cohort_root/'manifest.json'
    assert sha(cohort_manifest)==inputs['selected_cache_manifest_sha256']
    pins[cohort_manifest.relative_to(ROOT).as_posix()]=sha(cohort_manifest)
    cohort=json.loads(cohort_manifest.read_text())
    for name in ('canonical.parquet','assignments.parquet'):
        path=cohort_root/name
        assert sha(path)==cohort['outputs'][name]['sha256']
        pins[path.relative_to(ROOT).as_posix()]=sha(path)
    selected_users=random.Random(44).sample(list(selection.users),64)
    temp=ROOT/'artifacts/akt/runtime/real-t4-cohort-20261113-01'
    temp.mkdir(parents=True,exist_ok=True)
    connection=duckdb.connect(config={'memory_limit':'384MB','threads':'2','temp_directory':str(temp)})
    try:
        rows=connection.execute('''SELECT user_id,exercise,time_done,source_row,correct,suggested
            FROM read_parquet(?) WHERE user_id IN (SELECT unnest(?))
            QUALIFY row_number() OVER (PARTITION BY user_id ORDER BY time_done,source_row)<=300
            ORDER BY user_id,time_done,source_row''',[str(cohort_root/'canonical.parquet'),selected_users]).fetchall()
        folds=dict(connection.execute('SELECT user_id,fold FROM read_parquet(?) WHERE user_id IN (SELECT unnest(?))',
            [str(cohort_root/'assignments.parquet'),selected_users]).fetchall())
    finally:
        connection.close()
    by_user={user:[] for user in selected_users}
    for user,exercise,timestamp,source_row,correct,suggested in rows:
        assert user in roles.selection_users and folds[user] in (0,1,2,3)
        by_user[user].append(KTEvent(user,exercise,timestamp,source_row,correct,suggested,folds[user]))
    validation=[]
    for user in sorted(by_user):
        assert by_user[user]
        learner=LearnerEvents(user,folds[user],tuple(by_user[user]))
        for record in iter_windows(learner,native,training=True):
            assert type(record) is TrainingWindow, 'pilot selection OOV requires explicit accounting'
            validation.append(record)
    validation=random.Random(46).sample(validation,min(128,len(validation)))
    outputs={}
    for label,records,view in [('train',training,exported_train),('selection',validation,exported_selection)]:
        prepared=[]
        truths=[]
        scored_rows=[]
        for record in records:
            if label=='train':
                window=record.window
                mapped_record=record
            else:
                window=alias_window(record.window)
                mapped_record=window
                truths.append(record.targets)
            meta,arrays,_=_parts(mapped_record,view,exported_encoding,frozenset(view.users))
            prepared.append((meta,arrays))
            scored_rows.extend(window.inputs.source_rows[window.target_mask].tolist())
        assert len(scored_rows)==len(set(scored_rows))
        outputs[label]=_save_shard(output/(label+'.npz'),prepared,compressed=True)
        outputs[label].update(targets=len(scored_rows),users=len({record.window.inputs.user_ids[0] for record in records}),
                              lengths=[len(record.window.inputs.item_ids) for record in records])
        if label=='selection':
            offsets=np.cumsum([0]+[len(values) for values in truths],dtype=np.int64)
            with (output/'selection-truth.npz').open('xb') as stream:
                np.savez_compressed(stream,offsets=offsets,labels=np.concatenate(truths))
    (output/'roles.json').write_text(json.dumps(asdict(exported_roles),separators=(',',':'))+'\n',encoding='utf-8')
    (output/'encoding.json').write_bytes((ROOT/inputs['encoding_file']).read_bytes())
    (output/'graph.json').write_bytes((ROOT/request['graph_file']).read_bytes())
    assert sha(output/'graph.json')==request['graph_sha256']
    assert set(training[index].window.inputs.user_ids[0] for index in range(len(training)))<=set(exported_roles.train_users)
    assert set(alias_window(record.window).inputs.user_ids[0] for record in validation)<=set(exported_roles.selection_users)
    source_pins={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'src/knowledge_tracing/akt').glob('*.py')}
    summary=dict(status='REAL_JUNYI_THROUGHPUT_COHORT_PREPARED_NOT_TRAINED',seed=43,
        train_shard_indices=chosen,selection_users_sampled=64,selection_events_cap=300,
        outputs=outputs,source_roles_identity=roles.identity,export_roles_identity=exported_roles.identity,
        source_encoding_identity=encoding.identity,export_encoding_identity=exported_encoding.identity,
        vocabulary=717,source_pins=pins,code_pins=source_pins,
        exported_files={p.name:sha(p) for p in output.iterdir() if p.is_file()},
        learner_aliasing='bijection_by_frozen_role_and_tuple_index_no_resplit',
        calibration_events=False,outer_validation_events=False,holdout_accessed=False,
        checkpoint_included=False,model_selection=False,modal_spent_usd=0,
        max_gpu_seconds=180,elapsed_seconds=time.perf_counter()-started,
        limits_vi='Mẫu 32 window từ mỗi8shard train và tối đa128window từ64learner selection/300events. '
                  'Không đại diện đầy đủ đuôi dài selection hoặc full cache admission. Chỉ benchmark kỹ thuật, không chọn epoch/model.')
    (output/'cohort.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'cohort-receipt.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:summary[key] for key in ('status','train_shard_indices','vocabulary','elapsed_seconds')}))
    print(json.dumps({label:{key:value for key,value in meta.items() if key!='lengths'} for label,meta in outputs.items()}))


if __name__=='__main__':
    main()
