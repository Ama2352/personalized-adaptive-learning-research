"""Prepared remote evidence export only; never installs/retries or reads venv.

Default emits first48,000-byte chunk. Later cell may set CHUNK_INDEX before exec.
"""
import base64
import hashlib
import json
import math
from pathlib import Path
import stat
import zipfile

ROOT=Path("/content/KLTN_GPU08_20261108_01")
ATTEMPT=ROOT/"post-install-audit01"
ARCHIVE=ROOT/"gpu08-post-install-audit01-evidence.zip"
SOURCE_SHA="dd7738bfe06032ffaea6a921619767fd659e626ff53ee5a2a7203fb33f885132"
CHUNK_BYTES=48000
MAX_FILE=32*1024**2
MAX_TOTAL=48*1024**2
MAX_ARCHIVE=50*1024**2
STATUSES={"EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY","FAILED_READ_ONLY_POST_INSTALL_AUDIT"}
ALLOWED={"audit-child.py","audit.stdout","audit.stderr","result.json","failure.log","CANCEL"}
sha=lambda b:hashlib.sha256(b).hexdigest()


def read_regular(path,limit):
    assert path.is_relative_to(ROOT) and path.resolve().is_relative_to(ROOT)
    for p in (path,*path.parents):
        assert not p.is_symlink()
        if p==ROOT:break
    assert stat.S_ISREG(path.stat().st_mode)
    with path.open("rb") as stream:data=stream.read(limit+1)
    assert len(data)<=limit
    return data


def export(chunk_index=0):
    assert type(chunk_index) is int and chunk_index>=0 and ROOT.resolve()==ROOT and ATTEMPT.is_dir()
    source=read_regular(ROOT/"post_install_audit01.py",128*1024)
    assert sha(source)==SOURCE_SHA
    output_manifest_bytes=read_regular(ATTEMPT/"output-manifest.json",256*1024)
    output_manifest=json.loads(output_manifest_bytes)
    files=output_manifest["outputs"]
    assert isinstance(files,dict) and 1<=len(files)<=32 and "result.json" in files
    assert set(files)<=ALLOWED
    payloads={"post_install_audit01.py":source,"post-install-audit01/output-manifest.json":output_manifest_bytes}
    for name,item in files.items():
        assert Path(name).name==name and "\\" not in name and ":" not in name
        data=read_regular(ATTEMPT/name,MAX_FILE)
        assert len(data)==item["bytes"] and sha(data)==item["sha256"]
        payloads["post-install-audit01/"+name]=data
    result=json.loads(payloads["post-install-audit01/result.json"])
    status=result["status"]
    assert status in STATUSES and output_manifest["status"]==status
    assert result["install_calls"]==result["pip_calls"]==result["network_calls"]==result["gpu_model_steps"]==result["optimizer_steps"]==result["modal_calls"]==0
    assert result["prior_install02_status"]=="FAILED_RETAIN_PARTIAL_NO_RETRY"
    assert result["stage"]=="POST_INSTALL_AUDIT01_SEPARATE_FROM_FAILED_INSTALL02"
    if status=="EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY":
        assert result["cleanup_accepted"] is True and result["resource_accepted"] is True
        assert result["child_count"]==1 and result["child_returncode"]==0
        assert result["timeout_seconds"]==90
        assert all(type(result[k]) in (int,float) and math.isfinite(result[k]) and 0<=result[k]<=90 for k in ("elapsed_seconds","elapsed_wall_seconds"))
        assert result["audit"]["package_count"]==44 and result["audit"]["cuda_initialized"] is False and result["audit"]["cpu_scalar_check"] is True
    assert sum(map(len,payloads.values()))<=MAX_TOTAL
    manifest={"kind":"GPU08_POST_INSTALL_READONLY_AUDIT_EVIDENCE_SUCCESS_OR_FAILURE","stage_status":status,
        "audit_success_claimed":status=="EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY",
        "installation_success_claimed":False,
        "prior_install02_status":result["prior_install02_status"],"source_sha256":sha(source),
        "output_manifest_sha256":sha(output_manifest_bytes),"files":{n:{"sha256":sha(b),"bytes":len(b)} for n,b in payloads.items()},
        "scope":"Read-only audit evidence transport only; failed install02 unchanged, no install/retry/GPU acceptance or venv/tmp/cache/binary export."}
    manifest_bytes=(json.dumps(manifest,indent=2)+"\n").encode()
    assert len(manifest_bytes)<=256*1024
    if not ARCHIVE.exists():
        with zipfile.ZipFile(ARCHIVE,"x",compression=zipfile.ZIP_DEFLATED) as archive:
            for name,data in payloads.items():archive.writestr(name,data)
            archive.writestr("manifest.json",manifest_bytes)
    else:
        assert not ARCHIVE.is_symlink()
        with zipfile.ZipFile(ARCHIVE) as archive:
            assert set(archive.namelist())==set(payloads)|{"manifest.json"} and len(archive.namelist())==len(payloads)+1
            assert archive.read("manifest.json")==manifest_bytes
            for name,data in payloads.items():assert archive.read(name)==data
            assert archive.testzip() is None
    raw=read_regular(ARCHIVE,MAX_ARCHIVE)
    assert raw and chunk_index<math.ceil(len(raw)/CHUNK_BYTES)
    chunk=raw[chunk_index*CHUNK_BYTES:(chunk_index+1)*CHUNK_BYTES]
    return {"archive":ARCHIVE.name,"bytes":len(raw),"sha256":sha(raw),"chunk_bytes":CHUNK_BYTES,
        "total_chunks":math.ceil(len(raw)/CHUNK_BYTES),"chunk_index":chunk_index,"chunk_length":len(chunk),
        "chunk_sha256":sha(chunk),"chunk_b64":base64.b64encode(chunk).decode(),"selected_files":len(payloads),
        "manifest_sha256":sha(manifest_bytes),"stage_status":status,"source_sha256":sha(source),"evidence_only":True}


if __name__=="__main__":print(json.dumps(export(globals().get("CHUNK_INDEX",0))))
