"""One parser contract test; không producer/driver main hoặc file mutation."""
import argparse
import ast
import contextlib
import copy
import hashlib
import io
from pathlib import Path
import unittest

BASE=Path(__file__).parent


class GateCLIContract(unittest.TestCase):
    def test_generated_gate_argv_parses_and_missing_LF_args_fail_before_operation(self):
        producer=ast.parse((BASE/'prepare_source_delta_gate24_request02.py').read_bytes())
        builder=next(n for n in producer.body if isinstance(n,ast.FunctionDef) and n.name=='gate_argv')
        scope={};exec(compile(ast.Module(body=[builder],type_ignores=[]),'producer02-pure-builder','exec'),scope)
        driver=ast.parse((BASE/'linux_cpu_gate24_driver01.py').read_bytes())
        main=next(n for n in driver.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        body=[]
        for statement in main.body:
            body.append(copy.deepcopy(statement))
            if isinstance(statement,ast.Assign) and any(isinstance(n,ast.Name) and n.id=='args' for n in statement.targets):break
        body.append(ast.Return(value=ast.Name(id='args',ctx=ast.Load())))
        parser=ast.FunctionDef(name='parse_driver_only',args=copy.deepcopy(main.args),body=body,decorator_list=[],type_params=[])
        namespace={'argparse':argparse,'__doc__':'contract only'}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[parser],type_ignores=[])),'driver-real-parser-only','exec'),namespace)
        loader=BASE/'received-loader-evidence02-transfer03/upstream-loader-transfer03/result.json'
        audit=BASE/'received/post-checkout-audit01-result.json'
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        common=['--expected-source-sha256',sha(BASE/'linux_cpu_gate24_driver01.py'),
                '--loader-remediation-path','upstream-loader-transfer03/result.json','--loader-remediation-sha256',sha(loader),
                '--approval-reference','SYNTHETIC_CLI_CONTRACT_NOT_DISPATCH']
        argv=scope['gate_argv'](common,materialization_sha='d'*64,delta_result_sha='e'*64,
            upstream_path='post-checkout-audit01/result.json',upstream_sha=sha(audit),
            upstream_status='VERIFIED_LOCAL_DERIVED_LF_UPSTREAM_READONLY_NOT_LINUX_GATE')
        parsed=namespace['parse_driver_only'](argv)
        self.assertEqual(parsed.phase,'gate');self.assertEqual(parsed.upstream_audit_path,'post-checkout-audit01/result.json')
        self.assertEqual(parsed.upstream_audit_sha256,sha(audit));self.assertEqual(parsed.materialization_sha256,'d'*64)
        self.assertEqual(parsed.delta_result_sha256,'e'*64);self.assertEqual(parsed.loader_remediation_sha256,sha(loader))
        old_missing=argv[:]
        required=['--upstream-audit-path','--upstream-audit-sha256','--upstream-audit-status']
        for flag in required:
            index=old_missing.index(flag);del old_missing[index:index+2]
        errors=io.StringIO()
        with contextlib.redirect_stderr(errors),self.assertRaises(SystemExit) as stopped:
            namespace['parse_driver_only'](old_missing)
        self.assertEqual(stopped.exception.code,2)
        self.assertTrue(all(flag in errors.getvalue() for flag in required))


if __name__=='__main__':unittest.main(verbosity=2)
