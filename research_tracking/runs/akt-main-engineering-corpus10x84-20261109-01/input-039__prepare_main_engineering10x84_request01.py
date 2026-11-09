"""ROOT-only metadata builder; không dispatch hoặc tạo corpus/auth/model."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
FREEZE = PREP/'main_engineering10x84_source_freeze01.json'
FREEZE_SHA = '6f44f24f573f4c668eb3a34af87f189ad7d4f1e7db83afd987cfd0d1f43c7b8c'
WORKER = PREP/'collect_main_engineering10x84_01.py'
WORKER_SHA = '121386eef563fb88ac04e7c66849f169cf8de548fffaaee8c38be6c86f045e77'
OUTPUT = PREP/'main_engineering10x84_request01.ROOT.json'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts, 'fixed project path')
    cursor = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            cursor /= part
        need(not cursor.is_symlink() and not cursor.is_junction(), 'physical source/output parent')
    return path


def payload(path, cap=2*1024**2):
    physical(path)
    need(path.is_file() and path.stat().st_size <= cap, 'bounded regular metadata/source')
    raw = path.read_bytes()
    need(len(raw) <= cap, 'bounded readback')
    return raw


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def row_map(rows):
    need(type(rows) is list and rows, 'source-freeze rowlist')
    result = {}
    for row in rows:
        need(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'}, 'exact freeze source row')
        name = row['path']
        need(type(name) is str and name not in result and '\\' not in name and ':' not in name
             and not Path(name).is_absolute() and '..' not in Path(name).parts, 'unique relative POSIX path')
        raw = payload(ROOT/name)
        need(type(row['bytes']) is int and row['bytes'] == len(raw) and digest(raw) == row['sha256'], 'actual pinned source bytes')
        result[name] = row['sha256']
    return result


def main(args):
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    need(args.builder_sha256 == digest(payload(SELF)) and args.freeze_sha256 == FREEZE_SHA, 'external ROOT builder/freeze pins')
    need(type(args.approval_reference) is str and 0 < len(args.approval_reference.strip()) <= 256, 'ROOT operation reference')
    need(not OUTPUT.exists(), 'exclusive future request, no overwrite')
    freeze_raw = payload(FREEZE)
    need(digest(freeze_raw) == args.freeze_sha256, 'exact source-freeze payload')
    freeze = json.loads(freeze_raw)
    before = row_map(freeze['collection_sources'])
    dependencies = row_map(freeze['extra_dependencies'])
    owned = row_map(freeze['owned_sources'])
    need(digest(payload(WORKER)) == WORKER_SHA, 'reviewed worker definitions')
    spec = importlib.util.spec_from_file_location('reviewed_engineering10x84_metadata_definitions', WORKER)
    worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
    need(set(before) == set(worker.COLLECTION_SOURCES) and len(before) == 13, 'exact native collection13')
    extras = dict(dependencies)
    for name in (WORKER.relative_to(ROOT).as_posix(), (PREP/'run_main_engineering10x84_01.py').relative_to(ROOT).as_posix()):
        need(name in owned and name not in extras, 'unique controller row from owned_sources')
        extras[name] = owned[name]
    need(set(extras) == set(worker.EXTRA_SOURCES) and len(extras) == 6 and not set(extras) & set(before), 'exact disjoint extra6')
    prerequisites = row_map(freeze['prerequisites'])
    need(prerequisites == {worker.RUNTIME: worker.RUNTIME_SHA, worker.INDEX: worker.INDEX_SHA}, 'actual explicit prerequisite pins')
    request = dict(schema_version=1, purpose='GENUINE_10X84_ENGINEERING_CORPUS_NOT_RESEARCH_ALLOCATION',
        approval_reference=args.approval_reference, plan_recipe=copy.deepcopy(worker.PLAN),
        collection_recipe=copy.deepcopy(worker.RECIPE), profile='PG', generated_roles=list(worker.ROLES),
        limits=copy.deepcopy(worker.LIMITS), collection_sources=before, extra_sources=extras,
        runtime_report=worker.RUNTIME, runtime_sha256=worker.RUNTIME_SHA,
        gate_index=worker.INDEX, gate_index_sha256=worker.INDEX_SHA)
    need(worker.validate_contract(request) is request, 'actual closed14 contract validation only')
    need(not worker.OUT.exists() and not worker.OWNED.exists() and not worker.CORPUS.exists(), 'fresh operation/corpus paths')
    wire = (json.dumps(request, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    need(len(wire) <= 128*1024, 'request128KiB cap')
    # Recheck exact sources after constructing the wire, without teacher/corpus reads.
    checked = before | dependencies | owned | prerequisites
    need(all(digest(payload(ROOT/name)) == pin for name, pin in checked.items())
         and digest(payload(FREEZE)) == args.freeze_sha256 and digest(payload(SELF)) == args.builder_sha256,
         'all source/runtime/index/freeze posthashes')
    if args.write_reviewed_request:
        need(args.review_reference and args.review_reference.strip(), 'ROOT explicit materialization review')
        physical(OUTPUT)
        with OUTPUT.open('xb') as stream:
            stream.write(wire); stream.flush(); os.fsync(stream.fileno())
        need(payload(OUTPUT, 128*1024) == wire, 'exclusive request readback exact')
    print(json.dumps(dict(status='CREATED_REVIEWED_METADATA_REQUEST_NOT_DISPATCH_AUTHORITY' if args.write_reviewed_request
                          else 'CHECKED_METADATA_ONLY_NO_REQUEST_WRITTEN',
        request_path=OUTPUT.relative_to(ROOT).as_posix(), request_sha256=digest(wire), request_bytes=len(wire),
        collection_sources=13, extra_sources=6, generated_events_reservation=840,
        native_or_model_calls=0, actual_request_written=args.write_reviewed_request, dispatch_authority=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--builder-sha256', required=True); parser.add_argument('--freeze-sha256', required=True)
    parser.add_argument('--approval-reference', required=True)
    parser.add_argument('--write-reviewed-request', action='store_true'); parser.add_argument('--review-reference')
    main(parser.parse_args())
