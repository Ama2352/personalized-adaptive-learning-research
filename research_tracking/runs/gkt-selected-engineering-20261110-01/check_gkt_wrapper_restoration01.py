"""ROOT-only bounded stdlib projection, không import/execute worker hoặc NN."""
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

PREP=Path(__file__).resolve().parent
WORKER=PREP/'check_gkt_selected_fit01.py'
OUTPUT=PREP/'gkt-wrapper-restoration-precheck01.json'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker-sha256',required=True)
    args=parser.parse_args()
    payload=WORKER.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=args.worker_sha256:
        raise ValueError('Root reviewed exact worker bytes required')
    tree=ast.parse(payload,filename=str(WORKER))
    entry=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
    assignments=[node for node in ast.walk(entry) if isinstance(node,ast.Assign)]
    environment=next(node for node in assignments if isinstance(node.value,ast.Tuple)
        and any(isinstance(value,ast.Constant) and value.value=='TEMP' for value in node.value.elts))
    export=next(node for node in assignments if isinstance(node.value,ast.Lambda))
    names=(environment.targets[0].id,export.targets[0].id)
    if names!=('environment_keys','export_keys'):
        raise ValueError('Distinct stable environment/export locals required')
    for name in names:
        writes=[node for node in assignments if any(isinstance(target,ast.Name) and target.id==name for target in node.targets)]
        if len(writes)!=1:
            raise ValueError('Tracked local rebound in actual worker main')
    saved=next(node for node in assignments if any(isinstance(target,ast.Name) and target.id=='env' for target in node.targets))
    restored=next(node for node in assignments if any(isinstance(target,ast.Name) and target.id=='restored' for target in node.targets))
    restore_loop=next(node for node in ast.walk(entry) if isinstance(node,ast.For)
        and isinstance(node.iter,ast.Call) and isinstance(node.iter.func,ast.Attribute)
        and isinstance(node.iter.func.value,ast.Name) and node.iter.func.value.id=='env'
        and node.iter.func.attr=='items')
    environment_check=ast.Assign(targets=[ast.Name(id='environment_restored',ctx=ast.Store())],
        value=deepcopy(restored.value.values[0]))
    primary=RuntimeError('PRIMARY_SENTINEL_NOT_WORKER_EXECUTION')
    context={'os':SimpleNamespace(environ={'TEMP':'caller','COLUMNS':'113'}),'primary':primary}
    body=[deepcopy(environment),deepcopy(saved),deepcopy(export),
        ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Attribute(value=ast.Name(id='os',ctx=ast.Load()),
            attr='environ',ctx=ast.Load()),attr='update',ctx=ast.Load()),args=[ast.Dict(
                keys=[ast.Constant(value=key) for key in ('TEMP','TMP','TMPDIR','COLUMNS','LINES')],
                values=[ast.Constant(value='owned') for _ in range(5)])],keywords=[])),
        ast.Try(body=[ast.Raise(exc=ast.Name(id='primary',ctx=ast.Load()),cause=None)],handlers=[],orelse=[],
            finalbody=[deepcopy(restore_loop),environment_check])]
    projection=ast.fix_missing_locations(ast.Module(body=body,type_ignores=[]))
    observed=None
    try:
        exec(compile(projection,'<actual-worker-finally-projection>','exec'),context)
    except BaseException as error:
        observed=error
    if observed is not primary or context.get('environment_restored') is not True:
        raise ValueError('Actual restoration projection masks primary failure')
    if context['os'].environ!={'TEMP':'caller','COLUMNS':'113'}:
        raise ValueError('Exact original environment mapping not restored')
    result=dict(status='ACCEPTED_STDLIB_WRAPPER_LOCAL_AND_FINALLY_PROJECTION_NOT_NATIVE',
        worker_sha256=args.worker_sha256,checks=2,distinct_names=list(names),primary_exception_preserved=True,
        environment_restored=True,worker_module_imported=False,model_calls=0)
    with OUTPUT.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,sort_keys=True,indent=2,allow_nan=False)
        stream.write('\n')


if __name__=='__main__':
    main()
