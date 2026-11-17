"""Khôi phục source/input/model vào thư mục thử mới, kiểm độc lập layout và SHA."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
OUT=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages'
TARGET=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/cold-project'
sys.path.insert(0,str(B))
from khoi_phuc_ban_giao import extract,digest


def main():
    if TARGET.exists():
        assert (TARGET/'.cold-owned.json').is_file(),'Đích đã tồn tại ngoài lượt kiểm này.'
    else:
        TARGET.mkdir(parents=True)
        (TARGET/'.cold-owned.json').write_text(json.dumps(dict(owner='full-project-transfer-20261118-01',source=str(ROOT))),encoding='utf-8')
    start=time.monotonic();restored=0
    names=['01_SOURCE_VA_HO_SO_NGHIEN_CUU.zip']+[p.name for p in OUT.glob('03_*.zip')]
    records=[]
    for name in names:
        path=OUT/name
        assert path.is_file()
        restored+=extract(path,TARGET)
        records.append(dict(archive=name,sha256=digest(path)))
        print('COLD_RESTORED',name,flush=True)
    required=json.loads((ROOT/'research_tracking/runs/full-project-handoff-audit-20261118-01/REQUIRED_INPUTS02.json').read_text())
    for group in required['groups']:
        for row in group['files']:
            original=ROOT/row['path'];target=TARGET/row['path']
            if not target.exists():
                assert group['name']=='GRADE10_METHOD24_AND_CONDITIONS'
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
            assert target.stat().st_size==row['bytes'] and digest(target)==row['sha256']
    for name in ('01_JUNYI_REFIT_A0_A3.zip','02_JUNYI_SELECTED_A0_A3.zip','03_GRADE10_SELECTED_AND_LEGACY.zip'):
        archive=ROOT/'experiments/akt/results/artifact-offload-20261116-01'/name
        restored+=extract(archive,TARGET);records.append(dict(archive=name,sha256=digest(archive)))
        print('COLD_MODELS_RESTORED',name,flush=True)
    catalog=json.loads((ROOT/'research_tracking/runs/training-handoff-20261117-01/TRAINING_OUTPUTS_CATALOG01.json').read_text())
    models=[]
    for row in catalog['groups']['AKT_JUNYI']['selected']+catalog['groups']['AKT_JUNYI']['refits']:
        models.append(dict(path=row['checkpoint'].replace('\\','/'),sha256=row['sha256']))
    for row in catalog['groups']['AKT_GRADE10']['models']:
        models.append(dict(path=row['checkpoint'].replace('\\','/'),sha256=row['sha256']))
    assert len(models)==15
    for row in models:
        path=TARGET/row['path'];assert digest(path)==row['sha256']
        with zipfile.ZipFile(path) as checkpoint:
            assert checkpoint.testzip() is None
    upstream=TARGET/'artifacts/akt/dependencies/upstream'
    if not upstream.exists():
        upstream.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['git','-c','core.autocrlf=false','clone',str(OUT/'10_AKT_UPSTREAM.bundle'),str(upstream)],check=True)
        subprocess.run(['git','-C',str(upstream),'remote','set-url','origin','https://github.com/arghosh/AKT.git'],check=True)
    child=B/'cold_reader_child01.py'
    log=B/'cold_reader01.log'
    with log.open('w',encoding='utf-8') as stream:
        subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(child),str(TARGET)],cwd=TARGET,
                       stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=180,
                       env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    acceptance=dict(status='COLD_SOURCE_INPUT_AND_15_MODEL_LAYOUT_SHA_VERIFIED',
        restored_files=restored,required_input_files=790,primary_akt_models=15,
        archives=records,models=models,seconds=time.monotonic()-start,source_root=str(TARGET),
        reader_log='cold_reader01.log',new_training=False,
        limits=['Dùng dependency .venv hiện có để kiểm imports/readers trên source vừa giải nén.',
                'Chưa cài venv mới hoặc kiểm CUDA/training của máy người nhận.',
                '15checkpoint kiểm SHA và CRC container; không cập nhật trọng số hoặc đánh giá lại Test.'])
    (B/'COLD_RESTORE_ACCEPTANCE01.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('COLD_RESTORE_ACCEPTED',restored,'files',len(models),'models',flush=True)


if __name__=='__main__':
    main()
