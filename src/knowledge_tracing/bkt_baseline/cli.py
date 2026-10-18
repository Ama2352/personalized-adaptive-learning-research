"""Explicit phase commands for the Junyi standard BKT experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapter import verify_runtime
from .config import DEFAULT_ARTIFACTS, DEFAULT_CSV, preflight
from .pipeline import DataStore, run_cv, run_final_fit, run_pilot, run_test_once
from .preprocess import preprocess_csv
from .report import render_report
from .splits import create_split_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reproducible standard BKT baseline for Junyi")
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    commands = parser.add_subparsers(dest="command", required=True)
    preprocess = commands.add_parser("preprocess")
    preprocess.add_argument("--input-csv", type=Path, default=DEFAULT_CSV)
    commands.add_parser("split")
    commands.add_parser("verify-runtime")
    commands.add_parser("pilot")
    commands.add_parser("cv")
    commands.add_parser("final-fit")
    commands.add_parser("test")
    report = commands.add_parser("report")
    report.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.artifacts.resolve()

    if args.command == "verify-runtime":
        print(json.dumps(verify_runtime(), indent=2))
        return 0
    if args.command == "report":
        default_report = Path(__file__).resolve().parents[3] / "docs" / "bkt-baseline-artifact-report.md"
        destination = render_report(root, args.output or default_report)
        print(destination)
        return 0
    if args.command == "cv" and not (root / "pilot" / "pilot.json").is_file():
        raise RuntimeError("A completed Development-only pilot is required before cv")
    if args.command == "final-fit" and not (root / "cv" / "cv.json").is_file():
        raise RuntimeError("Completed five-fold CV is required before final-fit")
    if args.command == "test" and not (root / "final" / "final.json").is_file():
        raise RuntimeError("Completed fresh Development final-fit is required before test")

    resource = preflight(root, min_free_gb=12 if args.command == "preprocess" else 2)
    if args.command == "preprocess":
        result = preprocess_csv(args.input_csv, root / "derived", memory_limit="2GB")
    elif args.command == "split":
        if not (root / "derived" / "manifest.json").is_file():
            raise RuntimeError("preprocess must complete before split")
        result = create_split_manifest(root / "derived" / "canonical", root / "splits", seed=42)
    else:
        if not (root / "splits" / "manifest.json").is_file():
            raise RuntimeError("split must complete before model experiments")
        store = DataStore(root / "derived" / "canonical", root / "splits" / "assignments.parquet", root / "scratch")
        try:
            if args.command == "pilot":
                result = run_pilot(store, root / "pilot")
            elif args.command == "cv":
                selected = json.loads((root / "pilot" / "pilot.json").read_text(encoding="utf-8"))["selected_num_fits"]
                result = run_cv(store, root / "cv", num_fits=selected)
            elif args.command == "final-fit":
                selected = json.loads((root / "pilot" / "pilot.json").read_text(encoding="utf-8"))["selected_num_fits"]
                result = run_final_fit(store, root / "final", num_fits=selected)
            elif args.command == "test":
                result = run_test_once(store, root / "final", root / "test")
            else:
                raise AssertionError(args.command)
        finally:
            store.close()
    print(json.dumps({"command": args.command, "resources": resource, "output": str(root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
