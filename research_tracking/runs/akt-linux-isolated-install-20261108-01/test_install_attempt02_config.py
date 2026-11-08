"""Synthetic-only API guard tests; không import pip hoặc chạy controller/install."""
import ast
import hashlib
from pathlib import Path
import sys
import unittest

BASE=Path(__file__).parent
SOURCE=BASE/'install_stage_attempt02.py'
EXPECTED='021dcbe8a4a4a994d56572eb0ac76743c9a1bb3854cb56ca205da7017cb1a21f'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
TREE=ast.parse(SOURCE.read_bytes())
CHILD=next(ast.literal_eval(n.value) for n in TREE.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BASE_PIP' for t in n.targets))
HELPER=next(n for n in ast.parse(CHILD).body if isinstance(n,ast.FunctionDef) and n.name=='verify_effective_config')
NAMESPACE={}
exec(compile(ast.Module(body=[HELPER],type_ignores=[]),str(SOURCE),'exec'),NAMESPACE)
verify=NAMESPACE['verify_effective_config']
OLD_MODE='--old-guard' in sys.argv
if OLD_MODE:
    sys.argv.remove('--old-guard')
    original=BASE/'install_stage.py'
    assert hashlib.sha256(original.read_bytes()).hexdigest()=='28927535b16b66167e4c71a42a406d9a1c138b388806df093434cba6c0010a87'
    original_tree=ast.parse(original.read_bytes())
    old_child=next(ast.literal_eval(n.value) for n in original_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BASE_PIP' for t in n.targets))
    old_loop=next(n for n in ast.parse(old_child).body if isinstance(n,ast.For))
    class BindInputs(ast.NodeTransformer):
        def visit_Call(self,node):
            if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='c' and node.func.attr=='items':return ast.Name(id='items',ctx=ast.Load())
            return self.generic_visit(node)
        def visit_Attribute(self,node):
            if isinstance(node.value,ast.Name) and node.value.id=='os' and node.attr=='devnull':return ast.Name(id='devnull',ctx=ast.Load())
            return self.generic_visit(node)
    old_loop=BindInputs().visit(old_loop)
    wrapper=ast.parse("def verify_old(items,environ,devnull):\n return {'effective_config_keys':[':env:.config-file'],'config_api_shape':'flat','pip_environment_names':['PIP_CONFIG_FILE']}\n").body[0]
    wrapper.body.insert(0,old_loop)
    module=ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[]))
    exec(compile(module,str(original),'exec'),NAMESPACE)
    verify=NAMESPACE['verify_old']
DEVNULL='/dev/null'
ENV={'PIP_CONFIG_FILE':DEVNULL,'UNRELATED_HOST_KEY':'ignored'}
FLAT=[(':env:.config-file',DEVNULL)]
NESTED=[(':env:',{':env:.config-file':DEVNULL})]


class ConfigGuardTests(unittest.TestCase):
    def reject(self,items,env=None):
        with self.assertRaises(ValueError):verify(items,ENV if env is None else env,DEVNULL)

    def test_observed_nested_false_positive_in_old_guard(self):
        with self.assertRaises(ValueError):
            for key,value in NESTED:
                if not (key.endswith('config-file') and value==DEVNULL):raise ValueError('old guard rejected benign nested metadata')
        self.assertEqual(verify(NESTED,ENV,DEVNULL)['config_api_shape'],'nested')

    def test_exact_flat(self):
        self.assertEqual(verify(FLAT,ENV,DEVNULL)['config_api_shape'],'flat')

    def test_iterator_not_consumed_twice(self):
        self.assertEqual(verify(iter(NESTED),ENV,DEVNULL)['effective_config_keys'],[':env:.config-file'])

    def test_flat_target(self):self.reject(FLAT+[('install.target','/tmp/other')])
    def test_flat_index(self):self.reject(FLAT+[('global.index-url','https://example.invalid')])
    def test_nested_target(self):self.reject([(':env:',{':env:.config-file':DEVNULL,':env:.target':'/tmp/other'})])
    def test_nested_index(self):self.reject([(':env:',{':env:.config-file':DEVNULL,':env:.index-url':'https://example.invalid'})])
    def test_file_section(self):self.reject(NESTED+[('global',{'global.index-url':'https://example.invalid'})])
    def test_file_config_file_suffix(self):self.reject([('global.config-file',DEVNULL)])
    def test_wrong_nested_key(self):self.reject([(':env:',{'config-file':DEVNULL})])
    def test_unknown_section(self):self.reject([('global',{':env:.config-file':DEVNULL})])
    def test_duplicate_flat(self):self.reject(FLAT+FLAT)
    def test_duplicate_nested(self):self.reject(NESTED+NESTED)
    def test_mixed_flat_nested(self):self.reject(FLAT+NESTED)
    def test_missing_effective_entry(self):self.reject([])
    def test_empty_nested(self):self.reject([(':env:',{})])
    def test_wrong_scalar_type(self):self.reject([(':env:.config-file',False)])
    def test_wrong_nested_value(self):self.reject([(':env:',{':env:.config-file':None})])
    def test_wrong_scalar_path(self):self.reject([(':env:.config-file','/tmp/pip.conf')])
    def test_wrong_nested_path(self):self.reject([(':env:',{':env:.config-file':'/tmp/pip.conf'})])
    def test_missing_env(self):self.reject(FLAT,{})
    def test_wrong_env_path(self):self.reject(FLAT,{'PIP_CONFIG_FILE':'/tmp/pip.conf'})
    def test_env_target(self):self.reject(NESTED,{'PIP_CONFIG_FILE':DEVNULL,'PIP_TARGET':'/tmp/other'})
    def test_env_index(self):self.reject(NESTED,{'PIP_CONFIG_FILE':DEVNULL,'PIP_INDEX_URL':'https://example.invalid'})
    def test_env_even_ignored_pip_flag(self):self.reject(FLAT,{'PIP_CONFIG_FILE':DEVNULL,'PIP_HELP':'1'})
    def test_non_pair_item(self):self.reject(['wrong-shape'])
    def test_non_string_key(self):self.reject([(123,DEVNULL)])
    def test_no_values_in_audit(self):
        audit=verify(NESTED,ENV,DEVNULL)
        self.assertEqual(set(audit),{'effective_config_keys','config_api_shape','pip_environment_names'})
        self.assertNotIn(DEVNULL,str(audit))


if __name__=='__main__':unittest.main(verbosity=2)
