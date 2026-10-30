"""Command line entrypoint for the Development-only GAM-KT benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import PROJECT_ROOT, prepare_source_mapping, run_cv, run_pilot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Frozen-protocol Junyi GAM-KT Development benchmark")
    commands = parser.add_subparsers(dest="command", required=True)
    mapping = commands.add_parser("prepare-map", help="verify raw-to-canonical Development problem_type mapping")
    mapping.add_argument("--chunk-rows", type=int, default=100_000)
    pilot = commands.add_parser("pilot", help="run the bounded Development fold-0 pilot")
    pilot.add_argument("--users", type=int, default=2_000)
    pilot.add_argument("--chunk-rows", type=int, default=100_000)
    cv = commands.add_parser("cv", help="run frozen five-fold Development CV")
    cv.add_argument("--chunk-rows", type=int, default=100_000)
    cv.add_argument("--no-resume", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "prepare-map":
        result = prepare_source_mapping(chunk_rows=args.chunk_rows)
    elif args.command == "pilot":
        output = PROJECT_ROOT / "experiments/gam_kt/results/wsl_cpp/pilot"
        result = run_pilot(output, max_users=args.users, chunk_rows=args.chunk_rows)
    else:
        output = PROJECT_ROOT / "experiments/gam_kt/results/wsl_cpp/cv"
        if args.no_resume and output.exists() and any(output.iterdir()):
            raise FileExistsError(f"CV output is not empty: {output}")
        result = run_cv(output, resume=not args.no_resume, chunk_rows=args.chunk_rows)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
