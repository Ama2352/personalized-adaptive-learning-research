"""Chỉ chạy sau parent Gate19 PASS; không train/test/GPU/Git writes.

Ví dụ arguments cần điền từ parent actual PASS receipt:
  --expected-gate-sha <SHA> --expected-pass-count <N> --parent-pass-reference <text>
Mọi guard trước record_evidence_run: không tạo bundle đang chạy nếu Gate chưa sẵn.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

RUN="akt-simulator-engineering-20261108-01"
GATE="20261108-sim-trainer-19"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description="Đóng evidence chỉ sau parent-confirmed Gate19 PASS")
    parser.add_argument("--expected-gate-sha",required=True)
    parser.add_argument("--expected-pass-count",type=int,required=True)
    parser.add_argument("--parent-pass-reference",required=True)
    args=parser.parse_args()
    assert len(args.expected_gate_sha)==64 and args.parent_pass_reference.strip()
    preflight=ROOT/"artifacts/akt/preflight"
    gate=preflight/f"gate2-evidence-{GATE}.json"
    log=preflight/f"gate2-tests-{GATE}.log"
    junit=preflight/f"gate2-tests-{GATE}.xml"
    pointer=preflight/"gate2-current.json"
    assert gate.is_file() and sha(gate)==args.expected_gate_sha,"parent-confirmed Gate19 report missing/stale"
    report=json.loads(gate.read_text(encoding="utf8"))
    expected={"passed":args.expected_pass_count,"failed":0,"errors":0,"skipped":0}
    assert report["status"]=="PASS" and report["test_result"]==expected and args.expected_pass_count>=40
    assert sha(log)==report["test_log_sha256"] and sha(junit)==report["junit_sha256"]
    suites=ET.parse(junit).getroot().findall("testsuite")
    counts={key:sum(int(s.attrib[field]) for s in suites) for key,field in (("passed","tests"),("failed","failures"),("errors","errors"),("skipped","skipped"))}
    counts["passed"]-=counts["failed"]+counts["errors"]+counts["skipped"]
    assert counts==expected,"Gate19 JUnit/report counts differ"
    current=json.loads(pointer.read_text(encoding="utf8"))
    assert current["evidence_file"]==gate.name and current["evidence_sha256"]==sha(gate)
    assert current["test_log_file"]==log.name and current["test_log_sha256"]==sha(log)
    build=report["build_hashes"]
    for relative,digest in build.items():
        path=ROOT/relative
        assert path.resolve().is_relative_to(ROOT.resolve()) and path.is_file()
        assert sha(path)==digest,("Gate19 source-bound mismatch",relative)

    final=json.loads((OUT/"trial03-receipt.json").read_text(encoding="utf8"))
    assert final["exit_code"]==0 and final["actual_optimizer_steps"]==2
    assert final["source_before_sha256"]==final["source_after_sha256"]
    for relative,digest in final["source_before_sha256"].items():
        assert sha(ROOT/relative)==digest
    happy=ROOT/"artifacts/akt/synthetic/simeng-20261108-complete-14290678"
    partial=ROOT/"artifacts/akt/synthetic/simeng-20261108-partial-2412af63"
    invocation=json.loads((happy/"invocation.json").read_text(encoding="utf8"))
    outcome=json.loads((happy/"result.json").read_text(encoding="utf8"))
    sources=invocation["sources_sha256"]
    assert len(sources)==32 and sources==outcome["sources_post_sha256"]
    for relative,digest in sources.items():
        assert build[relative]==digest==sha(ROOT/relative),("native32/Gate19 binding mismatch",relative)
    test="tests/akt/test_simulator_engineering.py"
    assert build[test]==final["source_before_sha256"][test]==sha(ROOT/test)
    assert outcome["reload_max_abs_delta"]==0 and outcome["optimizer_steps"]==1
    assert outcome["selection_coverage"]["expected_rows"]==4 and outcome["selection_coverage"]["known_rows"]==3
    assert outcome["selection_coverage"]["unseen_rows"]==1
    assert (partial/"failure.json").is_file() and not (partial/"epoch1.pt").exists() and not (partial/"result.json").exists()

    mapping={}
    def add(path,name):
        assert path.is_file() and name not in mapping and len(name)<240
        assert path.suffix not in (".pt",".parquet",".zip"),"binary/model excluded"
        mapping[name]=path
    for relative in sources:
        add(ROOT/relative,"source__"+relative.replace("/","__"))
    add(ROOT/test,"source__tests__akt__test_simulator_engineering.py")
    add(ROOT/"research_tracking/reports/akt_simulator_engineering_readiness_20261108.md","readiness_report.md")
    add(ROOT/"src/knowledge_tracing/evidence.py","evidence_helper.py")
    for path in sorted(OUT.iterdir()):
        if path.is_file() and (path.suffix in (".json",".log",".xml",".py",".md") or ".before-trial" in path.name):
            add(path,"work__"+path.name)
    heavy=[]
    total_steps=0
    for trial in (1,2,3):
        receipt=json.loads((OUT/f"trial0{trial}-receipt.json").read_text(encoding="utf8"))
        total_steps+=receipt["actual_optimizer_steps"]
        for basename,relative in (("simulator_engineering.py","src/knowledge_tracing/akt/simulator_engineering.py"),
                                  ("test_simulator_engineering.py",test)):
            assert sha(OUT/f"{basename}.before-trial0{trial}")==receipt["source_before_sha256"][relative]
        for relative,digest in receipt["new_outputs_sha256"].items():
            path=ROOT/relative
            assert sha(path)==digest,("historical trial output drift",relative)
            if path.suffix==".pt":
                heavy.append({"path":relative,"sha256":digest,"bytes":path.stat().st_size,"copied":False,"scope":"engineering_only native toy checkpoint; no deserialize"})
            else:
                assert path.suffix in (".json",".log")
                add(path,"trial0"+str(trial)+"__"+path.parent.name+"__"+path.name)
    assert total_steps==6 and total_steps<=16
    for path in (gate,log,junit,pointer):
        add(path,"gate19__"+path.name)
    official_before=preflight/f"gate2-pointer-before-{GATE}.json"
    if official_before.is_file():
        add(official_before,"gate19__pointer_before_wrapper.json")
    before={name:{"path":path.relative_to(ROOT).as_posix(),"sha256":sha(path),"bytes":path.stat().st_size}
            for name,path in mapping.items()}
    reasoning={"provenance":"Parent read-only source review after trial02; not reproduced pre-fix failures",
        "ambient_cpu_device":{"before_source_sha256":"5ae344b34bfecc8d7e574d33fac67f941a4df5a8d3bf7c3d817b8017e25b07d9",
            "reason":"Native constructor allocates before .to(cpu); Adam lazy state follows ambient default device. Generic save_checkpoint may collect CUDA RNG when visible.",
            "fix":"Explicit CPU context around full run/reload and reject CUDA available/initialized before constructors/load.",
            "observed_after":"Happy actual update+internal reload under enclosing meta; direct meta reload0updates; mocked CUDA availability/init rejection0GPU.",
            "observed_failed_pre_fix_test":False},
        "dependency_binding":{"before":"9 selected native source files, omitted behavior imports",
            "reason":"inference_recipe, encoding/provenance/resources/types and shared simulator history/domain behavior could drift without subset inventory changing.",
            "fix":"Dynamically enumerate all29native py plus3root shared modules; no test file in model identity.",
            "observed_after":"Exact32source binding pre/post actual lifecycle; simulated resources.py mismatch rejects before torch.load.",
            "observed_failed_pre_fix_test":False},
        "history":"trial01/02 PASS are genuine historical snapshots; no fabricated red tests; first report existed after trial02 and is preserved in report-before-parent-fixes.md",
        "rng":"Python/NumPy/Torch global seeds and checkpoint RNG restoration are not caller-RNG preserving"}
    note="""# AKT simulator engineering-only lifecycle — 08/11/2026

Đây là plumbing một epoch toy, không scientific simulator trainer/selected-fit/RQ3.
Reuse native AKT d32CPU smoke, train_epoch/windows/checkpoint primitives; không giả
Junyifold, collector, calibration/final/refit, production bridge, realdata/GPU/cloud.
Explicit approval/budgets:2train+1selection learners,12events/learner,4steps,60s,
2GiBRSS/floor1GiB; cooperative checks, không OS isolation/hardkill.

Final trial03 40pass/17.67s; happy8train targets/1update,selection3known+1OOV,
checkpoint reload delta0. Intentionalpartial1step cófailure JSON/log vàkhông.pt/result.
3targetedinvocations:6totaloptimizersteps. Giữ trial01=33pass vàtrial02=36pass/source
riêng; fixes CPUambientdevice/dependencycoverage đến từ parent source review,
không có pre-fix failedtests được thực hiện cho hai review findings.

Gate19 chỉ CPU software/synthetic acceptance; report/log/XML/currentpointer được
kiểm exactSHA vàbuild binding trướccopy. Không nâng thành CUDA/fulltraining/efficacy.
Source32 snapshots là currentbytes khớp actualtrial03pre/postSHA+Gate19SHA;
không tuyên bố cả32files đều có physicalcopy trướctrial03. Hai owned source files
có physical pre-trial snapshots cho cả3lượt. Historical subset9 coverage giữ nguyên.

Không copy.pt/Parquet/binaries; heavy_checkpoint_inventory.json ghi exacthash/size.
copy_inventory.json cópre/postsource vàcopySHA. Sauclosure không sửabundle.
Đọc readiness_report.md vàparent_review_fix_provenance.json đểbiếtsemantics/limits.
S04/S05vẫnpending. Không bảo toàncallerRNG; chỉCPUdevicecontext/threadcount scope.
"""
    metadata={"kind":"AKT_SIMULATOR_ENGINEERING_ONLY_CPU_LIFECYCLE","weight_role":"engineering_only",
        "targeted_final":{"passed":40,"failed":0,"errors":0,"skipped":0,"pytest_seconds":17.67},
        "targeted_cumulative_optimizer_steps":total_steps,"gate19":{**expected,"report_sha256":sha(gate),"elapsed_seconds":report["elapsed_seconds"]},
        "parent_pass_reference":args.parent_pass_reference,"realdata_or_research_simulation":False,"gpu_or_cloud_execution":False,
        "source_snapshot_basis":"current exact bytes match32actualpre/postSHA andGate19; not all32physicalpre-run copies",
        "source_commit_execution":report["source_commit"]}
    with record_evidence_run(ROOT,RUN,metadata=metadata,sources=list(mapping.values()),note=note) as bundle:
        for name,path in mapping.items():
            with (bundle/name).open("xb") as target:target.write(path.read_bytes())
            assert sha(bundle/name)==before[name]["sha256"]
        after={name:sha(path) for name,path in mapping.items()}
        assert all(after[name]==item["sha256"] for name,item in before.items()),"source changed during copy"
        for name,value in (("copy_inventory.json",{"source_before":before,"source_after_sha256":after,
                            "copied_output_sha256":{name:sha(bundle/name) for name in mapping},"exact_pre_post_copy":True}),
                           ("native32_before_after.json",{"before":sources,"after":outcome["sources_post_sha256"],"gate19":{p:build[p] for p in sources},
                            "snapshot_basis":"post-run materialization matches recordedpre/post andGate19; no fabricated physicalpre-run certificate"}),
                           ("heavy_checkpoint_inventory.json",heavy),("parent_review_fix_provenance.json",reasoning)):
            (bundle/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        names=sorted([*mapping,"README.md","execution.log","copy_inventory.json","native32_before_after.json",
                      "heavy_checkpoint_inventory.json","parent_review_fix_provenance.json","force_add_paths.txt","manifest.json"])
        (bundle/"force_add_paths.txt").write_text("\n".join(f"research_tracking/runs/{RUN}/{name}" for name in names)+"\n",encoding="utf8")
    bundle=ROOT/"research_tracking/runs"/RUN
    verification=verify_evidence_bundle(bundle)
    manifest=json.loads((bundle/"manifest.json").read_text(encoding="utf8"))
    assert {p.name for p in bundle.iterdir()}==set(manifest["outputs_sha256"])|{"manifest.json"}
    assert sorted((bundle/"force_add_paths.txt").read_text().splitlines())==sorted(p.relative_to(ROOT).as_posix() for p in bundle.iterdir())
    result={**verification,"manifest_sha256":sha(bundle/"manifest.json"),"copied_sources":len(mapping),
            "source_pre_post_copy_exact":True,"all_output_sha_exact":True,"all_output_set_exact":True}
    with (OUT/"archive-closure-verification.json").open("x",encoding="utf8") as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
