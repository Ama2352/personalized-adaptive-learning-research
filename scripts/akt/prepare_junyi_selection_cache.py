"""Chuẩn bị selection window/metadata trên CPU, không train hoặc cấp GPU."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding,iter_junyi_phase_learners
from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
from knowledge_tracing.akt.research_junyi_selection_cache import build_selection_cache


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    args=parser.parse_args()
    request=json.loads(args.request.read_text(encoding='utf-8'))
    inputs=load_full_selected_cache(ROOT/request['selected_cache_root'],ROOT/request['roles_file'],
        expected_manifest_sha256=request['selected_manifest_sha256'],expected_roles_sha256=request['roles_sha256'])
    encoding=load_prepared_junyi_encoding(ROOT/request['encoding_file'],ROOT/request['encoding_receipt'],
        view=inputs.train,source_data_sha256=inputs.source_identity,
        expected_file_sha256=request['encoding_sha256'],expected_receipt_sha256=request['encoding_receipt_sha256'])
    receipt=build_selection_cache(ROOT/request['output_root'],
        iter_junyi_phase_learners(inputs.paths,inputs.selection,temp_dir=ROOT/'artifacts/akt/tmp/selection-cache'),
        view=inputs.selection,encoding=encoding,source_sha256=inputs.source_identity,
        expected_targets=inputs.selection_targets,max_seconds=request['max_seconds'],max_rss_bytes=request['max_rss_bytes'])
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
