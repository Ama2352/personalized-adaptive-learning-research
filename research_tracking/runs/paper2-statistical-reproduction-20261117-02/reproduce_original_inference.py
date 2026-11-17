"""Chạy lại đúng functions thống kê frozen trên seed outcomes, có CPU/RAM guard.

Không chạy cell sinh dữ liệu hoặc model. CLI yêu cầu output mới.
"""
import argparse
import ast
import csv
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT/'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
NOTEBOOK = PAPER/'source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb'
KEY = ('protocol','persona','proposed','baseline','metric')
FUNCTIONS = ('bootstrap_mean_ci','rank_biserial','holm_adjust','paired_tests')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def original_recipe():
    notebook=json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    configuration=ast.parse(''.join(notebook['cells'][3]['source']))
    assignments={node.targets[0].id:node.value for node in configuration.body
                 if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)}
    seed=ast.literal_eval(assignments['GLOBAL_SEED'])
    personas=ast.literal_eval(assignments['PERSONAS'])
    bootstrap=assignments['BOOTSTRAP_SAMPLES']
    if not isinstance(bootstrap,ast.IfExp) or ast.literal_eval(bootstrap.orelse)!=3000:
        raise ValueError('Frozen full bootstrap procedure changed')
    statistics=''.join(notebook['cells'][21]['source'])
    tree=ast.parse(statistics)
    definitions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS]
    if tuple(node.name for node in definitions)!=FUNCTIONS:
        raise ValueError('Frozen statistical function definitions changed')
    directions={node.targets[0].id:ast.literal_eval(node.value) for node in tree.body
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)
        and node.targets[0].id in ('replay_directions','closed_directions')}
    return dict(global_seed=seed,personas=personas,samples=3000,directions=directions,
        definitions=definitions,statistics_source=statistics,
        function_ast_sha256=hashlib.sha256(ast.dump(ast.Module(body=definitions,type_ignores=[])).encode()).hexdigest())


def seed_frame(path,model_column,pd):
    with path.open(encoding='utf-8',newline='') as stream:
        source=list(csv.DictReader(stream))
    expected={(persona,seed,model) for persona in ('PG','PY','PYH') for seed in range(1000,1050)
              for model in ('AdaptiveLMS','BKT','GAM-KT','Graph-GAM-KT')}
    keys=[(row['persona'],int(row['seed']),row[model_column]) for row in source]
    if len(keys)!=600 or len(set(keys))!=600 or set(keys)!=expected:
        raise ValueError('Exact frozen600seed grid required')
    rows=[]
    for row in source:
        converted={name:(value if name in ('persona',model_column) else int(value) if name=='seed' else float(value))
                   for name,value in row.items()}
        if any(not math.isfinite(value) for value in converted.values() if isinstance(value,float)):
            raise ValueError('Nonfinite source metric; do not silently drop rows')
        rows.append(converted)
    return pd.DataFrame(rows)


def worker(output):
    started=time.monotonic()
    recipe=original_recipe()
    print('IMPORTING_ORIGINAL_STATISTICAL_DEPENDENCIES',flush=True)
    import numpy as np
    import pandas as pd
    from scipy.stats import rankdata,wilcoxon
    namespace=dict(np=np,pd=pd,rankdata=rankdata,wilcoxon=wilcoxon,
        GLOBAL_SEED=recipe['global_seed'],PERSONAS=recipe['personas'],BOOTSTRAP_SAMPLES=recipe['samples'])
    module=ast.Module(body=recipe['definitions'],type_ignores=[])
    exec(compile(module,str(NOTEBOOK)+'#cell21','exec'),namespace)
    inputs=[NOTEBOOK,PAPER/'requirements.txt',PAPER/'environment/verification_environment.json',
        PAPER/'STATISTICAL_PROTOCOL.md',PAPER/'verify_claims.py']
    inputs += [PAPER/'frozen/simulation'/name for name in ('replay_metrics_by_seed.csv',
        'closed_loop_metrics_by_seed.csv','all_paired_tests_holm.csv','experiment_manifest.json')]
    pins={p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in inputs}
    computed=[]
    for protocol,name,column,direction_name in (
        ('fixed_replay','replay_metrics_by_seed.csv','model','replay_directions'),
        ('closed_loop','closed_loop_metrics_by_seed.csv','policy','closed_directions')):
        print('ORIGINAL_FUNCTION_START '+protocol,flush=True)
        frame=seed_frame(PAPER/'frozen/simulation'/name,column,pd)
        directions=recipe['directions'][direction_name]
        computed.extend(namespace['paired_tests'](frame,column,list(directions),directions,protocol).to_dict('records'))
        print('ORIGINAL_FUNCTION_COMPLETE '+protocol,flush=True)
    with (PAPER/'frozen/simulation/all_paired_tests_holm.csv').open(encoding='utf-8',newline='') as stream:
        frozen=list(csv.DictReader(stream))
    indexed={tuple(row[key] for key in KEY):row for row in computed}
    if len(computed)!=117 or len(indexed)!=117 or set(indexed)!={tuple(row[k] for k in KEY) for row in frozen}:
        raise ValueError('Original hypothesis population differs from frozen117')
    fields=('proposed_mean','baseline_mean','raw_delta','benefit_delta','bootstrap_ci_low','bootstrap_ci_high',
            'rank_biserial','wilcoxon_stat','p_value','p_holm')
    maximum={name:0. for name in fields}
    exact={name:0 for name in fields}
    near={name:0 for name in fields}
    comparisons=[]
    for row in frozen:
        key=tuple(row[name] for name in KEY)
        current=indexed[key]
        item={name:row[name] for name in KEY}
        for name in fields:
            original=float(row[name]); value=float(current[name]); error=abs(value-original)
            tolerance=5e-13 if name=='p_holm' else 1e-12
            maximum[name]=max(maximum[name],error)
            exact[name]+=int(value==original)
            near[name]+=int(error<=tolerance)
            item.update({name+'_frozen':original,name+'_recomputed':value,name+'_absolute_error':error,
                         name+'_within_original_verifier_tolerance':error<=tolerance})
        item['reject_holm_frozen']=row['reject_holm_05']=='True'
        item['reject_holm_recomputed']=bool(current['reject_holm_05'])
        comparisons.append(item)
    for name,rows in (('RECOMPUTED_117.csv',computed),('COMPARISON_117.csv',comparisons)):
        with (output/name).open('x',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    for p in inputs:
        if sha(p)!=pins[p.relative_to(ROOT).as_posix()]['sha256']:
            raise ValueError('Frozen source changed during computation')
    result=dict(status='ORIGINAL_STATISTICAL_FUNCTIONS_EXECUTED_COMPARISON_COMPLETE',hypotheses=117,
        versions={package:importlib.metadata.version(package) for package in ('numpy','pandas','scipy')},
        python=sys.version,global_seed=recipe['global_seed'],bootstrap_draws_per_hypothesis=3000,
        bootstrap_sample_unit='50 paired seeds within persona',families={'fixed_replay':45,'closed_loop':72},
        bootstrap_rng='numpy.default_rng(seed); one choice50(mean) per draw; per-hypothesis seed from original cell21',
        wilcoxon='scipy.stats.wilcoxon(delta,zero_method=wilcox,alternative=two-sided); original default method',
        csv_parse='stdlib float round-trip then DataFrame; no parser rounding/dropna introduced',
        function_ast_sha256=recipe['function_ast_sha256'],source_pins=pins,
        maximum_absolute_error=maximum,exact_equal_hypotheses=exact,
        within_original_verifier_tolerance=near,
        holm_rejection_mismatches=sum(row['reject_holm_frozen']!=row['reject_holm_recomputed'] for row in comparisons),
        worker_seconds=time.monotonic()-started,historical_library_versions_identified=False,
        limits_vi='Đã chạy lại thống kê từ seed outcomes bằng nguyên functions, không rerun simulator/model. '
        'Historical requirements không pin phiên bản. Mọi chênh lệch p/CI giữ nguyên, không đổi phương pháp để khớp.')
    with (output/'RESULT.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))


def guarded(output):
    import psutil
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'--output',str(output),'--worker']
    started=time.monotonic();peak=0;reason=None
    with (output/'worker.log').open('x',encoding='utf-8') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                try:
                    parent=psutil.Process(process.pid)
                    rss=sum(p.memory_info().rss for p in (parent,*parent.children(recursive=True)) if p.is_running())
                    peak=max(peak,rss)
                except psutil.NoSuchProcess:
                    continue
                if time.monotonic()-started>180:reason='wall180seconds'
                elif rss>256*1024**2:reason='rss256MiB'
                if reason:
                    for child in reversed(parent.children(recursive=True)):
                        try:child.kill()
                        except psutil.NoSuchProcess:pass
                    process.kill();process.wait();break
                time.sleep(.1)
        finally:
            if process.poll() is None:process.kill();process.wait()
    receipt=dict(status='WORKER_COMPLETE' if process.returncode==0 and reason is None else 'WORKER_STOPPED',
        returncode=process.returncode,stop_reason=reason,peak_process_tree_rss_bytes=peak,
        wall_seconds=time.monotonic()-started,max_rss_bytes=256*1024**2,max_wall_seconds=180)
    with (output/'RESOURCE_RECEIPT.json').open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2)
    print(json.dumps(receipt))
    if receipt['status']!='WORKER_COMPLETE':raise SystemExit(1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    output=args.output.resolve()
    allowed=(ROOT/'research_tracking/runs').resolve()
    relative=output.relative_to(allowed) if output.is_relative_to(allowed) else None
    if (relative is None or len(relative.parts)<2
            or not re.fullmatch(r'paper2-statistical-reproduction-\d{8}-\d{2}',relative.parts[0])):
        parser.error('New attempt directory inside a named Paper2 statistical-reproduction run required')
    if args.worker:
        worker(output)
    else:
        output.mkdir(parents=True,exist_ok=False)
        guarded(output)


if __name__=='__main__':main()
