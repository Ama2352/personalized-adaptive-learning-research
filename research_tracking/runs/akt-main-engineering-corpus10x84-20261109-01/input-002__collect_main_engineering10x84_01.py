"""Nguồn chuẩn bị corpus engineering riêng; không tự cấp quyền hoặc chạy fit.

ROOT phải review nguồn/request/caps rồi dispatch riêng. Không sửa canonical60.
Actual ResearchCollectionResult chỉ đến từ collect_research_role nguyên bản.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
CORPUS_ID = 'grade10-main-lifecycle-engineering10x84-20261109-01'
OUT = P/'main-engineering10x84-01'
OWNED = P/'main-engineering10x84-01-owned'
CORPUS = R/'artifacts/simulator/corpora'/CORPUS_ID
PROTOCOL = 'c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6'
RUNTIME = 'artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json'
RUNTIME_SHA = '3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b'
INDEX = 'artifacts/akt/preflight/gate2-main177-win-current-gate-20261109-05.json'
INDEX_SHA = 'e8162f6efce3ca0a443f6c40f69308b06b610e95d5a02504ba146e92b6f87366'
ROLES = ('train','selection','calibration')
COUNTS = dict(train=8,selection=1,calibration=1)
EVENTS = dict(train=672,selection=84,calibration=84)
PLAN = dict(namespace=CORPUS_ID,root_seed=42,development_learners=10,final_learners=1,protocol_sha256=PROTOCOL)
RECIPE = dict(policy='cyclic_items_seeded_offset',events_per_learner=84,start_unix_seconds=1767225600,gap_seconds=21600)
LIMITS = dict(worker_seconds=60.,outer_seconds=70.,owned_seconds=65.,cleanup_seconds=3.,finalization_seconds=5.,
    max_rss_bytes=512*1024**2,min_available_ram_bytes=2*1024**3,max_file_bytes=8*1024**2,
    max_total_bytes=16*1024**2,max_oracle_bytes=12*1024**2)
PACKAGE = 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
COLLECTION_SOURCES = (
    PACKAGE+'/source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb',
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
    'src/knowledge_tracing/simulator_research_collection.py','src/knowledge_tracing/paper2_reference.py',
    'src/knowledge_tracing/simulator_collection.py','src/knowledge_tracing/simulator_research_data.py',
    'src/knowledge_tracing/simulator_data.py','src/knowledge_tracing/simulator_bridge.py',
    'src/knowledge_tracing/akt/resources.py',
    *(PACKAGE+'/data/simulator_inputs/'+name for name in ('nodes.csv','edges.csv','question_bank.csv','concept_to_chapter_map.csv')))
SELF = P.relative_to(R).as_posix()+'/collect_main_engineering10x84_01.py'
EXTRA_SOURCES = (SELF,P.relative_to(R).as_posix()+'/run_main_engineering10x84_01.py',
    'scripts/research/windows_owned_worker.py','scripts/research/collect_development_corpus.py',
    'src/knowledge_tracing/simulator_corpus_publisher.py','src/knowledge_tracing/simulator_corpus_reader.py')
PUBLIC10 = {'corpus.json','bank.json','plan.json','train.jsonl','train.manifest.json',
    'selection.jsonl','selection.manifest.json','calibration.jsonl','calibration.manifest.json','DONE.json'}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def hex64(value):
    return type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def validate_contract(value):
    """Pure consistency only. A dict/SHA/reference is not dispatch authority."""
    need(type(value) is dict and set(value)=={'schema_version','purpose','approval_reference',
        'plan_recipe','collection_recipe','profile','generated_roles','limits','collection_sources','extra_sources',
        'runtime_report','runtime_sha256','gate_index','gate_index_sha256'},'closed engineering request')
    need(type(value['schema_version']) is int and value['schema_version']==1
         and value['purpose']=='GENUINE_10X84_ENGINEERING_CORPUS_NOT_RESEARCH_ALLOCATION'
         and type(value['approval_reference']) is str and 0<len(value['approval_reference'].strip())<=256,
         'explicit engineering purpose/ROOT reference')
    # JSON canonical equality also rejects bool==1 and int/float substitutions.
    for key,expected in (('plan_recipe',PLAN),('collection_recipe',RECIPE),('limits',LIMITS)):
        need(json.dumps(value[key],sort_keys=True,allow_nan=False)==json.dumps(expected,sort_keys=True,allow_nan=False),
             'fixed explicit '+key)
    need(value['profile']=='PG' and value['generated_roles']==list(ROLES), 'allPG fixture, no final events')
    for key,names in (('collection_sources',COLLECTION_SOURCES),('extra_sources',EXTRA_SOURCES)):
        need(type(value[key]) is dict and set(value[key])==set(names)
             and all(hex64(pin) for pin in value[key].values()),'exact source allowlist and lowercase SHA')
    need((value['runtime_report'],value['runtime_sha256'],value['gate_index'],value['gate_index_sha256'])
         == (RUNTIME,RUNTIME_SHA,INDEX,INDEX_SHA), 'actual current runtime/index inputs')
    return value


def failure_accounting(completed, active=None, receipt=None):
    """Hardkill without receipt remains UNKNOWN, never an invented zero."""
    need(set(completed)<=set(ROLES) and all(type(v) is int and v==EVENTS[k] for k,v in completed.items()),
         'only complete genuine role counters admitted')
    need(active is None or active in ROLES and active not in completed, 'active role disjoint')
    lower=sum(completed.values())
    actual=lower if active is None else None
    if receipt is not None:
        need(active is not None and type(receipt) is dict,'active collector failure receipt')
        attempts=receipt['interact_attempts'];returns=receipt['interact_returns']
        need(type(attempts) is int and type(returns) is int and 0<=returns<=attempts<=EVENTS[active],
             'bounded actual active counters')
        actual=lower+attempts
    return dict(reserved_teacher_attempts=840,completed_role_attempts=lower,
        actual_attempts=actual,actual_attempts_lower_bound=lower,actual_attempts_upper_bound=840,
        active_role=active,active_actual='UNKNOWN' if receipt is None and active else 'RECEIPT_OR_NO_ACTIVE_ROLE',
        automatic_retry=False)


def load_library(expected_sha):
    path=R/'scripts/research/collect_development_corpus.py'
    need(path.is_file() and not path.is_symlink() and path.stat().st_size<=2*1024**2
         and hashlib.sha256(path.read_bytes()).hexdigest()==expected_sha,'I/O helper source before definitions import')
    spec=importlib.util.spec_from_file_location('engineering_collection_io_only',path)
    library=importlib.util.module_from_spec(spec);spec.loader.exec_module(library)
    return library


def run(args):
    start=time.perf_counter()
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner=worker_gate()  # Before domain/NumPy/pandas imports and native work.
    relative=Path(args.request)
    need(not relative.is_absolute() and '..' not in relative.parts and '\\' not in args.request,
         'relative POSIX request')
    path=R/relative
    need(path.parent==P and path.is_file() and path.stat().st_size<=128*1024 and hex64(args.request_sha256),
         'reviewed request in existing prep')
    cursor=R
    for part in relative.parts:
        cursor/=part;need(not cursor.is_symlink() and not cursor.is_junction(),'physical request')
    raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==args.request_sha256,'request SHA before helper import')
    request=validate_contract(json.loads(raw))
    library=load_library(request['extra_sources']['scripts/research/collect_development_corpus.py'])
    need(request['approval_reference']==args.approval_reference,'exact ROOT dispatch reference')
    sources=request['collection_sources']|request['extra_sources']
    def pins():
        result={}
        for name,pin in sources.items():
            source=library.safe_file(name)
            need(source.is_file() and source.stat().st_size<=2*1024**2,'bounded pinned source')
            result[name]=hashlib.sha256(source.read_bytes()).hexdigest()
        return result
    before=pins();need(before==sources,'source pins before native imports')
    need(not OUT.exists() and not CORPUS.exists(),'fresh separate fixture destination, no reuse')
    OUT.mkdir()
    write=lambda name,value:library.write_json(OUT,name,value)
    write('reservation.json',dict(status='RESERVED_NOT_ACTUAL_COUNTS',reserved_teacher_attempts=840,
        actual_attempts=None,per_role_reservations=EVENTS,request_sha256=args.request_sha256,
        owner=owner,automatic_retry=False,canonical60_modified=False))
    # Actual Windows metadata phase, then network/undeclared process denial.
    phase=['windows_metadata'];denied=[];metadata_calls=[];git_calls=[]
    command=os.path.normcase(os.path.abspath(str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')))
    upstream=R/'artifacts/akt/dependencies/upstream'
    tails=[('rev-parse','HEAD'),('status','--porcelain','--untracked-files=all'),('remote','get-url','origin')]
    for name in ('akt.py','README.md','LICENSE'):
        tails += [('hash-object',name),('rev-parse','HEAD:'+name)]
    tails += [('rev-parse','HEAD^{tree}')]
    git_argv=[subprocess.list2cmdline(['git','-C',str(upstream),*tail]) for tail in tails]
    def audit(event,values):
        if event=='import' and str(values[0]).split('.')[0] in {'torch','sklearn','scipy','pyBKT','modal','boto3'}:
            denied.append(event+':'+str(values[0]));raise RuntimeError('no model/solver/cloud imports')
        if event=='subprocess.Popen':
            if phase[0]=='windows_metadata' and len(metadata_calls)<3 and type(values[0]) is str and type(values[1]) is str:
                allowed={command.casefold()+' /c "ver"','"'+command.casefold()+'" /c "ver"'}
                if os.path.normcase(os.path.abspath(values[0]))==command and values[1].strip().casefold() in allowed:
                    metadata_calls.append(values[1]);return
            if phase[0]=='prerequisites' and len(git_calls)<10 and values[0] in (None,'git') and values[1]==git_argv[len(git_calls)]:
                git_calls.append(values[1]);return
            denied.append(event);raise RuntimeError('undeclared child denied')
        if event=='os.system' or event.startswith(('os.spawn','os.posix_spawn')) or event.startswith('socket.') and not (phase[0]=='windows_metadata' and event=='socket.gethostname'):
            denied.append(event);raise RuntimeError('network or undeclared child denied')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
            target=Path(os.path.abspath(os.fsdecode(values[0])))
            if target.is_relative_to(R/'artifacts/simulator/corpora'):
                allowed=target.is_relative_to(CORPUS)
                if phase[0]=='public_reader':allowed=target in {CORPUS/name for name in PUBLIC10}
                if not allowed:denied.append('nonfixture_or_nonpublic_corpus');raise RuntimeError('separate corpus/read-only public boundary')
            if any(target==R/name or target.is_relative_to(R/name) for name in ('dataset','artifacts/bkt_baseline','venv','.wsl')):
                denied.append('protected');raise RuntimeError('protected data denied')
    sys.addaudithook(audit)
    results={};completed={};active=None;publication=None;error=None;metadata=None;resources=[]
    try:
        try:
            native=platform.uname();processor=platform.processor()
            metadata=dict(system=native.system,release=native.release,version=native.version,machine=native.machine,
                processor_cache_warmed=type(processor) is str,commands=metadata_calls,fixture_replaced=False)
            need(native.system=='Windows','actual Windows metadata')
        finally:phase[0]='closed_metadata'
        write('windows-metadata.json',metadata)
        sys.path.insert(0,str(R/'src'))
        from knowledge_tracing.akt.resources import memory_snapshot
        def left():
            remaining=60-(time.perf_counter()-start)
            need(math.isfinite(remaining) and remaining>0,'one global worker60s')
            sample=memory_snapshot();resources.append(sample)
            need(type(sample['process_rss_bytes']) is int and sample['process_rss_bytes']>=0
                 and type(sample['system_available_ram_bytes']) is int and sample['system_available_ram_bytes']>=0
                 and (sample.get('process_peak_rss_bytes') is None or
                      type(sample['process_peak_rss_bytes']) is int and sample['process_peak_rss_bytes']>=0),
                 'valid memory telemetry, no UNKNOWN acceptance')
            need(max(sample['process_rss_bytes'],sample.get('process_peak_rss_bytes') or 0)<=LIMITS['max_rss_bytes']
                 and sample['system_available_ram_bytes']>=LIMITS['min_available_ram_bytes'],'RSS512MiB/free2GiB')
            need(len(resources)<=128,'bounded phase telemetry')
            remaining=60-(time.perf_counter()-start);need(remaining>0,'global cap after telemetry')
            return remaining
        left()
        from knowledge_tracing.akt import authorization as auth
        from knowledge_tracing.akt.config import AKTConfig
        phase[0]='prerequisites'
        config=AKTConfig(output_dir=R/'artifacts/akt/readiness'/CORPUS_ID)
        runtime=auth.preflight(config,project_root=R,runtime_report_path=R/RUNTIME,lock_file=R/'requirements-akt.lock.txt')
        gate=auth.require_gate2_evidence(config,project_root=R,gate2_report=R/INDEX,lock_file=R/'requirements-akt.lock.txt')
        need(runtime['runtime_report_sha256']==RUNTIME_SHA and runtime['runtime'].get('runtime_schema_version')==2
             and gate['pointer_sha256']==INDEX_SHA and len(git_calls)==10,'genuine current prerequisites')
        write('prerequisites.json',dict(runtime=runtime,gate=gate,git_calls=git_calls))
        phase[0]='imports';left()
        from knowledge_tracing.simulator_research_data import ResearchSplitPlan,ShardLimits
        from knowledge_tracing.simulator_research_collection import (
            ResearchCollectionRecipe,ResearchCollectionLimits,collect_research_role,source_inventory)
        from knowledge_tracing.simulator_corpus_publisher import CorpusPublicationLimits,publish_research_corpus
        from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits,read_public_research_corpus
        left()
        plan=ResearchSplitPlan(**PLAN);recipe=ResearchCollectionRecipe(**RECIPE)
        need(source_inventory()==request['collection_sources'],'genuine13 collection source identities')
        need(dict(plan.split_plan.role_counts)==dict(train=8,selection=1,calibration=1,final=1),'exact split8/1/1/finalmetadata1')
        write('plan.json',plan.manifest())
        assignments=plan.split_plan.assignments()
        ordinal={assignment.learner_id:i for i,assignment in enumerate(assignments)}
        profiles={role:{a.learner_id:'PG' for a in plan.split_plan.assignments(role)} for role in ROLES}
        write('profiles.json',profiles)
        for active in ROLES:
            phase[0]='collect_'+active
            write(active+'.started.json',dict(reserved_role_attempts=EVENTS[active],completed_roles=completed,
                global_reservation=840,actual_active_attempts=None))
            limits=ResearchCollectionLimits(COUNTS[active],84,EVENTS[active],left(),LIMITS['max_rss_bytes'],LIMITS['min_available_ram_bytes'])
            result=collect_research_role(plan,role=active,profiles=profiles[active],recipe=recipe,limits=limits,
                expected_sources=request['collection_sources'])
            results[active]=result
            need(result.manifest['interact_attempts']==result.manifest['interact_returns']==EVENTS[active]
                 and result.manifest['audit']['reference_complete'],'actual complete role/reference support')
            completed[active]=EVENTS[active]
            write(active+'.collection.json',result.manifest);left()
        active=None;phase[0]='publish'
        publication=publish_research_corpus(plan,results,corpus_id=CORPUS_ID,expected_sources=request['collection_sources'],
            expected_protocol_sha256=PROTOCOL,limits=CorpusPublicationLimits(LIMITS['max_file_bytes'],LIMITS['max_total_bytes'],
                LIMITS['max_oracle_bytes'],ShardLimits(8,84,840),left(),LIMITS['max_rss_bytes'],LIMITS['min_available_ram_bytes']))
        write('publication.json',publication.payload());left()
        phase[0]='public_reader'
        public=read_public_research_corpus(CORPUS_ID,expected_corpus_sha256=publication.corpus_sha256,
            expected_done_sha256=publication.done_sha256,
            limits=CorpusReadLimits(8*1024**2,16*1024**2,262144,8,84,840,min(15.,left())))
        left();need(public.plan==plan and len(public.bank.items)==84,'actual reader plan/bank')
        event_ids=set()
        coverage={}
        for role in ROLES:
            actual=public.role_data(role)
            need(actual.trajectories==tuple(sorted(results[role].trajectories,key=lambda t:t.learner_id))
                 and actual.reference_complete,'actual public restart/content exact')
            coverage[role]={}
            for trajectory in actual.trajectories:
                observations=trajectory.observations
                need(len(observations)==84 and {o.query.item_id for o in observations}==set(public.bank.item_ids),
                     'per learner exact84 references, no favorable subset')
                for rank,o in enumerate(observations):
                    need(o.query.source_row==ordinal[trajectory.learner_id]*1000000+rank+1
                         and o.query.timestamp==1767225600+(rank+1)*21600
                         and o.query.source_row not in event_ids,'stable global event address/time')
                    event_ids.add(o.query.source_row)
                coverage[role][trajectory.learner_id]=84
        phase[0]='postcheck';left()
        need(len(event_ids)==840 and sum(completed.values())==840 and not denied,'full population and no caught guard attempt')
        need(pins()==before and source_inventory()==request['collection_sources'],'source pre/post exact')
        need(hashlib.sha256(path.read_bytes()).hexdigest()==args.request_sha256,'request unchanged')
        write('worker_result.json',dict(status='GENUINE_ENGINEERING_CORPUS_PENDING_OUTER',owner=owner,
            request_sha256=args.request_sha256,source_before=before,source_after=pins(),
            reserved_teacher_attempts=840,interact_attempts=840,interact_returns=840,
            role_attempts=completed,final_events=0,model_calls=0,optimizer_calls=0,
            publication=publication.payload(),public_reader_identity=public.identity,
            coverage_per_learner=coverage,role_audits={role:public.role_data(role).audit for role in ROLES},
            class_counts={role:public.role_data(role).class_counts for role in ROLES},resources=resources,
            metadata=metadata,git_calls=git_calls,denied=denied,elapsed_seconds=time.perf_counter()-start,
            scope='ENGINEERING_INTEGRATION_ONLY_NOT_RESEARCH_FIT_OR_REPLACEMENT_CORPUS'))
        left();need(not denied,'final guard counters unchanged')
        return 0
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc))
        with (OUT/'failure.log').open('x',encoding='utf-8') as stream:traceback.print_exc(file=stream)
        receipt=getattr(exc,'receipt',None)
        # Only the native collector receipt contains active-role interact counts.
        if not isinstance(receipt,dict) or not {'interact_attempts','interact_returns'}<=set(receipt):receipt=None
        if active in completed:
            active=None;receipt=None  # The just-completed role has durable exact counters.
        write('failure.json',dict(status='FAILED_NO_ACCEPTED_ENGINEERING_CORPUS',error=error,
            accounting=failure_accounting(completed,active,receipt),active_receipt=receipt,
            publication=None if publication is None else publication.payload(),resources=resources,
            denied=denied,metadata=metadata,elapsed_seconds=time.perf_counter()-start,
            published_bytes_are_not_acceptance=True,automatic_retry=False))
        return 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True);parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    raise SystemExit(run(parser.parse_args()))
