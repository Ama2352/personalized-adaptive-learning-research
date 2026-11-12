"""Chuẩn bị tiếp tục một logical run từ receipt và archive đã xác minh."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def checkpoint_rank(name):
    patterns = ((r'epoch-(\d{3})',2),(r'train-epoch-(\d{3})',1))
    for pattern,stage in patterns:
        match = re.fullmatch(pattern,name)
        if match:
            return int(match[1]),stage,0,name
    match = re.fullmatch(r'.*batch-epoch-(\d+)-step-(\d+)-[0-9a-f]+',name)
    if match:
        return int(match[1]),0,int(match[2]),name
    raise ValueError('Unknown native checkpoint name')


def verified_stop_proof(path,native):
    if path is None:
        return False
    proof=json.loads(path.read_text())
    dispatch=json.loads((native/'dispatch.json').read_text())
    source=path.parent/proof['source_file']
    if (proof['status']!='STOP_INDEPENDENTLY_RECONCILED'
            or proof['app']['app_id']!=dispatch['app_id']
            or proof['app']['state']!='stopped' or str(proof['app']['tasks'])!='0'
            or sha(source)!=proof['source_sha256']):
        raise ValueError('Independent stop proof must bind the previous owned App')
    row=next(item for item in json.loads(source.read_text()) if item['app_id']==dispatch['app_id'])
    if row!=proof['app']:
        raise ValueError('Stop proof differs from provider snapshot')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-execution',required=True)
    parser.add_argument('--execution',required=True)
    parser.add_argument('--previous-request',type=Path,required=True)
    parser.add_argument('--output-request',type=Path,required=True)
    parser.add_argument('--preemption-recovery',type=Path)
    parser.add_argument('--stop-proof',type=Path)
    args = parser.parse_args()
    for name in (args.previous_execution,args.execution):
        if not re.fullmatch(r'modal-junyi-main-selected-t4-20261112-\d{2}',name):
            raise ValueError('Owned main selected execution ID required')
    if args.execution==args.previous_execution:
        raise ValueError('Fresh execution ID required')
    native = ROOT/'experiments/akt/results'/args.previous_execution
    independent_stop=verified_stop_proof(args.stop_proof,native)
    recovery = None
    if args.preemption_recovery is not None:
        recovery = json.loads(args.preemption_recovery.read_text())
        if (recovery['status']!='PREEMPTION_CHECKPOINT_RECOVERED_VERIFIED_NOT_FINAL'
                or not independent_stop):
            raise ValueError('Verified preemption checkpoint and independent stop proof required')
        checkpoint = ROOT/recovery['local_checkpoint']
        if sha(checkpoint)!=recovery['files']['state.pt']['sha256']:
            raise ValueError('Recovered preemption checkpoint changed')
        index_path=ROOT/recovery.get('checkpoint_index_path',
            str((BUNDLE/'preemption-checkpoint-index.json').relative_to(ROOT)))
        if not index_path.resolve().is_relative_to(BUNDLE.resolve()):
            raise ValueError('Owned checkpoint index evidence required')
        transfers = json.loads(index_path.read_text())
        if (recovery['latest'] not in transfers
                or transfers[recovery['latest']]['files']!=recovery['files']):
            raise ValueError('Recovery checkpoint evidence differs from its Volume index')
    else:
        receipt = json.loads((native/'receipt.json').read_text())
        guard = json.loads((native/'app-budget-guard.json').read_text())
        if (receipt['status']!='PARTIAL_SELECTED_ONLY_NOT_FINAL'
                or receipt.get('download_inventory_verified') is not True
                or not (guard.get('stop_acknowledged') is True or independent_stop)):
            raise ValueError('Verified partial execution and acknowledged stop required')
        archive = native/'artifacts.zip'
        if sha(archive)!=receipt['archive_sha256']:
            raise ValueError('Previous native archive changed')
        transfers = receipt['checkpoint_transfers']
    request = json.loads(args.previous_request.read_text(encoding='utf-8'))
    logical = request.get('logical_run_id',request['run_id'])
    latest = max(transfers,key=checkpoint_rank)
    if recovery is not None and latest!=recovery['latest']:
        raise ValueError('Forensic recovery evidence is not the latest indexed checkpoint')
    retained = sorted({latest}|{name for name in transfers if re.fullmatch(r'epoch-\d{3}',name)},key=checkpoint_rank)
    envelopes = [dict(name=name,files=transfers[name]['files']) for name in retained]
    output = ROOT/'artifacts/akt/modal'/args.execution
    output.mkdir(parents=True,exist_ok=False)
    control_zip = output/'resume-control.zip'
    control_pins = {}
    control_files = {}
    if recovery is None:
        with zipfile.ZipFile(archive) as saved:
            inventory = json.loads(saved.read('SHA256.json'))
            logical_complete=f'experiments/akt/results/{logical}/COMPLETE.json'
            if logical_complete in saved.namelist():
                raise ValueError('Completed logical run cannot be resumed')
            for filename in ('run-manifest.json','initial-backbone.json'):
                member = f'experiments/akt/results/{logical}/{filename}'
                raw = saved.read(member)
                if hashlib.sha256(raw).hexdigest()!=inventory[member]['sha256']:
                    raise ValueError('Logical run control file changed')
                control_files[filename]=raw
    else:
        control_files['run-manifest.json']=(json.dumps(recovery['identity'],indent=2)+'\n').encode()
    with zipfile.ZipFile(control_zip,'x',zipfile.ZIP_DEFLATED) as control:
        for filename,raw in control_files.items():
            member = f'experiments/akt/results/{logical}/{filename}'
            control.writestr(member,raw)
            control_pins[member]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        control.writestr('MANIFEST.json',json.dumps(dict(files=control_pins),indent=2))
    request.update(run_id=args.execution,logical_run_id=logical,
        resume_from_execution_id=args.previous_execution,resume_checkpoints=envelopes,
        resume_checkpoint_name=latest,resume_checkpoint_sha256=transfers[latest]['files']['state.pt']['sha256'],
        allocation_id=args.execution.replace('modal-',''),root_review_status='DRAFT_PREPARED_NOT_DISPATCHED')
    request['archives']['resume_control']=dict(path=control_zip.relative_to(ROOT).as_posix(),sha256=sha(control_zip))
    if recovery is not None:
        request['control_reconstruction']=dict(kind='RECONSTRUCTED_FROM_PINNED_SOURCE_AND_CHECKPOINT',
            initial_backbone_missing=True,checkpoint_sha256=recovery['files']['state.pt']['sha256'],
            recovery_evidence_sha256=sha(args.preemption_recovery),stop_proof_sha256=sha(args.stop_proof),
            historical_control_file_bytes_recovered=False)
    if args.output_request.exists() or not args.output_request.resolve().is_relative_to(BUNDLE.resolve()):
        raise ValueError('Exclusive owned resume request output required')
    args.output_request.write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='RESUME_PREPARED_NOT_DISPATCHED',latest=latest,retained=retained,
                         logical_run=logical,execution=args.execution)),flush=True)


if __name__=='__main__':
    main()
