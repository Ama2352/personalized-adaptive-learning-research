"""Giữ nguyên candidate01, sửa đối chiếu stamp theo từng API ở candidate02."""
from pathlib import Path
import ast
import hashlib

p = Path(__file__).resolve().parent
source = p / 'main_selection_file_primitives_candidate01.py'
tests = p / 'test_main_selection_file_primitives_candidate01.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '2b7016f7d9a8b4b295d44d95e8eb1f39c1d4054dcb46bac25f8d875d62d8b335'
assert hashlib.sha256(tests.read_bytes()).hexdigest() == 'e2b2de67a468a076aef2a340c5eeaec291e60cdab0131e99bcaac52ea5dd40e9'
text = source.read_text(encoding='utf-8')
old = "                need(self._stamp(os.fstat(stream.fileno())) == token, 'Opened exact file identity')"
new = """                opened_token = self._stamp(os.fstat(stream.fileno()))
                # Path và handle có thể trả ctime khác nhau. Giữ kiểm ctime
                # trong từng API, identity/size/mtime vẫn phải khớp giữa hai API.
                need(opened_token[:4] == token[:4], 'Opened exact file identity')"""
assert text.count(old) == 1
text = text.replace(old, new).replace("need(self._stamp(os.fstat(stream.fileno())) == token\n",
                                   "need(self._stamp(os.fstat(stream.fileno())) == opened_token\n")
target = p / 'main_selection_file_primitives_candidate02.py'
assert not target.exists()
target.write_text(text, encoding='utf-8', newline='\n')
test_text = tests.read_text(encoding='utf-8').replace('main_selection_file_primitives_candidate01',
                                                  'main_selection_file_primitives_candidate02')
test_text = test_text.replace('import tempfile\n', 'import tempfile\nimport os\nfrom types import SimpleNamespace\n')
regression = '''    def test_ctime_checked_within_each_api(self):
        ref = self.put('ctime.json', b'{"value":1}')
        actual_fstat = os.fstat

        def shifted(fd, shift):
            value = actual_fstat(fd)
            return SimpleNamespace(st_dev=value.st_dev, st_ino=value.st_ino,
                st_size=value.st_size, st_mtime_ns=value.st_mtime_ns,
                st_ctime_ns=value.st_ctime_ns + shift)

        # Stable cross-API ctime difference is accepted, all content checks run.
        reader = m.BoundedArtifactReader(self.root, limits())
        with patch('os.fstat', side_effect=lambda fd: shifted(fd, 1000)):
            self.assertEqual(reader.read_json(ref), {'value': 1})
            self.assertEqual(reader.verify_unchanged()['files'], 1)
        self.assertEqual(reader.open_files, 0)

        # A change within the same handle API still poisons the operation.
        calls = []
        def changing(fd):
            calls.append(fd)
            return shifted(fd, len(calls))
        reader = m.BoundedArtifactReader(self.root, limits())
        with patch('os.fstat', side_effect=changing), self.assertRaisesRegex(ValueError, 'changed during read'):
            reader.read_json(ref)
        self.assertTrue(reader.failed)
        self.assertEqual(reader.open_files, 0)

'''
anchor = '    def test_all_nine_producer_headers_and_null_wire_strings(self):'
assert test_text.count(anchor) == 1
test_text = test_text.replace(anchor, regression + anchor)
target_tests = p / 'test_main_selection_file_primitives_candidate02.py'
assert not target_tests.exists()
target_tests.write_text(test_text, encoding='utf-8', newline='\n')
ast.parse(text)
ast.parse(test_text)
print('Candidate02 giữ các kiểm tra nội dung và stamp trong từng API, thêm một regression test.')
