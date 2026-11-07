"""Synthetic stored-artifact viewer: integrity, semantic parity and real HTTP."""
import gzip
import hashlib
import http.client
import json
import shutil
import threading

import pytest

from src.research_demo import evidence
from src.research_demo.evidence import EvidenceError, EvidenceStore
from src.research_demo.server import make_server


@pytest.fixture(scope="module")
def store():
    return EvidenceStore()


@pytest.fixture(scope="module")
def serving(store):
    server = make_server(0, store=store)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    yield server.server_port
    server.shutdown()
    server.server_close()
    worker.join(timeout=2)
    assert not worker.is_alive()


def request(port, target, method="GET", headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request(method, target, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_verified_complete_input_inventory(store):
    assert len(store.rows) == 3240
    assert {(k[0], k[1], k[2]) for k in store.rows} == {(p,s,v) for p in evidence.PROFILES for s in evidence.SEEDS for v in evidence.VARIANTS}
    for run, manifest_sha, filename, sha in evidence.PINS:
        folder = evidence.ROOT / "research_tracking" / "runs" / run
        assert hashlib.sha256((folder/"manifest.json").read_bytes()).hexdigest() == manifest_sha
        assert hashlib.sha256((folder/filename).read_bytes()).hexdigest() == sha


@pytest.mark.parametrize("variant", evidence.VARIANTS)
def test_every_snapshot_is_exact_projection_not_estimated_state(store, variant):
    for profile in evidence.PROFILES:
        for seed in evidence.SEEDS:
            for step in range(evidence.STEPS):
                raw = store.rows[(profile,seed,variant,step)]
                result = store.snapshot(profile,seed,variant,step)
                assert result["p_correct_logged_query"] == raw["probability"]
                assert result["concept_preview"] == raw["action"]
                assert result["ready"] == raw["ready"]
                assert {c for c,v in result["mastered_bool"].items() if v} == set(raw["mastered"])
                assert all(type(v) is bool for v in result["mastered_bool"].values())
                assert result["route_preview"] == [store.rows[(profile,seed,variant,i)]["action"] for i in range(step+1)]
                assert not ({"mastery", "correct", "p_true", "theta_before", "question", "learner_id"} & result.keys())


def test_curated_catalog_synthetic_only_and_missing_confidence(store):
    catalog = store.catalog()
    assert catalog["graph_confidence_gate"]["available"] is False
    assert {r["candidate"]:r["changed_action_preview_events"] for r in catalog["rq1"]} == {"graph_package":22,"empty_graph_package":0}
    assert {r["profile"]:r["seed_blocks"] for r in catalog["rq2_synthetic"]["profiles"]} == {"PG":10,"PY":10,"PYH":10}
    assert "junyi" not in catalog and "junyi" not in catalog["rq2_synthetic"]
    assert not {"learners", "raw", "test_predictions"} & catalog.keys()
    assert len(catalog["models"]) == 3
    assert "không phải replay AKT" in catalog["replay_model"]


@pytest.mark.parametrize("slot,filename", [(0,"manifest.json"),(0,"traces.jsonl.gz"),(1,"analysis.json"),(2,"conditions.json")])
def test_startup_tamper_fails_closed(tmp_path, monkeypatch, slot, filename):
    for run,_,name,_ in evidence.PINS:
        folder = tmp_path / "research_tracking" / "runs" / run
        folder.mkdir(parents=True)
        for selected in ("manifest.json",name):
            shutil.copyfile(evidence.ROOT/"research_tracking"/"runs"/run/selected,folder/selected)
    changed = tmp_path/"research_tracking"/"runs"/evidence.PINS[slot][0]/filename
    changed.write_bytes(changed.read_bytes()+b" ")
    monkeypatch.setattr(evidence,"ROOT",tmp_path)
    with pytest.raises(EvidenceError,match="SHA"):
        make_server(0)


def test_missing_source_and_path_escape_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence,"ROOT",tmp_path)
    with pytest.raises(EvidenceError):
        make_server(0)
    with pytest.raises(EvidenceError):
        evidence.bounded_read(tmp_path.parent/"outside.json",100)


def test_bounded_file_and_gzip(tmp_path,monkeypatch):
    monkeypatch.setattr(evidence,"ROOT",tmp_path)
    path=tmp_path/"oversize"
    path.write_bytes(b"x"*33)
    with pytest.raises(EvidenceError,match="bytes"):
        evidence.bounded_read(path,32)
    with pytest.raises(EvidenceError,match="giải nén"):
        evidence.decode_trace(gzip.compress(b" "*(16*1024*1024+1)))


@pytest.mark.parametrize("data",[b"not gzip",gzip.compress(b"{}\n"),b"\x1f\x8b"])
def test_bad_or_incomplete_gzip_rejected(data):
    with pytest.raises(EvidenceError):
        evidence.decode_trace(data)


@pytest.mark.parametrize("data",[b'{"x":1,"x":2}',b'{"x":NaN}',b'[[[',b'\xff'])
def test_invalid_json_rejected(data):
    with pytest.raises(EvidenceError):
        evidence.parse_json(data)


@pytest.mark.parametrize("kind",["duplicate","learner","step","probability","ready","concepts"])
def test_invalid_trace_contract_rejected(store,kind):
    rows=list(store.rows.values())
    row=dict(rows[0]);rows[0]=row
    if kind=="duplicate":rows[0]=rows[1]
    elif kind=="learner":row["learner_id"]="real-learner"
    elif kind=="step":row["event_id"]="012"
    elif kind=="probability":row["probability"]=float("nan")
    elif kind=="ready":row["ready"]=["not-in-inventory"]
    else:row["mastery"]={}
    with pytest.raises(EvidenceError):
        EvidenceStore._index(rows)


@pytest.mark.parametrize("route,mime",[("/","text/html"),("/assets/demo.css","text/css"),("/assets/demo.js","text/javascript"),("/api/catalog","application/json"),("/api/replay?profile=PG&seed=20000&variant=graph_package&step=0","application/json")])
def test_real_http_fixed_routes_and_security_headers(serving,route,mime):
    status,headers,body=request(serving,route)
    assert status==200 and body
    assert headers["Content-Type"].startswith(mime)
    assert headers["Cache-Control"]=="no-store"
    assert headers["X-Content-Type-Options"]=="nosniff"
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert "Access-Control-Allow-Origin" not in headers
    if route.startswith("/api/replay"):
        assert json.loads(body)["p_correct_logged_query"]==0.4941767100654444


@pytest.mark.parametrize("query",["","profile=PG&seed=20000&variant=graph_free&step=-1","profile=PG&seed=20000&variant=graph_free&step=120","profile=PG&seed=20000&variant=graph_free&step=00","profile=PG&seed=20000&variant=graph_free&step=1&file=secret","profile=PG&seed=20000&variant=graph_free&step=1&step=2","profile=PG&seed=20000&variant=other&step=1","profile=unknown&seed=20000&variant=graph_free&step=1","profile=PG&seed=42&variant=graph_free&step=1","profile=PG&seed=20000&variant=graph_free&step=%EF%BC%91","profile=PG&seed=20000&variant=graph_free&step=1.0"])
def test_http_query_allowlist(serving,query):
    assert request(serving,"/api/replay?"+query)[0]==400


@pytest.mark.parametrize("route",["/../dataset/secret","/%2e%2e/dataset/secret","/assets/../evidence.py","/api/file?path=dataset","/assets/demo.js?x=1","/api/catalog?x=1","/exports"])
def test_no_filesystem_or_export_routes(serving,route):
    assert request(serving,route)[0]==404


def test_head_and_no_mutations_or_foreign_origin(serving):
    assert request(serving,"/",method="HEAD")[2]==b""
    for method in ("POST","PUT","PATCH","DELETE","OPTIONS"):
        assert request(serving,"/api/catalog",method=method)[0]==405
    assert request(serving,"/api/catalog",headers={"Host":f"evil.example:{serving}"})[0]==403
    assert request(serving,"/api/catalog",headers={"Origin":"http://evil.example"})[0]==403
    assert request(serving,"/api/catalog",headers={"Origin":f"http://127.0.0.1:{serving}"})[0]==200
    assert request(serving,"http://evil.example/api/catalog")[0]==400


@pytest.mark.parametrize("host",["0.0.0.0","::","localhost","192.168.1.1"])
def test_never_bind_non_loopback_or_ambiguous_host(host):
    with pytest.raises(ValueError,match="127.0.0.1"):
        make_server(0,host=host)


def test_ui_safe_dom_and_explicit_preview_boundary():
    from src.research_demo.server import STATIC
    js=(STATIC/"demo.js").read_text(encoding="utf8")
    html=(STATIC/"index.html").read_text(encoding="utf8")
    assert "innerHTML" not in js and "eval(" not in js and "document.write" not in js
    assert "textContent" in js
    assert "Không phải action đã phục vụ" in html
    assert "không phải P(đã biết)" in html
    assert "confidence giả" in html
    assert "http://" not in html and "https://" not in html
