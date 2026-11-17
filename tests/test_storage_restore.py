"""Kiểm phục hồi từ gói lưu lạnh bằng dữ liệu tổng hợp nhỏ."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest,zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/storage'))
import restore_workspace as restore

def digest(data):return hashlib.sha256(data).hexdigest()

class RestoreTests(unittest.TestCase):
    def setUp(self):
        area=ROOT/'artifacts/akt/runtime/workspace-cleanup-20261118-01/restore-tests'
        area.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=area)
        self.base=Path(self.temp.name);self.downloads=self.base/'downloads';self.downloads.mkdir()
        self.target=self.base/'target';self.target.mkdir()
    def tearDown(self):
        self.assertTrue(self.base.resolve().is_relative_to((ROOT/'artifacts/akt/runtime').resolve()))
        self.temp.cleanup()
    def fixture(self,data=b'weights',member=True):
        path='experiments/akt/results/run/model.pt';sha=digest(data)
        payload=self.downloads/'drive1--source.zip'
        if member:
            with zipfile.ZipFile(payload,'w') as archive:archive.writestr('CONTENT/'+sha,data)
        else:payload.write_bytes(data)
        meta=dict(id='drive1',name='source.zip',size=str(payload.stat().st_size),sha256Checksum=digest(payload.read_bytes()))
        ref=dict(kind='bulk_member',file_id='drive1',member='CONTENT/'+sha) if member else dict(kind='drive_file',file_id='drive1')
        manifest=dict(files=[dict(path=path,bytes=len(data),sha256=sha,storage=ref)],drive_files={'drive1':meta})
        return manifest,path,payload
    def test_restore_exact_member(self):
        manifest,path,_=self.fixture()
        self.assertTrue(restore.restore_one(manifest,path,self.downloads,self.target))
        self.assertEqual((self.target/path).read_bytes(),b'weights')
    def test_direct_file_and_existing_identical(self):
        manifest,path,_=self.fixture(member=False)
        self.assertTrue(restore.restore_one(manifest,path,self.downloads,self.target))
        self.assertFalse(restore.restore_one(manifest,path,self.downloads,self.target))
    def test_existing_different_is_preserved(self):
        manifest,path,_=self.fixture();target=self.target/path;target.parent.mkdir(parents=True);target.write_bytes(b'old')
        with self.assertRaises(ValueError):restore.restore_one(manifest,path,self.downloads,self.target)
        self.assertEqual(target.read_bytes(),b'old')
    def test_corrupt_download_never_publishes(self):
        manifest,path,payload=self.fixture();payload.write_bytes(b'corrupt')
        with self.assertRaises((ValueError,FileNotFoundError)):restore.restore_one(manifest,path,self.downloads,self.target)
        self.assertFalse((self.target/path).exists())
    def test_parent_escape_is_rejected(self):
        with self.assertRaises(ValueError):restore.safe_path(self.target,'../outside')
        with self.assertRaises(ValueError):restore.safe_path(self.target,'C:/outside')
    def test_windows_device_name_is_rejected(self):
        with self.assertRaises(ValueError):restore.safe_path(self.target,'CON.txt')
    def test_member_size_is_bounded_before_publication(self):
        manifest,path,_=self.fixture(data=b'larger-than-declared')
        manifest['files'][0]['bytes']=1
        with self.assertRaisesRegex(ValueError,'vượt'):restore.restore_one(manifest,path,self.downloads,self.target)
        self.assertFalse((self.target/path).exists())
    def test_multipart_preserves_full_archive_bytes(self):
        data=b'abcdef';path='experiments/akt/results/run/artifacts.zip';drive={}
        for i,part in enumerate((b'abc',b'def'),1):
            p=self.downloads/f'p{i}--part{i}';p.write_bytes(part)
            drive[f'p{i}']=dict(id=f'p{i}',name=f'part{i}',size='3',sha256Checksum=digest(part))
        manifest=dict(files=[dict(path=path,bytes=6,sha256=digest(data),storage=dict(kind='drive_multipart',file_ids=['p1','p2']))],drive_files=drive)
        restore.restore_one(manifest,path,self.downloads,self.target)
        self.assertEqual((self.target/path).read_bytes(),data)

if __name__=='__main__':unittest.main()
