"""Giữ bảng Chặng17 trong chiều rộng màn hình nhỏ."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[4]
path = root / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do/BAO_CAO_NGHIEN_CUU.html'
before = path.read_bytes()
text = before.decode('utf-8')
css = '@media(max-width:700px){#chang-17 table{table-layout:fixed}#chang-17 th,#chang-17 td{min-width:0;overflow-wrap:anywhere;padding:.6rem .4rem}#chang-17 thead th:first-child{width:18%}}\n'
assert '#chang-17 table{table-layout:fixed}' not in text
text = text.replace('</style>', css + '</style>')
assert re.findall(r'<svg\b.*?</svg>', before.decode('utf-8'), re.S) == re.findall(r'<svg\b.*?</svg>', text, re.S)
path.write_bytes(text.encode('utf-8'))
print('CHAPTER17_MOBILE_TABLE_RULE_APPLIED')
