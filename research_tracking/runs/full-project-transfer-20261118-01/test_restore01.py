"""Hồi quy nhỏ cho khôi phục, dùng fixture mới và không nạp checkpoint thật."""
from pathlib import Path
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

B=Path(__file__).resolve().parent
ROOT=B.parents[2]
sys.path.insert(0,str(B))
import khoi_phuc_ban_giao as restore


class RestoreTests(unittest.TestCase):
    def setUp(self):
        temp=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/tests'
        temp.mkdir(parents=True,exist_ok=True)
        self.work=tempfile.TemporaryDirectory(dir=temp)
        self.base=Path(self.work.name)

    def tearDown(self):
        allowed=(ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/tests').resolve()
        self.assertTrue(self.base.resolve().is_relative_to(allowed))
        if os.name=='nt' and self.base.exists():
            shutil.rmtree('\\\\?\\'+str(self.base.resolve()))
        self.work.cleanup()

    def package(self,name,files):
        path=self.base/name
        with zipfile.ZipFile(path,'w') as archive:
            for member,raw in files.items():
                archive.writestr(member,raw)
        return path

    def test_two_model_packages_keep_independent_root_documents(self):
        target=self.base/'restore';target.mkdir()
        for number in (1,2):
            name=f'package{number}.zip'
            raw=str(number).encode()
            manifest=json.dumps(dict(files={f'models/{number}.pt':dict(sha256=hashlib.sha256(raw).hexdigest())})).encode()
            path=self.package(name,{f'models/{number}.pt':raw,'PACKAGE_MANIFEST.json':manifest,'HUONG_DAN.md':raw})
            restore.extract(path,target)
            self.assertEqual((target/f'models/{number}.pt').read_bytes(),raw)
            namespace=name+'-'+restore.digest(path)[:12]
            self.assertEqual((target/f'handoff-reference/package-docs/{namespace}/HUONG_DAN.md').read_bytes(),raw)

    def test_existing_different_content_is_preserved(self):
        target=self.base/'restore';target.mkdir();(target/'file.txt').write_bytes(b'old')
        path=self.package('a.zip',{'file.txt':b'new'})
        with self.assertRaises(ValueError):
            restore.extract(path,target)
        self.assertEqual((target/'file.txt').read_bytes(),b'old')

    def test_parent_escape_rejected(self):
        target=self.base/'restore';target.mkdir()
        with self.assertRaises(ValueError):
            restore.extract(self.package('bad.zip',{'../escaped':b'x'}),target)
        self.assertFalse((self.base/'escaped').exists())

    def test_member_digest_rejected_before_target_publication(self):
        target=self.base/'restore';target.mkdir()
        manifest=json.dumps(dict(files=[dict(path='data.txt',sha256='0'*64,bytes=1)])).encode()
        with self.assertRaises(ValueError):
            restore.extract(self.package('bad.zip',{'data.txt':b'x','HANDOFF_INVENTORY.json':manifest}),target)
        self.assertFalse((target/'data.txt').exists())

    def test_restore_twice_is_idempotent(self):
        target=self.base/'restore';target.mkdir()
        path=self.package('a.zip',{'data.txt':b'correct'})
        self.assertEqual(restore.extract(path,target),1)
        self.assertEqual(restore.extract(path,target),0)

    def test_deep_windows_path(self):
        target=self.base/'restore';target.mkdir()
        member='/'.join(['long-directory-'+'x'*30]*5)+'/file.txt'
        path=self.package('long.zip',{member:b'long-path-ok'})
        self.assertEqual(restore.extract(path,target),1)
        self.assertEqual(restore.local_path(target,member).read_bytes(),b'long-path-ok')


if __name__=='__main__':
    unittest.main(verbosity=2)
