"""Làm rõ khoảng cách chữ/số trong phần báo cáo mới, không đổi số liệu."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
HUMAN = ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'


def spaced(text):
    text = re.sub(r'(?<=[^\W\d_])(?=\d)|(?<=\d)(?=[^\W\d_])',' ',text)
    return text.replace('1000,1150,1300','1000, 1150, 1300')


md = HUMAN/'BAO_CAO.md'
text = md.read_text(encoding='utf-8')
start = text.index('## Chặng 15.')
end = text.index('## Còn phải chứng minh',start)
text = text[:start]+spaced(text[start:end])+text[end:]
for old,new in (('đạt299kiểm','đạt 299 kiểm'),('và18kiểm','và 18 kiểm'),
                ('đạt11kiểm','đạt 11 kiểm'),('và8kiểm','và 8 kiểm')):
    text = text.replace(old,new)
md.write_text(text,encoding='utf-8')
html = HUMAN/'BAO_CAO_NGHIEN_CUU.html'
text = html.read_text(encoding='utf-8')
start = text.index('<section id="chang-15">')
end = text.index('</section>',start)+len('</section>')
section = text[start:end]
section = re.sub(r'>([^<>]+)<',lambda match:'>'+spaced(match.group(1))+'<',section)
text = text[:start]+section+text[end:]
for old,new in (('đạt299kiểm','đạt 299 kiểm'),('và18kiểm','và 18 kiểm'),
                ('đạt11kiểm','đạt 11 kiểm'),('và8kiểm','và 8 kiểm')):
    text = text.replace(old,new)
html.write_text(text,encoding='utf-8')
print('NEW_SECTION_TYPOGRAPHY_ONLY_NUMBERS_PRESERVED')
