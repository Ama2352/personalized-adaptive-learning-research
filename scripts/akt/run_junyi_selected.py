"""Entry A0 Junyi selected-only, mặc định chỉ kiểm metadata/config."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.config import ResearchCUDAExecutionProfile, load_config
from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache, run_a0_junyi_selected


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
    args = parser.parse_args()
    profile = ResearchCUDAExecutionProfile(**json.loads(args.cuda_profile.read_text(encoding='utf-8')))
    config = load_config(args.config,cuda_profile=profile)
    inputs = load_full_selected_cache(args.cache,args.roles,
        expected_manifest_sha256=args.cache_sha256,expected_roles_sha256=args.roles_sha256)
    print(json.dumps(dict(status='JUNYI_SELECTED_INPUTS_PREPARED',run_id=config.run_id,
        train_targets=inputs.train_targets,selection_targets=inputs.selection_targets,
        inputs_identity=inputs.identity,execution_requested=args.run)),flush=True)
    if args.run:
        result = run_a0_junyi_selected(config,profile,inputs,authorization_file=args.authorization,
            expected_authorization_sha256=args.authorization_sha256,runtime_report=args.runtime_report,
            lock_file=args.lock_file,encoding_file=args.encoding_file,expected_encoding_sha256=args.encoding_sha256,
            train_window_cache=args.train_window_cache,
            expected_train_window_manifest_sha256=args.train_window_manifest_sha256,
            resume_checkpoint=args.resume_checkpoint,expected_resume_sha256=args.resume_sha256,
            encoding_receipt=args.encoding_receipt,
            expected_encoding_receipt_sha256=args.encoding_receipt_sha256)
        print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
