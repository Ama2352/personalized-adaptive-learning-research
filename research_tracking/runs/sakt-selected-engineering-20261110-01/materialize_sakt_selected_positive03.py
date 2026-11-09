"""Root-only materialize từ dry02 thật; import chỉ cung cấp decoder thuần metadata."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
DRY = PREP/'sakt-selected-positive-package02-owned/final.json'
DRY_SHA = '4ef52294b475c7fa0faf63a31dc13aad6e157ae32211ba724e9e027ac0814f87'
PROPOSAL = PREP/'sakt-selected-positive-package02/proposal.json'
PROPOSAL_SHA = '6d24c0f6c4365a5739d3006128c95ad076f841ecf77d50b5dbb36a7d9afa2fc9'
PACKET = PREP/'sakt_selected_positive02_packet.json'
PACKET_SHA = '862708f7c54964d61b93e2da215bbb59a4c0b5115a4677d2bfacbc1d91fbd6c4'
RUN_ID = 'sakt-selected-engineering10x84-20261110-01'
AUTH = ROOT/'experiments/sakt/authorizations'/(RUN_ID+'.json')
REQUEST = PREP/'sakt_selected_fit02_request.ROOT.json'
OUT = PREP/'sakt-selected-materialization03'
FIT_WORKER = PREP/'check_sakt_selected_fit02.py'
FIT_OUTER = PREP/'run_sakt_selected_fit02.py'
METADATA_HELPER = PREP/'prediction_mastery_trace_worker03.py'
METADATA_SHA = 'fc067d67ebc9018722aa66367fc186fe4a10e0f0b112475372f8024d4d74d631'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def valid_sha(value):
    need(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value), 'exact lowercase64hex SHA256 required')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path, cap=2**20):
    need(path.is_file() and path.stat().st_size <= cap, 'bounded exact metadata input')
    return json.loads(path.read_bytes())


def raw(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n').encode()


def publish(path, payload):
    need(len(payload) <= 2**20, 'bounded materialized metadata')
    with path.open('xb') as stream:
        need(stream.write(payload) == len(payload), 'complete new-file write')
        stream.flush(); os.fsync(stream.fileno())
    need(sha(path) == hashlib.sha256(payload).hexdigest(), 'published bytes readback')


def construct(proposal):
    """Khôi phục đúng typed wire; không đổi config hoặc cấp execution token."""
    from knowledge_tracing.sakt import research_execution as execution
    from knowledge_tracing.research_admission import MainSelectionContext
    valid_sha(proposal['selected_spec_sha256'])
    wire = dict(proposal['specification'])
    context = MainSelectionContext(**wire.pop('context'))
    recipe = dict(wire.pop('recipe')); recipe['betas'] = tuple(recipe['betas'])
    budget = execution.SAKTSelectedBudget(**wire.pop('budget'))
    wire['expected_sources'] = tuple(tuple(row) for row in wire['expected_sources'])
    spec = execution.SAKTSelectedExecutionSpec(context=context, recipe=execution.SAKTSelectedRecipe(**recipe), budget=budget, **wire)
    evidence_wire = proposal['evidence']
    components = tuple(execution.SAKTComponentAcceptance(row['kind'], **{
        key:execution.FilePin(**row[key]) for key in ('outer','child','owned')}) for row in evidence_wire['components'])
    evidence = execution.SAKTSelectedEvidence(**{key:execution.FilePin(**evidence_wire[key]) for key in ('runtime','gate_pointer','lock')},
        components=components, runtime_files=tuple(execution.FilePin(**pin) for pin in evidence_wire['runtime_files']))
    need(spec.run_id == RUN_ID and spec.identity == proposal['selected_spec_sha256']
         and execution.canonical(asdict(spec)) == proposal['specification'], 'exact actual dry typed specification')
    need(spec.output == ROOT/'experiments/sakt/results'/RUN_ID, 'single declared scientific output')
    return spec, evidence


def validate_dry():
    for digest in (DRY_SHA,PROPOSAL_SHA,PACKET_SHA,METADATA_SHA):valid_sha(digest)
    need(sha(DRY) == DRY_SHA and sha(PROPOSAL) == PROPOSAL_SHA and sha(PACKET) == PACKET_SHA, 'external accepted dry pins')
    dry, proposal, packet = read(DRY), read(PROPOSAL), read(PACKET)
    need(dry['status'] == 'ACCEPTED_SAKT_GENUINE_DRY_NOT_NN_AUTHORITY' and dry['errors'] == []
         and dry['owned_receipt']['accepted'] is True and dry['owned_receipt']['cleanup_accepted'] is True
         and dry['owned_receipt']['job_active_after_cleanup'] == 0 and dry['proposal_sha256'] == PROPOSAL_SHA
         and not (DRY.parent/'postwrite_rejection.json').exists(), 'genuine dry terminal/cleanup')
    need(proposal['status'] == 'GENUINE_SAKT_DRY_IDENTITY_NOT_EXECUTION_AUTHORITY'
         and proposal['explicit_root_review_and_materialization_required'] is True
         and proposal['requested_phases'] == ['select_train80','raw_selection10'], 'selected-only dry scope')
    for field in ('source_pins','input_pins','runtime_pins'):
        for name,digest in packet[field].items():
            valid_sha(digest)
            path = Path(name) if Path(name).is_absolute() else ROOT/name
            need(sha(path) == digest, 'unchanged dry source/input/runtime')
    return proposal, packet


def main():
    import argparse
    import threading
    import time
    start, wall = time.perf_counter(), time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--materialize', action='store_true', required=True)
    for name in ('self-sha256','fit-worker-sha256','fit-outer-sha256','approval-reference'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    for digest in (args.self_sha256,args.fit_worker_sha256,args.fit_outer_sha256):valid_sha(digest)
    sys.path[:0] = [str(ROOT/'src'),str(ROOT/'scripts/research')]
    from windows_owned_worker import entry
    entry()
    need(sha(Path(__file__)) == args.self_sha256 and sha(FIT_WORKER) == args.fit_worker_sha256
         and sha(FIT_OUTER) == args.fit_outer_sha256 and sha(METADATA_HELPER) == METADATA_SHA
         and 0 < len(args.approval_reference.strip()) <= 256, 'reviewed materializer/driver/reference')
    need(not OUT.exists() and not AUTH.exists() and not REQUEST.exists()
         and not (ROOT/'experiments/sakt/results'/RUN_ID).exists(), 'exclusive materialization and future fit')
    OUT.mkdir()
    blocked = {'torch','numpy','pandas','scipy','sklearn','modal','boto3'}
    need(not blocked.intersection(sys.modules),'fresh stdlib-only materialization')
    denied=[]; error=None; published=[]; after=None
    timer=threading.Timer(55.,lambda:os._exit(124));timer.daemon=True;timer.start()
    def check():
        need(max(time.perf_counter()-start,time.time()-wall)<55., 'one finite materialization deadline')
    allowed_files={AUTH,REQUEST}
    allowed_dirs={AUTH.parent,ROOT/'experiments/sakt/results'}
    def audit(kind, values):
        bad = kind == 'import' and str(values[0]).split('.')[0] in blocked
        bad = bad or kind == 'subprocess.Popen' or kind.startswith('socket.') or kind in ('os.system','os.link','os.symlink') or kind.startswith('os.spawn')
        if kind == 'open' and values and not isinstance(values[0],int):
            mode=values[1] or '';flags=values[2] if type(values[2]) is int else 0
            if any(c in mode for c in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR):
                path=Path(os.fsdecode(values[0])).absolute().resolve()
                bad=bad or (path not in allowed_files and not path.is_relative_to(OUT))
        if kind in ('os.mkdir','os.remove','os.rmdir','os.rename'):
            paths=values[:2] if kind=='os.rename' else values[:1]
            bad=bad or any(Path(v).absolute().resolve() not in allowed_dirs and not Path(v).absolute().resolve().is_relative_to(OUT) for v in paths)
            if kind!='os.mkdir': bad=True
        if bad:
            denied.append(kind);raise RuntimeError('materializer cannot execute NN/process/network or mutate other paths')
    sys.addaudithook(audit)
    try:
        check();proposal,packet=validate_dry();spec,evidence=construct(proposal)
        from knowledge_tracing.sakt import research_execution as execution
        actual=execution.prepare_sakt_selected_identity(spec,evidence)
        need(actual==proposal['actual_identity'] and not blocked.intersection(sys.modules),'actual unchanged identity, no NN')
        sources=dict(packet['source_pins'])
        for path in (Path(__file__).resolve(),PREP/'materialize_sakt_selected_positive02.py',FIT_WORKER,FIT_OUTER,METADATA_HELPER):
            sources[path.relative_to(ROOT).as_posix()]=sha(path)
        auth=dict(schema_version=1,scope=execution.SCOPE,decision='AUTHORIZE_BOUNDED_SAKT_MAIN_SELECTED_ONLY',
            run_id=RUN_ID,spec_sha256=spec.identity,recipe_sha256=execution.RECIPE_SHA256,identity=actual,
            caps=asdict(spec.budget),requested_phases=list(execution.PHASES),approval_reference=args.approval_reference)
        auth_raw=raw(auth)
        input_pins=dict(packet['input_pins'])
        for path in (DRY,PROPOSAL,PACKET):input_pins[path.relative_to(ROOT).as_posix()]=sha(path)
        request=dict(schema_version=1,kind='ROOT_REVIEWED_ACTUAL_SAKT_SELECTED_ENGINEERING_ONLY',
            proposal_sha256=PROPOSAL_SHA,dry_sha256=DRY_SHA,dry_packet_sha256=PACKET_SHA,
            specification=proposal['specification'],evidence=proposal['evidence'],selected_spec_sha256=spec.identity,
            authorization_file=AUTH.relative_to(ROOT).as_posix(),authorization_sha256=hashlib.sha256(auth_raw).hexdigest(),
            source_pins=sources,input_pins=input_pins,runtime_pins=packet['runtime_pins'],
            approval_reference=args.approval_reference,allocation=packet['future_NN_allocation'])
        request_raw=raw(request)
        need(len(auth_raw)<=2**20 and len(request_raw)<=2**20,'precomputed metadata byte caps')
        before=dict(authorization_existed=AUTH.exists(),request_existed=REQUEST.exists(),result_existed=spec.output.exists(),
            auth_parent_existed=AUTH.parent.exists(),result_parent_existed=spec.output.parent.exists(),source_pins=sources)
        publish(OUT/'before.json',raw(before))
        for directory in (AUTH.parent,spec.output.parent):
            need(directory.parent.is_dir() and directory.resolve()==directory.absolute()
                 and not directory.is_symlink() and not getattr(directory,'is_junction',lambda:False)(),'fixed physical new parent')
            if not directory.exists():directory.mkdir()
        check();publish(AUTH,auth_raw);published.append(AUTH.relative_to(ROOT).as_posix())
        publish(REQUEST,request_raw);published.append(REQUEST.relative_to(ROOT).as_posix())
        after=execution.prepare_sakt_selected_identity(spec,evidence)
        need(after==actual and all(sha(ROOT/n)==h for n,h in sources.items()),'identity and controller bytes after publication')
    except BaseException as caught:
        error=dict(type=type(caught).__name__,message=str(caught))
    finally:
        accepted=error is None and not denied and not blocked.intersection(sys.modules) and max(time.perf_counter()-start,time.time()-wall)<55.
        publish(OUT/'result.json',raw(dict(status='MATERIALIZED_SAKT_SELECTED_AUTH_REQUEST_NOT_EXECUTED' if accepted else 'FAILED_MATERIALIZATION_KEEP_PARTIAL',
            error=error,denied=denied,published=published,authorization_sha256=sha(AUTH) if AUTH.is_file() else None,
            request_sha256=sha(REQUEST) if REQUEST.is_file() else None,dry_sha256=DRY_SHA,proposal_sha256=PROPOSAL_SHA,
            actual_model_calls=0,nn_executed=False,automatic_retry=False,elapsed_seconds=max(time.perf_counter()-start,time.time()-wall))))
        if max(time.perf_counter()-start,time.time()-wall)>=55.:
            publish(OUT/'postwrite_rejection.json',raw(dict(reason='same materialization deadline after publication')));accepted=False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    main()
