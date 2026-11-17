"""Đo bounded SQLite fitter bằng100.000target tổng hợp, không đọc Junyi."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

import psutil
from knowledge_tracing import response_calibration as v1
from scripts.akt.local_response_calibration import fit_temperature_spooled,LocalCalibrationBudget

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
COUNT=100000


def rows():
    for i in range(COUNT):
        yield v1.CalibrationTarget('learner-'+str(i%1000),str(i),'exercise-'+str(i%717),
            hashlib.sha256(str(i).encode()).hexdigest(),i%2,.1+.8*(i%101)/100,'supported')


def main():
    before=psutil.virtual_memory().available
    if before<640*1024**2:
        raise MemoryError('synthetic scaling reserve unavailable')
    directory=ROOT/'artifacts/akt/tmp/local-calibration-spool-20261117-01'
    directory.mkdir(parents=True,exist_ok=False)
    binding=v1.PredictionBinding('SYNTHETIC_ONLY',*('a'*64 for _ in range(7)))
    partition=v1.CalibrationPartition(binding.split_sha256,tuple('learner-'+str(i) for i in range(1000)),('train',),None)
    budget=LocalCalibrationBudget(max_targets=COUNT,max_rss_bytes=512*1024**2,max_seconds=90)
    started=time.monotonic()
    result=fit_temperature_spooled(rows(),binding=binding,partition=partition,
        expected_target_keys=((r.learner_id,r.event_id,r.item_id,r.history_sha256) for r in rows()),
        database=directory/'fit.sqlite',budget=budget,max_evaluations=4)
    receipt=json.loads((directory/'fit.receipt.json').read_text())
    output=dict(status='SYNTHETIC_SCALING_PASSED',targets=COUNT,max_evaluations=4,
        available_before_bytes=before,wall_seconds=time.monotonic()-started,resource=receipt,
        calibration_payload=result.to_payload(),scientific_result=False,real_data_read=False)
    (HERE/'BENCHMARK01.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:output[key] for key in ('status','targets','wall_seconds')}))


if __name__=='__main__':
    main()
