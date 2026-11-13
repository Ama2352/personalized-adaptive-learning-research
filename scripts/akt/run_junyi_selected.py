"""Entry A0–A3 expert Junyi selected-only, mặc định chỉ kiểm metadata/config."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.config import ResearchCUDAExecutionProfile, load_config
from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache, run_junyi_selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config','cuda-profile','cache','roles','authorization','runtime-report','lock-file'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('cache-sha256','roles-sha256','authorization-sha256'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--encoding-file',type=Path)
    parser.add_argument('--encoding-sha256')
    parser.add_argument('--encoding-receipt',type=Path)
    parser.add_argument('--encoding-receipt-sha256')
    parser.add_argument('--train-window-cache',type=Path)
    parser.add_argument('--train-window-manifest-sha256')
    parser.add_argument('--resume-checkpoint',type=Path)
    parser.add_argument('--resume-sha256')
    parser.add_argument('--comparison-reference',type=Path)
    parser.add_argument('--comparison-reference-sha256')
    parser.add_argument('--validation-batch-size',type=int)
    parser.add_argument('--variant',choices=('A0','A1','A2','A3'),default='A0')
    parser.add_argument('--graph-file',type=Path)
    parser.add_argument('--graph-sha256')
    parser.add_argument('--confidence-file',type=Path)
    parser.add_argument('--confidence-sha256')
    parser.add_argument('--train-cache-admission-receipt',type=Path)
    parser.add_argument('--train-cache-admission-sha256')
    args = parser.parse_args()
    profile = ResearchCUDAExecutionProfile(**json.loads(args.cuda_profile.read_text(encoding='utf-8')))
    config = load_config(args.config,cuda_profile=profile)
    inputs = load_full_selected_cache(args.cache,args.roles,
        expected_manifest_sha256=args.cache_sha256,expected_roles_sha256=args.roles_sha256)
    condition=None
    if args.variant=='A0':
        if any(value is not None for value in (args.graph_file,args.graph_sha256,args.confidence_file,args.confidence_sha256)):
            parser.error('A0 requires graph-free inputs')
    else:
        if any(value is None for value in (args.graph_file,args.graph_sha256,args.encoding_file,
                                          args.encoding_receipt,args.encoding_sha256,args.encoding_receipt_sha256)):
            parser.error('Graph variants require pinned topology and prepared TRAIN80 encoding')
        from knowledge_tracing.akt.research_junyi_engineering import file_sha
        from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
        from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition
        from knowledge_tracing.akt.research_junyi_confidence_binding import load_binding
        from knowledge_tracing.shared_kt import PrerequisiteGraph
        if file_sha(args.graph_file)!=args.graph_sha256:
            parser.error('Graph SHA256 mismatch')
        encoding=load_prepared_junyi_encoding(args.encoding_file,args.encoding_receipt,
            view=inputs.train,source_data_sha256=inputs.source_identity,
            expected_file_sha256=args.encoding_sha256,expected_receipt_sha256=args.encoding_receipt_sha256)
        if args.variant=='A1' and (args.confidence_file is not None or args.confidence_sha256 is not None):
            parser.error('A1 uses fixed confidence')
        if args.variant in ('A2','A3') and (args.confidence_file is None or args.confidence_sha256 is None):
            parser.error('A2/A3 require pinned fitted TRAIN80 confidence')
        confidence=None if args.variant=='A1' else load_binding(args.confidence_file,expected_sha256=args.confidence_sha256)
        topology=json.loads(args.graph_file.read_text(encoding='utf-8'))
        condition=JunyiGraphCondition(encoding,
            PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges']),args.graph_sha256,
            variant=args.variant,confidence=confidence)
    print(json.dumps(dict(status='JUNYI_SELECTED_INPUTS_PREPARED',run_id=config.run_id,
        train_targets=inputs.train_targets,selection_targets=inputs.selection_targets,
        inputs_identity=inputs.identity,variant=args.variant,execution_requested=args.run)),flush=True)
    if args.run:
        result = run_junyi_selected(config,profile,inputs,authorization_file=args.authorization,
            expected_authorization_sha256=args.authorization_sha256,runtime_report=args.runtime_report,
            lock_file=args.lock_file,encoding_file=args.encoding_file,expected_encoding_sha256=args.encoding_sha256,
            train_window_cache=args.train_window_cache,
            expected_train_window_manifest_sha256=args.train_window_manifest_sha256,
            resume_checkpoint=args.resume_checkpoint,expected_resume_sha256=args.resume_sha256,
            encoding_receipt=args.encoding_receipt,
            expected_encoding_receipt_sha256=args.encoding_receipt_sha256,
            comparison_reference_file=args.comparison_reference,
            expected_comparison_reference_sha256=args.comparison_reference_sha256,
            validation_batch_size=args.validation_batch_size,graph_condition=condition,
            train_cache_admission_receipt=args.train_cache_admission_receipt,
            expected_train_cache_admission_sha256=args.train_cache_admission_sha256)
        print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
