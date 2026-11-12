"""Đọc cache cohort kỹ thuật Junyi đã ghim, giữ ranh giới role và source rows."""
import hashlib
import json
from pathlib import Path

from .config import PROJECT_ROOT
from .types import KTEvent,LearnerEvents


def iter_cached_phase_learners(cache_root, view, expected_manifest_sha256):
    root=Path(cache_root).resolve()
    allowed=(PROJECT_ROOT/'artifacts/akt/junyi-cohorts').resolve()
    if root==allowed or not root.is_relative_to(allowed):
        raise ValueError('Owned Junyi cohort cache required')
    manifest_path=root/'manifest.json'
    raw=manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_manifest_sha256:
        raise ValueError('Pinned cohort manifest mismatch')
    manifest=json.loads(raw)
    if (manifest.get('status')!='BOUNDED_COHORT_PREPARED_NOT_TRAINED'
            or manifest.get('purpose')!='BOUNDED_JUNYI_CUDA_ENGINEERING_COHORT'
            or manifest.get('roles_identity')!=view.roles.identity
            or manifest.get('outer_fold')!=4 or manifest.get('label_based_sampling') is not False):
        raise ValueError('Cache role/domain/purpose mismatch')
    phase_roles={'select_train80':('train',),'raw_selection10':('selection',),
                 'refit_union90':('train','selection'),'calibration_predict':('calibration',)}
    collected={}
    for role in phase_roles[view.scope]:
        path=root/(role+'.jsonl')
        if path.stat().st_size>32*1024**2:
            raise ValueError('Bounded cohort file exceeds32MiB')
        with path.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=manifest['outputs_sha256'][path.name]:
            raise ValueError('Cohort file digest mismatch')
        expected_users=set(manifest['roles'][role]['users'])
        frozen_users=set(getattr(view.roles,role+'_users'))
        if not expected_users<=frozen_users:
            raise ValueError('Cache learner belongs to another canonical role')
        seen=set()
        with path.open(encoding='utf-8') as stream:
            for line in stream:
                value=json.loads(line)
                user=value['user_id'];fold=value['fold'];events=value['events']
                if (user not in expected_users or user in seen or type(fold) is not int or fold not in (0,1,2,3)
                        or not 1<=len(events)<=manifest['max_events_per_user']):
                    raise ValueError('Cache learner/fold/event scope mismatch')
                seen.add(user)
                converted=[]
                for event in events:
                    if (type(event['correct']) is not int or event['correct'] not in (0,1)
                            or type(event['suggested']) is not int or event['suggested'] not in (0,1)
                            or type(event['source_row']) is not int or event['source_row']<=0
                            or type(event['time_done']) is not int or event['time_done']<0
                            or type(event['exercise']) is not str or not event['exercise']):
                        raise ValueError('Invalid cached event')
                    converted.append(KTEvent(user,event['exercise'],event['time_done'],event['source_row'],
                                             event['correct'],event['suggested'],fold))
                if user in view.users:
                    collected[user]=LearnerEvents(user,fold,tuple(converted))
        if seen!=expected_users:
            raise ValueError('Incomplete cache role coverage')
    if set(collected)!=set(view.users):
        raise ValueError('Requested phase cohort differs from cache')
    for user in view.users:
        yield collected[user]
