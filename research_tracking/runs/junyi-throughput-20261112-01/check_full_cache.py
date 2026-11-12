"""Đo strict admission toàn TRAIN80, CPU stream có giới hạn, không model."""
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, load_prepared_junyi_encoding
from knowledge_tracing.akt.research_junyi_window_cache import iter_junyi_window_cache
from knowledge_tracing.akt.resources import memory_snapshot

BUNDLE = Path(__file__).parent
CACHE = ROOT/'artifacts/akt/window-cache/full-train80-20261112-02'
started = time.monotonic()
result = dict(status='FAILED',training_performed=False,cloud_execution=False,records=0)
try:
    roles_file = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
    assert hashlib.sha256(roles_file.read_bytes()).hexdigest()=='b0ca8f6949edd226e48d1cdb24e34ea34a042a385467e1650755994e96567ba3'
    raw = json.loads(roles_file.read_text())
    for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
        raw[name] = tuple(raw[name])
    roles = JunyiResearchRoles(**raw)
    view = JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    receipt_file = CACHE.with_suffix('.encoding.receipt.json')
    # Encoding nằm cạnh cache, basename đã ghim trong receipt chuẩn bị.
    encoding_file = CACHE.with_suffix('.encoding.json')
    receipt = json.loads(receipt_file.read_text())
    encoding = load_prepared_junyi_encoding(encoding_file,receipt_file,view=view,
        source_data_sha256='dec001941b22e098029d544a9a0fd26c1ce8a956d3ee92341dede234033afb64',
        expected_file_sha256='4d5d7330d17f48b3b7d759bc331a99523093cfd249a0f9d7fd455480789c209f',
        expected_receipt_sha256=hashlib.sha256(receipt_file.read_bytes()).hexdigest())
    peak = 0
    for count,record in enumerate(iter_junyi_window_cache(CACHE,view=view,encoding=encoding,
            source_data_sha256=receipt['source_data_sha256'],expected_target_rows=13347331,
            expected_manifest_sha256='43f48045370b6811e537d7936ed307291e1dee88be313c111e4879198556a839'),1):
        if count%1000==0:
            memory = memory_snapshot()
            peak = max(peak,memory['process_rss_bytes'])
            result.update(records=count,seconds=time.monotonic()-started,peak_sampled_rss_bytes=peak)
            print(json.dumps(result),flush=True)
            if time.monotonic()-started>600 or memory['system_available_ram_bytes']<256*1024**2:
                raise RuntimeError('Bounded admission stopped by time or available RAM')
    assert count==232662 and 'torch' not in sys.modules
    result.update(status='FULL_TRAIN80_STRICT_CACHE_ADMISSION_PASS',records=count,torch_imported=False,
                  target_rows=13347331,learners=126774,peak_sampled_rss_bytes=peak)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (BUNDLE/'full-strict-failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (BUNDLE/'full-strict-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='FULL_TRAIN80_STRICT_CACHE_ADMISSION_PASS' else 1)
