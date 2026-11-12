"""Đóng gói đúng cohort Junyi đã duyệt và cache TRAIN80 tương ứng."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs,write_json
from knowledge_tracing.akt.research_junyi_selection import _identity
from knowledge_tracing.akt.research_junyi_data import iter_junyi_research_windows
from knowledge_tracing.akt.research_junyi_window_cache import build_junyi_window_cache
from knowledge_tracing.akt.encoding import save_encoding

BUNDLE=Path(__file__).parent
cohort=ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01'
roles=ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cohort_sha,roles_sha=sha(cohort/'manifest.json'),sha(roles)
views,encoding,_,options=prepare_inputs(cohort,roles,cohort_sha256=cohort_sha,roles_sha256=roles_sha)
source=_identity(dict(cache=cohort_sha,roles=roles_sha))
cache_root=ROOT/'artifacts/akt/window-cache/bounded320-optimization-20261112-01'
cache_root.mkdir(parents=True,exist_ok=False)
encoding_file=cache_root/'encoding.json'
encoding_sha=save_encoding(encoding.native,encoding_file)
receipt_file=cache_root/'encoding-receipt.json'
write_json(receipt_file,dict(status='JUNYI_TRAIN_ENCODING_FITTED',fit_view_identity=views['train'].identity,
    phase_scope=views['train'].scope,source_data_sha256=source,encoding_file_sha256=encoding_sha,
    encoding_identity=encoding.identity))
cached=build_junyi_window_cache(cache_root/'train',
    iter_junyi_research_windows(None,views['train'],encoding,**options),view=views['train'],encoding=encoding,
    source_data_sha256=source,expected_target_rows=11833)
output=ROOT/'artifacts/akt/modal/junyi-optimization-20261112-01'
output.mkdir(parents=True,exist_ok=False)
files=[cohort/'manifest.json',cohort/'train.jsonl',cohort/'selection.jsonl',roles]
files += [p for p in cache_root.rglob('*') if p.is_file()]
with zipfile.ZipFile(output/'data.zip','x',zipfile.ZIP_DEFLATED) as saved:
    pins={}
    for path in files:
        name=path.relative_to(ROOT).as_posix()
        pins[name]=sha(path)
        saved.write(path,name)
    saved.writestr('MANIFEST.json',json.dumps(dict(files=pins)))
relative=lambda p:p.relative_to(ROOT).as_posix()
data=dict(cohort_root=relative(cohort),cohort_manifest_sha256=cohort_sha,
    roles_path=relative(roles),roles_sha256=roles_sha,
    encoding_file=relative(encoding_file),encoding_sha256=encoding_sha,
    encoding_receipt=relative(receipt_file),encoding_receipt_sha256=sha(receipt_file),
    train_window_cache=relative(cache_root/'train'),train_window_manifest_sha256=cached['manifest_sha256'])
write_json(BUNDLE/'data-inputs.json',dict(data=data,archive=relative(output/'data.zip'),
    archive_sha256=sha(output/'data.zip'),files=pins,calibration_events_included=False,holdout_events_included=False))
print(json.dumps(dict(status='BOUNDED_APPROVED_DATA_PREPARED',archive_bytes=(output/'data.zip').stat().st_size,
                     train_windows=cached['summary']['windows'])))
