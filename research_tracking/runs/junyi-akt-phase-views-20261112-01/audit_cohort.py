"""Kiểm cohort Junyi thực qua phase/cache/vocabulary/window APIs, không NN."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_data import (JunyiPhaseView,fit_junyi_research_encoding,
    iter_junyi_phase_learners,iter_junyi_research_windows)
from knowledge_tracing.akt.types import UnseenTarget,TrainingWindow


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort',type=Path,required=True)
    parser.add_argument('--output-name',required=True)
    args=parser.parse_args()
    if Path(args.output_name).name!=args.output_name:
        raise ValueError('Local evidence output basename required')
    root=args.cohort.resolve()
    raw=(root/'manifest.json').read_bytes();manifest=json.loads(raw)
    role_root=ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01'
    role_payload=json.loads((role_root/'roles.json').read_text())
    for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
        role_payload[name]=tuple(role_payload[name])
    roles=JunyiResearchRoles(**role_payload)
    views={role:JunyiPhaseView(roles,scope,tuple(manifest['roles'][role]['users']),roles.identity)
           for role,scope in [('train','select_train80'),('selection','raw_selection10'),('calibration','calibration_predict')]}
    options=dict(cache_root=root,expected_cache_manifest_sha256=hashlib.sha256(raw).hexdigest())
    encoding=fit_junyi_research_encoding(None,views['train'],**options)
    statistics={}
    for role,view in views.items():
        learners=list(iter_junyi_phase_learners(None,view,**options))
        labels=Counter(event.correct for learner in learners for event in learner.events)
        supported=unsupported=window_count=0;lengths=Counter()
        if role=='calibration':
            # Cohort audit đo support theo vocabulary80. Model calibration sau refit dùng vocabulary90 riêng.
            from knowledge_tracing.akt.windows import iter_windows
            records=(record for learner in learners for record in iter_windows(learner,encoding.native,training=False))
        else:
            records=iter_junyi_research_windows(None,view,encoding,**options)
        for record in records:
            if isinstance(record,UnseenTarget):
                unsupported+=1
            else:
                window=record.window if isinstance(record,TrainingWindow) else record
                window_count+=1;lengths[len(window.inputs.item_ids)]+=1
                supported+=int(window.target_mask.sum())
        if supported+unsupported!=manifest['roles'][role]['retained_events']:
            raise ValueError('Target population mismatch')
        statistics[role]=dict(learners=len(learners),supported_targets=supported,oov_targets=unsupported,
            windows=window_count,window_lengths=dict(lengths),label_counts=dict(labels),
            coverage=supported/(supported+unsupported))
    result=dict(status='ACTUAL_COHORT_PHASE_ADAPTER_CHECKED_NO_NEURAL_FIT',
        corpus=str(root.relative_to(ROOT)).replace('\\','/'),manifest_sha256=options['expected_cache_manifest_sha256'],
        encoding_identity=encoding.identity,encoding_fit_scope='select_train80',
        vocabulary_items=len(encoding.native.vocabulary.values),role_statistics=statistics,
        optimizer_batches_per_epoch=(statistics['train']['windows']+3)//4,
        full_junyi_benchmark=False,training_performed=False,
        limits='Cohort kỹ thuật theo IDhash. OOV được giữ nguyên. Calibration support ở đây đo theo vocab80 để audit, chưa phải calibration của modelrefit90.')
    output=Path(__file__).with_name(args.output_name)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
