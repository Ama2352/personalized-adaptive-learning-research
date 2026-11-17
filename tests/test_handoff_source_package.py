"""Kiểm corpus tracked và tiếp tục đóng gói source sau gián đoạn."""
from pathlib import Path
import tempfile,sys,unittest,zipfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research_tracking/runs/workspace-cleanup-20261118-01'))
import publish_final as publisher

class SourcePackageTests(unittest.TestCase):
    def test_tracked_public_corpus_is_allowed_and_private_is_not(self):
        self.assertTrue(publisher.source_allowed('artifacts/simulator/corpora/public/manifest.json',True,100))
        self.assertFalse(publisher.source_allowed('artifacts/akt/private/token.json',True,100))
        self.assertFalse(publisher.source_allowed('dataset/raw.csv',True,100))
    def test_interruption_keeps_final_absent_and_retry_succeeds(self):
        area=ROOT/'artifacts/akt/runtime/workspace-cleanup-20261118-01/source-package-tests';area.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=area) as work:
            root=Path(work);a=root/'a.txt';a.write_text('a');b=root/'b.txt';b.write_text('b');target=root/'source.zip'
            original=zipfile.ZipFile.write
            def fail(archive,path,*args,**kwargs):
                if Path(path)==b:raise OSError('simulated interruption')
                return original(archive,path,*args,**kwargs)
            with patch.object(zipfile.ZipFile,'write',fail):
                with self.assertRaises(OSError):publisher.build_source_zip(target,root,'commit',[a,b])
            self.assertFalse(target.exists())
            self.assertTrue(target.with_name('source.zip.partial').exists())
            pins=publisher.build_source_zip(target,root,'commit',[a,b])
            self.assertEqual(len(pins),2)
            with zipfile.ZipFile(target) as archive:self.assertEqual(archive.read('b.txt'),b'b')

if __name__=='__main__':unittest.main()
