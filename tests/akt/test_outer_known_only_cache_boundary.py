"""Chứng minh vì sao tách sidecar OOV chưa đủ với cache frozen hiện hành."""
import pytest

from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_window_cache import _parts, _SequenceAudit
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, UnseenTarget
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.shared_kt import StableVocabulary


def outer_records(items):
    roles = JunyiResearchRoles(('t',), ('s',), ('c',), ('o',))
    fit = JunyiPhaseView(roles, 'refit_union90', ('s', 't'), roles.identity)
    view = JunyiPhaseView(roles, 'outer_evaluation', ('o',), roles.identity)
    encoding = JunyiResearchEncoding(
        ExerciseEncoding(StableVocabulary(('known',)), {'known': 1}), fit)
    learner = LearnerEvents('o', 4, tuple(
        KTEvent('o', item, 10 + index, index + 1, index % 2, 0, 4)
        for index, item in enumerate(items)))
    return view, encoding, list(iter_windows(learner, encoding.native, training=False))


def test_known_only_outer_without_oov_is_accepted_by_existing_audit():
    view, encoding, records = outer_records(['known', 'known'])
    audit = _SequenceAudit(view)
    for record in records:
        audit.add(*_parts(record, view, encoding, {'o'}))
    assert audit.summary()['target_rows'] == 2


def test_known_only_filter_preserves_native_history_but_creates_cache_rank_gap():
    view, encoding, records = outer_records(['known', 'new', 'known'])
    assert isinstance(records[1], UnseenTarget)
    known = [record for record in records if not isinstance(record, UnseenTarget)]
    assert [record.global_ranks.tolist() for record in known] == [[0], [2]]
    assert known[1].inputs.source_rows.tolist() == [3]
    assert known[1].history_used.tolist() == [0]
    assert known[1].context_reset.tolist() == [True]
    audit = _SequenceAudit(view)
    audit.add(*_parts(known[0], view, encoding, {'o'}))
    with pytest.raises(ValueError, match='Target rank/chronology mismatch'):
        audit.add(*_parts(known[1], view, encoding, {'o'}))
