"""--inspect-only chỉ đọc/hash public data; archive mode chỉ ROOT thực thi.

Không generator/model/NumPy/pandas/Torch, không parse canonical oracle/.
Canonical17files được tham chiếu bằng SHA, không copy vào evidence bundle.
"""
import argparse
import builtins
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
CORPUS_ID='grade10-development-lifecycle01-20261108'
BASE=ROOT/'artifacts/simulator/corpora'/CORPUS_ID
PUBLIC=('corpus.json','bank.json','plan.json','train.jsonl','train.manifest.json',
        'selection.jsonl','selection.manifest.json','calibration.jsonl','calibration.manifest.json')
EXPECTED=set(PUBLIC)|{'DONE.json','oracle/publication-inventory.json'}|{
    'oracle/'+role+suffix for role in ('train','selection','calibration') for suffix in ('.json','.collection.json')}
ROLES=('train','selection','calibration')

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as handle:
        while chunk:=handle.read(65536):digest.update(chunk)
    return digest.hexdigest()

def load(path):
    assert not path.is_relative_to(BASE/'oracle'),'canonical oracle JSON parsing forbidden'
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<=1024**2
    return json.loads(path.read_bytes())

def dump(path,value):
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')

def inspect():
    assert sha(PREP/'run.json')=='08a8975399b2c63474dd4db5d3dfd213024bfe451d21dce749ae025a78fb42de'
    run,worker,owned=load(PREP/'run.json'),load(PREP/'native01/worker_result.json'),load(PREP/'owned_launch_receipt.json')
    request=load(PREP/'request01.json');config=load(ROOT/'experiments/akt/configs/simulator-research-corpus01.json')
    observation=load(PREP/'root_dispatch_observation.json');terminal=json.loads(observation['tool']['output'])
    assert run['status']=='ACCEPTED_FIRST_DEVELOPMENT_CORPUS_NOT_MODEL_FITTED' and run['error'] is None
    assert observation['tool']['exit_code']==0 and terminal['run_sha256']==sha(PREP/'run.json')
    assert max(run['cumulative_seconds'],terminal['cumulative_seconds'],observation['tool']['wall_time_seconds'],
               observation['observed_dispatch_to_terminal_ms']/1000)<=120
    assert not any((PREP/name).exists() for name in ('post_publication_failure.json','outer_failure.log'))
    assert worker['status']=='WORKER_COMPLETE_PENDING_OUTER_ACCEPTANCE' and worker['outer_acceptance_required'] is True
    assert worker['interact_attempts']==worker['interact_returns']==run['actual_interact_attempts']==12600
    assert worker['final_events']==worker['model_calls']==worker['modal_spend_usd']==0
    assert owned['accepted'] and owned['cleanup_accepted'] and owned['cleanup_errors']==[]
    assert owned['job_active_after_cleanup']==0 and owned['popen_handle_closed'] is True
    assert owned['worker_returncode_before_cleanup']==owned['returncode']==0 and owned['actual_worker_in_job_before_GO'] is True
    assert worker['owner']['worker']==owned['actual_worker'] and worker['owner']['parent_owner']==owned['parent']
    assert worker['owner']['job_name']==owned['job_name']
    launch,ready,go=(load(PREP/'owned-launch01'/name) for name in ('launch.json','ready.json','GO.json'))
    assert ready['worker']==go['worker']==owned['actual_worker'] and ready['forbidden_imports']==[]
    assert launch['nonce']==ready['nonce']==go['nonce'] and sha(PREP/'owned-launch01/ready.json')==go['ready_sha256']
    assert launch['parent']==owned['parent'] and launch['job_name']==go['job_name']==owned['job_name']
    for name,digest in owned['output_sha256'].items():assert sha(PREP/'owned-launch01'/name)==digest
    assert sha(PREP/'run_native01.py')==run['outer_sha256']=='2445629d194337fa7d325b09b1f01f359f0ea5d5eef8750753d29d46ca2a3a1c'
    assert sha(PREP/'request01.json')==run['request_sha256']=='52a183e9022ff33937276e5e37f21d362ac06dfb2c2808ea7462df017dfea005'
    assert sha(ROOT/'experiments/akt/configs/simulator-research-corpus01.json')==request['config_sha256']=='8e7800482cea61a5f3ab66e4909de996fda57bcc059dd2751c2e4177dbfa263e'
    sources={**request['collection_sources'],**request['extra_sources']}
    assert len(sources)==17 and sources==run['source_sha256']
    source_before={name:sha(ROOT/name) for name in sources};assert source_before==sources
    assert {p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file()}==EXPECTED
    assert not (BASE/'failure.json').exists()
    canonical={row['path']:dict(sha256=row['sha256'],bytes=row['bytes']) for row in run['artifacts']}
    assert len(canonical)==17 and sum(row['bytes'] for row in canonical.values())==6985213
    for path,row in canonical.items():
        file=ROOT/path
        assert not file.is_symlink() and not getattr(file,'is_junction',lambda:False)()
        assert file.stat().st_size==row['bytes'] and sha(file)==row['sha256']
    assert {name for name,_,_ in run['publication']['files']}==EXPECTED
    assert run['publication']==worker['publication']
    public_opens=[];forbidden_imports=[];subprocess_events=[]
    phase=dict(typed=False,inspect=True)
    def audit(event,args):
        if phase['inspect'] and event=='subprocess.Popen':
            subprocess_events.append(event);raise RuntimeError('read-only QA cannot create subprocess')
        if phase['typed'] and event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
            path=Path(os.fsdecode(args[0])).absolute()
            if path.is_relative_to(BASE):
                assert path.name in (*PUBLIC,'DONE.json') and path.parent==BASE,'reader opened oracle/non-public path'
                public_opens.append(path.name)
    old_import=builtins.__import__
    def no_heavy(name,*args,**kwargs):
        if name.split('.')[0] in ('numpy','pandas','torch') or name in (
            'knowledge_tracing.simulator_research_collection','knowledge_tracing.simulator_corpus_publisher','knowledge_tracing.paper2_reference'):
            forbidden_imports.append(name);raise AssertionError('metadata QA attempted native/heavy import')
        return old_import(name,*args,**kwargs)
    sys.addaudithook(audit);builtins.__import__=no_heavy
    sys.path.insert(0,str(ROOT/'src'))
    try:
        from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits,read_public_research_corpus
        phase['typed']=True
        public=read_public_research_corpus(CORPUS_ID,
            expected_corpus_sha256=run['publication']['corpus_sha256'],expected_done_sha256=run['publication']['done_sha256'],
            limits=CorpusReadLimits(33554432,67108864,262144,48,210,12600,20.))
        phase['typed']=False
    finally:
        phase['typed']=False;builtins.__import__=old_import
    assert not forbidden_imports and not subprocess_events and not any(n in sys.modules for n in ('numpy','pandas','torch'))
    assert set(public_opens)==set(PUBLIC)|{'DONE.json'}
    assert public.identity==worker['public_reader_identity'] and public.input_bytes==worker['public_input_bytes']==1507656
    assert public.plan.identity==request['plan_sha256']=='7222b7c34051f41d99648421b940167c2da705efa604070957a23812273e02ed'
    assert public.plan.manifest()['final_events_read'] is False
    assignments=public.plan.split_plan.assignments();ordinal={a.learner_id:i for i,a in enumerate(assignments)}
    profiles=load(PREP/'native01/profiles.json')
    assert set(profiles)==set(ROLES)
    item_concept={row.item_id:row.concept_id for row in public.bank.items};concepts=set(item_concept.values())
    all_rows=set();all_learners=set();role_stats={};item_learners={item:set() for item in item_concept}
    concept_learners={concept:set() for concept in concepts}
    pairs={(p,c):set() for p in concepts for c in concepts if p!=c}
    for role in ROLES:
        data=public.role_data(role);expected_learners={a.learner_id for a in assignments if a.role==role}
        assert len(data.trajectories)==config['role_counts'][role] and data.reference_complete and data.two_class_support
        assert {t.learner_id for t in data.trajectories}==expected_learners==set(profiles[role])
        assert not (all_learners&expected_learners);all_learners.update(expected_learners)
        profile_counts=Counter(profiles[role].values())
        assert profile_counts==({'PG':16,'PY':16,'PYH':16} if role=='train' else {'PG':2,'PY':2,'PYH':2})
        labels=Counter();covered=set()
        for trajectory in data.trajectories:
            assert len(trajectory.observations)==210
            seen=set()
            for rank,event in enumerate(trajectory.observations):
                assert event.query.timestamp==1767225600+(rank+1)*21600
                assert event.query.source_row==ordinal[trajectory.learner_id]*1000000+rank+1
                assert event.query.source_row not in all_rows;all_rows.add(event.query.source_row)
                assert type(event.correct) is int and event.correct in (0,1)
                labels[event.correct]+=1;covered.add(event.query.item_id)
                if role=='train':
                    concept=item_concept[event.query.item_id]
                    item_learners[event.query.item_id].add(trajectory.learner_id)
                    concept_learners[concept].add(trajectory.learner_id)
                    for parent in seen-{concept}:pairs[parent,concept].add(trajectory.learner_id)
                    seen.add(concept)
        assert len(covered)==84 and [labels[0],labels[1]]==list(data.class_counts)==worker['class_counts'][role]
        assert sum(labels.values())==config['expected_events'][role]
        role_stats[role]=dict(learners=len(data.trajectories),events=sum(labels.values()),covered_items=len(covered),
            class_counts=dict(labels),profile_counts=dict(profile_counts),two_classes=True)
    assert len(all_rows)==12600 and len(all_learners)==60
    support=dict(min_train_unique_learners_per_item=min(map(len,item_learners.values())),
        min_train_unique_learners_per_concept=min(map(len,concept_learners.values())),
        ordered_distinct_concept_pairs=len(pairs),min_train_learners_with_parent_strictly_before_child=min(map(len,pairs.values())),
        pairs_supported_by_at_least20learners=sum(len(v)>=20 for v in pairs.values()))
    assert support==dict(min_train_unique_learners_per_item=38,min_train_unique_learners_per_concept=47,
        ordered_distinct_concept_pairs=756,min_train_learners_with_parent_strictly_before_child=45,
        pairs_supported_by_at_least20learners=756)
    assert source_before=={name:sha(ROOT/name) for name in sources}
    assert all(sha(ROOT/path)==row['sha256'] for path,row in canonical.items())
    # Archive helper may read Git identity later; process denial measures QA only.
    phase['inspect']=False
    return dict(status='INDEPENDENT_READ_ONLY_PASS_REAL_DEVELOPMENT_CORPUS_NOT_MODEL_FIT',
        corpus_id=CORPUS_ID,canonical_inventory=canonical,canonical_files=17,canonical_bytes=6985213,
        public_model_input_files=9,commit_marker_files=1,typed_reader_public_files_opened=sorted(set(public_opens)),
        canonical_oracle_json_parsed=False,roles=role_stats,clock=dict(start_unix_seconds=1767225600,gap_seconds=21600,events_per_learner=210),
        unique_source_rows=len(all_rows),support_coverage_only_not_oof_confidence=support,
        source_sha256=source_before,owner_cleanup=dict(actual_worker=owned['actual_worker'],popen=owned['popen'],
            job_active_after_cleanup=0,popen_handle_closed=True,accepted=True),
        timing=dict(worker_seconds=worker['elapsed_seconds'],owned_call_seconds=owned['elapsed_seconds'],
            outer_receipt_seconds=run['cumulative_seconds'],outer_terminal_seconds=terminal['cumulative_seconds'],
            tool_wall_seconds=observation['tool']['wall_time_seconds'],observed_outer_ms=observation['observed_dispatch_to_terminal_ms'],cap_seconds=120),
        public_reader_identity=public.identity,public_input_bytes=public.input_bytes,
        run_sha256=sha(PREP/'run.json'),actual_new_teacher_model_calls_during_inspection=0,
        limitation='Artifact/type/count/clock/support/source/process receipt verification only; no OOF confidence, neural fit, calibration, final events or RQ efficacy.')

def archive(proof):
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    report=ROOT/'research_tracking/reports/simulator_development_corpus_20261108.md'
    assert report.is_file(),'ROOT reviews report before closure'
    dump(PREP/'independent-verification01.json',proof)
    dump(PREP/'canonical-corpus-inventory01.json',dict(corpus_id=CORPUS_ID,files=proof['canonical_inventory'],
        policy='Canonical17bytes stay in canonical directory, not duplicated in this evidence bundle; oracle hashed opaque only.'))
    selected=[report,Path(__file__),ROOT/'experiments/akt/configs/simulator-research-corpus01.json',
              PREP/'independent-verification01.json',PREP/'canonical-corpus-inventory01.json']
    selected.extend(PREP/name for name in ('run_native01.py','prepare_request01.py','request01.json',
        'request01_metadata_check.json','dispatch.json','owned_launch_receipt.json','run.json',
        'root_dispatch_observation.json','verify_structural_support01.py','structural_support01.json',
        'structural_support01_access_erratum.json'))
    selected.extend(p for p in sorted((PREP/'native01').iterdir()) if p.is_file())
    selected.extend(p for p in sorted((PREP/'owned-launch01').iterdir()) if p.is_file())
    selected.extend(ROOT/name for name in proof['source_sha256'])
    assert all(p.is_file() and not p.is_relative_to(BASE) for p in selected)
    inventory=[dict(source=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256_before_copy=sha(p)) for p in selected]
    dump(PREP/'evidence-copy-inventory-before01.json',dict(inputs=inventory))
    os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=str(ROOT))
    with record_evidence_run(ROOT,'development-corpus-native-20261108-01',
        metadata=dict(kind='actual-native-development-observable-corpus-not-model-fit',actual_teacher_attempts=12600,
            actual_teacher_returns=12600,canonical_files=17,canonical_bytes=6985213,canonical_data_duplicated=False,
            model_calls=0,final_events=0,modal_spend_usd=0,oracle_json_parsed_during_independent_qa=False,
            run_sha256=proof['run_sha256'],timing=proof['timing'],source_snapshot_timing='current bytes verified equal reserved17sourcepins before/after actual run'),
        sources=[*selected,*[ROOT/name for name in proof['canonical_inventory']]],
        note='''# Corpus Development native đầu tiên — chưa fit model

Một actual12600teacher attempts/returns,48train+6selection+6calibration×210events;84items/role,0finalevents/model/Modal. Receipt+terminalRC0+ownedJob0/handlesclosed+all17fileSHA được kiểm; DONEalone không acceptance. Timing stages giữ riêng, toàn bộ<120s. Corpus17canonicalfiles6.985.213B không duplicate vào bundle; canonical-corpus-inventory01.json trỏ exactpaths/SHA/sizes, root giữ canonicalGitbytes riêng.

Independent read-only QA public9modelinputs+DONE dùng typedreader, counts/clock/globalrows/source17current/owner crossbindings; oracle chỉ streamhash opaque, không parse. Support38item/47concept/45strict-priorordered-pair learners trên756pairs là coverage, không OOF confidence/causal edge truth/estimatorfit. Two-class rolelabels không là responsecalibration hoặc modelaccuracy.

QA gốc structural_support01.json giữ nguyên bytes dù oracle_opened=false diễn đạt sai phạm vi truy cập. Erratum structural_support01_access_erratum.json đính kèm thay thế riêng flag này: đã mở7file oracle để hash opaque, không parse JSON hoặc dùng làm features/model. Không đổi số liệu, không chạy lại thí nghiệm; đây là sửa ghi chú truy cập.

Giữ rawoperator/Joblogs/source/config/request/QA/code snapshots và before=aftercopySHA, không neural artifacts hoặc originaldataset. ExplanatoryREADME ở evidence này, không thêm18thfile vào canonicalcorpus. Không benchmarkforecast/RQcompletion/trainingauthorization; actualmodelpipeline cầnreviewriêng.
''') as target:
        copied={}
        for index,(source,row) in enumerate(zip(selected,inventory),1):
            digest=row['sha256_before_copy']
            if digest not in copied:
                destination=target/f'input-{index:02d}__{source.name}'
                with destination.open('xb') as handle:handle.write(source.read_bytes())
                copied[digest]=destination
            destination=copied[digest]
            row.update(destination=destination.name,sha256_after_copy=sha(destination),source_sha256_after_copy=sha(source))
            assert row['sha256_before_copy']==row['sha256_after_copy']==row['source_sha256_after_copy']
        with (target/'copy-inventory.json').open('x',encoding='utf-8') as handle:
            json.dump(dict(input_aliases=len(inventory),unique_copies=len(copied),copies=inventory),handle,ensure_ascii=False,indent=2);handle.write('\n')
    result=dict(**verify_evidence_bundle(target),manifest_sha256=sha(target/'manifest.json'),physical_files=len(list(target.iterdir())),
        input_aliases=len(inventory),unique_copies=len(copied),report_sha256=sha(report))
    dump(PREP/'evidence-closure01.json',result)
    paths=[report.relative_to(ROOT).as_posix()]+[p.relative_to(ROOT).as_posix() for p in sorted(target.iterdir())]
    with (PREP/'evidence-stage-paths01.txt').open('x',encoding='utf-8') as handle:handle.write('\n'.join(paths)+'\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inspect-only',action='store_true');args=parser.parse_args()
    assert Path(sys.executable).absolute()==ROOT/'.venv/Scripts/python.exe'
    proof=inspect()
    if args.inspect_only:
        print(json.dumps({k:v for k,v in proof.items() if k not in ('canonical_inventory','source_sha256')},ensure_ascii=False))
    else:
        archive(proof)
