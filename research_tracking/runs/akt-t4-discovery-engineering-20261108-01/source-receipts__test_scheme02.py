"""Focused stdlib source-prefix regression; no operation/probe main or filesystem fixture."""
import argparse,ast,types,unittest
from pathlib import Path

class SchemeTests(unittest.TestCase):
    source=None
    def evaluate(self,schemes=('posix_local','venv')):
        tree=ast.parse(self.source.read_bytes())
        probe=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id=='PROBE' for t in n.targets))
        prefix=[]
        for node in ast.parse(probe).body:
            if isinstance(node,ast.FunctionDef):break
            if not isinstance(node,(ast.Import,ast.ImportFrom)):prefix.append(node)
        v=Path('/synthetic/project/.venv')
        def get_path(name,scheme=None,vars=None):
            self.assertEqual(name,'purelib');self.assertEqual(vars,{'base':str(v),'platbase':str(v)})
            return str(v/('lib/python3.13/site-packages' if scheme=='venv' else 'local/lib/python3.13/dist-packages'))
        env={'Path':Path,'sys':types.SimpleNamespace(argv=['probe',str(v)],flags=types.SimpleNamespace(no_site=1,isolated=1)),
             'sysconfig':types.SimpleNamespace(get_path=get_path,get_scheme_names=lambda:schemes)}
        exec(compile(ast.Module(body=prefix,type_ignores=[]),str(self.source),'exec'),env)
        return env['pure']
    def test_debian_default_does_not_override_explicit_venv(self):
        self.assertEqual(self.evaluate(),Path('/synthetic/project/.venv/lib/python3.13/site-packages'))
    def test_missing_venv_scheme_stops_without_fallback(self):
        with self.assertRaisesRegex(ValueError,'explicit venv scheme unavailable'):
            self.evaluate(schemes=('posix_local','posix_venv'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
    SchemeTests.source=a.source
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SchemeTests))
    raise SystemExit(0 if result.wasSuccessful() else 1)
