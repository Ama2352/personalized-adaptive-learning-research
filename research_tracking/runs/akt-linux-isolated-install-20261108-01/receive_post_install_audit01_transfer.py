"""Prepared local receiver; explicit receipt, exclusive directories, no dispatch.

first --receipt <raw bridge result>; chunk --receipt <next result>; finish
Never copies private receipts/Base64 to received evidence, only receipt SHA.
"""
import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path,PurePosixPath
import stat
import zipfile

WORK=Path(__file__).resolve().parent
TRANSFER=WORK/"transfer-post-audit01"
RECEIVED=WORK/"received-post-audit01"
ARCHIVE="gpu08-post-install-audit01-evidence.zip"
SOURCE_SHA="dd7738bfe06032ffaea6a921619767fd659e626ff53ee5a2a7203fb33f885132"
MAX_FILE=32*1024**2
MAX_TOTAL=48*1024**2
MAX_ARCHIVE=50*1024**2
ALLOWED={"audit-child.py","audit.stdout","audit.stderr","result.json","failure.log","CANCEL"}
STATUSES={"EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY","FAILED_READ_ONLY_POST_INSTALL_AUDIT"}
sha=lambda b:hashlib.sha256(b).hexdigest()


def receipt_payload(path):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<=2*1024**2
    raw=path.read_bytes();value=json.loads(raw)
    if "archive" in value:payload=value
    else:
        assert value.get("is_error") is False
        body=value.get("structured_content") or value.get("data")
        assert isinstance(body,dict) and not any(o.get("output_type")=="error" for o in body["outputs"])
        stdout="".join("".join(o.get("text",[])) if isinstance(o.get("text"),list) else o.get("text","")
                       for o in body["outputs"] if o.get("output_type")=="stream" and o.get("name")=="stdout")
        payload=json.loads(stdout)
    return payload,sha(raw)


def validate(payload):
    assert payload["archive"]==ARCHIVE and type(payload["bytes"]) is int and 0<payload["bytes"]<=MAX_ARCHIVE
    assert payload["chunk_bytes"]==48000 and payload["total_chunks"]==math.ceil(payload["bytes"]/48000)
    assert type(payload["chunk_index"]) is int and 0<=payload["chunk_index"]<payload["total_chunks"]
    assert payload["source_sha256"]==SOURCE_SHA and payload["stage_status"] in STATUSES
    assert payload["evidence_only"] is True and 2<=payload["selected_files"]<=34
    for name in ("sha256","manifest_sha256","chunk_sha256"):
        assert isinstance(payload[name],str) and len(payload[name])==64 and all(c in "0123456789abcdef" for c in payload[name])
    chunk=base64.b64decode(payload["chunk_b64"],validate=True)
    expected=min(48000,payload["bytes"]-payload["chunk_index"]*48000)
    assert len(chunk)==payload["chunk_length"]==expected and sha(chunk)==payload["chunk_sha256"]
    return chunk


def store_payload(payload,receipt_sha,first):
    chunk=validate(payload)
    if first:
        assert payload["chunk_index"]==0 and not TRANSFER.exists() and not RECEIVED.exists()
        TRANSFER.mkdir(exist_ok=False)
        plan={k:v for k,v in payload.items() if k not in {"chunk_b64","chunk_index","chunk_length","chunk_sha256"}}
        with (TRANSFER/"plan.json").open("x",encoding="utf8") as stream:json.dump(plan,stream,indent=2)
    else:
        assert TRANSFER.is_dir() and not TRANSFER.is_symlink() and not RECEIVED.exists()
        plan=json.loads((TRANSFER/"plan.json").read_text())
        assert all(payload[k]==v for k,v in plan.items())
    index=payload["chunk_index"]
    with (TRANSFER/f"chunk-{index:04d}.bin").open("xb") as stream:stream.write(chunk)
    with (TRANSFER/f"chunk-{index:04d}-receipt.json").open("x",encoding="utf8") as stream:
        json.dump({"index":index,"bytes":len(chunk),"sha256":sha(chunk),"input_receipt_sha256":receipt_sha},stream,indent=2)
    print(json.dumps({"stored_chunk":index,"sha256":sha(chunk),"stage_status":payload["stage_status"],"not_installer_acceptance":True}))


def finish():
    assert TRANSFER.is_dir() and not TRANSFER.is_symlink() and not RECEIVED.exists()
    plan=json.loads((TRANSFER/"plan.json").read_text())
    assert plan["archive"]==ARCHIVE and plan["chunk_bytes"]==48000 and 0<plan["bytes"]<=MAX_ARCHIVE
    pieces=[]
    for index in range(plan["total_chunks"]):
        p=TRANSFER/f"chunk-{index:04d}.bin";r=TRANSFER/f"chunk-{index:04d}-receipt.json"
        assert p.is_file() and r.is_file() and not p.is_symlink() and not r.is_symlink()
        b=p.read_bytes();receipt=json.loads(r.read_text())
        assert len(b)==receipt["bytes"]==min(48000,plan["bytes"]-index*48000) and sha(b)==receipt["sha256"]
        pieces.append(b)
    raw=b"".join(pieces)
    assert len(raw)==plan["bytes"] and sha(raw)==plan["sha256"]
    archive_path=TRANSFER/ARCHIVE
    with archive_path.open("xb") as stream:stream.write(raw)
    payloads={}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        assert len(names)==len(set(names))==plan["selected_files"]+1<=35
        assert "manifest.json" in names and sum(i.file_size for i in infos)<=MAX_TOTAL+256*1024
        for info in infos:
            name=info.filename;p=PurePosixPath(name);kind=stat.S_IFMT(info.external_attr>>16)
            assert not p.is_absolute() and ".." not in p.parts and "\\" not in name and ":" not in name and not info.is_dir()
            assert kind in (0,stat.S_IFREG) and not info.flag_bits&1 and 0<=info.file_size<=MAX_FILE
            assert name in {"manifest.json","post_install_audit01.py","post-install-audit01/output-manifest.json"} or (
                len(p.parts)==2 and p.parts[0]=="post-install-audit01" and p.parts[1] in ALLOWED)
        mbytes=archive.read("manifest.json");assert len(mbytes)<=256*1024 and sha(mbytes)==plan["manifest_sha256"]
        manifest=json.loads(mbytes)
        assert manifest["kind"]=="GPU08_POST_INSTALL_READONLY_AUDIT_EVIDENCE_SUCCESS_OR_FAILURE"
        assert manifest["stage_status"]==plan["stage_status"] and manifest["source_sha256"]==SOURCE_SHA
        assert set(names)==set(manifest["files"])|{"manifest.json"}
        assert archive.testzip() is None
        for name,item in manifest["files"].items():
            b=archive.read(name);assert len(b)==item["bytes"] and sha(b)==item["sha256"]
            payloads[name]=b
        assert sum(map(len,payloads.values()))<=MAX_TOTAL
        assert sha(payloads["post_install_audit01.py"])==SOURCE_SHA
        output=json.loads(payloads["post-install-audit01/output-manifest.json"])
        result=json.loads(payloads["post-install-audit01/result.json"])
        assert output["status"]==result["status"]==plan["stage_status"]
        assert set(output["outputs"])<=ALLOWED and "result.json" in output["outputs"]
        expected={"post_install_audit01.py","post-install-audit01/output-manifest.json"}|{"post-install-audit01/"+n for n in output["outputs"]}
        assert set(payloads)==expected
        for name,item in output["outputs"].items():
            b=payloads["post-install-audit01/"+name];assert len(b)==item["bytes"] and sha(b)==item["sha256"]
        assert result["install_calls"]==result["pip_calls"]==result["network_calls"]==result["gpu_model_steps"]==result["optimizer_steps"]==result["modal_calls"]==0
        assert result["prior_install02_status"]=="FAILED_RETAIN_PARTIAL_NO_RETRY"
        assert result["stage"]=="POST_INSTALL_AUDIT01_SEPARATE_FROM_FAILED_INSTALL02"
        if result["status"]=="EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY":
            assert result["cleanup_accepted"] is True and result["resource_accepted"] is True
            assert result["child_count"]==1 and result["child_returncode"]==0
            assert result["timeout_seconds"]==90
            assert all(type(result[k]) in (int,float) and math.isfinite(result[k]) and 0<=result[k]<=90 for k in ("elapsed_seconds","elapsed_wall_seconds"))
            assert result["audit"]["package_count"]==44 and result["audit"]["cuda_initialized"] is False and result["audit"]["cpu_scalar_check"] is True
        payloads["manifest.json"]=mbytes
    # Full path/size/CRC/SHA/member-set validation above precedes directory creation.
    RECEIVED.mkdir(exist_ok=False)
    for name,b in payloads.items():
        target=RECEIVED/name;target.parent.mkdir(parents=True,exist_ok=True)
        assert target.resolve().is_relative_to(RECEIVED.resolve())
        with target.open("xb") as stream:stream.write(b)
        assert sha(target.read_bytes())==sha(b)
    receipt={"status":"VERIFIED_EVIDENCE_TRANSPORT","files":len(payloads),"stage_status":plan["stage_status"],
        "archive_sha256":sha(raw),"manifest_sha256":plan["manifest_sha256"],"zip_crc_verified":True,"all_output_hashes_verified":True,
        "scope":"Transport integrity only; FAILED retained, no retry/installation/GPU acceptance inferred."}
    with (TRANSFER/"acceptance.json").open("x",encoding="utf8") as stream:json.dump(receipt,stream,indent=2)
    print(json.dumps(receipt))


def main():
    p=argparse.ArgumentParser(description="Receive read-only audit evidence only; never dispatch remote")
    p.add_argument("action",choices=("first","chunk","finish"));p.add_argument("--receipt",type=Path)
    args=p.parse_args()
    if args.action=="finish":
        assert args.receipt is None;finish()
    else:
        assert args.receipt is not None
        payload,receipt_sha=receipt_payload(args.receipt)
        store_payload(payload,receipt_sha,args.action=="first")


if __name__=="__main__":main()
