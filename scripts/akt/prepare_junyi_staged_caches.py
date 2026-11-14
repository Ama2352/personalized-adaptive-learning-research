"""Chuẩn bị cache train/selection A2/A3 trên CPU trước lượt thuê GPU."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))


def main():
    from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
    from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding,iter_junyi_phase_learners
    from knowledge_tracing.akt.research_junyi_confidence_binding import load_binding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition,JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_graph_cache import build_graph_context_cache,GraphContextCache
    from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
    from knowledge_tracing.akt.research_junyi_selection_cache import (
        build_selection_cache,SelectionCacheSession,write_selection_cpu_admission)
    from knowledge_tracing.akt.research_junyi_engineering import file_sha
    from knowledge_tracing.akt.research_junyi_confidence_run import write_closed
    from knowledge_tracing.akt.types import UnseenTarget
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--selection-output',type=Path,required=True)
    parser.add_argument('--max-seconds',type=int,default=1800)
    parser.add_argument('--max-rss-mib',type=int,default=768)
    args=parser.parse_args()
    if not 1<=args.max_seconds<=3600 or not 128<=args.max_rss_mib<=2048:
        raise ValueError('Explicit bounded CPU resources required')
    started=time.monotonic()
    def local(name):
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or 'private' in path.parts:
            raise ValueError('Input must stay within project outside private area')
        return path
    output=args.output.resolve()
    if not output.is_relative_to(ROOT/'artifacts/akt/graph-context-cache'):
        raise ValueError('Use owned graph-context-cache output')
    selection_root=args.selection_output.resolve()
    if not selection_root.is_relative_to(ROOT/'artifacts/akt/window-cache'):
        raise ValueError('Use owned selection window-cache output')
    worker=json.loads(args.request.read_text(encoding='utf-8'))
    output.mkdir(parents=True,exist_ok=True)
    write_closed(output/'REQUEST.json',dict(worker=worker,selection_output=selection_root.relative_to(ROOT).as_posix()))
    data=worker['inputs']
    inputs=load_full_selected_cache(local(data['selected_cache_root']),local(data['roles_path']),
        expected_manifest_sha256=data['selected_cache_manifest_sha256'],expected_roles_sha256=data['roles_sha256'])
    encoding=load_prepared_junyi_encoding(local(data['encoding_file']),local(data['encoding_receipt']),
        view=inputs.train,source_data_sha256=inputs.source_identity,
        expected_file_sha256=data['encoding_sha256'],expected_receipt_sha256=data['encoding_receipt_sha256'])
    confidence=load_binding(local(worker['confidence_file']),expected_sha256=worker['confidence_sha256'])
    graph_file=local(worker['graph_file'])
    if file_sha(graph_file)!=worker['graph_sha256']:
        raise ValueError('Topology SHA mismatch')
    graph_payload=json.loads(graph_file.read_text())
    graph=PrerequisiteGraph.from_edges(graph_payload['nodes'],graph_payload['corrected_edges'])
    def remaining():
        value=args.max_seconds-(time.monotonic()-started)
        if value<=0:
            raise TimeoutError('CPU preparation tranche exhausted')
        return value
    if not (selection_root/'COMPLETE.json').exists():
        if selection_root.exists():
            raise ValueError('Incomplete selection output preserved; choose a new selection-output')
        build_selection_cache(selection_root,iter_junyi_phase_learners(inputs.paths,inputs.selection),
            view=inputs.selection,encoding=encoding,source_sha256=inputs.source_identity,
            expected_targets=inputs.selection_targets,max_seconds=remaining(),
            max_rss_bytes=args.max_rss_mib*1024**2)
    selection_manifest_sha=file_sha(selection_root/'manifest.json')
    selection=SelectionCacheSession(selection_root,view=inputs.selection,encoding=encoding,
        source_sha256=inputs.source_identity,expected_targets=inputs.selection_targets,
        expected_manifest_sha256=selection_manifest_sha)
    join_receipt=output/'selection-admission.json'
    window_receipt=output/'selection-window-admission.json'
    if not join_receipt.exists():
        if window_receipt.exists():
            raise ValueError('Interrupted admission files preserved; choose new output')
        write_selection_cpu_admission(selection,join_receipt,window_receipt)
    else:
        SelectionCacheSession(selection_root,view=inputs.selection,encoding=encoding,
            source_sha256=inputs.source_identity,expected_targets=inputs.selection_targets,
            expected_manifest_sha256=selection_manifest_sha,admission_file=join_receipt,
            expected_admission_sha256=file_sha(join_receipt),window_admission_file=window_receipt,
            expected_window_admission_sha256=file_sha(window_receipt))
    train=JunyiWindowCacheSession(local(data['train_window_cache']),inputs.train,encoding,
        inputs.source_identity,inputs.train_targets,data['train_window_manifest_sha256'],
        admission_receipt=local(worker['train_admission_file']),
        expected_admission_sha256=worker['train_admission_sha256'])
    def entry(path,digest):
        return dict(path=path.relative_to(ROOT).as_posix(),sha256=digest)
    for variant in ('A2','A3'):
        condition=JunyiGraphCondition(encoding,graph,worker['graph_sha256'],variant=variant,confidence=confidence)
        fields=dict(selection_windows=entry(selection_root,selection_manifest_sha),
            selection_join_admission=entry(join_receipt,file_sha(join_receipt)),
            selection_window_admission=entry(window_receipt,file_sha(window_receipt)))
        for scope,session,view,manifest_sha in (
            ('train',train,inputs.train,data['train_window_manifest_sha256']),
            ('selection',selection.windows,inputs.selection,selection.manifest['window_manifest_sha256'])):
            phase=JunyiGraphPhaseSession(condition,view)
            path=output/(variant.lower()+'-'+scope+'.sqlite')
            receipt_path=path.with_suffix('.receipt.json')
            if path.exists():
                receipt=json.loads(receipt_path.read_text())
            else:
                summary=dict(session._summary)
                receipt=build_graph_context_cache(path,(row for row in session.iter_windows() if type(row) is not UnseenTarget),
                    phase,dataset_sha256=inputs.source_identity,window_manifest_sha256=manifest_sha,
                    expected_windows=summary['windows'],expected_targets=summary['target_rows']-summary['unseen_targets'],
                    max_seconds=remaining(),max_rss_bytes=args.max_rss_mib*1024**2)
                write_closed(receipt_path,receipt)
            GraphContextCache.open(path,receipt['cache_sha256'],phase,
                dataset_sha256=inputs.source_identity,window_manifest_sha256=manifest_sha)
            fields[scope+'_graph']=entry(path,receipt['cache_sha256'])
        write_closed(output/(variant.lower()+'-cpu-prepared.json'),fields)
    print(json.dumps(dict(status='CPU_CACHES_COMPLETE',seconds=time.monotonic()-started,
                         output=str(output),gpu_used=False)))


if __name__=='__main__':
    main()
