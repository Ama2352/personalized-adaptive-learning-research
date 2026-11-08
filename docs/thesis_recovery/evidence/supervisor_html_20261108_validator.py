"""Kiểm số liệu/trình bày HTML từ nguồn đã lưu; không thực thi notebook/model."""
from pathlib import Path
from html.parser import HTMLParser
import ast,hashlib,json,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
F=R/'research_tracking/supervisor_reports/2026-11-08/01_tien_do/BAO_CAO_NGHIEN_CUU.html'
raw=F.read_bytes();sha=hashlib.sha256(raw).hexdigest();doc=raw.decode('utf-8')
class Read(HTMLParser):
    def __init__(self):
        super().__init__();self.tables=[];self.current=None;self.row=None;self.cell=None;self.links=[];self.ids=[];self.scripts=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='a':self.links.append(attrs['href'])
        if tag=='script':self.scripts+=1
        if tag=='table':self.current=[];self.tables.append(self.current)
        if tag=='tr':self.row=[];self.current.append(self.row)
        if tag in ('td','th'):self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th'):self.row.append(''.join(self.cell).strip());self.cell=None
        if tag=='table':self.current=None
parser=Read();parser.feed(doc)
assert len(parser.tables)==5 and parser.scripts==0
assert len(parser.ids)==len(set(parser.ids)) and all(h.startswith('#') and h[1:] in parser.ids for h in parser.links)
assert not re.search(r'\b[a-fA-F0-9]{64}\b',doc)
assert all(s not in doc for s in ('research_tracking/','artifacts/','sha256','SHA-256','Run all','Run All','ROOT','Colab','localhost'))
baseline=(R/'docs/bkt-gam-kt-benchmark.md').read_text(encoding='utf-8').split('## Kết quả common-row',1)[1].split('## Paired cluster bootstrap',1)[0]
rows=[[s.strip() for s in line.split('|')[1:-1]] for line in baseline.splitlines() if re.match(r'^\| (AUC|Log Loss|Brier|ECE|Accuracy) \|',line)]
assert parser.tables[1][1:]==rows and len(rows)==5
assert parser.tables[4][1:]==[['Huấn luyện','48','10.080','84'],['Chọn số vòng học','6','1.260','84'],['Hiệu chỉnh xác suất','6','1.260','84']]
n=json.loads((P/'supervisor_notebook_before_html01.ipynb').read_bytes())
svg=re.findall(r'<svg\b.*?</svg>',doc,re.S);assert len(svg)==8
for cell,index in ((5,1),(8,3),(11,4),(13,5),(16,6),(20,7)):
    old=next(o['data']['image/svg+xml'] for o in n['cells'][cell]['outputs'] if 'image/svg+xml' in o.get('data',{}))
    old=''.join(old) if isinstance(old,list) else old
    before=list(ET.fromstring(old).iter());after=list(ET.fromstring(svg[index]).iter());assert len(before)==len(after)
    for a,b in zip(before,after):
        assert a.tag==b.tag
        keep=lambda node:{k:v for k,v in node.attrib.items() if k not in (('role','aria-label','x','y','text-anchor','fill') if cell in (5,16) and node.tag.endswith('text') else ('role','aria-label'))}
        assert keep(a)==keep(b),a.tag
    def data_numbers(nodes):
        selected=[(t.text or '') for t in nodes if t.tag.endswith('text') and (re.match(r'^(?:[+-]?\d|[AB]:|[AB]\d|[HL]=|T\s*\+|a=|Block|Khối|Control|Đối chứng)',t.text or '') or '(n=' in (t.text or ''))]
        return [float(v) for v in re.findall(r'[+-]?\d+(?:\.\d+)?',' '.join(selected))]
    assert data_numbers(before)==data_numbers(after)
receipt=json.loads((P/'supervisor_html01_build_receipt.json').read_bytes());browser=json.loads((P/'supervisor_html02_browser_qa.json').read_bytes())
assert receipt['output_sha256']==browser['html_sha256']==sha
assert receipt['numeric_records']==58 and receipt['sources_before_after_equal'] is True
assert browser['desktop']['svgOverflow']==[] and browser['mobile']['anchorTargetsValid'] is True
assert browser['desktop']['textCollisions']==browser['mobile']['textCollisions']==[]
old=(P/'supervisor_html_before_label_fix.html').read_text(encoding='utf-8')
assert re.search(r'<style>(.*?)</style>',old,re.S).group(1)==re.search(r'<style>(.*?)</style>',doc,re.S).group(1)
assert browser['mobile']['documentWidth']<=browser['mobile']['viewport'] and browser['mobile']['externalAssets']==0
assert browser['print']['printMedia'] and browser['print']['navHidden']
images={}
for name in ('supervisor_html_desktop_final.png','supervisor_html_mobile_final.png','supervisor_html_exposure_final.png','supervisor_html_fixed_labels_final.png','supervisor_html_ability_labels_final.png'):
    image=P/name;assert image.is_file();images[name]=hashlib.sha256(image.read_bytes()).hexdigest()
result=dict(status='SOURCE_NUMERICS_AND_BROWSER_LAYOUT_VERIFIED',html_sha256=sha,html_bytes=len(raw),tables=5,figures=8,
    baseline_rows_exact=5,existing_svg_quantitative_geometry_and_numbers_exact=6,source_pointer_records_checked_by_builder=58,
    hashes_and_internal_file_links_in_html=False,external_assets=0,script_tags=0,
    desktop_mobile_verified=True,text_collision_pairs=0,print_css_verified=True,pdf_pagination_verified=False,
    source_inventory=receipt['source_inventory'],screenshots_sha256=images,
    research_or_training_rerun=False,new_independent_N=0)
out=R/'docs/thesis_recovery/evidence/supervisor_html_20261108_validation.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('source_inventory','screenshots_sha256')},ensure_ascii=False))
