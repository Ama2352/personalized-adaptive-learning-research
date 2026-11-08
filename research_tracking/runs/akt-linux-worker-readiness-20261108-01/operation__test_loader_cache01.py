"""3stdlib guard cases; không Git/subprocess/model/remote execution."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import unittest

WORK=Path(__file__).resolve().parent
SOURCE=WORK/'materialize_cached_upstream_loader01.py'
spec=importlib.util.spec_from_file_location('loader_cache_offline_guards',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
REPO=WORK.parents[3]
LF_DIR=REPO/'artifacts/akt/local-tests/upstream-git-blob-profile-20261108-01'
RAW={name:(LF_DIR/name).read_bytes() for name in module.LF}
IDENTITY={'commit':module.PIN,'tree':module.TREE,'remote':module.URL,'files':module.LF}

class Guards(unittest.TestCase):
    def test_bad_loader_rejected_before_mutation_and_exact_child_argv(self):
        data=(WORK/'upstream-load_data-pinned-lf01.py').read_bytes()
        module.validate_loader(data,module.LOADER_BLOB)
        self.assertEqual(len(data),6428);self.assertEqual(hashlib.sha256(data).hexdigest(),module.LOADER_SHA)
        with self.assertRaises(ValueError):module.validate_loader(data[:-1],module.LOADER_BLOB)
        with self.assertRaises(ValueError):module.validate_loader(data,'0'*40)
        child=ast.parse(module.CHILD.replace('PROFILE_CONSTANTS','{}'))
        args=[tuple(arg.value for arg in n.args) for n in ast.walk(child)
              if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='required'
              and all(isinstance(a,ast.Constant) for a in n.args)]
        self.assertIn(('sparse-checkout','set','--no-cone','/akt.py','/README.md','/LICENSE','/load_data.py'),args)
        literals={n.value for n in ast.walk(child) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
        self.assertNotIn('fetch',literals);self.assertNotIn('clone',literals)
        self.assertIn(bytes([0]),[n.value for n in ast.walk(child) if isinstance(n,ast.Constant) and isinstance(n.value,bytes)])

    def test_original_source_drift_rejected(self):
        module.validate_original(IDENTITY,'',RAW)
        changed={**RAW,'akt.py':RAW['akt.py']+b'\n'}
        with self.assertRaises(ValueError):module.validate_original(IDENTITY,'',changed)
        with self.assertRaises(ValueError):module.validate_original({**IDENTITY,'tree':'0'*40},'',RAW)

    def test_dirty_checkout_rejected_and_environment_failclosed(self):
        with self.assertRaises(ValueError):module.validate_original(IDENTITY,' M akt.py',RAW)
        env=module.isolated_environment({'GIT_CONFIG_COUNT':'99','GIT_CONFIG_KEY_99':'credential.helper','GIT_DIR':'/outside',
            'HTTPS_PROXY':'private','API_TOKEN':'secret','PYTHONPATH':'outside','PIP_TARGET':'outside','KEEP':'yes'})
        self.assertNotIn('GIT_DIR',env);self.assertNotIn('GIT_CONFIG_KEY_99',env)
        self.assertNotIn('HTTPS_PROXY',env);self.assertNotIn('API_TOKEN',env);self.assertNotIn('PYTHONPATH',env)
        self.assertNotIn('PIP_TARGET',env);self.assertEqual(env['GIT_CONFIG_COUNT'],'6')
        self.assertEqual(env['GIT_ALLOW_PROTOCOL'],'__NO_TRANSPORT__');self.assertEqual(env['GIT_NO_LAZY_FETCH'],'1')
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'');self.assertEqual(env['KEEP'],'yes')

if __name__=='__main__':unittest.main(verbosity=2)
