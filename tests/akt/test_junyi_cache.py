"""Cache phải giữ role, byte identity, timeline và cấu trúc KT của Junyi."""
import hashlib
import json

import pytest

from knowledge_tracing.akt import research_junyi_cache as cache
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,fit_junyi_research_encoding,iter_junyi_research_windows
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.types import TrainingWindow,WindowInputs


@pytest.fixture
def case(tmp_path,monkeypatch):
    monkeypatch.setattr(cache,'PROJECT_ROOT',tmp_path)
    root=tmp_path/'artifacts/akt/junyi-cohorts/test';root.mkdir(parents=True)
    roles=make_junyi_research_roles([(str(i),i%5,'development') for i in range(40)])
    views={role:JunyiPhaseView(roles,scope,(getattr(roles,role+'_users')[0],),roles.identity)
           for role,scope in [('train','select_train80'),('selection','raw_selection10')]}
    records={role:dict(user_id=view.users[0],fold=0,original_events=2,
                      events=[dict(exercise='A',time_done=100+i,source_row=i+1,correct=i,suggested=0) for i in range(2)])
             for role,view in views.items()}
    def publish():
        manifest=dict(status='BOUNDED_COHORT_PREPARED_NOT_TRAINED',purpose='BOUNDED_JUNYI_CUDA_ENGINEERING_COHORT',
            roles_identity=roles.identity,outer_fold=4,label_based_sampling=False,max_events_per_user=300,roles={},outputs_sha256={})
        for role,record in records.items():
            path=root/(role+'.jsonl');path.write_text(json.dumps(record)+'\n',encoding='utf-8')
            manifest['roles'][role]=dict(users=[record['user_id']])
            manifest['outputs_sha256'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        path=root/'manifest.json';path.write_text(json.dumps(manifest),encoding='utf-8')
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return root,views,records,publish


def test_cache_flows_through_real_encoding_and_window_adapter(case):
    root,views,records,publish=case;digest=publish()
    kwargs=dict(cache_root=root,expected_cache_manifest_sha256=digest)
    encoding=fit_junyi_research_encoding(None,views['train'],**kwargs)
    assert encoding.native.vocabulary.values==('A',)
    assert all(isinstance(row,TrainingWindow) for row in iter_junyi_research_windows(None,views['train'],encoding,**kwargs))
    windows=list(iter_junyi_research_windows(None,views['selection'],encoding,**kwargs))
    assert isinstance(windows[0],WindowInputs)
    assert windows[0].inputs.prior_responses.tolist()==[-1,0]


def test_manifest_and_content_byte_changes_rejected(case):
    root,views,records,publish=case;digest=publish()
    with pytest.raises(ValueError,match='manifest'):
        list(cache.iter_cached_phase_learners(root,views['train'],'0'*64))
    with (root/'train.jsonl').open('a') as stream:stream.write(' ')
    with pytest.raises(ValueError,match='digest'):
        list(cache.iter_cached_phase_learners(root,views['train'],digest))


@pytest.mark.parametrize('kind',['wrong_role','outer_fold','nonbinary','reverse','missing_users'])
def test_consistently_hashed_bad_content_still_rejected(case,kind):
    root,views,records,publish=case
    if kind=='wrong_role':records['train']['user_id']=views['selection'].users[0]
    if kind=='outer_fold':records['train']['fold']=4
    if kind=='nonbinary':records['train']['events'][0]['correct']=2
    if kind=='reverse':records['train']['events'].reverse()
    if kind=='missing_users':records['train']['user_id']='foreign'
    digest=publish()
    from knowledge_tracing.akt.research_junyi_data import iter_junyi_phase_learners
    with pytest.raises(ValueError):
        list(iter_junyi_phase_learners(None,views['train'],cache_root=root,expected_cache_manifest_sha256=digest))
