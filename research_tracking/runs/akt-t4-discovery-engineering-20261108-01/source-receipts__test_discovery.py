"""Synthetic filesystem/snapshot tests only; no target child/model/GPU/network."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('offline_discovery',HERE/'discovery.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
PROFILE=json.loads((HERE/'discovery_profile01.json').read_text())
LOCK=(HERE.parents[1]/'gpu08-linux-20261108-01/received/resolution-attempt01/candidate-linux-cuda.lock.txt').read_bytes()


class DiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(dir=HERE/'trial02'/'tmp')
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name)/'project';cls.root.mkdir()
        cls.base=copy.deepcopy(PROFILE);cls.base['source_files']={};cls.payloads={}
        for i in range(161):
            name=f'src/fixture_{i}.py';path=cls.root/name;path.parent.mkdir(exist_ok=True)
            payload=f'#synthetic {i}\n'.encode();path.write_bytes(payload);cls.base['source_files'][name]=d.sha(payload)
            cls.payloads[path]=payload
        for name in cls.base['upstream_files']:
            path=cls.root/'artifacts/akt/dependencies/upstream'/name;path.parent.mkdir(parents=True,exist_ok=True)
            payload=f'#synthetic upstream {name}\n'.encode();path.write_bytes(payload);cls.base['upstream_files'][name]=d.sha(payload)
            cls.payloads[path]=payload
        lock=cls.root/cls.base['lock_relative'];lock.parent.mkdir(parents=True,exist_ok=True);lock.write_bytes(LOCK)
        cls.payloads[lock]=LOCK
        cls.v=cls.root/'.venv';cls.v.mkdir()
        cls.pure=cls.v/'lib/python3.13/site-packages';cls.pure.mkdir(parents=True)

    def setUp(self):
        self.p=copy.deepcopy(self.base)
        (self.v/'pyvenv.cfg').write_text('include-system-site-packages = false\n')
        self.q={'abi':copy.deepcopy(self.p['expected_host']),'executable':str(self.v/'bin/python'),
                'prefix':'/usr','base_prefix':'/usr','purelib':str(self.pure),'no_site':1,'isolated':1,
                'sys_path':[str(self.pure)],'distributions':[], 'origins':{},
                'cuda_visible_devices':'','nvidia_visible_devices':'','heavy_modules_imported':[]}
        for n,v in self.p['package_versions'].items():
            self.q['distributions'].append({'name':n,'version':v,'root':str(self.pure),
                                            'metadata_sha256':'a'*64,'record_sha256':'b'*64})
        for name in d.MODULES:
            self.q['origins'][name]=None if name=='pip' else {'path':str(self.pure/name/'__init__.py'),'sha256':'c'*64,'bytes':1}

    def inspect(self,q=True,abi=None,filesystem=False,**kwargs):
        call=lambda:d.inspect_snapshot(self.root,self.p,self.q if q else None,abi or self.p['expected_host'],**kwargs)
        if filesystem:return call()
        # Source gate itself has real filesystem positive/negative cases below.
        # Repeated target-snapshot cases reuse immutable source bytes, avoiding thousands of Windows reads/resolves.
        original_read,original_path=d.read,d.relative_path
        def path(root,name):
            p=root.joinpath(*name.split('/'))
            return p if p in self.payloads else original_path(root,name)
        def read(p,cap):
            if p not in self.payloads:return original_read(p,cap)
            b=self.payloads[p]
            if len(b)>cap:raise ValueError('input byte cap exceeded')
            return b
        with patch.object(d,'read',read),patch.object(d,'relative_path',path):return call()

    def stopped(self,**kwargs):
        result=self.inspect(**kwargs);self.assertEqual(result['status'],'STOP_PARTIAL_OR_IDENTITY_MISMATCH');return result

    def test_warm_is_candidate_not_ready_and_inputs_immutable(self):
        before=copy.deepcopy((self.p,self.q));r=self.inspect(filesystem=True)
        self.assertEqual(r['status'],'WARM_CANDIDATE_REQUIRES_AUDIT');self.assertEqual(before,(self.p,self.q))
        self.assertIn('actual target wheel tags',r['remaining']);self.assertEqual(r['gpu_queries'],0)

    def test_missing_root_is_cold(self):
        self.assertEqual(d.inspect_snapshot(self.root/'absent',self.p,None,self.p['expected_host'])['status'],'COLD_ROOT_ABSENT')

    def test_missing_venv_is_cold(self):
        destination=self.root/'venv-away'
        self.assertTrue(self.v.resolve().is_relative_to(HERE.resolve()))
        self.assertTrue(destination.resolve().is_relative_to(HERE.resolve()))
        self.v.rename(destination)
        try:self.assertEqual(self.inspect(q=False)['status'],'COLD_VENV_ABSENT')
        finally:destination.rename(self.v)

    def test_valid_empty_venv_is_cold_not_install_approval(self):
        self.q['distributions']=[];self.q['origins']={n:None for n in d.MODULES}
        self.assertEqual(self.inspect()['status'],'COLD_VENV_EMPTY_REQUIRES_INSTALL_APPROVAL')

    def test_empty_venv_residue_rejected(self):
        self.q['distributions']=[];self.q['origins']={n:None for n in d.MODULES};(self.pure/'leftover').mkdir()
        self.addCleanup((self.pure/'leftover').rmdir)
        self.stopped()

    def test_partial_missing_cfg_rejected(self):
        (self.v/'pyvenv.cfg').unlink();self.stopped()

    def test_inherited_venv_rejected(self):
        (self.v/'pyvenv.cfg').write_text('include-system-site-packages = true\n');self.stopped()

    def test_duplicate_cfg_rejected(self):
        (self.v/'pyvenv.cfg').write_text('include-system-site-packages = false\ninclude-system-site-packages = false\n');self.stopped()

    def test_existing_venv_requires_fresh_probe(self):
        self.assertEqual(self.stopped(q=False)['reason'],'existing venv lacks fresh target probe')

    def test_abi_patch_change_stops(self):
        abi=copy.deepcopy(self.p['expected_host']);abi['python_version']='3.13.19';self.stopped(abi=abi)

    def test_target_abi_mismatch_stops(self):
        self.q['abi']['soabi']='cpython-313t';self.stopped()

    def test_target_executable_must_be_lexical_venv_entry(self):
        self.q['executable']='/usr/bin/python3';self.stopped()

    def test_wrong_prefix_stops(self):
        self.q['prefix']=str(self.root);self.stopped()

    def test_site_startup_stops(self):
        self.q['no_site']=0;self.stopped()

    def test_external_sys_path_stops(self):
        self.q['sys_path'].append('/usr/lib/python3.13/site-packages');self.stopped()

    def test_external_origin_stops(self):
        self.q['origins']['torch']['path']='/usr/lib/python3.13/site-packages/torch/__init__.py';self.stopped()

    def test_missing_origin_fingerprint_stops(self):
        del self.q['origins']['numpy']['sha256'];self.stopped()

    def test_unexpected_target_pip_stops(self):
        self.q['origins']['pip']={'path':str(self.pure/'pip/__init__.py')};self.stopped()

    def test_distribution_duplicate_stops(self):
        self.q['distributions'].append(self.q['distributions'][0]);self.stopped()

    def test_distribution_version_stops(self):
        self.q['distributions'][0]['version']='0.invalid';self.stopped()

    def test_distribution_external_stops(self):
        self.q['distributions'][0]['root']='/usr/site-packages';self.stopped()

    def test_heavy_import_stops(self):
        self.q['heavy_modules_imported']=['torch'];self.stopped()

    def test_visibility_not_hidden_stops(self):
        self.q['cuda_visible_devices']='0';self.stopped()

    def test_source_sha_change_stops(self):
        path=self.root/'src/fixture_0.py';old=path.read_bytes();self.addCleanup(path.write_bytes,old)
        path.write_bytes(b'changed');self.stopped(filesystem=True)

    def test_source_missing_stops(self):
        path=self.root/'src/fixture_0.py';old=path.read_bytes();self.addCleanup(path.write_bytes,old)
        path.unlink();self.stopped(filesystem=True)

    def test_lock_sha_change_stops(self):
        path=self.root/self.p['lock_relative'];old=path.read_bytes();self.addCleanup(path.write_bytes,old)
        path.write_bytes(b'changed');self.stopped(filesystem=True)

    def test_traversal_rejected(self):
        k=next(iter(self.p['source_files']));self.p['source_files']['../escape']=self.p['source_files'].pop(k);self.stopped()

    def test_protected_dataset_rejected(self):
        k=next(iter(self.p['source_files']));self.p['source_files']['dataset/private']=self.p['source_files'].pop(k);self.stopped()

    def test_bool_schema_rejected(self):
        self.p['schema_version']=True
        with self.assertRaises(ValueError):self.inspect()

    def test_bool_gil_rejected(self):
        self.p['expected_host']['gil_disabled']=False
        with self.assertRaises(ValueError):self.inspect()

    def test_bad_sha_rejected(self):
        k=next(iter(self.p['source_files']));self.p['source_files'][k]='a'*65
        with self.assertRaises(ValueError):self.inspect()

    def test_timeout_before_source_read(self):
        with self.assertRaises(TimeoutError):self.inspect(clock=lambda:2,deadline=1)

    def test_post_read_timeout_not_cold_success(self):
        ticks=iter([0,0,100])
        result=self.inspect(clock=lambda:next(ticks),deadline=1)
        self.assertEqual(result['status'],'STOP_PARTIAL_OR_IDENTITY_MISMATCH');self.assertIn('TimeoutError',result['reason'])

    def test_probe_code_has_no_heavy_imports_or_gpu_calls(self):
        tree=ast.parse(d.PROBE)
        imports={a.name for node in ast.walk(tree) if isinstance(node,ast.Import) for a in node.names}
        self.assertFalse(imports & {'torch','numpy','pandas','scipy','pip'})
        self.assertNotIn('is_available(',d.PROBE);self.assertNotIn('nvidia-smi',d.PROBE)

    def test_exact_cli_parser_contract_and_required_flags(self):
        values={'--profile':'/content/profile.json','--profile-sha256':'a'*64,
                '--expected-source-sha256':'b'*64,'--attempt-id':'cpu-discovery01',
                '--approval-reference':'READ_ONLY_CPU_DISCOVERY_NO_INSTALL_GPU'}
        argv=[part for pair in values.items() for part in pair]
        parsed=d._parser().parse_args(argv);self.assertEqual(parsed.attempt_id,'cpu-discovery01')
        import contextlib,io
        for key in values:
            missing=[part for flag,value in values.items() if flag!=key for part in (flag,value)]
            with self.subTest(required=key),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                d._parser().parse_args(missing)


if __name__=='__main__':unittest.main()
