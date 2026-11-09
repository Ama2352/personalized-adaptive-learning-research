"""Synthetic stored-artifact viewer: integrity, semantic parity and real HTTP."""
import gzip
import csv
import copy
import io
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
    assert [r["id"] for r in catalog["models"]] == ["A0", "A1_EXPERT", "A1_LEARNED", "A2_EXPERT", "A2_LEARNED", "A3_EXPERT", "A3_LEARNED", "SAKT", "GKT"]
    assert all(r["replay_available"] is False for r in catalog["models"])
    assert catalog["replay_models"][0]["replay_available"] is True
    assert catalog["reference_models"][0]["name"] == "BKT"
    assert catalog["reference_models"][0]["replay_available"] is False
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
    assert request(serving,"/favicon.ico")[0]==204
    for method in ("POST","PUT","PATCH","DELETE","OPTIONS"):
        assert request(serving,"/api/catalog",method=method)[0]==405
    assert request(serving,"/api/catalog",headers={"Host":f"evil.example:{serving}"})[0]==403
    assert request(serving,"/api/catalog",headers={"Origin":"http://evil.example"})[0]==403
    assert request(serving,"/api/catalog",headers={"Origin":f"http://127.0.0.1:{serving}"})[0]==200
    assert request(serving,"http://evil.example/api/catalog",headers={"Host":f"127.0.0.1:{serving}"})[0]==400


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


@pytest.fixture(scope="module")
def closed_raw():
    folder=evidence.ROOT/"research_tracking/runs"/evidence.CLOSED_RUN
    with gzip.open(folder/evidence.CLOSED_PINS[0][0],"rt",encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def test_closed_pins_complete_projection_and_no_raw_or_oracle_fields(store,closed_raw):
    assert len(store.closed_rows)==3240 and len(store.closed_prefix)==2160 and len(store.closed_rankings)==18
    folder=evidence.ROOT/"research_tracking/runs"/evidence.CLOSED_RUN
    assert hashlib.sha256((folder/"manifest.json").read_bytes()).hexdigest()==evidence.CLOSED_MANIFEST_SHA
    for name,digest,_ in evidence.CLOSED_PINS:
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest
    for raw in closed_raw:
        s=store.closed_loop_snapshot(raw["profile"],raw["seed"],raw["variant"],raw["step"])
        assert s["mastered_bool"]==raw["mastered_decisions"]
        assert s["ready"]==raw["ready_set"] and s["candidates"]==raw["eligible_candidates"]
        assert s["balanced"]==raw["balanced_candidates"] and s["served_item"]==raw["served_tuple"]
        assert s["timestamp"]==raw["query"]["timestamp_iso"] and s["p_correct_served_item"]==raw["prediction"]
        assert s["native_B_scores"]==raw["mastery_score_calls"]
        assert s["route_served"][-1]==raw["served_tuple"]["concept"] and len(s["route_served"])==raw["step"]+1
        assert s["posthoc"] is True and s["new_independent_N"]==0
        assert not {"correct","y","p_true","theta_before","theta_after","outcome_sha256","mastery_calls",
                    "state_before_selection_sha256","p_correct_logged_query","reference"}&s.keys()
        assert not {"prior_visits","chapter_tie"}&s["native_B_scores"][0].keys()


def test_all_prefix_flags_and_archived_first_break_keys_exact_projection(store):
    folder=evidence.ROOT/"research_tracking/runs"/evidence.CLOSED_RUN
    with (folder/evidence.CLOSED_PINS[1][0]).open(encoding="utf-8",newline="") as stream:
        flags=list(csv.DictReader(stream))
    for raw in flags:
        c=store.closed_loop_snapshot(raw["profile"],int(raw["seed"]),raw["candidate"],int(raw["step"]))["comparison"]
        for field in ("common_before","common_after","current_same_served_tuple","current_same_timestamp","current_same_label"):
            assert c[field]==(raw[field]=="1")
        assert (c["explanation"] is not None)==(int(raw["step"])==c["first_break_step"])
    rank=json.loads((folder/evidence.CLOSED_PINS[2][0]).read_text(encoding="utf-8"))
    negatives=0
    for raw in rank["comparisons"]:
        first=raw["first_prefix_break"]
        if first is None:
            negatives+=1
            for step in range(120):
                c=store.closed_loop_snapshot(raw["profile"],raw["seed"],raw["candidate"],step)["comparison"]
                assert c["negative_case"] and c["common_before"] and c["first_break_step"] is None and c["explanation"] is None
            continue
        s=store.closed_loop_snapshot(raw["profile"],raw["seed"],raw["candidate"],first["step"])
        proof=s["comparison"]["explanation"]
        assert proof["classification"]==first["classification"]
        for variant,field in [("graph_free","left_native_replay"),(raw["candidate"],"right_native_replay")]:
            expected=[];native=first[field]
            for cid in native["B"]:
                key=native["native_keys"][cid]
                expected.append({"concept":cid,"score":key["score"],"chapter_tie":key["chapter_tie"],
                                 "prior_visits":key["prior_visits"],"selected":cid==native["chosen_concept"]})
            assert proof["ranking_keys"][variant]==expected
    assert negatives==7
    assert store.closed_loop_snapshot("PG",20000,"graph_free",0)["comparison"] is None


@pytest.mark.parametrize("name",["manifest.json"]+[p[0] for p in evidence.CLOSED_PINS])
def test_closed_startup_tamper_before_socket(tmp_path_factory,monkeypatch,name):
    # Short workspace fixture roots avoid legacy Windows MAX_PATH without OS changes.
    scratch=tmp_path_factory.mktemp("c")
    for run,_,filename,_ in evidence.PINS:
        dst=scratch/"research_tracking/runs"/run;dst.mkdir(parents=True)
        for selected in ("manifest.json",filename):
            shutil.copyfile(evidence.ROOT/"research_tracking/runs"/run/selected,dst/selected)
    folder=scratch/"research_tracking/runs"/evidence.CLOSED_RUN;folder.mkdir(parents=True)
    for selected in ["manifest.json"]+[p[0] for p in evidence.CLOSED_PINS]:
        shutil.copyfile(evidence.ROOT/"research_tracking/runs"/evidence.CLOSED_RUN/selected,folder/selected)
    changed=folder/name;changed.write_bytes(changed.read_bytes()+b" ")
    monkeypatch.setattr(evidence,"ROOT",scratch)
    with pytest.raises(EvidenceError,match="SHA"):
        make_server(0)


@pytest.mark.parametrize("kind",["duplicate","query","phase","M","score","selected","step"])
def test_closed_schema_and_phase_fail_closed(closed_raw,kind):
    rows=list(closed_raw);row=copy.deepcopy(rows[0]);rows[0]=row
    if kind=="duplicate":rows[0]=rows[1]
    elif kind=="query":row["query"]["question"]="not-selected"
    elif kind=="phase":row["phases"].reverse()
    elif kind=="M":row["mastered_decisions"][next(iter(row["mastered_decisions"]))]=1
    elif kind=="score":row["mastery_score_calls"]=["wrong"]
    elif kind=="selected":row["balanced_candidates"]=["outside-domain"]
    else:row["step"]=True
    with pytest.raises(EvidenceError):EvidenceStore._index_closed(rows)


def test_closed_expansion_bound_and_prefix_sticky_guard():
    with pytest.raises(EvidenceError,match="giải nén"):
        evidence.decode_closed_trace(gzip.compress(b" "*(32*1024*1024+1)))
    folder=evidence.ROOT/"research_tracking/runs"/evidence.CLOSED_RUN
    data=(folder/evidence.CLOSED_PINS[1][0]).read_text(encoding="utf-8")
    reader=csv.DictReader(io.StringIO(data));rows=list(reader);fields=reader.fieldnames
    target=next(v for v in rows if v["common_before"]=="0");target["common_before"]="1"
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    with pytest.raises(EvidenceError):EvidenceStore._index_prefix(stream.getvalue().encode())


@pytest.mark.parametrize("route,mime",[("/api/closed-loop?profile=PG&seed=20000&variant=graph_package&step=61","application/json"),
    ("/evidence/closed-loop/report","text/plain"),("/evidence/closed-loop/sources","application/json")])
def test_closed_http_fixed_routes_and_review_semantics(serving,route,mime):
    status,headers,body=request(serving,route)
    assert status==200 and headers["Content-Type"].startswith(mime)
    assert headers["Cache-Control"]=="no-store" and headers["X-Content-Type-Options"]=="nosniff"
    if route.startswith("/api/"):
        result=json.loads(body)
        assert result["comparison"]["first_break_step"]==61 and result["comparison"]["common_before"]
        assert result["comparison"]["explanation"] and result["posthoc"]
        assert not {"correct","p_true","reference","p_correct_logged_query"}&result.keys()
    elif route.endswith("/report"):
        assert hashlib.sha256(body).hexdigest()==evidence.CLOSED_PINS[5][1]
    else:
        result=json.loads(body)
        assert result["new_independent_N"]==0 and result["review"]=="PASS_PARENT_INDEPENDENT_RAW_RANKING_AND_DESCRIPTIVE_REVIEW"
        assert len(result["sources"])==6 and "CURRENT_SOURCE" not in result.keys()


@pytest.mark.parametrize("query",["profile=PG&seed=20000&variant=graph_package&step=00",
    "profile=PG&seed=20000&variant=graph_package&step=120","profile=PG&seed=20000&variant=other&step=1",
    "profile=PG&seed=20000&variant=graph_free&step=1&file=private","profile=PG&seed=20000&variant=graph_free&step=1&step=2"])
def test_closed_query_allowlist(serving,query):
    assert request(serving,"/api/closed-loop?"+query)[0]==400


@pytest.mark.parametrize("path",["/evidence/closed-loop/report?file=dataset","/evidence/closed-loop/private",
    "/evidence/closed-loop/../../dataset","/evidence?path=secret"])
def test_closed_no_arbitrary_document_or_private_file_routes(serving,path):
    assert request(serving,path)[0]==404


def test_closed_ui_context_and_cached_document_contract(store):
    from src.research_demo.server import STATIC
    js=(STATIC/"demo.js").read_text(encoding="utf-8");html=(STATIC/"index.html").read_text(encoding="utf-8")
    assert 'id="mode"' in html and 'id="jump-break"' in html and 'id="ranking"' in html
    assert "/api/closed-loop?" in js and "currentRequest" in js
    assert "không điền visits/chapter giả" in js and "không paired" in store.closed_loop_snapshot("PG",20000,"graph_package",61)["semantics"]
    assert "Post-hoc" in html and "new independent N = 0" in html and "B-score không là calibrated" in html
    assert "innerHTML" not in js and "eval(" not in js
    assert set(store.documents)=={"report","sources","fresh_sources"}


@pytest.fixture(scope="module")
def fresh_payloads():
    folder = evidence.ROOT / "research_tracking/runs" / evidence.FRESH_RUN
    return {evidence.Path(name).name: json.loads((folder/name).read_bytes())
            for name, _ in evidence.FRESH_PINS}


def test_fresh_all_conditions_exact_projection_and_high_control(store, fresh_payloads):
    expected_q, expected_k = EvidenceStore._index_fresh(fresh_payloads)
    assert len(expected_q) == 60 and len(expected_k) == 30
    for (block, ability, strength), raw in expected_q.items():
        view = store.fresh_source_snapshot(block, ability, "0" if strength == 0 else "0.55")
        assert view["expert_outcome"] == raw["expert"]
        assert view["learned_outcome"] == raw["learned"]
        assert view["Q_expert_minus_learned"] == raw["expert_minus_learned"]
        assert view["K_lambda_difference"] == expected_k[(block, ability)]["lambda_difference"]
        assert view["high_control_expected_inactive"] is (ability == 1300)
        assert view["viewer_model_calls"] == view["viewer_added_independent_N"] == 0
        assert not {"latent_identity", "uniform_identity", "oracle", "checkpoint"} & view.keys()
    high = [r for (b, a, s), r in expected_q.items() if a == 1300]
    assert all(r["expert_minus_learned"] != 0 for r in high)
    assert any(r["expert_minus_learned"] > 0 for r in high)
    assert any(r["expert_minus_learned"] < 0 for r in high)


@pytest.mark.parametrize("condition", [(True,1000,"0"),(21010,True,"0"),(21009,1000,"0"),
    (21010,999,"0"),(21010,1000,.55),(21010,1000,"0.550")])
def test_fresh_fixed_condition_allowlist(store, condition):
    with pytest.raises(EvidenceError):
        store.fresh_source_snapshot(*condition)


@pytest.mark.parametrize("kind", ["missing", "duplicate", "base", "uniform", "q", "k", "control", "nan"])
def test_fresh_population_coupling_and_arithmetic_rejected(fresh_payloads, kind):
    data = copy.deepcopy(fresh_payloads)
    if kind == "missing": data["outcomes.json"].pop()
    if kind == "duplicate": data["outcomes.json"][-1] = data["outcomes.json"][0]
    if kind in ("base", "uniform"):
        data["outcomes.json"][0]["latent_identity" if kind == "base" else "uniform_identity"] = "0"*64
    if kind == "q": data["graph_source_contrasts.json"][0]["expert_minus_learned"] += 1
    if kind == "k": data["conditional_lambda_contrasts.json"][0]["lambda_difference"] += 1
    if kind == "control": data["high_controls.json"][0]["endpoint_exact"] = False
    if kind == "nan": data["outcomes.json"][0]["outcome"] = float("nan")
    with pytest.raises(EvidenceError): EvidenceStore._index_fresh(data)


@pytest.mark.parametrize("filename", ["manifest.json", "acceptance.json", evidence.FRESH_PREFIX+"outcomes.json"])
def test_fresh_tamper_stops_before_listening(monkeypatch, filename):
    from src.research_demo import server
    original = evidence.bounded_read
    target = evidence.ROOT/"research_tracking/runs"/evidence.FRESH_RUN/filename
    def read(path, limit):
        raw = original(path, limit)
        return raw+b" " if path == target else raw
    def forbidden_listener(*args, **kwargs):
        raise AssertionError("Không được mở listener khi nguồn hỏng")
    monkeypatch.setattr(evidence, "bounded_read", read)
    monkeypatch.setattr(server, "ThreadingHTTPServer", forbidden_listener)
    with pytest.raises(EvidenceError, match="SHA"):
        server.make_server(0)


def test_fresh_ui_pinned_sources_and_reused_styles(store):
    from src.research_demo.server import STATIC, DOCUMENT_ROUTES
    html = (STATIC/"index.html").read_text(encoding="utf-8")
    js = (STATIC/"demo.js").read_text(encoding="utf-8")
    assert all(f'id="{name}"' in html for name in ("fresh-block", "fresh-ability", "fresh-lambda", "fresh-values"))
    assert "freshRequest" in js and "/api/rq2-source-contrast?" in js
    assert "innerHTML" not in js and "eval(" not in js
    assert "đối chứng âm dự kiến" in js and "Confidence không được" in html
    document = json.loads(store.documents["fresh_sources"][0])
    assert DOCUMENT_ROUTES["/evidence/fresh-source/sources"] == "fresh_sources"
    assert len(document["sources"]) == 7
    assert document["manifest_sha256"] == evidence.FRESH_MANIFEST_SHA
    assert len(store.provenance) == 16 and len({r["run"] for r in store.provenance}) == 5


@pytest.fixture
def unbound_handler(store, monkeypatch):
    """Chạy routing thật trên handler chưa bind, không tạo socket/server."""
    from email.message import Message
    from types import SimpleNamespace
    from src.research_demo import server
    def unbound(address, handler):
        return SimpleNamespace(handler=handler, address=address)
    monkeypatch.setattr(server, "ThreadingHTTPServer", unbound)
    facade = server.make_server(8765, store=store)
    handler = object.__new__(facade.handler)
    handler.server = SimpleNamespace(server_address=facade.address)
    handler.headers = Message()
    handler.headers["Host"] = "127.0.0.1:8765"
    return handler


def test_fresh_fixed_endpoint_without_socket(unbound_handler, store):
    replies = []
    unbound_handler.respond = lambda *args: replies.append(args)
    for block in evidence.FRESH_BLOCKS:
        for ability in evidence.FRESH_ABILITIES:
            for strength in ("0", "0.55"):
                unbound_handler.path = f"/api/rq2-source-contrast?block={block}&ability={ability}&lambda={strength}"
                unbound_handler.do_GET()
                assert replies[-1] == (200, store.fresh_source_snapshot(block, ability, strength))
    unbound_handler.path = "/evidence/fresh-source/sources"
    unbound_handler.do_GET()
    assert replies[-1] == (200, *store.documents["fresh_sources"])


@pytest.mark.parametrize("query", ["", "block=21010&ability=1000", "block=21010&ability=1000&lambda=0&path=x",
    "block=21010&block=21011&lambda=0", "block=021010&ability=1000&lambda=0",
    "block=21010&ability=1000&lambda=0.550", "block=21010&ability=1000&lambda=nan",
    "block=21009&ability=1000&lambda=0", "block=21010&ability=999&lambda=0"])
def test_fresh_query_route_rejects_without_socket(unbound_handler, query):
    replies = []
    unbound_handler.respond = lambda *args: replies.append(args)
    unbound_handler.path = "/api/rq2-source-contrast?"+query
    unbound_handler.do_GET()
    assert replies[-1][0] == 400


def test_fresh_endpoint_retains_host_and_origin_guard(unbound_handler):
    replies = []
    unbound_handler.respond = lambda *args: replies.append(args)
    unbound_handler.path = "/api/rq2-source-contrast?block=21010&ability=1000&lambda=0"
    unbound_handler.headers["Origin"] = "https://foreign.invalid"
    unbound_handler.do_GET()
    assert replies[-1][0] == 403
    del unbound_handler.headers["Origin"]
    unbound_handler.headers["Host"] = "foreign.invalid"
    unbound_handler.do_GET()
    assert replies[-1][0] == 403
