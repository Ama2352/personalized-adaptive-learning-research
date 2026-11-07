"""Đóng hồ sơ Paper1 từ nguồn đã lưu; chỉ đọc source/PDF, không chạy simulator."""

from __future__ import annotations

import argparse
import ast
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


RUN_ID = "paper1-revision-audit-20261107-01"
PREFIX = "paper1_revision_reconciliation_20261107"
BUNDLED_PYTHON_PACKAGES = Path(
    r"C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1104-2876-0_26.1104.2876.0_x64__3k8sg7r9htsxt\dependencies\python\Lib\site-packages"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_fingerprint(notebook: dict) -> str:
    payload = [
        {"cell_type": cell["cell_type"], "source": "".join(cell.get("source", []))}
        for cell in notebook["cells"]
    ]
    return sha(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--bundle", type=Path)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    expected_python = root / ".venv/Scripts/python.exe"
    if Path(sys.executable).resolve() != expected_python.resolve():
        raise RuntimeError("Chỉ dùng Python .venv của repository")
    sys.path.insert(0, str(root / "src"))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

    destination = args.bundle or root / "research_tracking/runs" / RUN_ID
    if args.verify_only:
        result = verify_evidence_bundle(destination)
        print(json.dumps({"run_id": RUN_ID, **result, "q01_closed": False, "s01_approved": False}, ensure_ascii=False, indent=2))
        return

    report_md = root / "research_tracking/reports" / (PREFIX + ".md")
    report_json = report_md.with_suffix(".json")
    audit = json.loads(report_json.read_text(encoding="utf-8"))
    inventory = audit["input_inventory"]
    if len(inventory) != 33:
        raise ValueError("Phải giữ nguyên inventory 33 inputs của audit nguồn")
    core = audit["current_notebook"]["path"]
    pdf = audit["pdf"]["path"]
    required = [root / entry["path"] for entry in inventory]
    script = Path(__file__).resolve()
    helper = root / "src/knowledge_tracing/evidence.py"
    sources = list(dict.fromkeys([script, helper, report_md, report_json, *required]))
    note = """# Hồ sơ audit revision Paper1 — 07/11/2026

Đóng bằng `record_evidence_run` hiện có. Snapshot hai reports đã review, giữ
inventory 33 inputs gốc và kiểm lại source/PDF/AST/Git blobs/archive members chỉ
đọc. Script được lưu để tái chạy **verification**; đây là phiên bản kiểm chứng
và đóng gói audit, không giả nhận là file script đã tồn tại ở lượt khám phá trước.

Không chạy notebook/simulator/model/realdata/Holdout, không GPU/cloud/network,
không Git mutation hoặc sửa paper/notebook/shared state/index. Chỉ copy báo cáo,
script/helper nhỏ và PNG trang3 đã xem; không copy toàn PDF hoặc 14 ZIP. Text
trang2–4, code-cell extract và candidate inventory là dẫn xuất để review.

`source_input_inventory.json` giữ nguyên 33 hashes của audit nguồn. Manifest
ghi hashes của sources hiện tại lúc đóng, còn `audit_verification.json` báo
đối chiếu snapshot cũ/current riêng. `copy_integrity.json` ghi pre/copy/post SHA.
Chỉ PNG trang3 được giữ (534.770 bytes) vì chứa Eq.7–9, Algorithm1 và latent/
50-seed setup; PNG trang2/4 giữ locator/hash trong report JSON, không nhân đôi.

Q01 chỉ thu hẹp local search, **chưa đóng toàn cục**; S01 vẫn cần tác giả/advisor.
Mismatch current notebook không bác bỏ finite tested-run claims của PDF.

Sau closure, chạy từ repo: `.venv\\Scripts\\python.exe
research_tracking\\runs\\paper1-revision-audit-20261107-01\\verify_paper1_revision_audit.py
--verify-only`. Lệnh chỉ kiểm outputs theo manifest, không scientific validity.
Không thêm/sửa output hoặc manifest sau khi bundle đã đóng.
"""
    with record_evidence_run(
        root, RUN_ID,
        metadata={
            "kind": "READ_ONLY_PAPER1_REVISION_AUDIT_ARCHIVE",
            "rq": ["RQ1", "RQ2"],
            "scope_vi": "Đóng gói và kiểm tĩnh nguồn/PDF/aggregates đã lưu, không thí nghiệm khoa học mới",
            "original_audit_head": audit["git_head_snapshot"],
            "original_input_count": 33,
            "q01_closed": False,
            "s01_approved": False,
            "notebook_or_simulator_executions": 0,
            "model_training_steps": 0,
            "raw_realdata_or_holdout_access": False,
            "our_cloud_jobs_started": 0,
        },
        sources=sources, note=note,
    ) as directory:
        copied = []

        def preserve(source: Path, name: str) -> None:
            data = source.read_bytes()
            before = sha(data)
            target = directory / name
            target.write_bytes(data)
            copied_sha = sha(target.read_bytes())
            after = sha(source.read_bytes())
            copied.append({
                "source": str(source.relative_to(root)) if source.is_relative_to(root) else str(source),
                "destination": name,
                "bytes": len(data),
                "source_pre_sha256": before,
                "destination_sha256": copied_sha,
                "source_post_sha256": after,
                "all_equal": before == copied_sha == after,
            })
            if not copied[-1]["all_equal"]:
                raise ValueError("Copy/source integrity failed: " + name)

        preserve(report_md, report_md.name)
        preserve(report_json, report_json.name)
        preserve(script, "verify_paper1_revision_audit.py")
        preserve(helper, "evidence_helper_source.py")
        page3 = next(x for x in audit["pdf"]["previews"] if x["path"].endswith("paper1-page-3.png"))
        if sha(Path(page3["path"]).read_bytes()) != page3["sha256"]:
            raise ValueError("PNG trang3 khác preview đã xem")
        preserve(Path(page3["path"]), "paper1-page-3.png")
        dump(directory / "source_input_inventory.json", {
            "original_report_json_sha256": sha(report_json.read_bytes()),
            "original_audit_captured_utc": audit["captured_utc"],
            "input_count": len(inventory),
            "input_inventory": inventory,
            "note_vi": "Giữ nguyên inventory snapshot gốc; không coi file current thay đổi là sửa lịch sử.",
        })
        with (directory / "audit_verification.log").open("x", encoding="utf-8") as log:
            with redirect_stdout(log), redirect_stderr(log):
                print("Chỉ kiểm tĩnh/source identity, không chạy notebook/simulator.")
                revalidation = []
                for entry in inventory:
                    actual = sha((root / entry["path"]).read_bytes())
                    revalidation.append({"path": entry["path"], "original_sha256": entry["sha256"], "current_sha256": actual, "match": actual == entry["sha256"]})
                notebook = json.loads((root / core).read_text(encoding="utf-8-sig"))
                code = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
                extract = (root / "docs/thesis_recovery/evidence/paper1_source.py.txt").read_text(encoding="utf-8-sig")
                ast_equal = ast.dump(ast.parse(code), include_attributes=False) == ast.dump(ast.parse(extract), include_attributes=False)
                if not ast_equal or source_fingerprint(notebook) != audit["current_notebook"]["source_fingerprint"]:
                    raise ValueError("Current/source extract khác audit nguồn")
                cells = []
                for index, cell in enumerate(notebook["cells"]):
                    if cell["cell_type"] != "code":
                        continue
                    source = "".join(cell["source"])
                    ast.parse(source)
                    cells.append({"cell_zero_based": index, "source_sha256": sha(source.encode())})
                expected_cells = [{"cell_zero_based": c["cell_zero_based"], "source_sha256": c["source_sha256"]} for c in audit["current_notebook"]["code_cell_inventory"]]
                if cells != expected_cells:
                    raise ValueError("Code cell hashes khác audit nguồn")
                code_export = "\n\n".join("# CELL " + str(i) + "\n" + "".join(c["source"]) for i, c in enumerate(notebook["cells"]) if c["cell_type"] == "code")
                (directory / "paper1_source_cells.txt").write_text(code_export, encoding="utf-8")
                sys.path.insert(0, str(BUNDLED_PYTHON_PACKAGES))
                from pypdf import PdfReader
                pages = [page.extract_text() for page in PdfReader(root / pdf).pages]
                page_checks = []
                for entry, text in zip(audit["pdf"]["page_checks"], pages, strict=True):
                    actual = sha(text.encode())
                    page_checks.append({"page_one_based": entry["page_one_based"], "text_sha256": actual, "matches_original_audit": actual == entry["extracted_text_sha256"]})
                if len(pages) != 5 or not all(p["matches_original_audit"] for p in page_checks):
                    raise ValueError("PDF page extraction khác audit nguồn")
                selected = "\n\n".join("--- Paper1 PDF page " + str(i + 1) + " ---\n" + pages[i] for i in (1, 2, 3))
                (directory / "selected_pdf_pages_2_3_4.txt").write_text(selected, encoding="utf-8")
                candidate_inventory = {key: audit[key] for key in ("git_source_history", "git_pdf_history", "git_reachable_and_reflog_blobs", "paper2_archive", "portable_kits", "failure_archive_directories")}
                dump(directory / "candidate_inventory.json", candidate_inventory)
                archive_checks = []
                for kit in audit["portable_kits"]:
                    with zipfile.ZipFile(root / kit["path"]) as archive:
                        for candidate in kit["candidates"]:
                            raw = archive.read(candidate["member"])
                            same = sha(raw) == candidate["sha256"] and source_fingerprint(json.loads(raw)) == audit["current_notebook"]["source_fingerprint"]
                            archive_checks.append({"archive": kit["path"], "member": candidate["member"], "match": same})
                with zipfile.ZipFile(root / audit["paper2_archive"]["path"]) as archive:
                    for candidate in audit["paper2_archive"]["notebook_candidates"]:
                        raw = archive.read(candidate["member"])
                        archive_checks.append({"archive": audit["paper2_archive"]["path"], "member": candidate["member"], "match": sha(raw) == candidate["sha256"]})
                if len(archive_checks) != 13 or not all(c["match"] for c in archive_checks):
                    raise ValueError("Archive source members khác audit nguồn")
                blob_checks = []
                for path, entries in audit["git_reachable_and_reflog_blobs"].items():
                    for entry in entries:
                        raw = subprocess.check_output(["git", "cat-file", "blob", entry["git_blob_oid"]], cwd=root)
                        blob_checks.append({"path": path, "git_blob_oid": entry["git_blob_oid"], "match": sha(raw) == entry["sha256"]})
                if not all(c["match"] for c in blob_checks):
                    raise ValueError("Git historical blob khác audit nguồn")
                if any(not entry["match"] for entry in revalidation if entry["path"] in (core, pdf)):
                    raise ValueError("Core PDF/notebook bytes đã thay đổi")
                result = {
                    "status": "passed_read_only_verification",
                    "source_inventory_checks": revalidation,
                    "source_inventory_count": len(revalidation),
                    "source_inventory_matches": sum(c["match"] for c in revalidation),
                    "source_AST_equals_historical_extract": ast_equal,
                    "code_cells": len(cells),
                    "code_cell_hashes_match_original_audit": cells == expected_cells,
                    "pdf_page_checks": page_checks,
                    "archive_source_member_checks": archive_checks,
                    "git_blob_checks": blob_checks,
                    "q01_closed": False,
                    "s01_approved": False,
                    "notebook_or_simulator_executions": 0,
                    "scope_vi": "Hash/AST/PDF extraction chỉ đọc; source drift của tài liệu chung được báo riêng, không viết lại snapshot gốc.",
                }
                dump(directory / "audit_verification.json", result)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                print("PASS: giữ nguyên source, PDF, candidate identities; Q01/S01 vẫn mở.")
        dump(directory / "copy_integrity.json", {"copies": copied, "all_equal": all(c["all_equal"] for c in copied)})
        for record in copied:
            source_path = Path(record["source"])
            if not source_path.is_absolute():
                source_path = root / source_path
            if sha(source_path.read_bytes()) != record["source_post_sha256"]:
                raise ValueError("Source đổi sau copy: " + str(source_path))

    # Không ghi thêm file vào bundle đã đóng; verification sau closure chỉ in ra stdout.
    verified = verify_evidence_bundle(destination)
    print(json.dumps({"run_id": RUN_ID, "bundle": str(destination), **verified, "q01_closed": False, "s01_approved": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
