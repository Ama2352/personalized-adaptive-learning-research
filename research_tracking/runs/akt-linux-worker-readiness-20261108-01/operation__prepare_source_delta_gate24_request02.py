"""Offline producer02: fix Gate24 required LF audit argv; producer01 preserved.

Không dispatch, không apply delta/Gate hoặc import operation modules.
"""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path,PurePosixPath
import re

WORK=Path(__file__).resolve().parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def pinned_json(path,expected):
    if not re.fullmatch('[a-f0-9]{64}',expected):raise ValueError('actual64hex receipt SHA required')
    raw=path.read_bytes()
    if sha(raw)!=expected:raise ValueError('actual received receipt SHA mismatch')
    return json.loads(raw)


def source_constant(tree,name):
    return next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id==name for t in node.targets))


def loader_path(value):
    path=PurePosixPath(value)
    if (path.is_absolute() or '..' in path.parts or '\\' in value or ':' in value or path.as_posix()!=value
            or len(path.parts)!=2 or not path.parts[0].startswith('upstream-loader-transfer') or path.name!='result.json'):
        raise ValueError('ROOT-relative POSIX actual loader result path required')
    return path.as_posix()


ACCEPTED_LF_AUDIT_SHA='1f116d3db2c88d2815bee73cb4471e56f6f442b744c4cd29cede7ce2a43cf952'
ACCEPTED_LF_AUDIT_STATUS='VERIFIED_LOCAL_DERIVED_LF_UPSTREAM_READONLY_NOT_LINUX_GATE'

def gate_argv(common,*,materialization_sha,delta_result_sha,upstream_path,upstream_sha,upstream_status):
    return ['--phase','gate',*common,'--materialization-sha256',materialization_sha,
            '--delta-result-sha256',delta_result_sha,'--upstream-audit-path',upstream_path,
            '--upstream-audit-sha256',upstream_sha,'--upstream-audit-status',upstream_status]


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--operation',choices=('delta','gate24'),required=True)
    p.add_argument('--expected-source-sha256',required=True)
    p.add_argument('--loader-remediation-receipt',type=Path,required=True)
    p.add_argument('--loader-remediation-relative-path',required=True)
    p.add_argument('--expected-loader-remediation-sha256',required=True)
    p.add_argument('--materialization-receipt',type=Path)
    p.add_argument('--expected-materialization-sha256')
    p.add_argument('--delta-result-receipt',type=Path)
    p.add_argument('--expected-delta-result-sha256')
    p.add_argument('--upstream-audit-receipt',type=Path)
    p.add_argument('--upstream-audit-relative-path')
    p.add_argument('--expected-upstream-audit-sha256')
    p.add_argument('--accepted-upstream-audit-status')
    p.add_argument('--approval-reference',required=True)
    args=p.parse_args(argv)
    source_name='apply_source_delta01.py' if args.operation=='delta' else 'linux_cpu_gate24_driver01.py'
    raw=(WORK/source_name).read_bytes();tree=ast.parse(raw)
    if sha(raw)!=args.expected_source_sha256 or not args.approval_reference.strip():raise ValueError('reviewed source SHA/approval required')
    reviewed_loader_source=source_constant(tree,'LOADER_SOURCE_SHA')
    if not re.fullmatch('[a-f0-9]{64}',reviewed_loader_source):raise ValueError('reviewed loader operation source still pending')
    receipt=pinned_json(args.loader_remediation_receipt,args.expected_loader_remediation_sha256)
    audit=receipt.get('audit',{})
    if (receipt.get('status')!='MATERIALIZED_TRANSFERRED_PINNED_LOADER_SOURCE_ONLY'
            or receipt.get('source_sha256')!=reviewed_loader_source or receipt.get('cleanup',{}).get('accepted') is not True
            or receipt.get('source_origin')!='LOCAL_PINNED_GIT_BLOB_TRANSFER'
            or audit.get('loader',{}).get('sha256')!='27550ccd07c1131971c4381f024c0f3795dba3d32b7f9fb4eea4ababd8bfe9e8'):
        raise ValueError('actual accepted loader remediation required BEFORE request creation')
    relative=loader_path(args.loader_remediation_relative_path)
    argv=['--expected-source-sha256',args.expected_source_sha256,'--loader-remediation-path',relative,
          '--loader-remediation-sha256',args.expected_loader_remediation_sha256,'--approval-reference',args.approval_reference]
    if args.operation=='gate24':
        if None in (args.materialization_receipt,args.expected_materialization_sha256,args.delta_result_receipt,args.expected_delta_result_sha256):
            raise ValueError('actual new materialization02 and accepted source-delta result required')
        material=pinned_json(args.materialization_receipt,args.expected_materialization_sha256)
        delta=pinned_json(args.delta_result_receipt,args.expected_delta_result_sha256)
        if (material.get('status')!='MATERIALIZED_SOURCE_DELTA_ONLY_NO_EXECUTION'
                or material.get('delta',{}).get('controller_source_sha256')!=source_constant(tree,'DELTA_SOURCE_SHA')
                or material.get('delta',{}).get('loader_remediation_sha256')!=args.expected_loader_remediation_sha256
                or material.get('delta',{}).get('loader_remediation_path')!=relative
                or delta.get('status')!='ACCEPTED_TEST_ONLY_SOURCE_DELTA_NO_EXECUTION'
                or delta.get('new_materialization_sha256')!=args.expected_materialization_sha256):
            raise ValueError('actual source-delta lineage mismatch')
        if None in (args.upstream_audit_receipt,args.upstream_audit_relative_path,args.expected_upstream_audit_sha256,args.accepted_upstream_audit_status):
            raise ValueError('Gate24 requires actual accepted LF audit receipt/path/SHA/status')
        lf=pinned_json(args.upstream_audit_receipt,args.expected_upstream_audit_sha256)
        lf_path=PurePosixPath(args.upstream_audit_relative_path)
        if (lf_path.is_absolute() or '..' in lf_path.parts or '\\' in args.upstream_audit_relative_path
                or ':' in args.upstream_audit_relative_path or lf_path.as_posix()!=args.upstream_audit_relative_path):
            raise ValueError('ROOT-relative POSIX LF audit path required')
        if (args.expected_upstream_audit_sha256!=ACCEPTED_LF_AUDIT_SHA
                or lf.get('status')!=args.accepted_upstream_audit_status or lf.get('status')!=ACCEPTED_LF_AUDIT_STATUS):
            raise ValueError('exact actual1f116 accepted LF audit required')
        argv=gate_argv(argv,materialization_sha=args.expected_materialization_sha256,
             delta_result_sha=args.expected_delta_result_sha256,upstream_path=lf_path.as_posix(),
             upstream_sha=args.expected_upstream_audit_sha256,upstream_status=args.accepted_upstream_audit_status)
    encoded=base64.b64encode(raw).decode()
    code=("import base64,hashlib\nfrom pathlib import Path\n"
          f"payload=base64.b64decode({encoded!r})\nexpected={args.expected_source_sha256!r}\n"
          "assert hashlib.sha256(payload).hexdigest()==expected\n"
          f"path=Path('/content/KLTN_GPU08_20261108_01/{source_name}')\n"
          "assert not path.is_symlink()\nif path.exists():\n assert path.is_file() and path.read_bytes()==payload\n"
          "else:\n with path.open('xb') as stream:stream.write(payload)\n"
          "assert hashlib.sha256(path.read_bytes()).hexdigest()==expected\n"
          "namespace={'__name__':'reviewed_source_operation','__file__':str(path)}\nexec(compile(payload,str(path),'exec'),namespace)\n"
          f"returncode=namespace['main']({argv!r})\n")
    destination=WORK.parent/'requests'/('gpu09-add-source-delta01.json' if args.operation=='delta' else 'gpu09-add-linux-gate24-02.json')
    with destination.open('x',encoding='utf-8') as stream:json.dump({'cellIndex':0,'language':'python','code':code},stream)
    contract={'status':'OFFLINE_REQUEST_PREPARED_NOT_DISPATCHED','operation':args.operation,'source_sha256':args.expected_source_sha256,
        'loader_remediation_path':relative,'loader_remediation_sha256':args.expected_loader_remediation_sha256,
        'materialization_sha256':args.expected_materialization_sha256,'delta_result_sha256':args.expected_delta_result_sha256,
        'native_gate_expected_passed':771 if args.operation=='gate24' else None,'native_gate_seconds':600 if args.operation=='gate24' else None,
        'outer_seconds':630 if args.operation=='gate24' else 30,'required_MCP_timeout_seconds':660 if args.operation=='gate24' else 60,
        'prior_runtime02_reused':args.operation=='gate24',
        'upstream_audit_sha256':args.expected_upstream_audit_sha256,'upstream_audit_path':args.upstream_audit_relative_path,
        'upstream_audit_status':args.accepted_upstream_audit_status,'request_sha256':sha(destination.read_bytes()),'executed':False}
    with (WORK/('source-delta01-request-contract.json' if args.operation=='delta' else 'linux-gate24-request02-contract.json')).open('x',encoding='utf-8') as stream:
        json.dump(contract,stream,indent=2);stream.write('\n')
    print(json.dumps({'prepared':str(destination),'executed':False,'contract':contract}))


if __name__=='__main__':main()
