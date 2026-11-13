"""Mã kiểm evidence giữ bytes cũ và phát hiện thay đổi, dùng cả Grade10/Junyi."""
from dataclasses import asdict, dataclass, replace

import pytest

from knowledge_tracing.akt.research_graph_model import _evidence_sha
from knowledge_tracing.simulator_bridge import identity_hash


@dataclass(frozen=True)
class Record:
    name: str
    values: tuple
    metadata: dict


def legacy(rows):
    return identity_hash(tuple(tuple(None if item is None else asdict(item)
                                     for item in row) for row in rows))


@pytest.mark.parametrize('value', [None, True, 0, -1, .25, -0., 'Tiếng Việt', (),
                                   (1, 2, 3), [False, .3], {'z': 2, 'a': None}])
def test_hash_matches_deepcopy_encoder(value):
    nested = Record('cạnh', (value,), {'nested': Record('A', (), {})})
    rows = ((None, nested), ())
    assert _evidence_sha(rows) == legacy(rows)
    assert _evidence_sha(((replace(nested, name='B'),),)) != _evidence_sha(((nested,),))


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_hash_rejects_nonfinite(value):
    with pytest.raises(ValueError):
        _evidence_sha(((Record('A', (value,), {}),),))


@pytest.mark.parametrize('rows', [[], ([],), ((1,),), ((Record,),)])
def test_hash_rejects_invalid_rows(rows):
    with pytest.raises(ValueError):
        _evidence_sha(rows)


def test_hash_rechecks_nested_mutation():
    item = Record('A', (), {'count': 1})
    rows = ((item,),)
    before = _evidence_sha(rows)
    item.metadata['count'] = 2
    assert _evidence_sha(rows) != before
    assert _evidence_sha(rows) == legacy(rows)
