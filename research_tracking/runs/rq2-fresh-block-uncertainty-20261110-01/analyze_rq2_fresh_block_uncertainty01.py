"""Thăm dò bất định fresh120 đã lưu, source-only tới ROOT review/adoption.

Chỉ bootstrap mười block ghép cặp, không gọi world/model hoặc kiểm định p.
"""
import time
START = time.perf_counter()

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PLAN = PREP/"RQ2_FRESH_BLOCK_UNCERTAINTY_SPEC01.md"
OUTPUT = PREP/"rq2-fresh-block-uncertainty01"
RUN = "research_tracking/runs/rq2-fresh-graph-recovery-20261110-01/"
PREFIX = "experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03/"
MANIFEST_SHA = "deff815a7360ab9d0ffcaf06e986ff2fc14ed07aa0ab8366880ade34445df11e"
PINS = {
    "acceptance.json": "56068d889137658244b4595c0289b78da15a995fe84d2a62f97579aca6f0b7b3",
    PREFIX+"summary.json": "73538ef1c229dd5b9a17af781fc13bdb810efd58fe1196bd70d8d95d31d74a7d",
    PREFIX+"outcomes.json": "35f6603726f21d717e1da8e75ada8369584fcdcbbacbf3d170981e027dd662fa",
    PREFIX+"graph_source_contrasts.json": "645b395c81eedea3d42a7ebfb6521e1be0c14aeafa70eb3412468100f22de330",
    PREFIX+"conditional_lambda_contrasts.json": "f48f5ec7f6683d8285288a5bffa05e46be2365d244aa83990c6797b43a721a38",
    PREFIX+"high_controls.json": "026adf45ff9022cd5928b237e90c371daffff62b6bb287ae881ddf468987668c",
    PREFIX+"admission.json": "9693f81685367cc3c12c4a23be757b8b64f56c68098ac3f65cd6994272a36868",
}
KERNEL = ROOT/"src/knowledge_tracing/research_selection.py"
KERNEL_SHA = "0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348"
BLOCKS = tuple(range(21010, 21020))
ABILITIES = (1000, 1150, 1300)
REPLICATES, SEED = 10000, 42
ESTIMATES = ("K1000", "K1150", "K1150_minus_K1000")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def guard():
    need(time.perf_counter()-START < 7, "Quá worker cap7giây, không retry tự động")


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def read(path, pin, limit=64*1024):
    guard()
    need(path.resolve(strict=True).is_relative_to(ROOT), "Nguồn ngoài workspace")
    with path.open("rb") as stream:
        raw = stream.read(limit+1)
    need(len(raw) <= limit and hashlib.sha256(raw).hexdigest() == pin, "Source/input SHA hoặc kích thước không khớp")
    return raw


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "JSON key trùng")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("JSON không hữu hạn")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def admit(payloads):
    """Không thay population hoặc chọn block theo dấu kết quả."""
    summary, acceptance = payloads["summary.json"], payloads["acceptance.json"]
    need(summary["primary_worlds"] == 120 and summary["primary_responses"] == 14400
         and summary["components"] == 60 and summary["contrasts"] == 30
         and summary["one_fixed_learned_graph"] is True, "Sai population fresh120")
    need(acceptance["kind"] == "recovered_fresh_simulation_replication_no_inference"
         and acceptance["summary"] == summary and acceptance["primary_blocks"] == 10
         and acceptance["source_input_stable"] is True
         and acceptance["no_human_causal_claim"] is True
         and acceptance["outer_sha256"] == "3cdd399ec6a94a17e0178dec76b416b87ed406ddef701a0d1cb420e2486c90d8",
         "Không khớp acceptance đã đóng")
    for name, pin in PINS.items():
        if name != "acceptance.json":
            need(acceptance["raw_output_sha256"][Path(name).name] == pin, "Raw output binding sai")
    expected = {(b, a, strength) for b in BLOCKS for a in ABILITIES for strength in (0., .55)}
    outcomes, q, k, bases, uniforms = {}, {}, {}, {}, {}
    for row in payloads["outcomes.json"]:
        condition = (row["block"], row["ability"], row["mechanism_strength"])
        need(type(condition[0]) is int and type(condition[1]) is int
             and finite(condition[2]) and condition in expected and row["graph_source"] in ("expert", "learned")
             and finite(row["outcome"]), "Outcome ngoài grid hoặc không hữu hạn")
        key = (*condition, row["graph_source"])
        need(key not in outcomes, "Outcome trùng")
        for field in ("latent_identity", "uniform_identity"):
            value = row[field]
            need(type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value), "Identity không đúng")
        need(bases.setdefault(condition[:2], row["latent_identity"]) == row["latent_identity"]
             and uniforms.setdefault(condition[0], row["uniform_identity"]) == row["uniform_identity"], "Coupled initial/U không khớp")
        outcomes[key] = row["outcome"]
    need(set(outcomes) == {(*c, g) for c in expected for g in ("expert", "learned")}, "Thiếu120outcomes")
    for row in payloads["graph_source_contrasts.json"]:
        condition = (row["block"], row["ability"], row["mechanism_strength"])
        need(condition in expected and condition not in q and finite(row["expert_minus_learned"]), "Q trùng/ngoài grid")
        need(row["expert"] == outcomes[(*condition, "expert")] and row["learned"] == outcomes[(*condition, "learned")]
             and row["expert_minus_learned"] == row["expert"]-row["learned"], "Q arithmetic không exact")
        q[condition] = row["expert_minus_learned"]
    need(set(q) == expected, "Thiếu60Q")
    for row in payloads["conditional_lambda_contrasts.json"]:
        key = (row["block"], row["ability"])
        need(key not in k and type(key[0]) is int and type(key[1]) is int
             and key in {(b, a) for b in BLOCKS for a in ABILITIES} and finite(row["lambda_difference"]), "K trùng/ngoài grid")
        need(row["lambda_difference"] == q[(*key, .55)]-q[(*key, 0.)], "K arithmetic không exact")
        k[key] = row["lambda_difference"]
    need(set(k) == {(b, a) for b in BLOCKS for a in ABILITIES}, "Thiếu30K")
    need(all(k[b, 1300] == 0. for b in BLOCKS), "Structural high control không khớp")
    controls = payloads["high_controls.json"]
    need(len(controls) == 20 and {(r["block"], r["graph"]) for r in controls} == {(b, g) for b in BLOCKS for g in ("full", "learned")}
         and all(r["endpoint_exact"] is True and r["observable_rows"] == r["oracle_rows"] == 120 for r in controls), "Thiếu high controls")
    need(payloads["admission.json"]["confidence_used_as_GAM_weight"] is False, "GAM confidence weight sai")
    return tuple((float(k[b, 1000]), float(k[b, 1150]), float(k[b, 1150]-k[b, 1000])) for b in BLOCKS)


def bootstrap_family(block_vectors, percentile, check):
    """Một shared draw mười block cho cả ba estimands, private MT19937."""
    need(type(block_vectors) is tuple and len(block_vectors) == 10
         and all(type(row) is tuple and len(row) == 3 and all(finite(v) for v in row) for row in block_vectors),
         "Cần đúng10vector ba đại lượng hữu hạn")
    generator = random.Random(SEED)
    digest = hashlib.sha256()
    draws = [[], [], []]
    for replicate in range(REPLICATES):
        if replicate % 64 == 0:
            check()
        indices = tuple(generator.randrange(10) for _ in range(10))
        digest.update(struct.pack(">10B", *indices))
        for column in range(3):
            draws[column].append(math.fsum(block_vectors[i][column] for i in indices)/10)
    estimates = []
    for column, name in enumerate(ESTIMATES):
        values = [row[column] for row in block_vectors]
        estimates.append({"estimand": name, "blocks": 10, "mean": math.fsum(values)/10,
            "observed_min": min(values), "observed_max": max(values),
            "signs": {"positive": sum(v > 0 for v in values), "negative": sum(v < 0 for v in values), "zero": sum(v == 0 for v in values)},
            "percentile_lower": percentile(draws[column], 1/120),
            "percentile_upper": percentile(draws[column], 119/120)})
        check()
    return estimates, draws, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Thăm dò paired-block bootstrap trên fresh120 đã đóng")
    parser.add_argument("--expected-source-sha", required=True)
    parser.add_argument("--expected-plan-sha", required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT/".venv", "Chỉ .venv -B")
    need(not OUTPUT.exists(), "Output phải mới, không resume/retry")
    source = Path(__file__).resolve()
    before = {"script": hashlib.sha256(read(source, args.expected_source_sha)).hexdigest(),
              "plan": hashlib.sha256(read(PLAN, args.expected_plan_sha)).hexdigest(),
              "kernel": hashlib.sha256(read(KERNEL, KERNEL_SHA)).hexdigest()}
    manifest = decode(read(ROOT/RUN/"manifest.json", MANIFEST_SHA))
    need(set(manifest) == {"kind", "input_inventory", "outputs_sha256"}
         and manifest["kind"] == "recovered_fresh_simulation_replication_no_inference", "Sai manifest recovery")
    payloads = {}
    for name, pin in PINS.items():
        need(manifest["outputs_sha256"].get(name) == pin, "Output không thuộc manifest đã ghim")
        payloads[Path(name).name] = decode(read(ROOT/RUN/name, pin))
    block_vectors = admit(payloads)
    forbidden = {"numpy", "pandas", "torch", "scipy", "sklearn"}
    need(not forbidden.intersection(sys.modules), "Scientific imports phải cold")
    def audit(event, values):
        if event.startswith("socket.") or event in {"subprocess.Popen", "os.system"}:
            raise RuntimeError("Không network/process trong cached analysis")
        if event == "import" and str(values[0]).split(".")[0] in forbidden:
            raise RuntimeError("Không scientific framework")
    sys.addaudithook(audit)
    sys.path.insert(0, str(ROOT/"src"))
    from knowledge_tracing.research_selection import linear_percentile
    global_rng = random.getstate()
    estimates, draws, draw_sha = bootstrap_family(block_vectors, linear_percentile, guard)
    need(random.getstate() == global_rng, "Caller global RNG đã đổi")
    summary = {"status": "POSTHOC_EXPLORATORY_NOT_RQ_COMPLETE", "independent_unit": "paired_seed_block",
        "blocks": list(BLOCKS), "replicates": REPLICATES, "seed": SEED,
        "family_estimands": list(ESTIMATES), "family_nominal_coverage": .95,
        "per_interval_nominal_coverage": 59/60, "lower_quantile": 1/120, "upper_quantile": 119/120,
        "quantile_algorithm": "linear-type7-v1", "draw_algorithm": "private-CPython-MT19937-randrange10-v1",
        "draw_sha256_encoding_10_unsigned_bytes_per_replicate": draw_sha,
        "aggregation": "binary64-per-block-K_then-fsum-over10-blocks",
        "estimates": estimates, "structural_K1300_tested": False,
        "limits_vi": ["Kết quả đã được xem trước, đây là phân tích thăm dò sau kết quả.",
            "10block cho bootstrap rời rạc và độ chính xác hữu hạn, coverage danh nghĩa chỉ xấp xỉ.",
            "Điều kiện vào một learned graph, expert world/controller và source world cố định.",
            "Không pooling E9, không p-value, causal humans hoặc graph-quality ranking."]}
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(("replicate", *ESTIMATES))
    for index, values in enumerate(zip(*draws)):
        writer.writerow((index, *values))
    blobs = {"summary.json": (json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode(),
             "bootstrap_means.csv": buffer.getvalue().encode()}
    need(all(len(raw) <= 1024*1024 for raw in blobs.values()), "Output vượt1MiB")
    guard()
    OUTPUT.mkdir()
    for name, raw in blobs.items():
        with (OUTPUT/name).open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    outputs = {}
    for name, raw in blobs.items():
        actual = (OUTPUT/name).read_bytes()
        need(actual == raw, "Output readback không exact")
        outputs[name] = {"sha256": hashlib.sha256(actual).hexdigest(), "bytes": len(actual)}
    for name, pin in PINS.items():
        read(ROOT/RUN/name, pin)
    read(ROOT/RUN/"manifest.json", MANIFEST_SHA)
    after = {"script": hashlib.sha256(read(source, args.expected_source_sha)).hexdigest(),
             "plan": hashlib.sha256(read(PLAN, args.expected_plan_sha)).hexdigest(),
             "kernel": hashlib.sha256(read(KERNEL, KERNEL_SHA)).hexdigest()}
    need(before == after and not forbidden.intersection(sys.modules), "Source/input drift hoặc heavy import")
    guard()
    receipt = {"status": "ACCEPTED_CACHED_EXPLORATORY_STATISTICS_ONLY", "source_before": before, "source_after": after,
        "input_pins": PINS, "manifest_sha256": MANIFEST_SHA, "outputs": outputs,
        "elapsed_seconds_before_final": time.perf_counter()-START, "worker_cap_seconds": 7,
        "outer_cap_seconds_proposed": 10, "blocks": 10, "replicates": 10000, "estimates": 3,
        "bootstrap_randrange_calls": 100000, "new_world_model_response_calls": 0,
        "global_random_state_unchanged": True, "structural_high_control_only": True}
    with (OUTPUT/"result.json").open("xb") as stream:
        stream.write((json.dumps(receipt, ensure_ascii=False, indent=2)+"\n").encode())
        stream.flush()
        os.fsync(stream.fileno())
    guard()
    print(json.dumps({"status": receipt["status"], "elapsed_seconds": time.perf_counter()-START}))


if __name__ == "__main__":
    main()
