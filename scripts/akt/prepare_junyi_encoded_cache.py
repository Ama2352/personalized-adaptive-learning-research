"""Chuẩn bị encoding TRAIN80 và cache windows trước GPU, chỉ tiền xử lý CPU."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.encoding import save_encoding
from knowledge_tracing.akt.research_junyi_data import (fit_junyi_research_encoding,
    iter_junyi_research_windows,load_prepared_junyi_encoding)
from knowledge_tracing.akt.research_junyi_engineering import write_json,file_sha
from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
from knowledge_tracing.akt.research_junyi_window_cache import build_junyi_window_cache


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('cache','roles','output','encoding-output','receipt'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--cache-sha256',required=True)
    parser.add_argument('--roles-sha256',required=True)
    parser.add_argument('--encoding-input',type=Path)
    parser.add_argument('--encoding-input-sha256')
    parser.add_argument('--encoding-input-receipt',type=Path)
    parser.add_argument('--encoding-input-receipt-sha256')
    args=parser.parse_args()
    base=(ROOT/'artifacts/akt/window-cache').resolve()
    if (args.encoding_output.resolve().parent!=base or args.encoding_output.exists()
            or not args.receipt.resolve().is_relative_to((ROOT/'research_tracking/runs').resolve())):
        raise ValueError('Owned exclusive encoding output and run receipt required')
    started=time.monotonic()
    inputs=load_full_selected_cache(args.cache,args.roles,expected_manifest_sha256=args.cache_sha256,
                                   expected_roles_sha256=args.roles_sha256)
    source_before=dict(cache=file_sha(args.cache/'manifest.json'),roles=file_sha(args.roles))
    temporary=ROOT/'artifacts/akt/tmp'/args.output.name
    options=dict(temp_dir=temporary)
    if (args.encoding_input is None)!=(args.encoding_input_sha256 is None):
        raise ValueError('Pinned existing encoding required together')
    if args.encoding_input is None:
        encoding=fit_junyi_research_encoding(inputs.paths,inputs.train,**options)
    else:
        if args.encoding_input_receipt is None or args.encoding_input_receipt_sha256 is None:
            raise ValueError('Existing encoding requires original fit lineage receipt')
        encoding=load_prepared_junyi_encoding(args.encoding_input,args.encoding_input_receipt,view=inputs.train,
            source_data_sha256=inputs.source_identity,expected_file_sha256=args.encoding_input_sha256,
            expected_receipt_sha256=args.encoding_input_receipt_sha256)
    print(json.dumps(dict(status='FULL_TRAIN80_ENCODING_FITTED',items=len(encoding.native.vocabulary.values),
                         encoding_identity=encoding.identity,encoding_reused=args.encoding_input is not None,
                         seconds=time.monotonic()-started)),flush=True)
    base.mkdir(parents=True,exist_ok=True)
    encoding_sha=save_encoding(encoding.native,args.encoding_output)
    write_json(args.encoding_output.with_suffix('.receipt.json'),dict(status='JUNYI_TRAIN_ENCODING_FITTED',
        fit_view_identity=inputs.train.identity,phase_scope=inputs.train.scope,
        source_data_sha256=inputs.source_identity,encoding_file_sha256=encoding_sha,
        encoding_identity=encoding.identity))
    result=build_junyi_window_cache(args.output,
        iter_junyi_research_windows(inputs.paths,inputs.train,encoding,**options),
        view=inputs.train,encoding=encoding,source_data_sha256=inputs.source_identity,
        expected_target_rows=inputs.train_targets)
    if source_before!=dict(cache=file_sha(args.cache/'manifest.json'),roles=file_sha(args.roles)):
        raise ValueError('Source changed during preprocessing')
    write_json(args.receipt,dict(status='FULL_JUNYI_TRAIN80_WINDOWS_PREPARED_NOT_TRAINED',cache=result,
        encoding_file=str(args.encoding_output.relative_to(ROOT)),encoding_sha256=encoding_sha,
        encoding_identity=encoding.identity,source_identity=inputs.source_identity,
        seconds=time.monotonic()-started,neural_training_performed=False))
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
