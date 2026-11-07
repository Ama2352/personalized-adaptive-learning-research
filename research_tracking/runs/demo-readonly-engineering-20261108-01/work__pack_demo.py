"""Đóng bundle demo immutable; không chạy app/model/test và không ghi Git/index."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
from src.research_demo.evidence import EvidenceStore, PINS

OUT=Path(__file__).resolve().parent
RUN="demo-readonly-engineering-20261108-01"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
store=EvidenceStore()
receipt=json.loads((OUT/"trial04-receipt.json").read_text(encoding="utf8"))
assert receipt["exit_code"]==0 and receipt["source_sha256"]==receipt["source_post_sha256"]
for path,digest in receipt["source_sha256"].items():
    assert sha(ROOT/path)==digest,("current source differs from final tests",path)
suite=ET.parse(OUT/"pytest-trial04.xml").getroot().find("testsuite")
assert suite is not None and (suite.attrib["tests"],suite.attrib["failures"],suite.attrib["errors"],suite.attrib["skipped"])==("53","0","0","0")
mobile=json.loads((OUT/"browser-final-390.json").read_text(encoding="utf8"))
controls=json.loads((OUT/"browser-final-controls.json").read_text(encoding="utf8"))
assert mobile["width"]==390 and mobile["bodyWidth"]<=390 and not mobile["error"]
assert controls["parity"] and controls["routeParity"] and not controls["overflow"] and not controls["error"]
for name in ("preview-shutdown.json","preview02-shutdown.json","preview03-shutdown.json"):
    assert json.loads((OUT/name).read_text())["listener_closed"]
for name in ("browser-final-console.log","browser-final-390-console.log"):
    assert "Errors: 0, Warnings: 0" in (OUT/name).read_text()

mapping={}
def add(source,name):
    assert source.is_file() and name not in mapping and len(name)<240
    assert source.suffix not in (".pt",".parquet",".zip")
    mapping[name]=source
for path in sorted((ROOT/"src/research_demo").rglob("*.py"))+sorted((ROOT/"src/research_demo/static").glob("*"))+[ROOT/"tests/demo/test_viewer.py"]:
    add(path,"source__"+path.relative_to(ROOT).as_posix().replace("/","__"))
add(ROOT/"research_tracking/reports/demo_readiness_20261108.md","report__demo_readiness_20261108.md")
for path in sorted(OUT.iterdir()):
    if path.is_file() and path.suffix in (".json",".log",".xml",".py",".png"):
        add(path,"work__"+path.name)
for attempt in range(1,5):
    folder=OUT/f"source-before-trial0{attempt}"
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            add(path,f"trial0{attempt}-source__"+path.relative_to(folder).as_posix().replace("/","__"))
for run,_,filename,_ in PINS:
    for name in ("manifest.json",filename):
        add(ROOT/"research_tracking/runs"/run/name,"input__"+run+"__"+name)

before={name:{"path":source.relative_to(ROOT).as_posix(),"sha256":sha(source),"bytes":source.stat().st_size} for name,source in mapping.items()}
note="""# Demo MVP chỉ đọc artifact synthetic — 08/11/2026

Bundle kiểm kỹ thuật E11 một phần, không kết quả fitted CG-AKT/RQ3 hoặc efficacy.
Chỉ localhost Python stdlib + HTML/CSS/JS; replay GAM-KT/Paper2 fixed-stream,
không served action, không latent mastery probability. RQ2 API chỉ synthetic factorial.
3 manifest + 3 selected outputs được ghim SHA; input snapshots giữ đúng byte nguồn.
Model status là phạm vi hồ sơ của MVP, không runtime health check/model selector.

Final targeted trial04: 53pass/0fail/error/skip,1.92s. Giữ trial01 sandbox/temp +
assertion failure và trial02 Host fixture assertion failure; trial03 pass trước visualfix.
Source trước mỗi trial được lưu riêng, không gán final hash cho lịch sử.
Playwright desktop/control parity và true390px mobile không pageoverflow,console0error.
Files browser-final-mobile.json/mobile-final.png thực tế1037px; true390 là final-390.
Cả3 owned visual-QA listeners đã đóng; không model/simulator/GPU/dataset queries mới.

Đọc report__demo_readiness_20261108.md để biết command,nguồn,semantics/giới hạn.
copy_inventory.json ghi SHA input trước/sau copy; manifest hash mọi output sau closure.
Không sửa bundle sau closure. Source snapshots historical không tự là entrypoint hiện hành.
Không sửa index/state/Git và không copy model/Parquet/credentials.
"""
metadata={"kind":"READONLY_SYNTHETIC_ARTIFACT_VIEWER_ENGINEERING_PARTIAL_E11","rq":["RQ1","RQ2"],"model_or_simulator_runs":0,"real_data_queries":0,"gpu_or_cloud_execution":False,"formal_inference":False,"targeted_tests":{"passed":53,"failed":0,"errors":0,"skipped":0,"pytest_seconds":1.92},"source_verified_selected_inputs":store.provenance,"copy_policy":"exclusive flat copies, exact pre/post SHA; no historical edits"}
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=list(mapping.values()),note=note) as bundle:
    for name,source in mapping.items():
        with (bundle/name).open("xb") as target:
            target.write(source.read_bytes())
        assert sha(bundle/name)==before[name]["sha256"],name
    after={name:sha(source) for name,source in mapping.items()}
    assert all(after[name]==item["sha256"] for name,item in before.items())
    inventory={"source_inventory_before":before,"source_sha256_after":after,"copied_output_sha256":{name:sha(bundle/name) for name in mapping},"pre_post_source_identity":True,"exact_copy_identity":True,"excluded":"tmp fixture folders, pycache, .pt, Parquet, credentials; no dataset read", "test_source_binding":"source-before-trial04 and current hashes equal trial04-receipt; earlier trials retain their source snapshots"}
    (bundle/"copy_inventory.json").write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    expected=sorted([*mapping,"README.md","execution.log","copy_inventory.json","files-to-force-add.txt","manifest.json"])
    (bundle/"files-to-force-add.txt").write_text("\n".join(f"research_tracking/runs/{RUN}/{name}" for name in expected)+"\n",encoding="utf8")
bundle=ROOT/"research_tracking/runs"/RUN
verification=verify_evidence_bundle(bundle)
manifest=json.loads((bundle/"manifest.json").read_text(encoding="utf8"))
assert {p.name for p in bundle.iterdir()}==set(manifest["outputs_sha256"])|{"manifest.json"}
assert sorted((bundle/"files-to-force-add.txt").read_text().splitlines())==sorted(p.relative_to(ROOT).as_posix() for p in bundle.iterdir())
result={**verification,"manifest_sha256":sha(bundle/"manifest.json"),"copied_inputs":len(mapping),"all_source_pre_post_sha_exact":True,"all_output_sha_exact":True,"all_output_set_exact":True,"source_and_report_frozen":True}
with (OUT/"closure-verification.json").open("x",encoding="utf8") as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
