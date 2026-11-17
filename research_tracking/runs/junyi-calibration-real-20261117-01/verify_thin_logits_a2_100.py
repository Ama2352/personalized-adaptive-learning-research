"""Kiểm solver dùng bảng hẹp trên toàn cohort A2 đã nghiệm thu, nguồn read-only."""
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
VOLUME=ROOT/'artifacts/akt/local-calibration/20261117'
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(1,str(ROOT/'scripts/akt'))
from knowledge_tracing.response_calibration import PredictionBinding,TemperatureCalibration
from local_response_calibration import LocalCalibrationBudget,_Monitor,_Logits,_solver


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    accepted=json.loads((BUNDLE/'LOCAL_A2_FIT_ACCEPTANCE100.json').read_text(encoding='utf-8'))
    body=accepted['calibration']
    reference=TemperatureCalibration.from_payload(body,binding=PredictionBinding(**body['binding']))
    source=VOLUME/'junyi-calibration-real-20261117-01/a2-fit-freecpu-a2-100/payloads/fit/targets.sqlite'
    assert source.is_file() and not source.with_name(source.name+'-journal').exists()
    source_sha=sha(source)
    target=VOLUME/'a2-thin-validation100.sqlite'
    assert not target.exists()
    started=time.monotonic()
    with sqlite3.connect(target,uri=True) as connection:
        connection.execute('PRAGMA cache_size=-8192')
        connection.execute('PRAGMA mmap_size=0')
        connection.execute('ATTACH DATABASE ? AS original',(source.as_uri()+'?mode=ro',))
        with connection:
            connection.execute('CREATE TABLE logits(ordinal INTEGER PRIMARY KEY,logit REAL NOT NULL,correct INTEGER NOT NULL)')
            connection.execute('INSERT INTO logits(logit,correct) SELECT logit,correct FROM original.targets WHERE probability IS NOT NULL ORDER BY learner,event,item,history')
        count=connection.execute('SELECT count(*) FROM logits').fetchone()[0]
        assert count==reference.supported_targets
        assert [connection.execute('SELECT count(*) FROM logits WHERE correct=?',(label,)).fetchone()[0] for label in (0,1)]==body['class_counts']
        common={name:getattr(reference,name) for name in ('binding','partition_sha256','targets_sha256',
            'implementation_sha256','total_targets','supported_targets','class_counts','unsupported_counts')}
        monitor=_Monitor(LocalCalibrationBudget(max_targets=reference.total_targets,max_seconds=900),target)
        solve,solver_sha=_solver()
        actual=solve(_Logits(connection,count,monitor),common,200)
        monitor.check()
        assert actual.to_payload()==reference.to_payload()
        assert sha(source)==source_sha
        receipt=dict(status='FULL_A2_THIN_LOGITS_EXACT_CALIBRATION_PARITY',targets=reference.total_targets,
            supported_targets=count,reference_calibration_identity=reference.identity,result_identity=actual.identity,
            original_database_sha256=source_sha,original_database_bytes=source.stat().st_size,
            thin_database_bytes=target.stat().st_size,solver_ast_sha256=solver_sha,
            adapter_sha256=sha(ROOT/'scripts/akt/local_response_calibration.py'),
            wall_seconds=time.monotonic()-started,sampled_peak_rss_bytes=monitor.peak_rss,
            measured_comparison='Toàn payload khớp exact A2 đã nghiệm thu; không là lượt đánh giá độc lập',
            original_database_modified=False)
    (BUNDLE/'THIN_LOGITS_A2_FULL_PARITY100.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
