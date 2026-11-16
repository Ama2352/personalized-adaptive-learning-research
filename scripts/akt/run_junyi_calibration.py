"""Kiểm metadata và probe CPU nhỏ; real export/fit cần cloud-first artifact sink."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))


def _need(ok,message):
    if not ok:
        raise ValueError(message)


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def _owned(name):
    path=Path(name)
    _need(not path.is_absolute() and '..' not in path.parts and 'private' not in path.parts,
          'owned public project path required')
    path=(ROOT/path).resolve()
    _need(path.is_relative_to(ROOT.resolve()),'input outside project')
    return path


def _pinned(entry):
    path=_owned(entry['path'])
    _need(_sha(path)==entry['sha256'],'pinned input changed: '+entry['path'])
    return path


def _output(request):
    output=_owned(request['output'])
    _need(output.parent==(ROOT/'experiments/akt/results').resolve()
          and output.name==request['run_id'],'unique owned inference output required')
    return output


def _assets(request):
    from knowledge_tracing.akt.research_junyi_inference import inspect_cpu_refit_export,JunyiCPUInferenceBudget
    index=_pinned(request['model_index'])
    return inspect_cpu_refit_export(index.parent,expected_index_sha256=request['model_index']['sha256'],
        output=_output(request),run_id=request['run_id'],budget=JunyiCPUInferenceBudget(**request['budget']))


def _calibration_data(request,assets):
    from knowledge_tracing.akt.config import DataPaths
    prepared=json.loads(_pinned(request['data_receipt']).read_text(encoding='utf-8'))
    _need(prepared['status']=='FULL_CALIBRATION10_SOURCE_PREPARED','prepared calibration-only source required')
    paths=DataPaths(**{name:_owned(value) for name,value in prepared['data_paths'].items()})
    _need(_sha(paths.canonical_manifest)==prepared['manifest_sha256'],'calibration cache manifest changed')
    manifest=json.loads(paths.canonical_manifest.read_text(encoding='utf-8'))
    _need(manifest['purpose']=='JUNYI_REFIT90_RESPONSE_CALIBRATION_SOURCE'
          and manifest['roles_identity']==assets['calibration'].roles.identity
          and manifest['phase_identity']==assets['calibration'].identity
          and manifest['encoding_identity']==assets['encoding'].identity
          and all(manifest[key] is False for key in ('train_events_included','selection_events_included',
              'outer_events_included','holdout_events_included')),'calibration source phase/role mismatch')
    for name in ('canonical','assignments'):
        pin=manifest['outputs'][getattr(paths,name).name]
        _need(getattr(paths,name).stat().st_size==pin['bytes'] and _sha(getattr(paths,name))==pin['sha256'],
              'calibration cache data changed')
    _need(all(_sha(getattr(paths,name))==value for name,value in prepared['source_pins'].items()),
          'calibration source metadata pin mismatch')
    population=json.loads(_pinned(request['population']).read_text(encoding='utf-8'))
    counts=prepared['counts']
    budget=assets['budget']
    _need(population['targets']==counts['targets']<=budget.max_targets
          and counts['learners']<=budget.max_users and counts['max_learner_events']<=budget.max_learner_events,
          'calibration source exceeds declared workload')
    return paths,prepared['source_pins'],population


def execute(request):
    """Local CLI chạy probe nhỏ; real export/fit chờ cloud-first artifact sink."""
    _need(request['operation']=='probe',
          'Full Junyi export/fit requires the cloud-first artifact sink; local execution is disabled')
    from knowledge_tracing.akt.prediction import _write_json_atomic
    from knowledge_tracing.akt.research_junyi_inference import probe_real_weights
    output=_output(request)
    _need('data_receipt' not in request and 'population' not in request,'technical probe uses synthetic events only')
    result=probe_real_weights(_assets(request),targets=request['synthetic_targets'])
    _write_json_atomic(output/'RESULT.json',result)
    return result


def _kill_worker(process):
    import psutil
    try:
        root=psutil.Process(process.pid)
        children=root.children(recursive=True)
        for child in reversed(children):
            try:child.kill()
            except psutil.NoSuchProcess:pass
        root.kill()
    except psutil.NoSuchProcess:
        pass
    process.wait()


def run_guarded(request,path,digest):
    """Parent nhẹ giám sát đúng process con của lượt này, có hard wall/RAM cap."""
    import psutil
    output=_output(request)
    _need(not output.exists(),'new CPU inference run directory required')
    budget=request['budget']
    _need(psutil.virtual_memory().available>=budget['min_available_ram_bytes'],
          'insufficient available RAM before worker startup')
    output.mkdir()
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'--request',str(path),
             '--request-sha256',digest,'--worker']
    started=time.monotonic()
    peak=0
    reason=None
    with (output/'worker-stdout.log').open('x',encoding='utf-8') as out, (output/'worker-stderr.log').open('x',encoding='utf-8') as err:
        process=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=err)
        try:
            while process.poll() is None:
                try:
                    parent=psutil.Process(process.pid)
                    processes=[parent,*parent.children(recursive=True)]
                    rss=sum(p.memory_info().rss for p in processes if p.is_running())
                    peak=max(peak,rss)
                except psutil.NoSuchProcess:
                    continue
                if time.monotonic()-started>budget['max_seconds']:
                    reason='wall_time_cap'
                elif rss>budget['max_rss_bytes']:
                    reason='worker_tree_rss_cap'
                elif psutil.virtual_memory().available<budget['min_available_ram_bytes']:
                    reason='system_available_ram_floor'
                if reason:
                    _kill_worker(process)
                    break
                time.sleep(.5)
        except BaseException:
            _kill_worker(process)
            raise
    result=dict(status='WORKER_COMPLETE' if process.returncode==0 and reason is None else 'WORKER_STOPPED',
        returncode=process.returncode,stop_reason=reason,wall_seconds=time.monotonic()-started,
        peak_worker_tree_rss_bytes=peak,request_sha256=digest)
    with (output/'PARENT_RECEIPT.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    _need(result['status']=='WORKER_COMPLETE','CPU worker stopped; inspect owned logs and receipt')
    return json.loads((output/'RESULT.json').read_text(encoding='utf-8'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--request-sha256')
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    _need(Path(sys.prefix).resolve()==(ROOT/'.venv').resolve(),'local CPU launcher requires repository .venv')
    request=json.loads(args.request.read_text(encoding='utf-8'))
    _need(request.get('schema')=='junyi-cpu-calibration-request-v1'
          and request.get('operation') in ('probe','export','fit'),'explicit CPU calibration operation required')
    digest=_sha(args.request)
    if not args.run and not args.worker:
        assets=_assets(request)
        if request['operation']!='probe' and 'data_receipt' in request:
            _calibration_data(request,assets)
        print(json.dumps(dict(status='CPU_CALIBRATION_METADATA_INSPECTED',operation=request['operation'],
            model=assets['index']['model'],encoding=assets['encoding'].identity,
            roles=assets['calibration'].roles.identity,request_sha256=digest)))
        return
    _need(digest==args.request_sha256,'pinned CPU execution request required')
    _need(request['operation']=='probe',
          'Full Junyi export/fit requires the cloud-first artifact sink; local execution is disabled')
    result=execute(request) if args.worker else run_guarded(request,args.request.resolve(),digest)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
