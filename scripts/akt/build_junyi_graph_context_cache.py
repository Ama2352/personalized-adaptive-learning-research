"""Chuẩn bị cache A1 trên CPU từ window cache đã ghim, không train hoặc cấp GPU."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))

from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache, file_sha
from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
from knowledge_tracing.akt.research_junyi_graph_cache import build_graph_context_cache
from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
from knowledge_tracing.shared_kt import PrerequisiteGraph


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    args=parser.parse_args()
    request=json.loads(args.request.read_text(encoding='utf-8'))
    inputs=load_full_selected_cache(ROOT/request['selected_cache_root'],ROOT/request['roles_file'],
        expected_manifest_sha256=request['selected_manifest_sha256'],
        expected_roles_sha256=request['roles_sha256'])
    view, targets, origin = inputs.train, inputs.train_targets, None
    if request.get('phase_scope') == 'refit_union90':
        from knowledge_tracing.akt.research_junyi_refit import refit_view
        refit = refit_view(inputs)
        view, targets = refit.view, refit.targets
        origin = load_prepared_junyi_encoding(ROOT/request['encoding80_file'], ROOT/request['encoding80_receipt'],
            view=inputs.train, source_data_sha256=inputs.source_identity,
            expected_file_sha256=request['encoding80_sha256'],
            expected_receipt_sha256=request['encoding80_receipt_sha256'])
    encoding=load_prepared_junyi_encoding(ROOT/request['encoding_file'],ROOT/request['encoding_receipt'],
        view=view,source_data_sha256=inputs.source_identity,
        expected_file_sha256=request['encoding_sha256'],
        expected_receipt_sha256=request['encoding_receipt_sha256'])
    graph_path=ROOT/request['graph_file']
    if file_sha(graph_path)!=request['graph_sha256']:
        raise ValueError('Graph source SHA mismatch')
    topology=json.loads(graph_path.read_text(encoding='utf-8'))
    graph=PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges'])
    variant = request.get('variant', 'A1')
    confidence = None
    if variant in ('A2', 'A3'):
        from knowledge_tracing.akt.research_junyi_confidence_binding import load_binding
        confidence = load_binding(ROOT/request['confidence_file'], expected_sha256=request['confidence_sha256'])
    condition=JunyiGraphCondition(encoding,graph,request['graph_sha256'], variant=variant,
        confidence=confidence, train80_origin=origin)
    if origin is not None:
        from knowledge_tracing.akt.research_junyi_refit import validate_selected_lineage
        for name in ('epoch_plan', 'selected_index'):
            assert file_sha(ROOT/request[name]['path']) == request[name]['sha256']
        plan = json.loads((ROOT/request['epoch_plan']['path']).read_text())
        assert plan['selected_inputs_identity'] == inputs.identity and plan['roles_identity'] == view.roles.identity
        validate_selected_lineage(plan, variant, json.loads((ROOT/request['selected_index']['path']).read_text()), condition)
    session=JunyiWindowCacheSession(ROOT/request['train_window_cache'],view=view,
        encoding=encoding,source_data_sha256=inputs.source_identity,
        expected_target_rows=targets,
        expected_manifest_sha256=request['train_window_manifest_sha256'],
        admission_receipt=None if request.get('admission_file') is None else ROOT/request['admission_file'],
        expected_admission_sha256=request.get('admission_sha256'))
    receipt=build_graph_context_cache(ROOT/request['output_file'],session.iter_windows(),
        JunyiGraphPhaseSession(condition,view),dataset_sha256=inputs.source_identity,
        window_manifest_sha256=request['train_window_manifest_sha256'],
        expected_windows=session.strict_records_verified,expected_targets=targets,
        max_seconds=request['max_seconds'],max_rss_bytes=request['max_rss_bytes'])
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
