"""Fixed evidence allowlist and bounded, verified, read-only projections."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ("PG", "PY", "PYH")
SEEDS = (20000, 20001, 20002)
VARIANTS = ("graph_free", "graph_package", "empty_graph_package")
STEPS = 120
PINS = (
    ("cpu-rq12-20261107-03", "6592a80768e6608355cde1fd545ee90f6ca4ec937b2284a1e3eb42fae4f766f0", "traces.jsonl.gz", "22b065e8e0206403d2bcd41d175eeb1d686ed8bbf204c64f74d0e93d2aca0497"),
    ("cpu-rq1-transitions-20261108-01", "ff09520a20c7d0b6cbe18bdbfad3d4017e3106ca8628aa9cd2d38a4cb6591827", "analysis.json", "597d4ce320af4601665d206b7ffe1fe1250ebd96114893e87a53e70ff49d3d28"),
    ("rq2-conditions-evidence-20261108-01", "ed31bed55099c6e360d63dee47384b366744abc2f278b89d8a009a655c7ffc61", "conditions.json", "5bbc381f8f5bc7b86f6035c6502a05e50728f7ee7202546eee46048b6bd2d6a1"),
)


class EvidenceError(ValueError):
    """Missing, stale, malformed or oversized evidence; startup must stop."""


def bounded_read(path: Path, limit: int) -> bytes:
    # A fixed allowlist does not follow symlinks outside the checkout.
    try:
        path.resolve(strict=True).relative_to(ROOT.resolve())
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
    except (OSError, ValueError) as exc:
        raise EvidenceError("Không đọc được nguồn allowlist trong repository") from exc
    if len(data) > limit:
        raise EvidenceError("Nguồn vượt giới hạn bytes")
    return data


def parse_json(data: bytes):
    def reject_constant(value):
        raise EvidenceError("JSON không hữu hạn: " + value)

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise EvidenceError("JSON trùng khóa")
            result[key] = value
        return result
    try:
        return json.loads(data, parse_constant=reject_constant, object_pairs_hook=unique_pairs)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EvidenceError("JSON không hợp lệ") from exc


def decode_trace(data: bytes) -> list[dict]:
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            expanded = stream.read(16 * 1024 * 1024 + 1)
    except (OSError, EOFError, zlib.error) as exc:
        raise EvidenceError("Gzip không hợp lệ") from exc
    if len(expanded) > 16 * 1024 * 1024:
        raise EvidenceError("Gzip giải nén vượt giới hạn")
    lines = expanded.splitlines()
    if len(lines) != len(PROFILES) * len(SEEDS) * len(VARIANTS) * STEPS:
        raise EvidenceError("Số snapshot không đúng hợp đồng fixed-stream")
    if any(len(line) > 65536 for line in lines):
        raise EvidenceError("Dòng trace vượt giới hạn")
    return [parse_json(line) for line in lines]


class EvidenceStore:
    def __init__(self):
        payloads, self.provenance = [], []
        for run, manifest_sha, filename, file_sha in PINS:
            folder = ROOT / "research_tracking" / "runs" / run
            manifest_bytes = bounded_read(folder / "manifest.json", 256 * 1024)
            if hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha:
                raise EvidenceError("SHA manifest không khớp: " + run)
            manifest = parse_json(manifest_bytes)
            if manifest.get("status") != "completed" or manifest.get("outputs_sha256", {}).get(filename) != file_sha:
                raise EvidenceError("Output không được manifest completed chứng nhận")
            data = bounded_read(folder / filename, 256 * 1024 if filename.endswith(".gz") else 2 * 1024 * 1024)
            if hashlib.sha256(data).hexdigest() != file_sha:
                raise EvidenceError("SHA output không khớp: " + filename)
            payloads.append(data)
            self.provenance.append({"run": run, "file": filename, "sha256": file_sha, "manifest_sha256": manifest_sha})
        self.rows = self._index(decode_trace(payloads[0]))
        rq1, rq2 = parse_json(payloads[1]), parse_json(payloads[2])
        # Only selected synthetic aggregates are exposed, never the Junyi section.
        self.rq1 = [row for row in rq1["fixed_stream"]["groups"] if row["scope"] == "pooled"]
        self.rq2 = rq2["factorial"]
        self.limits = rq1["limits_vi"] + rq2["limits_vi"]

    @staticmethod
    def _index(rows):
        indexed = {}
        expected_keys = {"variant", "event_id", "learner_id", "correct", "probability", "mastery", "ready", "action", "mastered"}
        concepts = None
        for row in rows:
            if not isinstance(row, dict) or set(row) != expected_keys:
                raise EvidenceError("Schema trace không khớp")
            learner = row["learner_id"]
            if not isinstance(learner, str) or learner not in {f"{seed}-{p}" for seed in SEEDS for p in PROFILES}:
                raise EvidenceError("Identity không thuộc synthetic allowlist")
            seed, profile = learner.split("-")
            event = row["event_id"]
            if row["variant"] not in VARIANTS or event not in {str(i) for i in range(STEPS)}:
                raise EvidenceError("Variant/step không hợp lệ")
            probability = row["probability"]
            if type(probability) not in (int, float) or not math.isfinite(probability) or not 0 <= probability <= 1:
                raise EvidenceError("p không hợp lệ")
            mastery = row["mastery"]
            if not isinstance(mastery, dict) or len(mastery) != 28 or any(not isinstance(k, str) or len(k) > 120 for k in mastery):
                raise EvidenceError("Concept inventory không hợp lệ")
            if concepts is None:
                concepts = set(mastery)
            if set(mastery) != concepts:
                raise EvidenceError("Concept inventory thay đổi")
            for field in ("mastered", "ready"):
                values = row[field]
                if not isinstance(values, list) or any(not isinstance(v, str) for v in values) or len(values) != len(set(values)) or not set(values) <= concepts:
                    raise EvidenceError("Concept set không hợp lệ")
            if row["action"] is not None and row["action"] not in concepts:
                raise EvidenceError("Concept preview không hợp lệ")
            key = (profile, int(seed), row["variant"], int(event))
            if key in indexed:
                raise EvidenceError("Snapshot trùng identity")
            indexed[key] = row
        if len(indexed) != 3240:
            raise EvidenceError("Thiếu snapshot")
        return indexed

    def catalog(self):
        return {
            "profiles": PROFILES, "seeds": SEEDS, "variants": VARIANTS, "steps": STEPS,
            "status": "Demo một phần E11 • chỉ đọc artifact synthetic đã lưu",
            "replay_model": "GAM-KT / Paper2 diagnostic; không phải replay AKT",
            "models": [
                {"name": "AKT", "status": "Chỉ có kiểm kỹ thuật synthetic CPU/CUDA có giới hạn; chưa kết quả fit nghiên cứu đầy đủ."},
                {"name": "CG-AKT", "status": "Prototype tách biệt; chưa fitted trong demo."},
                {"name": "SAKT", "status": "Chưa xác minh trong phạm vi demo này."},
            ],
            "graph_confidence_gate": {"available": False, "reason": "Không có artifact edge confidence/gate cho replay; không suy diễn giá trị."},
            "rq1": self.rq1, "rq2_synthetic": self.rq2,
            "limits_vi": self.limits, "sources": self.provenance,
        }

    def snapshot(self, profile: str, seed: int, variant: str, step: int):
        if profile not in PROFILES or seed not in SEEDS or variant not in VARIANTS or type(step) is not int or not 0 <= step < STEPS:
            raise EvidenceError("Lựa chọn ngoài allowlist")
        row = self.rows[(profile, seed, variant, step)]
        base = self.rows[(profile, seed, "graph_free", step)]
        return {
            "profile": profile, "seed": seed, "variant": variant, "step": step,
            "p_correct_logged_query": row["probability"],
            "mastered_bool": {concept: concept in row["mastered"] for concept in row["mastery"]},
            "ready": row["ready"], "concept_preview": row["action"],
            "route_preview": [self.rows[(profile, seed, variant, i)]["action"] for i in range(step + 1)],
            "reference": {"variant": "graph_free", "p_correct_logged_query": base["probability"], "concept_preview": base["action"], "p_changed_exact": row["probability"] != base["probability"], "preview_changed": row["action"] != base["action"]},
            "semantics": "Snapshot trước cập nhật; concept preview trên bản sao, không action đã phục vụ. p của current logged query, không của concept preview. Trace thiếu item/question/timestamp. Mastery là native boolean, không P(đã biết).",
        }
