"""Đóng bundle chỉ sau parent Gate20 PASS; không chạy tests/models/Git writes."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
RUN="akt-graph-prototype-engineering-20261108-01"
GATE="20261108-graph-prototype-20"
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description="Chỉ archive sau parent-confirmed Gate20 PASS")
    parser.add_argument("--expected-gate-sha",required=True)
    parser.add_argument("--expected-pass-count",required=True,type=int)
    parser.add_argument("--parent-pass-reference",required=True)
    args=parser.parse_args()
    assert len(args.expected_gate_sha)==64 and args.parent_pass_reference.strip()
    preflight=ROOT/"artifacts/akt/preflight"
    gate=preflight/f"gate2-evidence-{GATE}.json"
    log=preflight/f"gate2-tests-{GATE}.log"
    junit=preflight/f"gate2-tests-{GATE}.xml"
    pointer=preflight/"gate2-current.json"
    assert gate.is_file() and sha(gate)==args.expected_gate_sha,"Parent-confirmed Gate20 missing/stale"
    report=json.loads(gate.read_text(encoding="utf8"))
    counts={"passed":args.expected_pass_count,"failed":0,"errors":0,"skipped":0}
    assert report["status"]=="PASS" and report["test_result"]==counts and counts["passed"]>=23
    assert sha(log)==report["test_log_sha256"] and sha(junit)==report["junit_sha256"]
    xml=ET.parse(junit).getroot().findall("testsuite")
    observed={key:sum(int(s.attrib[field]) for s in xml) for key,field in
              (("passed","tests"),("failed","failures"),("errors","errors"),("skipped","skipped"))}
    observed["passed"]-=observed["failed"]+observed["errors"]+observed["skipped"]
    assert observed==counts
    current=json.loads(pointer.read_text(encoding="utf8"))
    assert current["evidence_file"]==gate.name and current["evidence_sha256"]==sha(gate)
    assert current["test_log_file"]==log.name and current["test_log_sha256"]==sha(log)
    build=report["build_hashes"]
    for relative,digest in build.items():
        path=ROOT/relative
        assert path.is_file() and path.resolve().is_relative_to(ROOT.resolve())
        assert sha(path)==digest,("Gate20 build source mismatch",relative)
    trial=json.loads((OUT/"trial01-receipt.json").read_text(encoding="utf8"))
    before=trial["source_before_sha256"]
    assert trial["exit_code"]==0 and trial["optimizer_steps"]==0 and len(before)==36
    assert before==trial["source_after_sha256"]
    for relative,digest in before.items():
        assert build[relative]==digest==sha(ROOT/relative)
    for name,digest in trial["trial_outputs_sha256"].items():
        assert sha(OUT/name)==digest
    suite=ET.parse(OUT/"pytest-trial01.xml").getroot().find("testsuite")
    assert (suite.attrib["tests"],suite.attrib["failures"],suite.attrib["errors"],suite.attrib["skipped"])==("23","0","0","0")
    owned={"src/knowledge_tracing/akt/graph_prototype.py":"graph_prototype.py",
           "tests/akt/test_graph_prototype.py":"test_graph_prototype.py"}
    for relative,basename in owned.items():
        assert sha(OUT/(basename+".before-trial01"))==before[relative]
    native=sorted((ROOT/"src/knowledge_tracing/akt").glob("*.py"))
    helpers=[ROOT/"src/knowledge_tracing"/name for name in
             ("simulator_data.py","simulator_bridge.py","shared_kt.py","graph_context.py","graph_augmentation.py")]
    upstream=ROOT/"artifacts/akt/dependencies/upstream/akt.py"
    assert sha(upstream)==report["source"]["files"]["akt.py"]=="be2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d"
    model_paths=native+helpers+[upstream]
    assert len(model_paths)==36
    model_inventory={p.relative_to(ROOT).as_posix():sha(p) for p in model_paths}
    covered={p:d for p,d in model_inventory.items() if p in before}
    assert len(covered)==35 and all(before[p]==d for p,d in covered.items())

    mapping={}
    def add(path,name):
        assert path.is_file() and name not in mapping and len(name)<240
        assert path.suffix not in (".pt",".parquet",".zip")
        mapping[name]=path
    for path in model_paths:
        add(path,"source__"+path.relative_to(ROOT).as_posix().replace("/","__"))
    add(ROOT/"tests/akt/test_graph_prototype.py","source__test_graph_prototype.py")
    add(ROOT/"research_tracking/reports/akt_graph_prototype_readiness_20261108.md","readiness_report.md")
    add(ROOT/"src/knowledge_tracing/evidence.py","evidence_helper.py")
    for path in sorted(OUT.iterdir()):
        if path.is_file() and (path.suffix in (".json",".log",".xml",".py",".md") or ".before-trial" in path.name):
            add(path,"work__"+path.name)
    for path in (gate,log,junit,pointer):add(path,"gate20__"+path.name)
    official_before=preflight/f"gate2-pointer-before-{GATE}.json"
    if official_before.is_file():add(official_before,"gate20__pointer_before_wrapper.json")
    copied_before={name:{"path":p.relative_to(ROOT).as_posix(),"sha256":sha(p),"bytes":p.stat().st_size} for name,p in mapping.items()}
    review={"scope":"Pretest read-only source review,0models/tests before fixes; first targeted invocation23PASS",
        "reviewer":"rq12_evidence_synthesis; parent-authorized review before first run",
        "initial_source_sha256":"360eaa696549c3a751cf2effb910800a431abb1841dc7ca74909a6c29d2d54f6",
        "final_source_sha256":before["src/knowledge_tracing/akt/graph_prototype.py"],
        "findings":[{"priority":"P2","reason":"Bank/vocab/graph/recipe digest omitted actual behavior-source bytes and post-construction source drift.",
                     "fix":"Dynamic native*.py +5root helpers +actual pinnedakt.py snapshot; checks constructor/batchprep/forward before+after; source identity in batch binding.",
                     "after_test":"Simulated inventory mismatch rejects before message/native path; no actual frozen source edits."},
                    {"reason":"A0 could register unvalidated caller branch parameters despite CPU/tiny contract.",
                     "fix":"A0 requires both message_module and readout None before native construction."}],
        "pre_fix_failed_tests":False,"old_pretest_physical_snapshot_available":False,
        "limitation":"Initial SHA and reasoning preserved from review messages, not reconstructed physical source or fabricated red tests.",
        "static_positive_review":"Six NonRasch ops, native mask/current-future causality, full-prefix OOV/globalrank and mixed same-forward path inspected before execution."}
    note="""# A0/A1 AKT graph prototype engineering — 08/11/2026

Đây là forward/backward toyCPU engineering, không fittedCG-AKT/RQ3/adoptS04/S05.
23targetedcasesPASS4.35s,0optimizersteps/fit/simulationevents; nativeoffparity và
jointbackbone/branchgradients, mixedinactiveprobabilities từcùngforward, OOVngoài
knownwindow khônggraphrescue. Featurechỉobserved-parent-mean, fixedc1/g1 A1;
A2/A3/learnedconfidence/gate/train_epochcollator/integration vẫnchưaimplement.

Giữ exactsource/test/readinessreport, targetedlog/XML/receipt+physicalbefore2owned
files. Preteststaticreview fixes córeasoning trướcpositivecases,0testsruns trướcfix,
khôngfakered. Native/helpers/upstreampinnedakt snapshots khôngbinary.

Wrapper36pre/postsourceSHA includes test, excludes upstream. Model/batch source36
includes upstream, excludes test;35paths overlap vàkhớpactualtargetedbefore/after.
Model guard36pre/post assertions đãpass; không cófull36runtimeidentityJSON riêng
được exporttrongtests. Model36archiveinventory làpost-runmaterialization, upstream
khớpactualGate20sourceSHA+constructorpinnedverification. Khôngbịa physicalpre-run
copieschoall36. Payloadseal chỉin-processconsistency, khôngcryptographicattestation.

Toymax12<context100: OOV/globalrank path verified, chưaempiricalfull100rollover.
Gate20CPUsoftware/syntheticPASS khônglàCUDA/trainingthroughput/efficacyresult.
No.pt/Parquet/ZIP/modelweights. Khôngsửabundle sauclosure; parenthandleindices/Git.
"""
    metadata={"kind":"AKT_A0_A1_GRAPH_FORWARD_BACKWARD_ENGINEERING_ONLY","weight_role":"engineering_only",
        "feature_recipe":"engineering-observed-parent-mean-v1","variants":["A0","A1"],
        "targeted":{"passed":23,"failed":0,"errors":0,"skipped":0,"pytest_seconds":4.35,"optimizer_steps":0},
        "gate20":{**counts,"report_sha256":sha(gate),"elapsed_seconds":report["elapsed_seconds"]},
        "parent_pass_reference":args.parent_pass_reference,"research_methodology_adopted":False,
        "gpu_cloud_or_realdata":False,"graph_aware_train_epoch_integration":False}
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=list(mapping.values()),note=note) as bundle:
        for name,path in mapping.items():
            with (bundle/name).open("xb") as target:target.write(path.read_bytes())
            assert sha(bundle/name)==copied_before[name]["sha256"]
        copied_after={name:sha(path) for name,path in mapping.items()}
        assert all(copied_after[name]==item["sha256"] for name,item in copied_before.items())
        inventory={"source_before":copied_before,"source_after_sha256":copied_after,
            "copied_output_sha256":{name:sha(bundle/name) for name in mapping},"exact_pre_post_copy":True}
        source_binding={"wrapper_actual_before":before,"wrapper_actual_after":trial["source_after_sha256"],
            "model36_materialized_at_archive":model_inventory,"overlap35_actual_before_after":covered,
            "upstream_sha_from_gate20":report["source"]["files"]["akt.py"],
            "limitations":"Runtime full36identity only internal assertions, not separately exported; archive materialization is not a physical pre-test snapshot of all files."}
        for name,value in (("copy_inventory.json",inventory),("source36_before_after_and_model_binding.json",source_binding),
                           ("pretest_static_review_provenance.json",review)):
            (bundle/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        names=sorted([*mapping,"README.md","execution.log","copy_inventory.json","source36_before_after_and_model_binding.json",
                      "pretest_static_review_provenance.json","force_add_paths.txt","manifest.json"])
        (bundle/"force_add_paths.txt").write_text("\n".join(f"research_tracking/runs/{RUN}/{name}" for name in names)+"\n",encoding="utf8")
    bundle=ROOT/"research_tracking/runs"/RUN
    verification=verify_evidence_bundle(bundle)
    manifest=json.loads((bundle/"manifest.json").read_text(encoding="utf8"))
    assert {p.name for p in bundle.iterdir()}==set(manifest["outputs_sha256"])|{"manifest.json"}
    assert sorted((bundle/"force_add_paths.txt").read_text().splitlines())==sorted(p.relative_to(ROOT).as_posix() for p in bundle.iterdir())
    result={**verification,"manifest_sha256":sha(bundle/"manifest.json"),"copied_sources":len(mapping),
            "source_pre_post_copy_exact":True,"all_output_sha_exact":True,"all_output_set_exact":True}
    with (OUT/"archive-closure-verification.json").open("x",encoding="utf8") as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
