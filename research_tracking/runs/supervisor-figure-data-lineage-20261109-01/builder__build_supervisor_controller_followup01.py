"""ROOT-only candidate builder after research bundle closure; no publish/execution of research."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
BASE='research_tracking/supervisor_reports/2026-11-09/01_tien_do/'
NEW='research_tracking/runs/rq1-fixed-controller-candidates-20261109-01/'
BASE_PINS={'BAO_CAO_NGHIEN_CUU.html':'105b58fe49039a1760de619c44427a6fc5cf84c87682ad1a2b91c6e4ed530fdd',
           'BAO_CAO.md':'e4032e6191160d675db9556b017a72cfeb4c79b184a66118e098d4b2c5f639ca'}
NEW_PINS={'summary.json':'b74ed4cddc318053ebf4219ba2fae4ce39080c4ebe93750a06d68aa3ae9aeb57',
          'validation.json':'dc71a69af1c703295a2db2791c3a78cde6c476b6165277916a21b43dafd861b9'}


def need(ok,message):
    if not ok:raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(relative):
    path=ROOT/relative;cursor=ROOT
    for part in path.relative_to(ROOT).parts:
        cursor/=part;need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'no source alias')
    need(path.is_file() and path.stat().st_size<=2*1024**2,'bounded frozen report input')
    return path.read_bytes()


def once(text,old,new):
    need(text.count(old)==1,'unique narrative anchor: '+old[:55])
    return text.replace(old,new,1)


def svgs(raw):
    return re.findall(rb'<svg\b.*?</svg>',raw,flags=re.DOTALL)


def figure(cells):
    expected={(False,False):1007,(False,True):17,(True,False):51,(True,True):5}
    need(cells==expected,'accepted B/CID cells')
    pieces=[]
    for b in (False,True):
        for a in (False,True):
            x,y=300+275*int(a),115+100*int(b)
            label=f'{cells[(b,a)]:,}'.replace(',','.')
            pieces.append(f'<rect x="{x}" y="{y}" width="255" height="85" rx="6" fill="{("#edf2f5" if not b else "#e3f0f1")}"/>'
                f'<text x="{x+127.5}" y="{y+53}" text-anchor="middle" font-size="32" font-weight="600">{label}</text>')
    image=('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 400" role="img" aria-labelledby="pool-key-title pool-key-desc">'
        '<title id="pool-key-title">Tập ứng viên cuối và khái niệm được chọn: hai đầu ra khác nhau</title>'
        '<desc id="pool-key-desc">1080cặp tình huống. Tập cuối giữ và khái niệm giữ1007; tập giữ nhưng khái niệm đổi17; tập đổi nhưng khái niệm giữ51; cả hai đổi5. Tập cuối tái dựng từ nguồn; không phễu nhân quả.</desc>'
        '<rect width="920" height="400" fill="white"/><g font-family="Segoe UI,Arial,sans-serif" fill="#17324d">'
        '<text x="30" y="35" font-size="21" font-weight="600">Sau lọc cân bằng, cùng tập chưa chắc cùng khái niệm thắng</text>'
        '<text x="427" y="85" text-anchor="middle" font-size="17">Khái niệm giữ nguyên</text>'
        '<text x="702" y="85" text-anchor="middle" font-size="17">Khái niệm thay đổi</text>'
        '<text x="30" y="155" font-size="18">Tập ứng viên cuối giữ nguyên</text>'
        '<text x="30" y="255" font-size="18">Tập ứng viên cuối thay đổi</text>'+''.join(pieces)+
        '<text x="30" y="345" font-size="17">Cùng 1.080 tình huống, không thêm mẫu độc lập.</text>'
        '<text x="30" y="378" font-size="16">Bốn ô mô tả lựa chọn thử trên trạng thái đã lưu, không phải lợi ích học tập.</text></g></svg>')
    ET.fromstring(image)
    return '<figure><div class="svg-frame">'+image+'</div><figcaption>Các tập ứng viên được tái dựng theo đúng bộ lọc của nguồn, chưa được ghi trực tiếp trong nhật ký. Khái niệm thắng khớp toàn bộ hai nhánh; đây là đề xuất thử, chưa là bài đã giao. Không đọc bảng như phễu nhân quả hoặc bằng chứng điểm thành thạo đã hiệu chuẩn.</figcaption></figure>'


def html(old,cells):
    old_svgs=svgs(old);need(len(old_svgs)==9,'exact published9 SVGs')
    text=old.decode('utf-8')
    text=once(text,'Đã xác định ngoại lệ đủ số lần luyện trong bộ điều khiển.',
        'Đã tái dựng các bước lọc và xếp hạng để phân biệt khác biệt bị bộ lọc giữ lại với trường hợp cùng khái niệm vẫn thắng. Ngoại lệ đủ số lần luyện trong bộ điều khiển cũng đã được xác định.')
    block=('<div class="measure"><h3>Đi thêm một bước: điều gì xảy ra sau tập cho phép?</h3>'
        '<p>Bảng trước giữ đúng những gì được ghi trực tiếp. Để giải thích quyết định, nhóm tái dựng các bước tiếp theo từ quy tắc nguồn và lịch sử câu hỏi chung: '
        'bỏ lặp nếu cần, cân bằng số lần luyện, rồi xếp hạng trong tập còn lại. Không chạy lại mô hình. '
        'Tập cho phép và khái niệm thắng khớp toàn bộ hai nhánh trên 1.080 tình huống; các tập trung gian được gọi rõ là kết quả tái dựng.</p>'
        '<p><strong>55 lần tập cho phép đổi nhưng đề xuất giữ nguyên có hai kiểu khác nhau:</strong> '
        '4 lần khác biệt không còn trong tập cuối sau cân bằng số lượt; 51 lần tập cuối vẫn khác nhau nhưng cùng một khái niệm đứng đầu. '
        'Ở chiều ngược lại, 17 lần đổi khái niệm có cùng tập cuối; khóa xếp hạng của mô hình giải thích đúng lựa chọn ở từng nhánh, với cùng bối cảnh chương và số lượt trước đó.</p></div>'+figure(cells)+
        '<div class="measure"><p>4 trường hợp cân bằng nằm trong hồ sơ PYH; 51 trường hợp cùng khái niệm thắng nằm trong một quỹ đạo PG. '
        '17 trường hợp đổi khái niệm trong cùng tập gồm 15 ở PG và 2 ở PY; các nhóm không đổi vẫn được giữ. '
        'Không suy từ các hồ sơ này thành quy luật về năng lực học sinh.</p>'
        '<p><strong>Đã giải thích được các bước dẫn đến lựa chọn khái niệm trong mẫu này; chưa giải thích được lợi ích học tập.</strong> '
        'Điểm dùng để xếp hạng do mô hình gốc tính, khác xác suất đúng của câu hỏi thực tế đang xét. Nhóm chưa kiểm tra độ khớp của điểm này với tỉ lệ trả lời đúng trên câu hỏi tham chiếu. '
        'Phép kiểm chưa giải thích vì sao điểm ấy thay đổi, chưa tách riêng từng cơ chế tác động của đồ thị và chưa khôi phục quy tắc chọn độ khó hay bài tập từ điểm này. '
        'Không gọi kết quả là tác động nhân quả chỉ do điểm số; số mẫu độc lập mới vẫn bằng 0.</p></div>')
    anchor='<div class="measure"><p>Các số đếm trên là những đầu ra được so riêng, không phải các tầng của một phễu nhân quả.'
    text=once(text,anchor,block+'\n'+anchor)
    raw=text.encode('utf-8');after=svgs(raw)
    need(len(after)==10 and [s for s in after if s in old_svgs]==old_svgs,'all9 oldSVG exact bytes/order unchanged')
    for s in after:ET.fromstring(s)
    progress_caption='Phân biệt phần đã làm với kết luận còn thiếu'.encode()
    for table in re.findall(rb'<table\b.*?</table>',old,flags=re.DOTALL):
        if progress_caption not in table:need(table in raw,'inherited numeric table bytes changed')
    need(len(re.findall(rb'<section id="chang-[1-4]"',raw))==4 and b'<script' not in raw.lower(),'same4stages/static standalone')
    return raw,old_svgs


def markdown(old):
    text=old.decode('utf-8')
    addition=('**Tái dựng các bước lọc giúp giải thích cụ thể hơn.** Trong 55 lần tập cho phép đổi nhưng đề xuất giữ nguyên, '
        '4 lần khác biệt bị loại khỏi tập cuối sau cân bằng số lượt; 51 lần tập cuối vẫn khác nhưng cùng khái niệm thắng. '
        '17 lần đổi khái niệm trong cùng tập cuối khớp khóa xếp hạng của nguồn. Đây là giải thích quyết định thử từ dữ liệu đã lưu, '
        'không phải các tập ứng viên ghi trực tiếp, thành thạo đã hiệu chuẩn hoặc lợi ích học tập; không thêm mẫu độc lập.\n\n')
    return once(text,'**Tiếp theo, nhóm kiểm điều kiện người học.**',addition+'**Tiếp theo, nhóm kiểm điều kiện người học.**').encode('utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-research-manifest-sha256',required=True)
    parser.add_argument('--output-name',default='supervisor-report-20261109-controller-candidate01')
    parser.add_argument('--provenance-name',default='supervisor_report_controller_followup01_provenance.json')
    args=parser.parse_args()
    need(re.fullmatch('[0-9a-f]{64}',args.expected_research_manifest_sha256),'ROOT exact closed manifest pin')
    for name in (args.output_name,args.provenance_name):
        need(name and len(name)<=100 and not any(c in name for c in '/\\:\t\r\n') and name not in ('.','..'),'direct prep basename')
    before={BASE+n:read(BASE+n) for n in BASE_PINS};before.update({NEW+n:read(NEW+n) for n in NEW_PINS})
    manifest_raw=read(NEW+'manifest.json');need(digest(manifest_raw)==args.expected_research_manifest_sha256,'reviewed closed research manifest')
    manifest=json.loads(manifest_raw)
    need(manifest['status']=='completed','bundle must close before candidate build')
    for name,pin in NEW_PINS.items():
        need(manifest['outputs_sha256'][name]==pin,'closed research output binding')
    need(all(digest(before[BASE+n])==h for n,h in BASE_PINS.items()) and all(digest(before[NEW+n])==h for n,h in NEW_PINS.items()),'frozen base/data source SHA')
    summary=json.loads(before[NEW+'summary.json']);validation=json.loads(before[NEW+'validation.json']);pooled=summary['groups'][0]
    need(validation['source_R_membership_exact']==validation['source_CID_exact']==2160 and validation['paired_snapshots']==1080
         and validation['new_independent_N']==validation['native_model_simulator_calls']==0 and len(summary['groups'])==16,'all-row no-new-N source acceptance')
    need(pooled['C_changes_B_same']==4 and pooled['B_changes_CID_same']==51
         and pooled['same_B_CID_changed_local_key_explanation']==17 and pooled['qid_or_difficulty_only_preview_changes']==0,'accepted mechanical cases')
    cells={(r['B_changed'],r['CID_changed']):r['count'] for r in pooled['B_CID_cells']}
    html_raw,old_svgs=html(before[BASE+'BAO_CAO_NGHIEN_CUU.html'],cells);md_raw=markdown(before[BASE+'BAO_CAO.md'])
    need(len(html_raw)<=128*1024 and len(md_raw)<=16*1024,'small2readerfiles')
    out=PREP/args.output_name;provenance_path=PREP/args.provenance_name
    need(not out.exists() and not provenance_path.exists(),'exclusive candidate only, never overwrite published09')
    source=Path(__file__).resolve();source_sha=digest(source.read_bytes());out.mkdir()
    for name,raw in (('BAO_CAO.md',md_raw),('BAO_CAO_NGHIEN_CUU.html',html_raw)):
        with (out/name).open('xb') as stream:stream.write(raw)
    need(all(read(n)==b for n,b in before.items()) and read(NEW+'manifest.json')==manifest_raw
         and digest(source.read_bytes())==source_sha,'frozen source/builder beforeafter')
    proof=dict(status='CANDIDATE_ONLY_ROOT_VISUAL_QA_BEFORE_PUBLISH',base_commit_reference='ab471ca',builder_sha256=source_sha,
        inputs_sha256={**{n:digest(b) for n,b in before.items()},NEW+'manifest.json':args.expected_research_manifest_sha256},
        inherited_svg_sha256=[digest(s) for s in old_svgs],inherited_svg_exact=9,total_svg_count=10,
        source_mapping=[dict(feature='B-by-CID2x2',path=NEW+'summary.json',pointer='/groups/0/B_CID_cells'),
            dict(feature='4balance/51commonwinner/17same-B-CIDchange',path=NEW+'summary.json',pointers=[
                '/groups/0/C_changes_B_same','/groups/0/B_changes_CID_same','/groups/0/same_B_CID_changed_local_key_explanation']),
            dict(feature='2160sourceR/CID andno independentN',path=NEW+'validation.json',pointers=[
                '/source_R_membership_exact','/source_CID_exact','/new_independent_N'])],
        outputs_sha256={n:digest((out/n).read_bytes()) for n in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html')},
        published_files_modified=False,research_or_tests_rerun=False,
        non_circular_inventory='Frozen base/closedresearch inputs only; candidate hashes are separate outputs.')
    with provenance_path.open('x',encoding='utf-8') as stream:
        json.dump(proof,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=proof['status'],candidate=out.relative_to(ROOT).as_posix(),provenance_sha256=digest(provenance_path.read_bytes()))))


if __name__=='__main__':main()
