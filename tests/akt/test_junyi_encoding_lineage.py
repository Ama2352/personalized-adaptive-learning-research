"""Encoding chuẩn bị trước phải giữ đúng source và phase fit ban đầu."""
import hashlib
import json

import pytest

from knowledge_tracing.akt.encoding import ExerciseEncoding,save_encoding
from knowledge_tracing.akt.research_junyi_data import (JunyiPhaseView,JunyiResearchEncoding,
    load_prepared_junyi_encoding)
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.shared_kt import StableVocabulary


@pytest.fixture
def prepared(tmp_path):
    roles=make_junyi_research_roles([(str(i),i%5,'development') for i in range(30)])
    view=JunyiPhaseView(roles,'select_train80',roles.train_users[:2],roles.identity)
    encoding=JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(('A',)),{'A':2}),view)
    path=tmp_path/'encoding.json';sha=save_encoding(encoding.native,path)
    receipt=dict(status='JUNYI_TRAIN_ENCODING_FITTED',fit_view_identity=view.identity,
        phase_scope=view.scope,source_data_sha256='a'*64,encoding_file_sha256=sha,
        encoding_identity=encoding.identity)
    return path,tmp_path/'receipt.json',view,receipt,sha


def load(prepared):
    path,receipt_path,view,receipt,sha=prepared
    receipt_path.write_text(json.dumps(receipt))
    return load_prepared_junyi_encoding(path,receipt_path,view=view,source_data_sha256='a'*64,
        expected_file_sha256=sha,expected_receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest())


def test_original_fit_lineage_is_preserved(prepared):
    assert load(prepared).identity==prepared[3]['encoding_identity']


@pytest.mark.parametrize('field,value',[('status','PASS'),('phase_scope','refit_union90'),
    ('fit_view_identity','f'*64),('source_data_sha256','b'*64),('encoding_file_sha256','c'*64),
    ('encoding_identity','d'*64)])
def test_relabelled_or_foreign_encoding_is_rejected(prepared,field,value):
    prepared[3][field]=value
    with pytest.raises(ValueError):
        load(prepared)


def test_file_drift_is_rejected(prepared):
    prepared[0].write_text('{}')
    with pytest.raises(ValueError,match='changed'):
        load(prepared)
