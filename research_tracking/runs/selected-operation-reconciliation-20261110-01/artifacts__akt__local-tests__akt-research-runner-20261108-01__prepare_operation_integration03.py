"""Tái dùng lượt metadata02, bổ sung receipt và hash đầu ra thật, không chạy NN."""
from pathlib import Path

prep = Path(__file__).resolve().parent
source = (prep / 'check_selected_metadata02.py').read_text(encoding='utf-8-sig')
source = source.replace('selected-metadata-integration02', 'selected-operation-integration03')
source = source.replace('== 39', '== 43').replace('tests=39', 'tests=43').replace('PASS39', 'PASS43')
source = source.replace('validate_selected_metadata, DOCUMENT_ROLES, CLAIM_ARTIFACTS',
                        'validate_selected_metadata, validate_engineering_operation, DOCUMENT_ROLES, CLAIM_ARTIFACTS')
source = source.replace('1024 * 2**20, 1024, 1', '2048 * 2**20, 1024, 1')
anchor = 'summaries, pins = {}, {}'
assert source.count(anchor) == 1
source = source.replace(anchor, '''operations = {
    'A0': ('research_tracking/runs/akt-public-selected-resume-20261110-01/execution/graph29-a0-continuous01/outer-final.json',
           'research_tracking/runs/akt-public-selected-resume-20261110-01/execution/graph29-a0-continuous01-owned/receipt.json',
           'research_tracking/runs/akt-public-selected-resume-20261110-01/execution/graph29-a0-continuous01/result.json',
           'graph29_a0_continuous01_request.ROOT.json'),
    'A1_EXPERT': ('research_tracking/runs/a1-expert-selected-engineering-20261110-01/accepted__outer-final.json',
           'research_tracking/runs/a1-expert-selected-engineering-20261110-01/owned__receipt.json',
           'research_tracking/runs/a1-expert-selected-engineering-20261110-01/accepted__result.json',
           'a1_expert_engineering03_request.ROOT.json'),
    'SAKT': ('research_tracking/runs/sakt-selected-engineering-20261110-01/fit05__outer-final.json',
           'research_tracking/runs/sakt-selected-engineering-20261110-01/fit_owned05__receipt.json',
           'research_tracking/runs/sakt-selected-engineering-20261110-01/fit05__result.json',
           'sakt_selected_fit05_request.ROOT.json'),
    'GKT': ('research_tracking/runs/gkt-selected-engineering-20261110-01/gkt-selected-fit03__outer-final.json',
           'research_tracking/runs/gkt-selected-engineering-20261110-01/gkt-selected-fit03-owned__receipt.json',
           'research_tracking/runs/gkt-selected-engineering-20261110-01/gkt-selected-fit03__result.json',
           'gkt_selected_fit03_request.ROOT.json')}
summaries, pins, operation_pins = {}, {}, {}''')
anchor = "        summaries[candidate] = dict(full_targets=claim.full_targets, selected_epoch=claim.selected_epoch,"
assert source.count(anchor) == 1
source = source.replace(anchor, '''        outer_path, owned_path, worker_path, request_name = operations[candidate]
        receipt_refs = {key: ref(ROOT / path) for key, path in
                        (('outer', outer_path), ('owned', owned_path), ('worker', worker_path))}
        receipts = {key: reader.read_json(value) for key, value in receipt_refs.items()}
        outer, owned, worker = (receipts[key] for key in ('outer', 'owned', 'worker'))
        request_ref = ref(P / request_name)
        executable_worker_ref = ref(Path(owned['command'][2]))
        reader.verify_file(request_ref)
        reader.verify_file(executable_worker_ref)
        native_refs = {path: FileRef(path, record['sha256'], record['bytes'])
                       for path, record in worker['native_outputs'].items()}
        for pinned in native_refs.values():
            reader.verify_file(pinned)
        validate_engineering_operation(candidate_id=candidate, outer=outer, owned=owned, worker=worker,
            request_ref=request_ref, worker_ref=executable_worker_ref,
            expected_source_hashes=worker['source_before'], native_refs=native_refs,
            expected_input_hashes=worker.get('input_before'), expected_runtime_hashes=worker.get('runtime_before'))
        operation_pins[candidate] = dict(receipts={key: asdict(value) for key, value in receipt_refs.items()},
            request=asdict(request_ref), worker=asdict(executable_worker_ref),
            native_files=len(native_refs), native_bytes=sum(value.size_bytes for value in native_refs.values()),
            expected_source_pins_from_historical_receipt=True, full_file_admission=False)
''' + anchor)
source = source.replace('operation_receipts_reviewed=False, expected_claim_pins_independent=False,',
    'operation_receipts_reviewed=True, operation_pins=operation_pins, expected_claim_pins_independent=False,')
source = source.replace('ACCEPTED_PRODUCER_METADATA_REHEARSAL_NOT_OPERATION_ADMISSION',
    'ACCEPTED_FOUR_ENGINEERING_OPERATION_RECONCILIATIONS_NOT_MAIN_ADMISSION')
source = source.replace('four producer metadata rehearsals; source bytes checked, no operation admission.',
    'four engineering receipt reconciliations; native bytes checked, no main admission.')
(prep / 'check_selected_operations03.py').write_text(source, encoding='utf-8')
launcher = (prep / 'run_selected_metadata02.py').read_text(encoding='utf-8-sig')
launcher = launcher.replace('selected-metadata-dispatch02', 'selected-operation-dispatch03')
launcher = launcher.replace('check_selected_metadata02.py', 'check_selected_operations03.py')
(prep / 'run_selected_operations03.py').write_text(launcher, encoding='utf-8')
print('Prepared exact receipt integration using cached outputs, timeout45s.')
