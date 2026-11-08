"""Current pack entrypoint: accepted Gate21 plus rejected historical Gate20.

Old pack_graph_prototype.py is an unexecuted historical Gate20 preparation;
do not use it as acceptance after Gate20 resource rejection.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
RUN="akt-graph-prototype-engineering-20261108-01"
GATE="20261108-elapsed-guard-21"
OLD="20261108-graph-prototype-20"
sys.path.insert(0,str(ROOT/"src"))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
from knowledge_tracing.akt.authorization import validate_gate2_elapsed_budget

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def xml_counts(path):
    suites=ET.parse(path).getroot().findall("testsuite")
    counts={key:sum(int(s.attrib[field]) for s in suites) for key,field in
            (("passed","tests"),("failed","failures"),("errors","errors"),("skipped","skipped"))}
    counts["passed"]-=counts["failed"]+counts["errors"]+counts["skipped"]
    return counts


def main():
    parser=argparse.ArgumentParser(description="Archive only parent-confirmed budget-accepted Gate21")
    parser.add_argument("--expected-gate-sha",required=True)
    parser.add_argument("--expected-pass-count",type=int,required=True)
    parser.add_argument("--parent-pass-reference",required=True)
    args=parser.parse_args()
    assert len(args.expected_gate_sha)==64 and args.parent_pass_reference.strip()
    preflight=ROOT/"artifacts/akt/preflight"
    gate=preflight/f"gate2-evidence-{GATE}.json"
    log=preflight/f"gate2-tests-{GATE}.log"
    xml=preflight/f"gate2-tests-{GATE}.xml"
    pointer=preflight/"gate2-current.json"
    assert gate.is_file() and sha(gate)==args.expected_gate_sha,"parent Gate21 report missing/stale"
    report=json.loads(gate.read_text(encoding="utf8"))
    expected={"passed":args.expected_pass_count,"failed":0,"errors":0,"skipped":0}
    assert report["status"]=="PASS" and report["test_result"]==expected and args.expected_pass_count>=23
    assert report["timeout_seconds"]==540
    validate_gate2_elapsed_budget(report["elapsed_seconds"],report["timeout_seconds"])
    assert sha(log)==report["test_log_sha256"] and sha(xml)==report["junit_sha256"] and xml_counts(xml)==expected
    current=json.loads(pointer.read_text(encoding="utf8"))
    assert current["evidence_file"]==gate.name and current["evidence_sha256"]==sha(gate)
    assert current["test_log_file"]==log.name and current["test_log_sha256"]==sha(log)
    build=report["build_hashes"]
    for relative,digest in build.items():
        p=ROOT/relative
        assert p.is_file() and p.resolve().is_relative_to(ROOT.resolve()) and sha(p)==digest,("new Gate21 source drift",relative)

    old_gate=preflight/f"gate2-evidence-{OLD}.json"
    old_log=preflight/f"gate2-tests-{OLD}.log"
    old_xml=preflight/f"gate2-tests-{OLD}.xml"
    audit=preflight/f"gate2-resource-audit-{OLD}.json"
    assert sha(old_gate)=="9d86b215bd936f04880bcd9bc775f2016784f279572109c39c017d46375fe351"
    assert sha(audit)=="e6a53ade40d01ee4229fcc3fe5b8d3e7364c984e3c37a632e4e49810b4c1a9c7"
    old=json.loads(old_gate.read_text(encoding="utf8"));rejection=json.loads(audit.read_text(encoding="utf8"))
    assert old["status"]=="PASS" and old["test_result"]=={"passed":724,"failed":0,"errors":0,"skipped":0}
    assert sha(old_log)==old["test_log_sha256"] and sha(old_xml)==old["junit_sha256"] and xml_counts(old_xml)==old["test_result"]
    assert rejection["status"]=="REJECTED_RESOURCE_BOUND" and rejection["execution_authorization"] is False
    assert rejection["original_evidence_sha256"]==sha(old_gate)
    rejected=False
    try:validate_gate2_elapsed_budget(old["elapsed_seconds"],old["timeout_seconds"])
    except (ValueError,TypeError):rejected=True
    assert rejected,"historical Gate20 must remain rejected"
    changes={p:{"old":s,"new":build.get(p)} for p,s in old["build_hashes"].items() if build.get(p)!=s}
    assert set(changes)=={"src/knowledge_tracing/akt/authorization.py","scripts/akt/refresh_gate2.py",
                          "tests/akt/test_runner.py","tests/akt/test_gate2_refresh.py"}

    trials=[json.loads((OUT/f"trial0{i}-receipt.json").read_text(encoding="utf8")) for i in (1,2)]
    for receipt in trials:
        assert receipt["exit_code"]==0 and receipt["optimizer_steps"]==0
        assert receipt["source_before_sha256"]==receipt["source_after_sha256"]
        for name,digest in receipt["trial_outputs_sha256"].items():assert sha(OUT/name)==digest
    assert xml_counts(OUT/"pytest-trial01.xml")==xml_counts(OUT/"pytest-trial02.xml")=={"passed":23,"failed":0,"errors":0,"skipped":0}
    first,latest=trials
    assert latest["functional_pass"] is True and latest["resource_verdict"]=="ACCEPTED" and latest["post_elapsed_cap_seconds"]==30
    assert all(math.isfinite(v) and 0<=v<=30 for v in (latest["elapsed_seconds"],latest["elapsed_wall_seconds"]))
    assert latest["cumulative_controller_seconds"]<=90
    before=latest["source_before_sha256"]
    assert len(before)==36
    assert {p for p,s in first["source_before_sha256"].items() if before[p]!=s}=={"src/knowledge_tracing/akt/authorization.py"}
    for relative,digest in before.items():assert sha(ROOT/relative)==digest==build[relative]
    for folder,values in (("source36-trial01-materialized",first["source_before_sha256"]),
                           ("source36-trial02-before",before),("source36-trial02-after",latest["source_after_sha256"])):
        for relative,digest in values.items():assert sha(OUT/folder/relative)==digest
    readiness=ROOT/"research_tracking/reports/akt_graph_prototype_readiness_20261108.md"
    assert sha(readiness)=="d15da2a060522b0955aefbd016f7d1415554fbbddbe885a2aa855f3c64d54dad"
    assert sha(OUT/"readiness_report_before_dependency_update_a7.md")=="a7ae0826617821383a9aeae5d499b9dd15bef73ef20d9a94e347d60fda98780f"
    native=sorted((ROOT/"src/knowledge_tracing/akt").glob("*.py"))
    helpers=[ROOT/"src/knowledge_tracing"/name for name in ("simulator_data.py","simulator_bridge.py","shared_kt.py","graph_context.py","graph_augmentation.py")]
    upstream=ROOT/"artifacts/akt/dependencies/upstream/akt.py"
    assert sha(upstream)==report["source"]["files"]["akt.py"]==old["source"]["files"]["akt.py"]
    model_inventory={p.relative_to(ROOT).as_posix():sha(p) for p in native+helpers+[upstream]}
    assert len(model_inventory)==36 and len(set(model_inventory)&set(before))==35

    mapping={}
    def add(p,name):
        assert p.is_file() and name not in mapping and len(name)<240 and p.suffix not in (".pt",".parquet",".zip")
        mapping[name]=p
    for relative in model_inventory:add(ROOT/relative,"newsource__"+relative.replace("/","__"))
    add(ROOT/"tests/akt/test_graph_prototype.py","newsource__test_graph_prototype.py")
    add(readiness,"readiness_report_with_resource_addendum.md")
    add(ROOT/"src/knowledge_tracing/evidence.py","evidence_helper.py")
    for p in sorted(OUT.iterdir()):
        if p.is_file() and (p.suffix in (".json",".log",".xml",".py",".md") or ".before-trial" in p.name):add(p,"work__"+p.name)
    for folder,prefix in (("source36-trial01-materialized","oldsource__"),("source36-trial02-before","targeted02-before__"),("source36-trial02-after","targeted02-after__")):
        for p in sorted((OUT/folder).rglob("*.py")):add(p,prefix+p.relative_to(OUT/folder).as_posix().replace("/","__"))
    for p in (old_gate,old_log,old_xml,audit):add(p,"gate20_rejected__"+p.name)
    for p in (gate,log,xml,pointer):add(p,"gate21_accepted__"+p.name)
    for tag in (OLD,GATE):
        p=preflight/f"gate2-pointer-before-{tag}.json"
        if p.is_file():add(p,"pointer_before__"+p.name)
    historical_fix=ROOT/"research_tracking/runs/gate2-budget-fix-20261108-01"
    historical_manifest=json.loads((historical_fix/"manifest.json").read_text(encoding="utf8"))
    assert sha(historical_fix/"manifest.json")=="d43bcfdcbc4af505271cd7b6b1a2f2f66b37b0a777af0c7adeb9b999c23b5760"
    old_guard_sources={"pre_fix__authorization.py.before":"src/knowledge_tracing/akt/authorization.py",
        "pre_fix__refresh_gate2.py.before":"scripts/akt/refresh_gate2.py","pre_fix__test_gate2_refresh.py.before":"tests/akt/test_gate2_refresh.py",
        "pre_fix__test_runner.py.before":"tests/akt/test_runner.py"}
    for name,relative in old_guard_sources.items():
        p=historical_fix/name
        assert sha(p)==historical_manifest["outputs_sha256"][name]==old["build_hashes"][relative]
        add(p,"old_guard_source__"+name)
    for name in ("manifest.json","pre_fix__source_inventory.json","source_binding_comparison.json"):
        p=historical_fix/name
        if name!="manifest.json":assert sha(p)==historical_manifest["outputs_sha256"][name]
        add(p,"gate_fix_provenance__"+name)
    fix=ROOT/"artifacts/akt/local-tests/gate2-budget-fix-trial-20261108-02"
    for p in sorted(fix.iterdir()):
        if p.is_file() and p.name in {"authorization.py.snapshot","refresh_gate2.py.snapshot","test_gate2_refresh.py.snapshot","test_runner.py.snapshot",
                                     "final_verification.json","report_verification.json","run.json","pytest.log","pytest.xml","run_controller.py"}:
            add(p,"elapsed_fix__"+p.name)
    snapshot_map={"authorization.py.snapshot":"src/knowledge_tracing/akt/authorization.py","refresh_gate2.py.snapshot":"scripts/akt/refresh_gate2.py",
                  "test_gate2_refresh.py.snapshot":"tests/akt/test_gate2_refresh.py","test_runner.py.snapshot":"tests/akt/test_runner.py"}
    for name,relative in snapshot_map.items():assert sha(fix/name)==build[relative]
    assert xml_counts(fix/"pytest.xml")=={"passed":47,"failed":0,"errors":0,"skipped":0}
    copied_before={name:{"path":p.relative_to(ROOT).as_posix(),"sha256":sha(p),"bytes":p.stat().st_size} for name,p in mapping.items()}
    provenance={"pretest_review":{"initial_source_sha256":"360eaa696549c3a751cf2effb910800a431abb1841dc7ca74909a6c29d2d54f6",
        "findings":"Missing actual helper/upstream source binding; A0 registering unvalidated branch parameters",
        "fixed_before_first_run":True,"observed_pre_fix_failed_tests":False,"physical_initial_snapshot_available":False,
        "positive_after":"23targeted tests passed; no fabricated red tests; constructor/batch/forward source guards and A0-none tested"},
        "gate20":{"functional_passed":724,"resource_verdict":"REJECTED","elapsed_seconds":old["elapsed_seconds"],
                  "timeout_seconds":old["timeout_seconds"],"report_sha256":sha(old_gate),"audit_sha256":sha(audit),
                  "cause":"UNRESOLVED; no throughput/regression/cost inference"},
        "gate21":{"functional_counts":expected,"resource_verdict":"ACCEPTED","elapsed_seconds":report["elapsed_seconds"],"timeout_seconds":540},
        "four_gate_build_changes":changes,"targeted_dependency_change":"authorization.py only; old/new byte versions separately preserved",
        "four_old_guard_source_basis":{"bundle":"gate2-budget-fix-20261108-01","manifest_sha256":sha(historical_fix/"manifest.json"),"exact_old_gate20_hashes":True},
        "snapshot_limit":"Old35unchanged wrapper files materialized by exact historical SHA; oldauth from immutable historical bundle. Never claim all old snapshots were physical pre-run copies."}
    note="""# A0/A1 graph prototype engineering — accepted Gate21, rejected Gate20

23targetedcases CPU forward/backward,0optimizer/fit/simulationevents. Feature
engineering-observed-parent-mean-v1, A1fixedc1/g1. Not S04/S05 adoption, fullCG-AKT,
A2/A3/confidenceestimator/gate/graph-aware train_epoch integration or efficacy.
Max12events<context100: OOV/globalrank proof, not full100rollover runtime proof.
Payload/source binding is in-process consistency, not cryptographic attestation.

Gate20 original functional724PASS is PRESERVED but resourceREJECTED1083.995>540;
its audit/revoked meaning is separate, never accepted by this bundle. Gate21 must
PASS functionalcounts+strictpostelapsed<=540 and published currentpointer beforecopy.
No elapsed regression/cost inference. Raw historical Gate20 report bytes unchanged.

Targeted01 source/reporta7 remainhistorical. Targeted02 oneauthorized rerun after
auth elapsed guard change has23PASS and explicitQPC/wallpostcheck<=30,0updates.
Original graph source/test c7e9/5e2a unchanged. Old/new36wrapper snapshots separate;
oldauth from existingimmutable bytes, not reconstructed from newsource. Old35others
materializedcurrentbytes equal historicalSHA, not assertedphysicalpre-run copies.
Model36inventory includes upstream/excludes test; wrapper36 includes test/excludes
upstream;35overlap. Source binding modulechecks were actualassertions, fullmodel36
identity was not independentlyexported duringtests; archiveinventory ismaterialized.

Preteststaticreviewfixes preceded first run; no fakepre-fixfailedtests. See report,
copyinventory/provenance for restrictions. No binaryweights/pt/Parquet/ZIP. No source,
oldbundle,index/state/Git modifications. Do not modify this bundle afterclosure.
Old work__pack_graph_prototype.py is historical unexecuted Gate20 preparation,
not current acceptance entrypoint; current pack entrypoint uses Gate21 checks.
"""
    metadata={"kind":"AKT_A0_A1_GRAPH_ENGINEERING_WITH_RESOURCE_REJECTION_HISTORY","weight_role":"engineering_only",
        "targeted01":{"passed":23,"optimizer_steps":0,"elapsed_seconds":first["elapsed_seconds"]},
        "targeted02":{"passed":23,"optimizer_steps":0,"elapsed_seconds":latest["elapsed_seconds"],"wall_seconds":latest["elapsed_wall_seconds"],"resource_verdict":"ACCEPTED","cap_seconds":30},
        "gate20_functional_passed":724,"gate20_resource_verdict":"REJECTED","gate21":{**expected,"elapsed_seconds":report["elapsed_seconds"],"timeout_seconds":540,"resource_verdict":"ACCEPTED"},
        "parent_pass_reference":args.parent_pass_reference,"research_adoption":False,"gpu_realdata_or_cloud":False}
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=list(mapping.values()),note=note) as bundle:
        for name,p in mapping.items():
            with (bundle/name).open("xb") as target:target.write(p.read_bytes())
            assert sha(bundle/name)==copied_before[name]["sha256"]
        copied_after={name:sha(p) for name,p in mapping.items()}
        assert all(copied_after[name]==entry["sha256"] for name,entry in copied_before.items())
        outputs={"copy_inventory.json":{"source_before":copied_before,"source_after_sha256":copied_after,"copied_output_sha256":{n:sha(bundle/n) for n in mapping},"exact_pre_post_copy":True},
            "old_new_source_binding.json":{"targeted01_actual_before":first["source_before_sha256"],"targeted01_actual_after":first["source_after_sha256"],
                "targeted02_actual_before":before,"targeted02_actual_after":latest["source_after_sha256"],"model36_new_materialized":model_inventory,"gate21_build_hashes":build},
            "review_resource_and_dependency_provenance.json":provenance}
        for name,value in outputs.items():(bundle/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        names=sorted([*mapping,*outputs,"README.md","execution.log","force_add_paths.txt","manifest.json"])
        (bundle/"force_add_paths.txt").write_text("\n".join(f"research_tracking/runs/{RUN}/{name}" for name in names)+"\n",encoding="utf8")
    bundle=ROOT/"research_tracking/runs"/RUN
    verified=verify_evidence_bundle(bundle)
    manifest=json.loads((bundle/"manifest.json").read_text(encoding="utf8"))
    assert {p.name for p in bundle.iterdir()}==set(manifest["outputs_sha256"])|{"manifest.json"}
    assert sorted((bundle/"force_add_paths.txt").read_text().splitlines())==sorted(p.relative_to(ROOT).as_posix() for p in bundle.iterdir())
    result={**verified,"manifest_sha256":sha(bundle/"manifest.json"),"copied_sources":len(mapping),"all_output_sha_exact":True,"all_output_set_exact":True,"source_pre_post_copy_exact":True}
    with (OUT/"archive-closure-verification-gate21.json").open("x",encoding="utf8") as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
