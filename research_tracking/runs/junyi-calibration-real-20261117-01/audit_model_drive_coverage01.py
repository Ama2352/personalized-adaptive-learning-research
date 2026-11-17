"""Chỉ đọc metadata lưu trữ để định vị model/checkpoint trên Drive.

Không mở ZIP, checkpoint hoặc dataset, không gọi mạng/Modal.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RETENTION = ROOT/'research_tracking/runs/artifact-retention-audit-20261116-01'
OFFLOAD = ROOT/'experiments/akt/results/artifact-offload-20261116-01'
REFIT = ROOT/'research_tracking/runs/junyi-refit-pipeline-20261114-01'
PARENT = '1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7'
PINS = {}


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    PINS[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    return json.loads(raw)


def require(condition,message):
    if not condition:
        raise ValueError(message)


def enrich_owners():
    coverage = read(HERE/'MODEL_DRIVE_COVERAGE01.json')
    legacy = read(HERE/'MODEL_DRIVE_OWNERS01.json')
    history = read(HERE/'MODEL_DRIVE_HISTORY_OWNERS01.json')
    owners = {row['id']:row for document in (legacy,history) for row in document['files']}
    for row in coverage['models']:
        identifiers = ([part['file_id'] for part in row['parts']] if 'parts' in row else
            [row['primary_drive_url'].split('/d/')[1].split('/')[0]])
        evidence = [owners[file_id] for file_id in identifiers]
        require(all(item['status']=='DRIVE_METADATA_SHA_VERIFIED' for item in evidence),'Owner metadata unavailable')
        row['drive_owner_status'] = 'OWNED_BY_SANG' if all(item['owned_by_sang'] for item in evidence) else 'SHARED_FOLDER_OTHER_OWNER'
        row['drive_owners'] = sorted({email for item in evidence for email in item['owners']})
    for row in coverage['latest_checkpoints']:
        file_id = row['drive_url'].split('/d/')[1].split('/')[0]
        evidence = owners[file_id]
        require(evidence['status']=='DRIVE_METADATA_SHA_VERIFIED'
            and evidence['expected_sha256']==row['archive_sha256'],'History owner/archive pin mismatch')
        row['drive_owner_status'] = 'OWNED_BY_SANG' if evidence['owned_by_sang'] else 'OTHER_OWNER'
        row['drive_owners'] = evidence['owners']
    coverage['owner_metadata_pins'] = dict(PINS)
    coverage['authenticated_owner_check_account'] = legacy['authenticated_account']
    coverage['models_owned_by_sang'] = sum(row['drive_owner_status']=='OWNED_BY_SANG' for row in coverage['models'])
    coverage['models_shared_other_owner'] = sum(row['drive_owner_status']=='SHARED_FOLDER_OTHER_OWNER' for row in coverage['models'])
    coverage['checkpoint_entries_owned_by_sang'] = sum(row['drive_owner_status']=='OWNED_BY_SANG' for row in coverage['latest_checkpoints'])
    with (HERE/'MODEL_DRIVE_COVERAGE02.json').open('x',encoding='utf-8') as stream:
        json.dump(coverage,stream,ensure_ascii=False,indent=2)
    print(json.dumps({key:coverage[key] for key in ('models_owned_by_sang','models_shared_other_owner',
                                                  'checkpoint_entries_owned_by_sang')}))


def use_sang_copies():
    coverage=read(HERE/'MODEL_DRIVE_COVERAGE02.json')
    state=read(HERE/'MODEL_BACKUP_COPY_STATE01.json')
    verified=read(HERE/'MODEL_BACKUP_POSTCOPY_VERIFY01.json')
    require(state['status']=='COMPLETE_THIRTEEN_SERVER_COPIES_SHA_OWNER_VERIFIED'
        and verified['status']=='PASS_FRESH_SOURCE_AND_DESTINATION_POSTCOPY_METADATA'
        and len(verified['files'])==13,'Fresh copied backup acceptance required')
    copies={row['source_id']:row for row in state['copies']}
    checked={row['source_id']:row for row in verified['files']}
    for source_id,row in copies.items():
        require(checked[source_id]['destination_id']==row['destination_id']
            and checked[source_id]['sha256']==row['sha256'] and checked[source_id]['destination_owned_by_sang'],
            'Copied backup verification mapping changed')
    for archive in coverage['split_archives'].values():
        for part in archive['parts']:
            copy=copies[part['file_id']]
            require(copy['sha256']==part['sha256'] and copy['bytes']==part['bytes'],'Copied part pin mismatch')
            part.update(original_file_id=part['file_id'],file_id=copy['destination_id'],url=copy['destination_url'])
    for row in coverage['models']:
        if 'parts' in row:
            row['parts']=coverage['split_archives'][row['archive']]['parts']
            row['prior_backup_owners']=row['drive_owners']
            row['drive_owners']=['honguyenminhsang2005@gmail.com']
            row['drive_owner_status']='OWNED_BY_SANG'
            row['limit_vi']='Selected-fit, còn refit/calibration; backup mới do Sang sở hữu, nguồn cũ giữ nguyên.'
        else:
            row['alternate_archive_parts']=coverage['split_archives']['01_JUNYI_REFIT_A0_A3.zip']['parts']
    coverage.update(models_owned_by_sang=11,models_shared_other_owner=0,
        independent_backup_folder_url=state['folder_url'],independent_backup_folder_id=state['folder_id'],
        source_files_preserved=True,new_storage_evidence_pins=dict(PINS))
    with (HERE/'MODEL_DRIVE_COVERAGE03.json').open('x',encoding='utf-8') as stream:
        json.dump(coverage,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(models_owned_by_sang=11,checkpoint_entries_owned_by_sang=5,
        source_files_preserved=True,folder_url=state['folder_url'])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owners',action='store_true')
    parser.add_argument('--sang-copies',action='store_true')
    args = parser.parse_args()
    if args.sang_copies:
        use_sang_copies()
        return
    if args.owners:
        enrich_owners()
        return
    uploaded = read(RETENTION/'DRIVE_UPLOAD_RECEIPT01.json')
    packages = read(RETENTION/'PACKAGES.json')
    split = read(OFFLOAD/'drive-transfer-parts-20261116-01/DRIVE_PARTS_MANIFEST.json')
    split_verified = read(RETENTION/'DRIVE_PARTS_PREPARED.json')
    require(split_verified['manifest_sha256']==PINS[(OFFLOAD/'drive-transfer-parts-20261116-01/DRIVE_PARTS_MANIFEST.json').relative_to(ROOT).as_posix()]['sha256'], 'Split manifest pin changed')
    require(split_verified['status']=='PASS_SPLIT_AND_RECONSTRUCTION_HASH','Missing split reconstruction evidence')
    remote = {row['name']:row for row in uploaded['files']}
    archive_receipts = {}
    for archive in split['archives']:
        package = next(row for row in packages['packages'] if Path(row['path']).name==archive['name'])
        require(package['sha256']==archive['sha256'] and package['source_and_members_verified'], 'Archive package/member verification missing')
        parts=[]
        for part in archive['parts']:
            row=remote[part['name']]
            require(row['remote_sha256_verified'] and row['metadata_verified']
                and row['parent_id']==PARENT and row['sha256']==part['sha256'] and row['bytes']==part['bytes'],
                'Archive Drive part mismatch')
            parts.append(dict(name=part['name'],file_id=row['id'],url=row['url'],bytes=row['bytes'],sha256=row['sha256']))
        archive_receipts[archive['name']] = dict(archive_sha256=archive['sha256'],parts=parts,
            reconstruction='ordered parts locally concatenation-hash verified before upload; remote parts SHA verified')
    input_plan = read(ROOT/'research_tracking/runs/cloud-calibration-inputs-20261117-01/INPUT_PLAN04.json')
    input_receipt = read(ROOT/'research_tracking/runs/cloud-calibration-input-upload-20261117-01/STRICT_ACCEPTANCE.json')
    require(input_receipt['status']=='INPUT_ZIP_DRIVE_SHA256_VERIFIED'
        and input_receipt['account']=='honguyenminhsang2005@gmail.com'
        and input_receipt['input_plan_sha256']==PINS['research_tracking/runs/cloud-calibration-inputs-20261117-01/INPUT_PLAN04.json']['sha256'],
        'Current input ZIP/plan receipt mismatch')
    plan_files = {row['path']:row for row in input_plan['files']}
    refit_members = read(OFFLOAD/'01_JUNYI_REFIT_A0_A3.zip.manifest.json')['files']
    grade_members = read(OFFLOAD/'03_GRADE10_SELECTED_AND_LEGACY.zip.manifest.json')['files']
    protected = {row['path']:row for row in read(ROOT/'research_tracking/runs/history-cleanup-20261117-01/PROTECTED_FILES.json')}
    protected_acceptance = read(ROOT/'research_tracking/runs/history-cleanup-20261117-01/ACCEPTANCE.json')
    require(protected_acceptance['protected_files_sha256_verified']==44, 'Missing protected-file SHA acceptance')
    models=[]
    checkpoints=[]
    relocation=read(ROOT/'research_tracking/runs/history-cleanup-20261117-01/RELOCATION_MANIFEST.json')
    for variant in ('A0','A1','A2','A3'):
        export=ROOT/f'experiments/akt/results/model-export-{variant.lower()}-refit-20261114-01'
        index=read(export/'MODEL_INDEX.json')
        path=(export/index['checkpoint_file']).relative_to(ROOT).as_posix()
        require(index['epochs']==9 and index['phase']=='refit90','Unexpected completed refit model')
        for inventory in (plan_files,refit_members,protected):
            require(inventory[path]['sha256']==index['checkpoint_sha256'] and inventory[path]['bytes']==index['checkpoint_bytes'],
                    'Refit checkpoint member inventory mismatch')
        require((ROOT/path).stat().st_size==index['checkpoint_bytes'],'Refit file size changed')
        models.append(dict(model=variant,domain='Junyi',phase='refit90',epoch=9,local_source=path,
            bytes=index['checkpoint_bytes'],sha256=index['checkpoint_sha256'],status='ĐÃ CÓ DRIVE',
            primary_drive_url='https://drive.google.com/file/d/'+input_receipt['file_id']+'/view',
            archive_member=path,archive_sha256=input_receipt['sha256'],
            alternate_archive='01_JUNYI_REFIT_A0_A3.zip',
            member_pin_sources=['INPUT_PLAN04.json','01_JUNYI_REFIT_A0_A3.zip.manifest.json','MODEL_INDEX.json']))
        if variant=='A3':
            final=read(REFIT/'a3-final-acceptance01.json')
            operation=ROOT/final['operation']
            member_inventory=read(operation/'remote-inventory.json')
            complete=read(operation/'COMPLETE.json')
            checkpoint_state='model/Adam finite, RNG present per a3-final-acceptance01.json'
        else:
            copy=read(REFIT/f'{variant.lower()}-refit-canonical-copy-verified.json')
            operation=ROOT/copy['source'].split('/files/')[0]
            member_inventory=read(operation/'remote-inventory.json')
            complete=read(operation/'COMPLETE.json')
            checkpoint_state='Epoch9 state file identified by metadata; optimizer/RNG tensors not reopened in this audit'
        archive_path=(operation/'artifacts.zip').relative_to(ROOT).as_posix()
        stored=next(group for group in relocation['groups'] if archive_path in group['paths'])
        require(stored['sha256']==complete['archive_sha256'],'History archive lineage mismatch')
        member='outputs/'+Path(index['source_output']).name+'/checkpoints/epoch-009/state.pt'
        pin=member_inventory['files'][member]
        require(pin['sha256']==index['checkpoint_sha256'] and pin['bytes']==index['checkpoint_bytes'], 'Latest epoch checkpoint pin mismatch')
        checkpoints.append(dict(model=variant,epoch=9,kind='complete_epoch',status='ĐÃ CÓ DRIVE',
            local_source=index['source_output']+'/checkpoints/epoch-009/state.pt',member=member,
            bytes=pin['bytes'],sha256=pin['sha256'],drive_url=stored['remote_url'],
            archive_sha256=stored['sha256'],optimizer_rng_verification=checkpoint_state,
            member_inventory=(operation/'remote-inventory.json').relative_to(ROOT).as_posix()))
        if variant=='A3':
            for key,pin in member_inventory['files'].items():
                if '/batch-recovery/' in key and 'epoch-9-step-2040-' in key:
                    checkpoints.append(dict(model='A3',epoch=9,optimizer_step=2040,kind='batch_recovery',
                        status='ĐÃ CÓ DRIVE',member=key,bytes=pin['bytes'],sha256=pin['sha256'],
                        drive_url=stored['remote_url'],archive_sha256=stored['sha256'],
                        optimizer_rng_verification='Member pinned; no tensor/recovery execution in this audit'))
    grade_index_path=ROOT/'experiments/akt/results/model-export-20261112-01/MODEL_INDEX.json'
    grade_index=read(grade_index_path)
    require(PINS[grade_index_path.relative_to(ROOT).as_posix()]['sha256']==grade_members[grade_index_path.relative_to(ROOT).as_posix()]['sha256'], 'Grade10 model index changed')
    for entry in grade_index['entries']:
        if entry['dataset']!='Grade10':
            continue
        path='experiments/akt/results/model-export-20261112-01/'+entry['destination']
        for inventory in (grade_members,protected):
            require(inventory[path]['sha256']==entry['sha256'] and inventory[path]['bytes']==entry['bytes'],'Grade10 member pin mismatch')
        require((ROOT/path).stat().st_size==entry['bytes'],'Grade10 file size changed')
        models.append(dict(model=entry['model'],domain='Grade10',phase=entry['phase'],epoch=entry['epoch'],
            local_source=path,bytes=entry['bytes'],sha256=entry['sha256'],status='ĐÃ CÓ DRIVE',
            archive_member=path,archive='03_GRADE10_SELECTED_AND_LEGACY.zip',
            archive_sha256=archive_receipts['03_GRADE10_SELECTED_AND_LEGACY.zip']['archive_sha256'],
            parts=archive_receipts['03_GRADE10_SELECTED_AND_LEGACY.zip']['parts'],
            limit_vi='Selected-fit, còn refit/calibration. Backup parts kiểm trước đây qua connector Dương vào đúng thư mục Sang.'))
    require(len(models)==11 and len(checkpoints)>=4,'Missing requested model/checkpoint coverage')
    output=dict(status='OFFLINE_METADATA_COVERAGE_RECONCILED',models=models,latest_checkpoints=checkpoints,
        split_archives=archive_receipts,source_pins=PINS,missing_drive_evidence=[],
        temporary_volume_only_in_scope=[],no_network_or_payload_read=True,
        limits_vi='Đối chiếu receipts/member inventories đã có và kích thước local, không tải/mở ZIP/PT hoặc '
        'nạp tensor. Không kiểm quyền truy cập Drive lại hôm nay. Chưa khẳng định mọi artifact của KLTN có Drive. '
        'Optimizer/RNG chỉ ghi mức bằng chứng riêng từng checkpoint, không suy deep tensor validation từ archive SHA.')
    with (HERE/'MODEL_DRIVE_COVERAGE01.json').open('x',encoding='utf-8') as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status=output['status'],models=len(models),latest_checkpoints=len(checkpoints),
        source_pins=len(PINS),missing_drive_evidence=0)))


if __name__=='__main__':
    main()
