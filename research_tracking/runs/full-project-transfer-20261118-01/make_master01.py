"""Tạo chỉ mục một cửa và quy tắc khôi phục, bảo toàn manifest lịch sử."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def copied_mode(row):
    name=row['destination']['name'];role=row['role'];path=row['drive_path']
    if role=='COLD_HISTORY':
        if any(p in name for p in ('modal-main60-a0-selected-20261112-01__','modal-main60-a1-expert-selected-20261112-02__')):
            return dict(tier='ready',restore_mode='root',restore_order=30)
        return dict(tier='archive',restore_mode='none')
    if role=='TRAINING_OUTPUT':
        if name.startswith('SOURCE_PROTOCOLS'):
            return dict(tier='archive',restore_mode='subdir',restore_subdir='handoff-reference/previous-protocols')
        return dict(tier='ready',restore_mode='root',restore_order=20)
    if role=='MODEL_OR_AUDIT':
        return dict(tier='ready' if '.part' in name else 'archive',restore_mode='none')
    if role=='GRADE10_SUPPORT_OR_CONFIDENCE':
        return dict(tier='ready',restore_mode='root',restore_order=20)
    if role=='OUTER_EVALUATION':
        return dict(tier='ready',restore_mode='subdir',restore_order=40,
                    restore_subdir='experiments/akt/results/handoff-outer-20261117/'+Path(name).stem)
    if role=='FROZEN_SOURCE_AND_FIGURES':
        return dict(tier='ready',restore_mode='subdir',restore_order=40,restore_subdir='handoff-reference/frozen-outer-source-and-figures')
    if role=='CALIBRATION':
        relative=path.split('Junyi_calibration/',1)[1]
        if name.lower().endswith('.zip'):
            return dict(tier='ready',restore_mode='subdir',restore_order=40,
                restore_subdir='experiments/akt/results/handoff-calibration/'+str(Path(relative).with_suffix('')).replace('\\','/'))
        return dict(tier='ready',restore_mode='copy_file',restore_order=40,
                    restore_file='experiments/akt/results/handoff-calibration/'+relative)
    return dict(tier='archive',restore_mode='none')


def main():
    uploaded=json.loads((B/'UPLOADED_PACKAGES01.json').read_text(encoding='utf-8'))
    copied=json.loads((B/'COPIED_ASSETS01.json').read_text(encoding='utf-8'))
    assert uploaded['status']=='ALL_LOCAL_PACKAGES_DRIVE_SHA256_VERIFIED'
    assert copied['status']=='ALL_SERVER_COPIES_SOURCE_AND_DESTINATION_SHA256_VERIFIED'
    assets=[]
    supplement=json.loads((B/'SUPPLEMENT_UPLOAD01.json').read_text(encoding='utf-8'))
    uploaded['files'].append(supplement)
    uploaded['files'].append(json.loads((B/'FROZEN_INPUTS_UPLOAD01.json').read_text(encoding='utf-8')))
    uploaded['files'].append(json.loads((B/'PROJECT_GIT_UPLOAD01.json').read_text(encoding='utf-8')))
    uploaded['files'].append(json.loads((B/'TRACKED_UPLOAD01.json').read_text(encoding='utf-8')))
    for row in uploaded['files']:
        assets.append(dict(file_id=row['id'],name=row['name'],bytes=int(row['size']),sha256=row['sha256Checksum'],
            url=row['webViewLink'],drive_path=row['drive_path'],role=row['role'],tier='ready',
            restore_mode='none' if row['role'] in {'UPSTREAM_BUNDLE','PROJECT_GIT_BUNDLE'} else 'root',restore_order=0 if row['role']=='SOURCE' else 10))
    for row in copied['files']:
        meta=row['destination']
        assets.append(dict(file_id=meta['id'],name=meta['name'],bytes=int(meta['size']),sha256=meta['sha256Checksum'],
            url=meta['webViewLink'],drive_path=row['drive_path'],role=row['role'],source_file_id=row['source_id'],**copied_mode(row)))
    originals=json.loads((B/'ORIGINAL_RUNS_UPLOAD01.json').read_text(encoding='utf-8'))
    assert originals['status']=='ALL_SIX_ORIGINAL_RUN_ARCHIVES_VERIFIED'
    for row in originals['files']:
        assets.append(dict(file_id=row['id'],name=row['name'],bytes=int(row['size']),sha256=row['sha256Checksum'],
            url=row['webViewLink'],drive_path=row['drive_path'],role=row['role'],tier='ready',
            restore_mode='archive_and_root',restore_archive_file=row['original_archive'],restore_order=30))
    groups=[]
    for name in ('01_JUNYI_REFIT_A0_A3.zip','02_JUNYI_SELECTED_A0_A3.zip','03_GRADE10_SELECTED_AND_LEGACY.zip'):
        parts=sorted((a for a in assets if a['name'].startswith(name+'.part')),key=lambda a:a['name'])
        assert parts
        archive=ROOT/'experiments/akt/results/artifact-offload-20261116-01'/name
        groups.append(dict(archive_name=name,bytes=archive.stat().st_size,sha256=sha(archive),parts=[r['drive_path'] for r in parts]))
    grade=json.loads((ROOT/'research_tracking/runs/full-project-handoff-audit-20261118-01/GRADE10_SUPPORT01.json').read_text())
    models=[]
    catalog=json.loads((ROOT/'research_tracking/runs/training-handoff-20261117-01/TRAINING_OUTPUTS_CATALOG01.json').read_text())
    for row in catalog['groups']['AKT_JUNYI']['selected']+catalog['groups']['AKT_JUNYI']['refits']:
        models.append(dict(model=row['model'],domain='Junyi',path=row['checkpoint'].replace('\\','/'),sha256=row['sha256'],bytes=row['bytes']))
    for row in grade['models']:
        path=ROOT/row['compact_checkpoint']
        models.append(dict(model=row['model'],domain='Grade10',path=row['compact_checkpoint'],sha256=row['checkpoint_sha256'],bytes=path.stat().st_size))
    master=dict(schema='KLTN_COMPLETE_HANDOFF_V1',as_of='2026-11-18',master_folder=uploaded['master'],
        source_snapshot=json.loads((B/'PLAN01.json').read_text()),assets=assets,multipart_groups=groups,
        grade10_checkpoint_relocations=grade['models'],primary_akt_models=models,
        totals=dict(files=len(assets),bytes=sum(a['bytes'] for a in assets),ready_files=sum(a['tier']=='ready' for a in assets),
                    ready_bytes=sum(a['bytes'] for a in assets if a['tier']=='ready')),
        interpretation='Đủ bộ file theo allowlist và bản sao đã nghiệm thu; các model nghiên cứu/baseline còn thiếu vẫn cần thực hiện đúng protocol.',
        preserved_originals=True,
        exclusions=['Môi trường .venv/venv/WSL và thông tin đăng nhập cá nhân',
                    'Các bản staged và cache trùng đã có bộ chuẩn tương ứng',
                    'Các fixture kỹ thuật dựng lại được; evidence nguồn/log đã giữ trong snapshot hoặc archive lịch sử'])
    (B/'MANIFEST_BAN_GIAO.json').write_text(json.dumps(master,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('MASTER_MANIFEST_READY',master['totals'],flush=True)


if __name__=='__main__':
    main()
