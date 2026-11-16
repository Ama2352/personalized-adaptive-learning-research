"""Chuẩn bị nguồn calibration10 riêng, giữ frozen roles/refit90 vocabulary."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
ROLE_ROOT = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01'
CANONICAL = ROOT/'artifacts/bkt_baseline/derived/canonical'
ASSIGNMENTS = ROOT/'artifacts/bkt_baseline/splits/assignments.parquet'
CANONICAL_MANIFEST = ROOT/'artifacts/bkt_baseline/derived/manifest.json'
SPLIT_MANIFEST = ROOT/'artifacts/bkt_baseline/splits/manifest.json'
ENCODING = ROOT/'artifacts/akt/window-cache/full-refit90-20261114-01.encoding.json'
ENCODING_RECEIPT = ROOT/'artifacts/akt/window-cache/full-refit90-20261114-01.encoding.receipt.json'
SELECTED_MANIFEST = ROOT/'artifacts/akt/junyi-cohorts/outer4-selected-full-20261112-03/manifest.json'

SELECT_SQL = """SELECT c.user_id,c.exercise,c.time_done,c.source_row,c.correct,c.suggested
    FROM read_parquet($source,hive_partitioning=true) c
    JOIN requested_calibration_users u ON c.user_id=u.user_id"""
COPY_SQL = 'COPY ('+SELECT_SQL+' ORDER BY c.user_id,c.time_done,c.source_row) TO $destination (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 50000)'
COPY_ASSIGNMENTS_SQL = """COPY (SELECT user_id,CAST(fold AS INTEGER) fold,'development' AS "partition"
    FROM requested_calibration_users ORDER BY user_id)
    TO $destination (FORMAT PARQUET, COMPRESSION ZSTD)"""


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write_new(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(payload,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def owned(path,base):
    path=path.absolute()
    if path==base or not path.is_relative_to(base) or path.resolve()!=path:
        raise ValueError('Owned physical output path required')
    for ancestor in (path,*path.parents):
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():
            raise ValueError('Output alias rejected')
    return path


class Budget:
    def __init__(self,args,evidence,output):
        import psutil
        self.process=psutil.Process()
        self.args=args
        self.evidence=evidence
        self.output=output
        self.start=time.monotonic()
        self.peak_rss=0
        self.stop=threading.Event()
        self.thread=threading.Thread(target=self.watch,daemon=True)

    def watch(self):
        next_output_check=0.
        while not self.stop.wait(.1):
            rss=self.process.memory_info().rss
            self.peak_rss=max(self.peak_rss,rss)
            elapsed=time.monotonic()-self.start
            reason=None
            if rss>self.args.max_rss_mib*1024**2:
                reason='MAX_RSS'
            elif elapsed>self.args.max_seconds:
                reason='MAX_SECONDS'
            elif self.args.mode=='prepare' and elapsed>=next_output_check:
                next_output_check=elapsed+1.
                if self.output.exists() and sum(p.stat().st_size for p in self.output.glob('*') if p.is_file())>self.args.max_output_mib*1024**2:
                    reason='MAX_OUTPUT'
            if reason:
                try:
                    write_new(self.evidence/(self.args.mode+'-'+self.args.attempt+'-RESOURCE-FAILURE.json'),
                        dict(status='RESOURCE_STOP',reason=reason,rss_bytes=rss,elapsed_seconds=elapsed,
                             note_vi='Chỉ dừng chính process tiền xử lý. Output dở được giữ, chưa công bố complete.'))
                finally:
                    os._exit(124)

    def close(self):
        self.stop.set()
        self.thread.join()
        return dict(elapsed_seconds=time.monotonic()-self.start,sampled_peak_rss_bytes=self.peak_rss)


def register_inputs(con,requested,values):
    import pandas as pd
    con.register('requested_calibration_users',requested)
    con.register('refit_vocabulary',pd.DataFrame({'exercise':values}))


def count_population(con,source):
    selected='('+SELECT_SQL+')'
    result=con.execute("""SELECT COUNT(*) targets,COUNT(DISTINCT c.user_id) learners,
        COUNT(DISTINCT c.source_row) unique_source_rows,
        COUNT(*) FILTER(WHERE c.correct=1) positive_labels,
        COUNT(*) FILTER(WHERE c.correct=0) negative_labels,
        COUNT(*) FILTER(WHERE c.correct NOT IN (0,1) OR c.correct IS NULL OR c.suggested NOT IN (0,1)
            OR c.suggested IS NULL OR c.source_row<=0 OR c.source_row IS NULL
            OR c.time_done<0 OR c.time_done IS NULL OR c.exercise IS NULL OR c.exercise='') invalid_rows,
        COUNT(*) FILTER(WHERE v.exercise IS NULL) oov_targets,
        COUNT(DISTINCT c.exercise) exercises
        FROM """+selected+" c LEFT JOIN refit_vocabulary v ON c.exercise=v.exercise",{'source':source}).fetchone()
    names=('targets','learners','unique_source_rows','positive_labels','negative_labels','invalid_rows','oov_targets','exercises')
    counts=dict(zip(names,map(int,result)))
    counts['max_learner_events']=int(con.execute('SELECT MAX(n) FROM (SELECT c.user_id,COUNT(*) n FROM '+selected+' c GROUP BY c.user_id)',{'source':source}).fetchone()[0])
    if counts['targets']!=counts['unique_source_rows'] or counts['invalid_rows']:
        raise ValueError('Invalid calibration targets or duplicated source_row')
    return counts


def frozen_inputs():
    from knowledge_tracing.akt.config import DataPaths
    from knowledge_tracing.akt.data import read_development_assignments
    from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView
    role_manifest=load(ROLE_ROOT/'manifest.json')
    if sha(ROLE_ROOT/'roles.json')!=role_manifest['outputs_sha256']['roles.json']:
        raise ValueError('Frozen roles changed')
    payload=load(ROLE_ROOT/'roles.json')
    for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
        payload[name]=tuple(payload[name])
    roles=JunyiResearchRoles(**payload)
    view=JunyiPhaseView(roles,'calibration_predict',roles.calibration_users,roles.identity)
    if roles.identity!=role_manifest['identity'] or len(view.users)!=15847 or not view.full_role_coverage:
        raise ValueError('Frozen full calibration10 role required')
    paths=DataPaths(CANONICAL,ASSIGNMENTS,CANONICAL_MANIFEST,SPLIT_MANIFEST)
    if sha(ASSIGNMENTS)!=role_manifest['source_sha256'][ASSIGNMENTS.relative_to(ROOT).as_posix()]:
        raise ValueError('Frozen assignments changed')
    assignments=read_development_assignments(paths)
    requested=assignments[assignments.user_id.isin(view.users)].copy()
    if len(requested)!=len(view.users) or not set(requested.user_id)==set(view.users) or not requested.fold.isin((0,1,2,3)).all():
        raise ValueError('Calibration learner Development/fold boundary mismatch')
    receipt=load(ENCODING_RECEIPT)
    if receipt['phase_scope']!='refit_union90' or sha(ENCODING)!=receipt['encoding_file_sha256']:
        raise ValueError('Frozen refit90 encoding required')
    vocabulary=load(ENCODING)['values']
    pins={path.relative_to(ROOT).as_posix():sha(path) for path in
          (ASSIGNMENTS,CANONICAL_MANIFEST,SPLIT_MANIFEST,ROLE_ROOT/'roles.json',ROLE_ROOT/'manifest.json',ENCODING,ENCODING_RECEIPT,SELECTED_MANIFEST)}
    return view,requested,vocabulary,pins,receipt


def run(args,evidence,output):
    import duckdb
    view,requested,values,pins,encoding_receipt=frozen_inputs()
    if args.mode=='population':
        from knowledge_tracing.akt.config import DataPaths
        from knowledge_tracing.akt.research_junyi_calibration import prepare_calibration_population
        prepared=load(evidence/'PREPARED.json')
        if sha(output/'manifest.json')!=prepared['manifest_sha256']:
            raise ValueError('Prepared calibration source manifest changed')
        manifest=load(output/'manifest.json')
        if (manifest['roles_identity']!=view.roles.identity or manifest['phase_identity']!=view.identity
                or manifest['encoding_identity']!=encoding_receipt['encoding_identity']):
            raise ValueError('Prepared calibration phase/encoding lineage mismatch')
        for name,pin in manifest['outputs'].items():
            if (output/name).stat().st_size!=pin['bytes'] or sha(output/name)!=pin['sha256']:
                raise ValueError('Prepared calibration source data changed')
        paths=DataPaths(**{key:ROOT/value for key,value in prepared['data_paths'].items()})
        population=prepare_calibration_population(paths,view,source_pins=prepared['source_pins'],
            max_targets=args.max_targets,max_learner_events=manifest['counts']['max_learner_events'])
        if population['targets']!=manifest['counts']['targets']:
            raise ValueError('Calibration population differs from source counts')
        for name,pin in manifest['outputs'].items():
            if sha(output/name)!=pin['sha256']:
                raise ValueError('Prepared calibration source changed during population audit')
        write_new(evidence/'POPULATION.json',population)
        return dict(status='FULL_CALIBRATION10_POPULATION_PREPARED',targets=population['targets'],
                    identity=population['identity'],phase_identity=view.identity)
    pattern=str(CANONICAL/'**/*.parquet')
    source_stats={p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns)
                  for p in sorted(CANONICAL.rglob('*.parquet'))}
    if len(source_stats)!=726:
        raise ValueError('Canonical source file scope changed')
    temporary=owned(ROOT/'artifacts/akt/tmp'/output.name,ROOT/'artifacts/akt/tmp')
    temporary.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(config=dict(memory_limit='256MB',threads='1',temp_directory=str(temporary),max_temp_directory_size='512MB'))
    try:
        register_inputs(con,requested,values)
        if args.mode=='count':
            counts=count_population(con,pattern)
            if counts['learners']!=15847 or not 0<counts['targets']<=args.max_targets:
                raise ValueError('Calibration population exceeds frozen learner/target scope')
            if any(dict(bytes=(ROOT/name).stat().st_size,mtime_ns=(ROOT/name).stat().st_mtime_ns)!=value
                   for name,value in source_stats.items()) or any(sha(ROOT/name)!=digest for name,digest in pins.items()):
                raise ValueError('Source metadata changed during count stage')
            result=dict(status='CALIBRATION10_SOURCE_COUNTS_VERIFIED',counts=counts,roles_identity=view.roles.identity,
                phase_identity=view.identity,refit_encoding_identity=encoding_receipt['encoding_identity'],
                source_pins=pins,canonical_files=len(source_stats),canonical_bytes=sum(x['bytes'] for x in source_stats.values()),
                holdout_or_outer_events_returned=False,train_or_selection_events_returned=False,
                labels_used_for_model_selection=False,source_stats=source_stats)
            write_new(evidence/'COUNT.json',result)
            return result
        count=load(evidence/'COUNT.json')
        if count['source_pins']!=pins or count['roles_identity']!=view.roles.identity or count['source_stats']!=source_stats:
            raise ValueError('Source differs from admitted count stage')
        if output.exists():
            raise ValueError('New calibration source output required')
        expected=load(SELECTED_MANIFEST)['source_sha256']
        for name in source_stats:
            if sha(ROOT/name)!=expected[name]:
                raise ValueError('Canonical source SHA differs from frozen source inventory')
        output.mkdir(parents=True,exist_ok=False)
        target=output/'canonical.parquet'
        con.execute(COPY_SQL,dict(source=pattern,destination=str(target)))
        assignment_target=output/'assignments.parquet'
        con.execute(COPY_ASSIGNMENTS_SQL,dict(destination=str(assignment_target)))
        actual=count_population(con,str(target))
        if actual!=count['counts']:
            raise ValueError('Prepared calibration source target/OOV coverage differs')
        for name in source_stats:
            if sha(ROOT/name)!=expected[name]:
                raise ValueError('Canonical source changed while copying')
        if any(sha(ROOT/name)!=digest for name,digest in pins.items()):
            raise ValueError('Frozen metadata changed while preparing source')
        manifest=dict(status='FULL_CALIBRATION10_SOURCE_PREPARED',purpose='JUNYI_REFIT90_RESPONSE_CALIBRATION_SOURCE',
            counts=actual,roles_identity=view.roles.identity,phase_identity=view.identity,
            encoding_identity=encoding_receipt['encoding_identity'],encoding_phase='refit_union90',
            source_sha256={**pins,**{name:expected[name] for name in source_stats}},
            outputs={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (target,assignment_target)},
            data_paths=dict(canonical=target.relative_to(ROOT).as_posix(),assignments=assignment_target.relative_to(ROOT).as_posix(),
                            canonical_manifest=(output/'manifest.json').relative_to(ROOT).as_posix(),split_manifest=SPLIT_MANIFEST.relative_to(ROOT).as_posix()),
            reader='iter_junyi_phase_learners, calibration_predict, full roles.calibration_users',
            graph_and_confidence_scope='Frozen TRAIN80 artifacts remain separate',
            train_events_included=False,selection_events_included=False,outer_events_included=False,holdout_events_included=False,
            neural_training_performed=False,calibration_fit_performed=False)
        write_new(output/'manifest.json',manifest)
        write_new(evidence/'PREPARED.json',dict(status=manifest['status'],output=output.relative_to(ROOT).as_posix(),
            manifest_sha256=sha(output/'manifest.json'),counts=actual,data_paths=manifest['data_paths'],
            source_pins=dict(canonical_manifest=sha(output/'manifest.json'),split_manifest=sha(SPLIT_MANIFEST))))
        return dict(status=manifest['status'],counts=actual,output=output.relative_to(ROOT).as_posix())
    finally:
        con.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('count','prepare','population'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,default=ROOT/'research_tracking/runs/junyi-calibration-data-20261117-01')
    parser.add_argument('--max-targets',type=int,required=True)
    parser.add_argument('--max-seconds',type=float,required=True)
    parser.add_argument('--max-rss-mib',type=int,required=True)
    parser.add_argument('--max-output-mib',type=int,default=160)
    parser.add_argument('--attempt',default='02')
    args=parser.parse_args()
    if (not 0<args.max_targets<=3000000 or not 0<args.max_seconds<=600
            or not 128<=args.max_rss_mib<=2048 or not 1<=args.max_output_mib<=512
            or not re.fullmatch(r'[a-zA-Z0-9_-]{1,24}',args.attempt)):
        raise ValueError('Explicit bounded preprocessing caps required')
    output=owned(args.output,ROOT/'artifacts/akt/junyi-cohorts')
    evidence=owned(args.evidence,ROOT/'research_tracking/runs')
    evidence.mkdir(parents=True,exist_ok=True)
    source_pin=sha(Path(__file__).resolve())
    write_new(evidence/(args.mode+'-'+args.attempt+'-SOURCE.json'),
              dict(script=Path(__file__).resolve().relative_to(ROOT).as_posix(),sha256=source_pin,
                   arguments={key:str(value) if isinstance(value,Path) else value for key,value in vars(args).items()},
                   scope_vi='Pin source hiện hành trước stage mới. Các stage count/prepare đầu có trước khi bổ sung nhánh population.'))
    budget=Budget(args,evidence,output)
    budget.thread.start()
    try:
        result=run(args,evidence,output)
    except BaseException as error:
        write_new(evidence/(args.mode+'-'+args.attempt+'-FAILURE.json'),dict(status='FAILED_PRESERVED',error_type=type(error).__name__,error=str(error)))
        raise
    finally:
        resource=budget.close()
        write_new(evidence/(args.mode+'-'+args.attempt+'-RESOURCES.json'),resource)
    if sha(Path(__file__).resolve())!=source_pin:
        raise ValueError('Preprocessor source changed during stage')
    print(json.dumps({key:value for key,value in result.items() if key not in ('source_pins','source_stats')},ensure_ascii=False))


if __name__=='__main__':
    main()
