"""Đọc corpus mới khôi phục và Parquet metadata; không mở nhãn Test để scoring."""
from pathlib import Path
import hashlib
import json
import os
import sys

root=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root/'src'))
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',
                  GIT_CONFIG_VALUE_0=str(root/'artifacts/akt/dependencies/upstream'))
from knowledge_tracing.akt.provenance import verify_upstream
from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits,read_public_research_corpus
import knowledge_tracing.simulator_corpus_reader as reader
assert Path(reader.__file__).resolve().is_relative_to(root)

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

source=verify_upstream(root/'artifacts/akt/dependencies/upstream','01b7e8d7d7c862cabc9467108e3e7f2555653a88')
corpus_id='grade10-development-lifecycle01-20261108'
folder=root/'artifacts/simulator/corpora'/corpus_id
corpus=read_public_research_corpus(corpus_id,expected_corpus_sha256=sha(folder/'corpus.json'),
    expected_done_sha256=sha(folder/'DONE.json'),limits=CorpusReadLimits(8*1024**2,16*1024**2,262144,48,210,12600,30.))
roles={name:corpus.role_data(name).audit for name in ('train','selection','calibration')}
print('RESTORED_READER_SOURCE',reader.__file__)
print('GRADE10_PUBLIC_ROLES_READ',list(roles))
import pyarrow.parquet as pq
canonical=root/'artifacts/bkt_baseline/derived/canonical'
files=list(canonical.rglob('*.parquet'))
rows=sum(pq.ParquetFile(path).metadata.num_rows for path in files)
expected=json.loads((root/'artifacts/bkt_baseline/derived/manifest.json').read_text())['canonical_rows']
assert len(files)==726 and rows==expected==25924553
assert pq.ParquetFile(root/'artifacts/bkt_baseline/splits/assignments.parquet').metadata.num_rows==247606
print('CANONICAL_FOOTERS_VERIFIED',len(files),rows,'ASSIGNMENTS',247606)
print('UPSTREAM_PIN_AND_CLEAN_CHECKOUT_VERIFIED',source['commit'])
