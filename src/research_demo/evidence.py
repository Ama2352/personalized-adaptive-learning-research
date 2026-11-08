"""Fixed evidence allowlist and bounded, verified, read-only projections."""
from __future__ import annotations

import gzip
import csv
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
CLOSED_RUN = "rq1-closed-loop-reconstruction-20261108-02"
CLOSED_MANIFEST_SHA = "c8bd8f387e5101fca641098257dd5a99d67d2f838cefc3b53b7d9d55248bcb16"
CLOSED_PINS = (
    ("accepted_fast__observed_metadata.jsonl.gz", "1ab8dcd5c5521c1f4055887f8d53032592a74e71949e9caaed83898c6efeb5ce", 1024*1024),
    ("descriptive__common_prefix_flags.csv", "a61432f3dc5f019fd7d799fba58db3a477c7bd3c7b526c2f962fe1c769a59563", 512*1024),
    ("posthoc__ranking_candidate.json", "119d75da6bdf97f58fea2ff265a5590c956308d24eabf9cf6d194a7f627a0e77", 256*1024),
    ("prep__parent-ranking-review.json", "ddbc77152d09c41c10d8bc4dbba86697e9d9bbe46a4f7dfd9ef61db62b1ec8a4", 16*1024),
    ("closure_review.json", "f59ff3d4d98ca7aff46fe198dd78526f1f5bee17c883ef881052d1addbfe9093", 16*1024),
    ("rq1_closed_loop_reconstruction_20261108.md", "5d86a7636dfb03faa8bdc4c364f0cefb673091c38ffc6634281bfa9ba167aab0", 64*1024),
)
CLOSED_PHASES = ["before_selection", "after_selection_bookkeeping", "before_predict", "after_predict",
    "before_environment_interact", "after_environment_interact", "legacy_written", "before_update", "after_update"]
CLOSED_LIMITS = [
    "Current-source reconstruction: nguyên runner lịch sử a585 vẫn thiếu; không backfill metadata lịch sử.",
    "Ranking là giải thích source-local post-hoc cho concept CID, không replay choose_question/difficulty hoặc chứng minh causal/learning benefit.",
    "Native B-score không là calibrated mastery probability. P của served item được tính sau select; không gây ra same-step selection.",
    "Sau khi histories diverge, không ghép ΔP/loss theo ordinal timestep. Ba seed families cũ, new independent N = 0.",
    "Empty chỉ là empty estimator; controller G và environment G chung. Package khác không đồng nghĩa edge-only effect.",
]


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


def decode_closed_trace(data: bytes) -> list[dict]:
    """Separate bounds/schema: never relax the historical fixed-stream decoder."""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            expanded = stream.read(32 * 1024 * 1024 + 1)
    except (OSError, EOFError, zlib.error) as exc:
        raise EvidenceError("Closed-loop gzip không hợp lệ") from exc
    if len(expanded) > 32 * 1024 * 1024:
        raise EvidenceError("Closed-loop giải nén vượt giới hạn")
    lines = expanded.splitlines()
    if len(lines) != 3240 or any(len(line) > 65536 for line in lines):
        raise EvidenceError("Closed-loop row/line bound không khớp")
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
        self._load_closed_loop()

    def _load_closed_loop(self):
        folder = ROOT / "research_tracking/runs" / CLOSED_RUN
        manifest_bytes = bounded_read(folder / "manifest.json", 256*1024)
        if hashlib.sha256(manifest_bytes).hexdigest() != CLOSED_MANIFEST_SHA:
            raise EvidenceError("SHA manifest closed-loop không khớp")
        manifest = parse_json(manifest_bytes)
        payloads = {}
        for name, expected, limit in CLOSED_PINS:
            if manifest.get("status") != "completed" or manifest.get("outputs_sha256", {}).get(name) != expected:
                raise EvidenceError("Closed-loop output không thuộc manifest completed")
            data = bounded_read(folder / name, limit)
            if hashlib.sha256(data).hexdigest() != expected:
                raise EvidenceError("SHA closed-loop output không khớp: " + name)
            payloads[name] = data
            self.provenance.append({"run": CLOSED_RUN, "file": name, "sha256": expected,
                                    "manifest_sha256": CLOSED_MANIFEST_SHA})
        self.closed_rows = self._index_closed(decode_closed_trace(payloads[CLOSED_PINS[0][0]]))
        self.closed_prefix = self._index_prefix(payloads[CLOSED_PINS[1][0]])
        ranking = parse_json(payloads[CLOSED_PINS[2][0]])
        review, closure = parse_json(payloads[CLOSED_PINS[3][0]]), parse_json(payloads[CLOSED_PINS[4][0]])
        if (review.get("status") != "PASS_PARENT_INDEPENDENT_RAW_RANKING_AND_DESCRIPTIVE_REVIEW"
                or review.get("raw_rank_keys_verified") != 3240 or review.get("comparisons") != 18
                or closure.get("methodology_adoption") is not False
                or closure.get("parent_ranking_review_sha256") != CLOSED_PINS[3][1]
                or closure.get("posthoc_role") != "EXPLORATORY_SOURCE_LOCAL_CID_EXPLANATION_PARENT_REVIEWED_NOT_CONFIRMATORY"
                or ranking.get("rank_replays_validated") != 3240 or ranking.get("unsupported") != []
                or ranking.get("new_independent_N") != 0 or ranking.get("original_a585_whole_source_recovered") is not False):
            raise EvidenceError("Closed-loop post-hoc review/role không khớp")
        self.closed_rankings = self._index_rankings(ranking)
        self.closed_review = {key: review[key] for key in ("full_same_membership_score_choices", "full_membership_change",
            "empty_same_membership_score_choices", "empty_negative_cases")}
        sources = {"scope": "Committed synthetic allowlist; chỉ các outputs liệt kê được startup kiểm SHA.",
            "run": CLOSED_RUN, "manifest_sha256": CLOSED_MANIFEST_SHA,
            "sources": [p for p in self.provenance if p["run"] == CLOSED_RUN], "limits_vi": CLOSED_LIMITS,
            "review": review["status"], "posthoc_role": closure["posthoc_role"],
            "generated_ranking_status_historical": ranking["status"], "new_independent_N": 0}
        self.documents = {"report": (payloads[CLOSED_PINS[5][0]], "text/plain"),
            "sources": (json.dumps(sources, ensure_ascii=False, allow_nan=False).encode("utf-8"), "application/json")}

    @staticmethod
    def _index_closed(rows):
        required = {"balanced_candidates", "correct", "eligible_candidates", "full_mastery_score_vector_available",
            "is_served_in_simulator", "legacy_row_sha256", "mastered_decisions", "mastery_calls",
            "mastery_ready_capture_phase", "mastery_score_calls", "outcome_sha256", "phases", "prediction",
            "prediction_capture_phase", "profile", "query", "ready_set", "seed", "select_timestamp_argument",
            "served_tuple", "state_after_selection_sha256", "state_after_update_sha256", "state_before_selection_sha256",
            "step", "variant"}
        indexed, concepts = {}, None
        for row in rows:
            if not isinstance(row, dict) or set(row) != required:
                raise EvidenceError("Schema closed-loop không khớp")
            key = (row["profile"], row["seed"], row["variant"], row["step"])
            if (row["profile"] not in PROFILES or type(row["seed"]) is not int or row["seed"] not in SEEDS
                    or row["variant"] not in VARIANTS or type(row["step"]) is not int or not 0 <= row["step"] < STEPS
                    or key in indexed):
                raise EvidenceError("Closed-loop identity/duplicate không hợp lệ")
            mastered = row["mastered_decisions"]
            if (not isinstance(mastered, dict) or len(mastered) != 28
                    or any(not isinstance(c, str) or len(c) > 120 or type(v) is not bool for c,v in mastered.items())):
                raise EvidenceError("Closed-loop M28 phải là explicit boolean")
            if concepts is None:
                concepts = set(mastered)
            if set(mastered) != concepts:
                raise EvidenceError("Closed-loop concept inventory drift")
            for field in ("ready_set", "eligible_candidates", "balanced_candidates"):
                values = row[field]
                if (not isinstance(values, list) or not values or any(not isinstance(v,str) for v in values)
                        or len(values) != len(set(values)) or not set(values) <= concepts):
                    raise EvidenceError("Closed-loop R/C/B không hợp lệ")
            item, query = row["served_tuple"], row["query"]
            if (not isinstance(item,dict) or set(item) != {"concept","question","difficulty"}
                    or not isinstance(query,dict) or set(query) != {"concept","question","difficulty","timestamp_iso","timestamp_ns"}
                    or item["concept"] not in row["balanced_candidates"]
                    or not set(row["balanced_candidates"]) <= set(row["eligible_candidates"])
                    or not isinstance(item["question"],str) or not 1 <= len(item["question"]) <= 180
                    or type(item["difficulty"]) is not float or not math.isfinite(item["difficulty"])
                    or any(query[k] != item[k] for k in item)
                    or not isinstance(query["timestamp_iso"],str) or len(query["timestamp_iso"]) > 64
                    or type(query["timestamp_ns"]) is not int):
                raise EvidenceError("Closed-loop selected/query/B subset C không hợp lệ")
            scores = row["mastery_score_calls"]
            if (not isinstance(scores,list) or any(not isinstance(s,dict) for s in scores)
                    or [s.get("concept") for s in scores] != row["balanced_candidates"]
                    or any(set(s) != {"concept","score"} or type(s["score"]) is not float
                           or not math.isfinite(s["score"]) for s in scores)):
                raise EvidenceError("Captured native B-score coverage không khớp")
            if (row["phases"] != CLOSED_PHASES or row["select_timestamp_argument"] is not None
                    or row["is_served_in_simulator"] is not True or row["full_mastery_score_vector_available"] is not False
                    or row["mastery_ready_capture_phase"] != "during_selection_before_bookkeeping"
                    or row["prediction_capture_phase"] != "after_selection_bookkeeping_before_environment_interact"
                    or type(row["prediction"]) is not float or not math.isfinite(row["prediction"])
                    or not 0 <= row["prediction"] <= 1 or type(row["correct"]) is not int or row["correct"] not in (0,1)):
                raise EvidenceError("Closed-loop P/phase semantics không khớp")
            # Deliberately drop raw labels, oracle outcomes, state hashes and call traces.
            indexed[key] = {"mastered_bool": mastered, "ready": row["ready_set"],
                "candidates": row["eligible_candidates"], "balanced": row["balanced_candidates"],
                "served_item": item, "timestamp": query["timestamp_iso"],
                "p_correct_served_item": row["prediction"], "native_B_scores": scores}
        if len(indexed) != 3240:
            raise EvidenceError("Thiếu closed-loop snapshot")
        return indexed

    @staticmethod
    def _index_prefix(data):
        fields = ["seed","profile","candidate","step","common_before","common_after","current_same_served_tuple",
            "current_same_timestamp","current_same_label","M_setdiff","R_setdiff","C_setdiff","B_setdiff","served_tuple_diff"]
        try:
            reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
            if reader.fieldnames != fields:
                raise EvidenceError("Prefix CSV schema không khớp")
            indexed = {}
            for row in reader:
                if set(row) != set(fields) or any(v is None for v in row.values()):
                    raise EvidenceError("Prefix row không hợp lệ")
                seed, step = int(row["seed"]), int(row["step"])
                if str(seed) != row["seed"] or str(step) != row["step"]:
                    raise EvidenceError("Prefix integer không canonical")
                key = (row["profile"], seed, row["candidate"], step)
                if (key[0] not in PROFILES or seed not in SEEDS or key[2] not in VARIANTS[1:]
                        or not 0 <= step < STEPS or key in indexed):
                    raise EvidenceError("Prefix identity không hợp lệ")
                flags = {}
                for field in fields[4:]:
                    allowed = ("0","1") if field in fields[4:9] or row["common_before"] == "1" else ("",)
                    if row[field] not in allowed:
                        raise EvidenceError("Prefix flag không hợp lệ")
                    flags[field] = None if row[field] == "" else row[field] == "1"
                indexed[key] = flags
            if len(indexed) != 2160:
                raise EvidenceError("Thiếu prefix comparison events")
            for profile in PROFILES:
                for seed in SEEDS:
                    for candidate in VARIANTS[1:]:
                        past_common = True
                        for step in range(STEPS):
                            flags = indexed[(profile,seed,candidate,step)]
                            if flags["common_before"] != past_common or flags["common_after"] != (
                                past_common and flags["current_same_served_tuple"] and flags["current_same_timestamp"] and flags["current_same_label"]):
                                raise EvidenceError("Prefix phải sticky sau divergence")
                            past_common = flags["common_after"]
            return indexed
        except (ValueError, UnicodeError, KeyError, csv.Error) as exc:
            raise EvidenceError("Prefix CSV không hợp lệ") from exc

    def _index_rankings(self, ranking):
        result = {}
        for row in ranking.get("comparisons", []):
            key = (row["profile"],row["seed"],row["candidate"])
            if (key[0] not in PROFILES or key[1] not in SEEDS or key[2] not in VARIANTS[1:]
                    or key in result or row["rank_replayed_events_both_sides_all_steps"] != 240):
                raise EvidenceError("Ranking comparison không hợp lệ")
            first = row["first_prefix_break"]
            flags = [self.closed_prefix[(*key,i)] for i in range(STEPS)]
            breaks = [i for i,f in enumerate(flags) if f["common_before"] and not f["common_after"]]
            if (row["common_before_events"] != sum(f["common_before"] for f in flags)
                    or row["negative_case"] != (first is None)
                    or (None if first is None else first["step"]) != (breaks[0] if breaks else None)):
                raise EvidenceError("Archived first-break/sticky prefix không khớp")
            if first is None:
                if row["common_before_events"] != 120:
                    raise EvidenceError("Negative prefix coverage không khớp")
                detail = None
            else:
                step = first["step"]
                if (type(step) is not int or not 0 <= step < STEPS or not self.closed_prefix[(*key,step)]["common_before"]
                        or not isinstance(first["reasons"],list) or not first["reasons"]
                        or not set(first["reasons"]) <= {"served_tuple","timestamp","label"}
                        or first["classification"] not in {"SAME_B_TIES_NATIVE_B_SCORE_RANKING_EXPLAINS_CONCEPT_CHOICE",
                                                           "B_MEMBERSHIP_DIFF_SCORE_ONLY_EXPLANATION_NOT_CLAIMED"}):
                    raise EvidenceError("First break không thuộc common-before")
                detail = {"step":step,"reasons":first["reasons"],"classification":first["classification"],
                          "same_membership_sets":first.get("same_membership_sets"), "ranking_keys":{}}
                for variant, field in [("graph_free","left_native_replay"),(key[2],"right_native_replay")]:
                    replay = first.get(field)
                    if replay is None:
                        continue
                    observed = self.closed_rows[(key[0],key[1],variant,step)]
                    if replay["chosen_concept"] != observed["served_item"]["concept"] or replay["B"] != observed["balanced"]:
                        raise EvidenceError("Archived ranking/served concept mismatch")
                    scores = {v["concept"]:v["score"] for v in observed["native_B_scores"]}
                    values = []
                    if set(replay["native_keys"]) != set(replay["B"]):
                        raise EvidenceError("Archived key coverage không khớp")
                    for cid in replay["B"]:
                        value = replay["native_keys"][cid]
                        if (value["score"] != scores[cid] or value["score_hex"] != scores[cid].hex()
                                or value["lexical_cid"] != cid or type(value["chapter_tie"]) is not int
                                or value["chapter_tie"] not in (0,1)
                                or type(value["prior_visits"]) is not int or not 0 <= value["prior_visits"] <= step):
                            raise EvidenceError("Archived native key không khớp")
                        values.append({"concept":cid,"score":value["score"],"chapter_tie":value["chapter_tie"],
                                       "prior_visits":value["prior_visits"],"selected":cid==replay["chosen_concept"]})
                    detail["ranking_keys"][variant] = values
            result[key] = {"common_before_events":row["common_before_events"],"first_break":detail,
                           "negative_case":row["negative_case"]}
        if len(result) != 18:
            raise EvidenceError("Thiếu ranking comparisons")
        return result

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
            "modes": [{"id":"fixed_preview","label":"Fixed stream · preview", "endpoint":"/api/replay"},
                      {"id":"closed_loop","label":"Closed loop · quyết định đã phục vụ", "endpoint":"/api/closed-loop"}],
            "closed_loop": {"posthoc":True,"new_independent_N":0,"reviewed_summary":self.closed_review,
                "limits_vi":CLOSED_LIMITS,"source_links":[{"label":"Báo cáo source snapshot","url":"/evidence/closed-loop/report"},
                                                         {"label":"Nguồn, SHA và phạm vi review","url":"/evidence/closed-loop/sources"}]},
        }

    def closed_loop_snapshot(self, profile: str, seed: int, variant: str, step: int):
        if (profile not in PROFILES or type(seed) is not int or seed not in SEEDS or variant not in VARIANTS
                or type(step) is not int or not 0 <= step < STEPS):
            raise EvidenceError("Closed-loop lựa chọn ngoài allowlist")
        row = self.closed_rows[(profile,seed,variant,step)]
        comparison = None
        if variant != "graph_free":
            summary = self.closed_rankings[(profile,seed,variant)]
            first = summary["first_break"]
            comparison = {**self.closed_prefix[(profile,seed,variant,step)],
                "first_break_step":None if first is None else first["step"],
                "first_break_reasons":[] if first is None else first["reasons"],
                "negative_case":summary["negative_case"],
                "explanation":first if first is not None and first["step"] == step else None}
        return {"mode":"closed_loop","profile":profile,"seed":seed,"variant":variant,"step":step, **row,
            "route_served":[self.closed_rows[(profile,seed,variant,i)]["served_item"]["concept"] for i in range(step+1)],
            "comparison":comparison,"posthoc":True,"new_independent_N":0,
            "semantics":"M/R/C/B trước bookkeeping; served-item P sau select, trước interact/update. Native B-score không calibrated mastery; không paired ΔP/loss sau divergence. Current-source reconstruction, không historical backfill."}

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
