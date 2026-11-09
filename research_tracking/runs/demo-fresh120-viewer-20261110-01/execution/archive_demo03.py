"""Đóng pure/HTTP/UI evidence cho viewer fresh120, không đóng toàn demo nghiên cứu."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
BUNDLE=ROOT/'research_tracking/runs/demo-fresh120-viewer-20261110-01'
FILES=('src/research_demo/__main__.py','src/research_demo/evidence.py','src/research_demo/server.py',
       'src/research_demo/static/index.html','src/research_demo/static/demo.js','tests/demo/test_viewer.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


http=json.loads((HERE/'http02-receipt.json').read_bytes())
assert http['accepted'] and http['counts']==dict(tests=113,failures=0,errors=0,skipped=0)
assert http['source_before']==http['source_after']=={n:sha(ROOT/n) for n in FILES}
assert (HERE/'demo03_desktop01.png').is_file() and (HERE/'demo03_mobile01.png').is_file()
BUNDLE.mkdir(exist_ok=False)
files=[p for p in HERE.rglob('*') if p.is_file() and 'http02-temp' not in p.parts
       and '__pycache__' not in p.parts]
files += [ROOT/name for name in FILES]
write(BUNDLE/'inventory_before_copy.json',{p.relative_to(ROOT).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files})
for source in files:
    relative=source.relative_to(ROOT)
    if source.is_relative_to(HERE):
        relative=Path('execution')/source.relative_to(HERE)
    target=BUNDLE/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    assert sha(source)==sha(target)
write(BUNDLE/'visual_QA.json',dict(desktop_width=1280,mobile_width=390,document_mobile_width=375,
    high_condition=dict(block=21010,ability=1300,mechanism='0',Q_display='-0.111290',K_display='0.000000'),
    medium_condition=dict(block=21017,ability=1150,mechanism='0.55',Q_display='0.698315',K_display='0.079790'),
    error_panel_hidden=True,review='Root đã xem cả2ảnh, bảng không đè số hoặc tràn ngang. Đổi3controls đã thực thi JavaScript vàAPI thật.',
    cleanup='Ownedpage.close đã thực hiện, server29925 terminal sauCtrl-C.',
    scope='Stored-evidence viewer, không tạo model/world call hoặc mẫu mới.'))
(BUNDLE/'README.md').write_text('# Demo xem lại đối chứng fresh120\n\n'
    'Thêm endpoint cố định và bảng chọn block/khởi tạo/lambda từ JSON đã đóng. '
    'Catalog giữ9điều kiện main, GAMreplay cùng BKTthamchiếuJunyi được phân vai rõ. '
    'Pure39đạt dưới30s, fullHTTP113đạt11,60s trong60s. Counts39nằm trong113, khôngcộngthành152testunique. '
    'Root kiểmJavaScriptđổiđiềukiệnthật cùngảnhdesktop1280/mobile390, khôngoverflow. '
    'Giữảnhgốc,source6files,beforeinventory vàrawlogs. Root đãđóngtab/server. '
    'Đây là viewer kếtquảcũ. Luồngmodelsfitted/chọnbàicho learner mới vẫn còn, T21 vàRQchưahoàntất.\n',encoding='utf-8')
write(BUNDLE/'manifest.json',dict(kind='stored_research_evidence_demo_engineering',
    outputs_sha256={p.relative_to(BUNDLE).as_posix():sha(p) for p in BUNDLE.rglob('*') if p.is_file()}))
state_path=ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state=json.loads(state_path.read_bytes())
state['DEMO03_20261110']=dict(status='STORED_FRESH120_VIEWER_PURE_HTTP_UI_ACCEPTED',
    tests_full=113,pure_subset=39,bundle=BUNDLE.relative_to(ROOT).as_posix(),
    new_world_calls=0,NN_calls=0,full_research_demo_complete=False)
write(state_path,state)
task_path=ROOT/'docs/thesis_recovery/TASKS.json'
tasks=json.loads(task_path.read_bytes())
assert not any(t['id']=='DEMO03' for t in tasks['tasks'])
tasks['tasks'].append(dict(id='DEMO03',rq=['RQ1','RQ2'],workstream='research_demo',priority='P1',owner='Codex',
    dependencies=['RQDIAG29','DEMO02'],research_objective='Xem tương tác các đối chứng nguồn đồ thị đã đóng.',
    required_inputs='Fresh120manifest/acceptance và7JSON nhỏ được ghimSHA.',
    files_components=list(FILES),implementation_objective='Endpointallowlist/read-only vàsamepagepanel, catalogroleđúng.',
    acceptance_criteria='Đủ60choices, strictschema/tamper/query/Host/Origin vàoldHTTPregressions; visualdesktop/mobile.',
    verification_steps='Actualpure39/fullHTTP113/JScontrols+2screenshots; noNN/servercleanup.',
    required_artifacts=[BUNDLE.relative_to(ROOT).as_posix()],estimated_work='HTTPfull11,60s, effortchưatách.',
    compute_cost_category='local_CPU_no_cloud',authorization_requirements='Root đãduyệtgói demo read-only trongquyềnusergiao.',
    status='COMPLETED_VIEWER_ONLY_NOT_T21',blockers=[]))
write(task_path,tasks)
for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'):
    path=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'/name
    text=path.read_text(encoding='utf-8')
    marker='Các mốc này chưa là so sánh mô hình đã huấn luyện, chưa kiểm public producer resume hoặc CUDA.'
    addition=(' Phần xem lại minh chứng trong demo đã cho đổi khối mô phỏng, mức khởi tạo và cơ chế phạt để đọc số liệu tương ứng. '
        'Các mô hình đã huấn luyện và luồng chọn bài cho người học mới vẫn còn cần được nối.')
    assert text.count(marker)==1
    path.write_text(text.replace(marker,marker+addition),encoding='utf-8')
with (ROOT/'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a',encoding='utf-8') as stream:
    stream.write('\n\n## 10/11 — DEMO03 viewer đã qua HTTP và UI\n\n'
        'Source6files, pure39/fullHTTP113 làsubsetrelation. Root kiểmactualJS3controls, highQ−.111290/K0 '
        'vàmediumQ.698315/K.079790, ảnh1280/390 khôngoverflow. Tab/server đãđóng. '
        'Bundle giữbefore/source/logs/screenshots. KhôngnewN/modelcalls, T21vẫnpendingfittedrecommendation.\n')
print('DEMO03_BUNDLE_STATE_AND_TWO_REPORTS_UPDATED',len(files))
