"""ROOT-only request vận hành mới sau RAM reject0NN; không tạo hoặc đổi auth."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
OLD=PREP/'gkt_selected_fit02_request.ROOT.json'
NEW=PREP/'gkt_selected_fit03_request.ROOT.json'
OUT=PREP/'gkt-operational-retry03-preparation'
NATIVE=ROOT/'experiments/gkt/results/gkt-selected-engineering10x84-20261110-01'
PROOFS={
    'gkt-selected-fit02/result.json':'dca099af74822fb5eb404def9910eb9f2897ad97cba43d0ec201d55f7220572c',
    'gkt-selected-fit02/outer-final.json':'18f9950a9990a5cc17dddf1f3788ea1a223c987da0dbb65f599aeebd7b001cc7',
    'gkt-selected-fit02-owned/receipt.json':'42fec1720ee687ac61ba0df373b36eda0e86fbfdf41cc178b52d56da26333379',
}


def need(ok,message):
    if not ok:raise ValueError(message)


def main():
    started=time.perf_counter()
    parser=argparse.ArgumentParser()
    for name in ('self-sha256','worker-sha256','outer-sha256','retry-approval-reference'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts/research'),str(PREP)]
    from windows_owned_worker import entry,safe
    entry()
    from materialize_gkt_selected_positive03 import sha,read,raw,publish
    need(sha(Path(__file__))==args.self_sha256 and args.retry_approval_reference.strip(),'Root reviewed retry source/reference')
    need(sha(OLD)=='6c5dd05ab0c326c350393d92a5f46d09845ddcbcf7cd76ba86aca55a083b3c6a','actual unchanged request02')
    need(not NEW.exists() and not OUT.exists() and not NATIVE.exists(),'fresh request03 and no native output')
    for name,digest in PROOFS.items():need(sha(safe(PREP/name))==digest,'unchanged actual failure02')
    previous=read(PREP/'gkt-selected-fit02/result.json')
    outer=read(PREP/'gkt-selected-fit02/outer-final.json')
    owned=read(PREP/'gkt-selected-fit02-owned/receipt.json')
    observer=previous['observer']
    need(previous['status']=='REJECTED_GKT_KEEP_PARTIAL'
         and previous['error']==dict(type='ValueError',message='GKT preallocation RAM floor')
         and observer['installed_after_actual_lazy_tools'] is False
         and observer['counts']['lazy_tools']['started']==0
         and observer['training_targets']==observer['selection_targets']==0
         and observer['constructor_metadata']==observer['epochs']==[],'actual preallocation0NN failure only')
    need(outer['owned_receipt']==owned and owned['cleanup_accepted'] is True
         and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed'] is True
         and owned['cleanup_errors']==[],'actual failed attempt cleaned')
    request=read(OLD)
    auth=safe(ROOT/request['authorization_file'])
    need(sha(auth)==request['authorization_sha256']=='57e6d84ecec5dbf1b67d85478eba59dbfdc995dc7fb7b286b0e31d057105ca68','same actual GKT auth bytes')
    for key in ('source_pins','input_pins','runtime_pins'):
        for name,digest in request[key].items():
            path=Path(name) if Path(name).is_absolute() else safe(ROOT/name)
            need(sha(path)==digest,'unchanged prior source/input/runtime')
    sources=dict(request['source_pins'])
    for stem,digest in (('check_gkt_selected_fit',args.worker_sha256),('run_gkt_selected_fit',args.outer_sha256)):
        old_name=(PREP/(stem+'02.py')).relative_to(ROOT).as_posix()
        new_path=safe(PREP/(stem+'03.py'))
        need(sha(new_path)==digest,'new reviewed operational controller')
        del sources[old_name]
        sources[new_path.relative_to(ROOT).as_posix()]=digest
    sources[Path(__file__).resolve().relative_to(ROOT).as_posix()]=args.self_sha256
    request['source_pins']=sources
    request['operational_retry']=dict(prior_request_sha256=sha(OLD),prior_failure_sha256=PROOFS,
        prior_actual_nn_calls=0,authorization_unchanged=True,
        root_retry_approval_reference=args.retry_approval_reference,
        guard_floors_unchanged=True,automatic_retry=False)
    payload=raw(request)
    blocked={'torch','numpy','pandas','scipy','sklearn','modal','boto3'}
    need(not blocked.intersection(sys.modules),'stdlib-only request preparation')
    def audit(event,values):
        if event=='import' and str(values[0]).split('.')[0] in blocked:raise RuntimeError('no scientific imports')
        if event=='subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.link','os.symlink'):
            raise RuntimeError('no child/network/link')
        if event=='open' and values and not isinstance(values[0],int):
            mode=values[1] or '';flags=values[2] if type(values[2]) is int else 0
            if any(c in mode for c in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR):
                path=Path(os.fsdecode(values[0])).absolute().resolve()
                need(path==NEW or path.is_relative_to(OUT),'only request03 and own prep writes')
        if event in ('os.remove','os.rmdir','os.rename'):raise RuntimeError('no mutation existing files')
        if event=='os.mkdir':need(Path(values[0]).absolute().resolve()==OUT,'only own prep directory')
    sys.addaudithook(audit)
    OUT.mkdir()
    need(time.perf_counter()-started<25.,'bounded metadata preparation')
    publish(NEW,payload)
    need(sha(auth)==request['authorization_sha256'] and sha(OLD)=='6c5dd05ab0c326c350393d92a5f46d09845ddcbcf7cd76ba86aca55a083b3c6a'
         and not NATIVE.exists(),'unchanged auth/request02 and no native run')
    publish(OUT/'result.json',raw(dict(status='PREPARED_ROOT_REVIEWED_GKT_OPERATIONAL_REQUEST03_NOT_EXECUTED',
        request_sha256=sha(NEW),authorization_sha256=sha(auth),nn_calls=0,
        prior_failure_sha256=PROOFS,elapsed_seconds=time.perf_counter()-started)))


if __name__=='__main__':
    main()
