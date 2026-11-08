"""Worker corpus Development: phải qua owned gate trước native imports.

Không train, không final events. Cấu hình đã chốt không tự cấp quyền chạy;
request/source/owner/caps phải được reviewer chốt riêng trước dispatch.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
CONFIG = 'experiments/akt/configs/simulator-research-corpus01.json'
CONFIG_SHA = '8e7800482cea61a5f3ab66e4909de996fda57bcc059dd2751c2e4177dbfa263e'
PLAN_SHA = '7222b7c34051f41d99648421b940167c2da705efa604070957a23812273e02ed'
SELF = 'scripts/research/collect_development_corpus.py'
EXTRA_SOURCES = (SELF, 'scripts/research/windows_owned_worker.py',
    'src/knowledge_tracing/simulator_corpus_publisher.py',
    'src/knowledge_tracing/simulator_corpus_reader.py')
PAPER2_PACKAGE = 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
COLLECTION_SOURCES = (
    PAPER2_PACKAGE+'/source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb',
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
    'src/knowledge_tracing/simulator_research_collection.py',
    'src/knowledge_tracing/paper2_reference.py',
    'src/knowledge_tracing/simulator_collection.py',
    'src/knowledge_tracing/simulator_research_data.py',
    'src/knowledge_tracing/simulator_data.py',
    'src/knowledge_tracing/simulator_bridge.py',
    'src/knowledge_tracing/akt/resources.py',
    *(PAPER2_PACKAGE+'/data/simulator_inputs/'+name for name in
      ('nodes.csv','edges.csv','question_bank.csv','concept_to_chapter_map.csv')))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def safe_file(relative):
    require(type(relative) is str and '\\' not in relative and ':' not in relative,
            'relative POSIX path required')
    parts = Path(relative).parts
    require(parts and '..' not in parts and not Path(relative).is_absolute(), 'unsafe relative path')
    require(ROOT.resolve() == ROOT.absolute() and not ROOT.is_symlink()
            and not getattr(ROOT, 'is_junction', lambda: False)(), 'physical project root required')
    cursor = ROOT
    for part in parts:
        cursor = cursor/part
        require(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias')
    require(cursor.resolve().is_relative_to(ROOT.resolve()), 'outside project path')
    return cursor


def read_json(relative, expected_sha, max_bytes):
    require(type(expected_sha) is str and len(expected_sha) == 64
            and all(c in '0123456789abcdef' for c in expected_sha), 'explicit SHA required')
    path = safe_file(relative)
    require(path.is_file() and path.stat().st_size <= max_bytes, 'bounded regular JSON required')
    raw = path.read_bytes()
    require(len(raw) <= max_bytes and hashlib.sha256(raw).hexdigest() == expected_sha, 'request/config SHA mismatch')
    value = json.loads(raw)
    require(type(value) is dict, 'JSON object required')
    return value


def validate_request(relative, expected_sha):
    """Metadata-only: không import collector/model hoặc sinh dữ liệu."""
    require(relative.startswith('artifacts/akt/local-tests/'), 'reviewed local request only')
    request = read_json(relative, expected_sha, 128*1024)
    require(set(request) == {'schema_version', 'purpose', 'approval_reference', 'config_sha256',
        'plan_sha256', 'collection_sources', 'extra_sources', 'output_relative'}, 'closed request schema')
    require(type(request['schema_version']) is int and request['schema_version'] == 1
            and request['purpose'] == 'first_development_corpus_lifecycle_pilot'
            and type(request['approval_reference']) is str and request['approval_reference'].strip(),
            'explicit reviewed purpose/reference required')
    require(request['config_sha256'] == CONFIG_SHA and request['plan_sha256'] == PLAN_SHA, 'frozen profile only')
    config = read_json(CONFIG, CONFIG_SHA, 64*1024)
    require(config['expected_events'] == dict(train=10080, selection=1260, calibration=1260, total=12600, final=0)
            and config['role_counts'] == dict(train=48, selection=6, calibration=6), 'frozen counts mismatch')
    require(type(request['collection_sources']) is dict and set(request['collection_sources']) == set(COLLECTION_SOURCES),
            'exact thirteen allowlisted collection source paths required before source reads')
    require(type(request['extra_sources']) is dict and set(request['extra_sources']) == set(EXTRA_SOURCES), 'exact extra source inventory')
    for name, expected in (request['collection_sources'] | request['extra_sources']).items():
        require(type(expected) is str and len(expected) == 64
                and all(c in '0123456789abcdef' for c in expected), 'source SHA required')
        path = safe_file(name)
        require(path.is_file() and path.stat().st_size <= 2*1024**2, 'bounded source required')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'source drift: '+name)
    output = request['output_relative']
    require(type(output) is str and output.startswith('artifacts/akt/local-tests/development-corpus-20261108-01/'),
            'fixed-purpose local output required')
    require(not safe_file(output).exists(), 'exclusive worker output required')
    require(not safe_file('artifacts/simulator/corpora/'+config['corpus_id']).exists(),
            'fresh corpus destination required before collection')
    return request, config


def write_json(directory, name, value):
    with (directory/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def run(request_relative, request_sha, owner):
    start = time.perf_counter()
    require(type(owner) is dict and owner.get('status') == 'OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE'
            and type(owner.get('worker')) is dict and owner['worker'].get('pid') == os.getpid(),
            'owned gate receipt for current worker required; not research authorization')
    request, config = validate_request(request_relative, request_sha)
    output = safe_file(request['output_relative'])
    output.mkdir(parents=True, exist_ok=False)
    # Reserve toàn operation trước imports/native; hardkill không được ghi0calls.
    write_json(output, 'reservation.json', dict(status='RESERVED_NOT_ACTUAL_COUNTS',
        max_teacher_attempts=12600, actual_attempts=None, no_automatic_retry=True,
        request_sha256=request_sha, owner=owner, purpose=request['purpose']))
    results = {}; active_role = None; publication = None; failure = None
    try:
        sys.path.insert(0, str(ROOT/'src'))
        from knowledge_tracing.akt.resources import memory_snapshot
        global_limits = config['global_limits']
        def left():
            remaining = global_limits['max_wall_seconds']-(time.perf_counter()-start)
            require(math.isfinite(remaining) and remaining > 0, 'whole-operation wall cap')
            sample = memory_snapshot()
            rss = sample['process_rss_bytes']; peak = sample['process_peak_rss_bytes']
            available = sample['system_available_ram_bytes']
            require(type(rss) is int and rss >= 0 and type(available) is int and available >= 0
                    and (peak is None or type(peak) is int and peak >= 0), 'valid memory telemetry required')
            require(max(rss,peak or 0) <= global_limits['max_rss_bytes'], 'whole-operation RSS/peak cap')
            require(available >= global_limits['min_available_ram_bytes'], 'whole-operation free-RAM floor')
            remaining = global_limits['max_wall_seconds']-(time.perf_counter()-start)
            require(remaining > 0, 'wall cap after telemetry')
            return remaining
        left()  # Trước NumPy/pandas/native source imports.
        from knowledge_tracing.simulator_research_data import ResearchSplitPlan, ShardLimits
        from knowledge_tracing.simulator_research_collection import (
            ResearchCollectionRecipe, ResearchCollectionLimits,
            collect_research_role, source_inventory)
        from knowledge_tracing.simulator_corpus_publisher import (
            CorpusPublicationLimits, publish_research_corpus)
        from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus
        left()
        plan = ResearchSplitPlan(**config['plan_recipe'])
        require(plan.identity == PLAN_SHA and source_inventory() == request['collection_sources'], 'actual source/plan mismatch')
        recipe = ResearchCollectionRecipe(**config['collection_recipe'])
        write_json(output, 'plan.json', plan.manifest())
        profiles = {role: {a.learner_id: ('PG','PY','PYH')[i%3]
                    for i,a in enumerate(plan.split_plan.assignments(role))}
                    for role in config['generated_roles']}
        write_json(output, 'profiles.json', profiles)
        for active_role in config['generated_roles']:
            count = config['role_counts'][active_role]
            limits = ResearchCollectionLimits(count, 210, count*210, left(),
                global_limits['max_rss_bytes'], global_limits['min_available_ram_bytes'])
            result = collect_research_role(plan, role=active_role, profiles=profiles[active_role],
                recipe=recipe, limits=limits, expected_sources=request['collection_sources'])
            results[active_role] = result
            require(result.manifest['interact_attempts'] == count*210
                    and result.manifest['interact_returns'] == count*210, 'actual role counts mismatch')
            write_json(output, active_role+'.collection.json', result.manifest)
            require(result.manifest['audit']['reference_complete'], 'missing reference support in role '+active_role)
            left()
        active_role = None
        p = config['publication_limits']
        limits = CorpusPublicationLimits(p['max_file_bytes'], p['max_total_bytes'], p['max_oracle_bytes'],
            ShardLimits(48,210,12600), min(p['max_wall_seconds'],left()),
            global_limits['max_rss_bytes'], global_limits['min_available_ram_bytes'])
        publication = publish_research_corpus(plan, results, corpus_id=config['corpus_id'],
            expected_sources=request['collection_sources'], expected_protocol_sha256=plan.protocol_sha256, limits=limits)
        write_json(output,'publication.json',publication.payload())
        public = read_public_research_corpus(config['corpus_id'], expected_corpus_sha256=publication.corpus_sha256,
            expected_done_sha256=publication.done_sha256,
            limits=CorpusReadLimits(p['max_file_bytes'],p['max_total_bytes'],256*1024,48,210,12600,min(20.,left())))
        left()  # Reader dùng byte/wall caps; memory phải kiểm ở worker toàn operation.
        require(public.plan == plan, 'restart plan mismatch')
        for role in config['generated_roles']:
            actual = public.role_data(role)
            require(actual.trajectories == tuple(sorted(results[role].trajectories,key=lambda t:t.learner_id))
                    and actual.reference_complete, 'public restart/content mismatch')
        require(source_inventory() == request['collection_sources'], 'source drift after collection')
        for name, expected in request['extra_sources'].items():
            require(hashlib.sha256(safe_file(name).read_bytes()).hexdigest() == expected, 'extra source drift')
        left()
        write_json(output,'worker_result.json',dict(status='WORKER_COMPLETE_PENDING_OUTER_ACCEPTANCE',
            request_sha256=request_sha,config_sha256=CONFIG_SHA,plan_sha256=PLAN_SHA,owner=owner,
            interact_attempts=sum(r.manifest['interact_attempts'] for r in results.values()),
            interact_returns=sum(r.manifest['interact_returns'] for r in results.values()),
            publication=publication.payload(),public_reader_identity=public.identity,
            public_input_bytes=public.input_bytes,role_audits={r:public.role_data(r).audit for r in config['generated_roles']},
            class_counts={r:public.role_data(r).class_counts for r in config['generated_roles']},
            elapsed_seconds=time.perf_counter()-start,outer_acceptance_required=True,
            model_calls=0,final_events=0,modal_spend_usd=0))
        left()
        return 0
    except Exception as error:
        failure = getattr(error, 'receipt', None)
        with (output/'failure.log').open('x',encoding='utf-8') as stream:
            traceback.print_exc(file=stream)
        write_json(output,'failure.json',dict(status='FAILED_NO_USABLE_CORPUS_ACCEPTANCE',
            type=type(error).__name__,message=str(error),active_role=active_role,
            reserved_teacher_attempts=12600,completed_role_attempts=sum(r.manifest['interact_attempts'] for r in results.values()),
            active_role_receipt=failure,elapsed_seconds=time.perf_counter()-start,
            published_but_not_accepted=None if publication is None else publication.payload(),
            automatic_retry=False,original_work_not_rolled_back=True))
        return 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True)
    parser.add_argument('--request-sha256',required=True)
    args=parser.parse_args()
    from windows_owned_worker import worker_gate
    owner=worker_gate()  # Không native/model imports trước dòng này.
    return run(args.request,args.request_sha256,owner)


if __name__=='__main__':
    raise SystemExit(main())
