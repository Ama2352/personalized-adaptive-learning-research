"""Kiểm nội dung cache calibration bằng hai chiều EXCEPT ALL trên nguồn."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import json
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('calibration_prep',ROOT/'scripts/akt/prepare_junyi_calibration_data.py')
prep=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)
OUTPUT=ROOT/'artifacts/akt/junyi-cohorts/outer4-calibration-full-20261117-01'
args=SimpleNamespace(mode='semantic-audit',attempt='01',max_seconds=180,max_rss_mib=512,max_output_mib=160)
guard=prep.Budget(args,HERE,OUTPUT)
guard.thread.start()
try:
    import duckdb
    view,requested,values,_,_=prep.frozen_inputs()
    manifest=prep.load(OUTPUT/'manifest.json')
    receipt=prep.load(HERE/'PREPARED.json')
    before=prep.sha(OUTPUT/'manifest.json')
    assert before==receipt['manifest_sha256']
    assert manifest['roles_identity']==view.roles.identity and manifest['phase_identity']==view.identity
    for name,pin in manifest['outputs'].items():
        assert prep.sha(OUTPUT/name)==pin['sha256']
    temp=ROOT/'artifacts/akt/tmp/calibration-semantic-audit-20261117-01'
    temp.mkdir(parents=True,exist_ok=False)
    with duckdb.connect(config=dict(memory_limit='256MB',threads='1',temp_directory=str(temp),max_temp_directory_size='512MB')) as con:
        prep.register_inputs(con,requested,values)
        source=prep.SELECT_SQL
        target='SELECT user_id,exercise,time_done,source_row,correct,suggested FROM read_parquet($target)'
        parameters=dict(source=str(prep.CANONICAL/'**/*.parquet'),target=str(OUTPUT/'canonical.parquet'))
        source_minus_target=int(con.execute('SELECT COUNT(*) FROM (('+source+') EXCEPT ALL ('+target+'))',parameters).fetchone()[0])
        target_minus_source=int(con.execute('SELECT COUNT(*) FROM (('+target+') EXCEPT ALL ('+source+'))',parameters).fetchone()[0])
        assert source_minus_target==target_minus_source==0
        assignments=con.execute("SELECT COUNT(*) n,COUNT(DISTINCT a.user_id) users,COUNT(*) FILTER(WHERE u.user_id IS NULL OR a.fold<>u.fold OR a.partition<>'development') invalid FROM read_parquet(?) a LEFT JOIN requested_calibration_users u ON a.user_id=u.user_id",[str(OUTPUT/'assignments.parquet')]).fetchone()
        assert tuple(map(int,assignments))==(15847,15847,0)
    for name,pin in manifest['outputs'].items():
        assert prep.sha(OUTPUT/name)==pin['sha256']
    assert prep.sha(OUTPUT/'manifest.json')==before
    result=dict(status='PREPARED_CALIBRATION_SOURCE_EXACT',
        source_minus_cache_rows=source_minus_target,cache_minus_source_rows=target_minus_source,
        compared_columns=['user_id','exercise','time_done','source_row','correct','suggested'],
        exact_assignment_learners=15847,foreign_assignment_rows=0,
        source_sha256=prep.sha(Path(__file__).resolve()),preprocessor_source_sha256=prep.sha(ROOT/'scripts/akt/prepare_junyi_calibration_data.py'),
        cache_manifest_sha256=before,cache_files_sha_before_after_equal=True,
        source_generation_note_vi='Count/prepare đầu chạy trước khi thêm nhánhpopulation. Kiểm này xác nhận lại toàn nội dung cache theo sourcepreprocessor hiện hành và nguồn frozen, giữ artifact đã công bố nguyên bytes.',
        new_model_or_training_calls=0)
    prep.write_new(HERE/'SEMANTIC_SOURCE_ACCEPTANCE.json',result)
finally:
    resources=guard.close()
    prep.write_new(HERE/'semantic-audit-RESOURCES.json',resources)
print(json.dumps(result,ensure_ascii=False))
