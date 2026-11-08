"""Chỉ tạo MCP add-cell request local; không gửi/chạy remote hoặc import driver."""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase',choices=('runtime','gate'),required=True)
    p.add_argument('--expected-driver-sha256',required=True)
    p.add_argument('--upstream-audit-receipt',type=Path,required=True,help='bản receipt LF actual đã nhận và verify local')
    p.add_argument('--upstream-audit-relative-path',required=True,help='receipt cùng bytes trên remote ROOT')
    p.add_argument('--expected-upstream-audit-sha256',required=True)
    p.add_argument('--accepted-upstream-audit-status',required=True,help='literal status đã được parent review, không dùng status FAILED')
    p.add_argument('--runtime-result-receipt',type=Path,help='Gate mode: actual accepted runtime phase receipt đã nhận local')
    p.add_argument('--expected-runtime-result-sha256')
    p.add_argument('--approval-reference',required=True)
    args=p.parse_args()
    work=Path(__file__).resolve().parent
    source=work/'linux_cpu_validation_driver02.py';raw=source.read_bytes()
    if sha(raw)!=args.expected_driver_sha256:raise ValueError('reviewed driver SHA mismatch')
    ast.parse(raw)  # Syntax only; never import/execute operation source.
    audit_raw=args.upstream_audit_receipt.read_bytes()
    audit=json.loads(audit_raw)
    if (sha(audit_raw)!=args.expected_upstream_audit_sha256 or audit.get('status')!=args.accepted_upstream_audit_status
            or any(word in args.accepted_upstream_audit_status.upper() for word in ('FAIL','REJECT','PENDING','NOT_ACCEPT'))):
        raise ValueError('verified accepted LF audit receipt required')
    relative=PurePosixPath(args.upstream_audit_relative_path)
    if (relative.is_absolute() or '..' in relative.parts or '\\' in args.upstream_audit_relative_path
            or ':' in args.upstream_audit_relative_path):raise ValueError('ROOT-relative POSIX LF audit path required')
    argv=['--phase',args.phase,'--expected-source-sha256',args.expected_driver_sha256,
          '--upstream-audit-path',relative.as_posix(),'--upstream-audit-sha256',args.expected_upstream_audit_sha256,
          '--upstream-audit-status',args.accepted_upstream_audit_status,'--approval-reference',args.approval_reference]
    runtime_sha=None
    if args.phase=='gate':
        if args.runtime_result_receipt is None or not args.expected_runtime_result_sha256:
            raise ValueError('actual runtime result must be received/verified before preparing Gate request')
        runtime_raw=args.runtime_result_receipt.read_bytes();runtime=json.loads(runtime_raw)
        runtime_sha=sha(runtime_raw)
        if (runtime_sha!=args.expected_runtime_result_sha256 or runtime.get('status')!='ACCEPTED_NATIVE_RUNTIME_CPU'
                or runtime.get('cleanup_accepted') is not True or runtime.get('driver_source_sha256')!=args.expected_driver_sha256
                or runtime.get('upstream_audit_sha256')!=args.expected_upstream_audit_sha256):
            raise ValueError('verified matching native runtime phase required')
        argv+=['--runtime-result-sha256',runtime_sha]
    encoded=base64.b64encode(raw).decode('ascii')
    code=("import base64,hashlib\nfrom pathlib import Path\n"
          f"payload=base64.b64decode({encoded!r})\nexpected={args.expected_driver_sha256!r}\n"
          "assert hashlib.sha256(payload).hexdigest()==expected\n"
          "path=Path('/content/KLTN_GPU08_20261108_01/linux_cpu_validation_driver02.py')\n"
          "assert not path.is_symlink()\n"
          "if path.exists():\n assert path.is_file() and path.read_bytes()==payload\n"
          "else:\n with path.open('xb') as stream:stream.write(payload)\n"
          "namespace={'__name__':'linux_cpu_validation_operation','__file__':str(path)}\n"
          "exec(compile(payload,str(path),'exec'),namespace)\n"
          f"returncode=namespace['main']({argv!r})\n")
    requests=work.parent/'requests'
    output=requests/f'gpu09-add-linux-cpu-{args.phase}-validation-02.json'
    with output.open('x',encoding='utf-8') as stream:
        json.dump({'cellIndex':0,'language':'python','code':code},stream)
    contract={'status':'REQUEST_PREPARED_OFFLINE_NOT_DISPATCHED','phase':args.phase,
              'driver_sha256':args.expected_driver_sha256,'upstream_audit_sha256':args.expected_upstream_audit_sha256,
              'upstream_audit_status':args.accepted_upstream_audit_status,'runtime_result_sha256':runtime_sha,
              'request_sha256':sha(output.read_bytes()),'outer_timeout_seconds':60 if args.phase=='runtime' else 630,
              'native_gate_timeout_seconds':600,'required_mcp_execution_timeout_seconds':660,
              'must_not_dispatch_if_bridge_remaining_seconds_below':660,
              'approval_reference':args.approval_reference,'executed':False,
              'no_install_gpu_realdata_fullCV_modal_phase':True}
    with (work/f'linux-cpu-{args.phase}-request02-contract.json').open('x',encoding='utf-8') as stream:
        json.dump(contract,stream,indent=2);stream.write('\n')
    print(json.dumps({'prepared':str(output),'phase':args.phase,'executed':False,'driver_sha256':args.expected_driver_sha256}))

if __name__=='__main__':main()
