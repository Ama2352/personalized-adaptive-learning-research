"""Synthetic RECORD-path tests only; không import package target hoặc tạo venv."""
import ast
from pathlib import Path,PurePosixPath
import sys
import unittest

BASE=Path(__file__).parent
SOURCE=BASE/'post_install_audit01.py'
tree=ast.parse(SOURCE.read_bytes())
child=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHILD' for t in n.targets))
function=next(n for n in ast.parse(child).body if isinstance(n,ast.FunctionDef) and n.name=='select_root_metadata')
namespace={'Path':Path,'PurePosixPath':PurePosixPath}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(SOURCE),'exec'),namespace)
select=namespace['select_root_metadata']
if '--old-matcher' in sys.argv:
    sys.argv.remove('--old-matcher')
    original=ast.parse((BASE/'install_stage_attempt02.py').read_bytes())
    body=next(ast.literal_eval(n.value) for n in original.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='AUDIT' for t in n.targets))
    original_loop=next(n for n in ast.parse(body).body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='d')
    assignment=next(n for n in original_loop.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='metadata' for t in n.targets))
    class BindLocate(ast.NodeTransformer):
        def visit_Attribute(self,node):
            if isinstance(node.value,ast.Name) and node.value.id=='d' and node.attr=='locate_file':return ast.Name(id='locate_file',ctx=ast.Load())
            return self.generic_visit(node)
    assignment=BindLocate().visit(assignment)
    wrapper=ast.parse("def old(files,locate_file,venv,purelib):\n for f in files:assert Path(locate_file(f)).resolve().is_relative_to(venv.resolve())\n assert len(metadata)==1\n return metadata[0]\n").body[0]
    wrapper.body.insert(1,assignment)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),str(BASE/'install_stage_attempt02.py'),'exec'),namespace)
    select=namespace['old']

VENV=(BASE/'synthetic-uncreated-venv').resolve()
PURE=VENV/'lib/python3.13/site-packages'
ROOT='setuptools-84.2.1.dist-info/METADATA'
NESTED=[f'setuptools/_vendor/package{i}-1.0.dist-info/METADATA' for i in range(12)]
def locate(name):return PURE/name


class MetadataTests(unittest.TestCase):
    def reject(self,files,mapping=None):
        with self.assertRaises((ValueError,AssertionError)):select(files,locate if mapping is None else mapping,VENV,PURE)
    def test_plain_root(self):self.assertEqual(select([ROOT],locate,VENV,PURE),PURE/ROOT)
    def test_root_plus_one_nested(self):self.assertEqual(select([ROOT,NESTED[0]],locate,VENV,PURE),PURE/ROOT)
    def test_observed_thirteen_all_depth_one_root(self):self.assertEqual(select([ROOT,*NESTED],locate,VENV,PURE),PURE/ROOT)
    def test_nested_order_independent(self):self.assertEqual(select([*NESTED,ROOT],locate,VENV,PURE),PURE/ROOT)
    def test_bin_script_inside_venv(self):
        files=[ROOT,'../../../bin/tool']
        self.assertEqual(select(files,locate,VENV,PURE),PURE/ROOT)
    def test_missing_root(self):self.reject(['pkg/__init__.py'])
    def test_nested_only(self):self.reject(NESTED)
    def test_multiple_root(self):self.reject([ROOT,'other-1.0.dist-info/METADATA'])
    def test_duplicate_root(self):self.reject([ROOT,ROOT])
    def test_root_escape(self):self.reject([ROOT],lambda name:VENV.parent/'outside'/name)
    def test_nonmetadata_record_escape(self):self.reject([ROOT,'escaped.py'],lambda name:VENV.parent/name if name=='escaped.py' else locate(name))
    def test_nested_record_escape(self):self.reject([ROOT,NESTED[0]],lambda name:VENV.parent/name if name==NESTED[0] else locate(name))
    def test_root_in_venv_wrong_purelib(self):self.reject([ROOT],lambda name:VENV/'wrong-site'/name)
    def test_wrong_root_directory_suffix(self):self.reject(['setuptools-84.2.1.info/METADATA'])
    def test_wrong_metadata_case(self):self.reject(['setuptools-84.2.1.dist-info/metadata'])
    def test_nested_extra_depth(self):self.reject(['pkg/data/'+ROOT])


if __name__=='__main__':unittest.main(verbosity=2)
