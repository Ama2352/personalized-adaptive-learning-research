"""Kiểm contract bàn giao và mức kết luận, không thực thi model hoặc mở nhãn Test."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent


def load(name):
    return json.loads((B/name).read_text(encoding='utf-8'))


class Tables(HTMLParser):
    def __init__(self):
        super().__init__();self.tables=0;self.cells=[];self.row=None;self.links=[]

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='table':
            self.tables+=1
        if tag=='tr':
            self.row=0
        if tag in {'td','th'}:
            assert self.row is not None
            self.row+=1
        if tag=='a' and 'href' in attrs:
            self.links.append(attrs['href'])

    def handle_endtag(self,tag):
        if tag=='tr':
            self.cells.append(self.row);self.row=None


def main():
    inventory=load('PACKAGE_INVENTORY01.json')['batches']+load('CONFIDENCE_OUTPUTS_INVENTORY01.json')['batches']
    receipts=load('NEW_ARCHIVES_DRIVE01.json')['files']+load('CONFIDENCE_ARCHIVES_DRIVE01.json')['files']
    assert len(inventory)==len(receipts)==17
    expected={b['name']:b for b in inventory}
    paths=set()
    for batch in inventory:
        assert sum(r['bytes'] for r in batch['files'])==batch['source_bytes']
        for row in batch['files']:
            path=Path(row['path'])
            assert not path.is_absolute() and '..' not in path.parts and 'private' not in path.parts
            assert re.fullmatch('[0-9a-f]{64}',row['sha256'])
            assert row['path'] not in paths
            paths.add(row['path'])
    folder=load('DRIVE_FOLDER01.json')['id']
    for receipt in receipts:
        batch=expected[receipt['name']]
        assert receipt['member_count']==len(batch['files']) and receipt['source_bytes']==batch['source_bytes']
        assert receipt['source_rehashed_after_transfer'] and receipt['zip_members_verified']
        assert receipt['parents']==[folder] and receipt['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
        assert re.fullmatch('[0-9a-f]{64}',receipt['sha256Checksum'])
    catalog=load('TRAINING_OUTPUTS_CATALOG01.json')
    assert catalog['groups']['BKT']['cv_exercise_fit_instances']==3537
    assert catalog['groups']['BKT']['final_pkl_files']==720
    assert len(catalog['groups']['GAM_KT']['difficulty_banks'])==5
    assert catalog['groups']['AKT_JUNYI']['selected_total_executed_epochs']==48
    assert catalog['groups']['AKT_JUNYI']['refit_total_epochs']==36
    assert len(catalog['groups']['AKT_GRADE10']['models'])==7
    assert catalog['remaining_neural_training_phases']['total']==21
    report=(B/'BAN_GIAO_TRAINING.html').read_text(encoding='utf-8')
    parser=Tables();parser.feed(report)
    assert parser.tables==5 and len(parser.cells)>30
    assert all(n in {3,4,5} for n in parser.cells)
    assert all(link.startswith('https://drive.google.com/') for link in parser.links)
    assert 'chưa phát hiện' in report and 'mộtfold/mộtseed' in report
    human=ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
    for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'):
        text=(human/name).read_text(encoding='utf-8')
        assert '21phase' in text and 'learnedJunyi' in text
        assert 'độ lớn hiệu ứng' in text and 'khoảng bất định' in text
    result=dict(status='HANDOFF_CONTRACT_AND_REPORT_SEMANTIC_CHECKS_PASSED',
        archives=len(receipts),source_files=len(paths),source_bytes=sum(b['source_bytes'] for b in inventory),
        archive_bytes=sum(int(r['size']) for r in receipts),reused_model_parts=len(load('REUSED_MODEL_DRIVE01.json')['files']),
        reused_outer_and_history_files=len(load('REUSED_EVALUATION_HISTORY_DRIVE01.json')['files']),
        html_tables=parser.tables,html_rows=len(parser.cells),visual_browser_review_performed=False,
        verification_scope='Kiểm inventory/receipt/HTML parser/claim theo metadata đã nghiệm thu; không rerun model hoặc Test')
    (B/'QA01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
