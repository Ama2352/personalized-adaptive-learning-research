"""Đóng operationalfailure fresh120, không chạy lại model/world hoặc sửa parent."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02'
RUN = 'rq2-fresh-graph-source-attempt02-20261109-01'
FILES = (
    ('worker02.py', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/worker_rq2_fresh_graph_source02.py', 'cdd471e4d960b4ad339320a5c94ab783f92c938a4e078feacdb3e3d943c6bac7'),
    ('outer02.py', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/run_rq2_fresh_graph_source02.py', 'ed8e958a930c419b0824162b8999749a9de9f20ade88500948041437b6aaad1a'),
    ('plan02.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_fresh_graph_source02_plan.json', 'caf38156db3e6d05b253750c123bf83fc7bf1a0449acc784042f83a301e5a13c'),
    ('worker01_source_only.py', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/worker_rq2_fresh_graph_source01.py', '6d706bca231a5f1d60feae8363d653b24621df2b8a0ca1ffa18059a523af2c88'),
    ('outer01_source_only.py', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/run_rq2_fresh_graph_source01.py', '7ee37784a7c32f8479c125147507510e2ce1999e44eaf4caa84708d34ef203f2'),
    ('plan01_source_only.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_fresh_graph_source01_plan.json', 'f47ec19b6a0072abbffd484f0dfde405800c1f536ef51c697a689b1da720cc66'),
    ('handoff01.md', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_FRESH_GRAPH_SOURCE_HANDOFF01.md', '88d712e04ab0024d33808f01ad04fe54d15297e687a6b22d8254cbabf97789ba'),
    ('handoff02.md', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_FRESH_GRAPH_SOURCE_HANDOFF02.md', '8a8865b0a1d351a0f0756936e7d53b9fd16657fa9da112af038fd098ae05d2bb'),
    ('design.md', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_FRESH_GRAPH_SOURCE_REPLICATION_DESIGN01.md', '47fd5733677d922ac555205e99df45dd5c52f56449f53f3e3cc8d924756ed223'),
    ('workledger.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_fresh_graph_source_replication_workledger01.json', '0a73b633ce8c85ffd391e57301c44d71baeeaa8083042914c3db5fe6d0e18fd3'),
    ('root_preflight01.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_fresh120_root_preflight01.json', '56c1d66b9571be30aa4bbea3bc85035ba30ae7c44ad04b6ae2f3f0c161755451'),
    ('root_preflight02.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_fresh120_root_preflight02.json', 'd29398d99e69ca6296cfc829c54dd3c847881ab4975ff1c386c41d9cc2923f50'),
    ('seed_audit02.txt', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_replication_seed_audit02.txt', 'c7001c9f2db6ce9a46b6f019c163341a98b7e359c438e5cf9e55f0c9ea47ea87'),
    ('verify_prefix.ps1', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/verify_rq2_fresh02_prefix01.ps1', '097c4ab0f64e228c1d8ee881e93eda4c2e1239d12eff416f76774e83ddee437c'),
    ('verify_prefix_counter_error01.ps1', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/verify_rq2_fresh02_prefix_counter_error01.ps1', 'b7ebd03740319bf6da8e2b89cc49c69bb38e13e0d827a963912eaabf85f3c748'),
    ('verifier_metadata_failure01.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_fresh02_prefix_verifier_metadata_failure01.json', '4dace3a2cfd9d1994981770b9023d1bb7f550014dfb146d1ed65b1dde6d954da'),
    ('prefix_verification.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_fresh02_prefix_verification01.json', '9551e0b85ca48cb5fe05236b6ee8bc75e0c471fc2e17d48c5f751a23ff845f95'),
    ('science_source_equivalence.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_fresh01_02_science_source_equivalence01.json', 'd142da3517cb26c48631c23e8143b1008947ecbc197e80f9071288539704b3fc'),
    ('continuation_proposal.md', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_FRESH120_CONTINUATION_PROPOSAL01.md', 'c98735b5048ac7428350d3806a47dc319c248d6c937b52ed37ebd276c6503847'),
    ('report_draft.md', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_FRESH120_ATTEMPT02_FAILURE_REPORT_DRAFT01.md', '189bceb1906c99d2d73db3c392c26ba2edcc93c5157bca57b50a011c00894d1c'),
    ('native__seed_reservation.json', 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02/seed_reservation.json', 'b14eb1dc91e959bf1cf89e95e89f6ab80c4f21a3be5a808b920689acf94b3464'),
    ('native__shared_inputs.json', 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02/shared_inputs.json', 'f14e91731535a351ca91d83d69ebe7aa287def900a71bb9de85d6fb9717ebc64'),
    ('native__admission.json', 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02/admission.json', '0716f3efb057e12b7ec2050fcb580568d268239f3831ad52f1572047da7470c7'),
    ('native__dispatch.json', 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02/dispatch.json', 'f29f2e0515da55e98210265aa3ebd0f5fc094a9c21ccdb05dad7a05545836f83'),
    ('native__worker_run.json', 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02/worker_run.json', '0d31ee04abbebb6dc69c8d66ac040f1f4c233047be7381567bb678a07b438b1e'),
    ('native__failure.log', 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02/failure.log', '7e2d71ef1ee93a139362df410e822cebe138caa3cf62c2cb591875a25b3c776a'),
    ('native__cell_ledger.jsonl', 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02/cell_ledger.jsonl', 'a3df0333b20a69ee697c9ed35829fe672f135caa85297b5cd0d7b323deb6d373'),
    ('outer_final.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-fresh-graph-source02-outer/final.json', 'fb26467c7c4f58b4a678b8df2e7b326c9cc8ac8e336e4962afebea28ecdc93e9'),
    ('owned__GO.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-fresh-graph-source02-owned/GO.json', 'ae02d1ee2211508770f127c799ddc774200497d880fafd1d32aee32e8b6e80d0'),
    ('owned__launch.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-fresh-graph-source02-owned/launch.json', '7747dcaad5d0257696460f719ae596d6f7b85faee42b74ae367541c524a5a91c'),
    ('owned__ready.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-fresh-graph-source02-owned/ready.json', '8184c887be54cbccae0555f5f0cb2c250cd552a28398d377bb9b16eaf37aedc5'),
    ('owned__receipt.json', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-fresh-graph-source02-owned/receipt.json', '05e9b323e55dd21c8053b1dbf77c20f6906d5902a5ff30439ae32272113715cc'),
    ('owned__stderr.log', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-fresh-graph-source02-owned/stderr.log', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    ('owned__stdout.log', 'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-fresh-graph-source02-owned/stdout.log', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
)
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json')


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def inventory():
    result = {}
    for alias, relative, expected in FILES:
        path = ROOT/relative
        need(sha(path) == expected, 'selected source drift '+alias)
        result[alias] = dict(source=relative, sha256=expected, bytes=path.stat().st_size)
    path = Path(__file__).resolve()
    result['archiver.py'] = dict(source=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)
    need(len(result) == 35, '35selectedcopies')
    return result


def validate():
    selected = inventory()
    outer = read(PREP/'rq2-fresh-graph-source02-outer/final.json')
    worker = read(NATIVE/'worker_run.json')
    proof = read(PREP/'rq2_fresh02_prefix_verification01.json')
    plan = read(PREP/'rq2_fresh_graph_source02_plan.json')
    need(outer['status'] == 'REJECTED_RETAIN_NO_RETRY' and worker['error']['message'] == 'Available1536MiB'
         and worker['error']['active_cell'] == 'F062' and worker['monitor_errors'] == ['ValueError: Available1536MiB'], 'RAM failure provenance')
    owned = outer['owned_receipt']
    need(owned['returncode'] == 1 and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup'] == 0
         and owned['popen_handle_closed'] is True and owned['GO_released'] is True
         and owned['actual_worker_in_job_before_GO'] is True and not owned['errors'], 'actual body/cleanup')
    need(worker['monitor_stopped'] is True and worker['job_query_handle_closed'] is True
         and worker['resource_scope'] == 'SAMPLED_EXACT_OWNED_JOB_RSS_AND_WORKER_HIGHWATER_NOT_OS_QUOTA', 'resource scope/handles')
    counts = dict(environment_constructor=62, policy_builder=62, select=7350, predict=7350, interact=7350,
                  update=7350, oracle_theta_probe=7350, oracle_probability_probe=7350, snapshot=61,
                  anchor_generation=10, uniform_array_generation=10)
    need(worker['direct_attempts'] == worker['direct_returns'] == counts
         and worker['completed_cells'] == 61 and worker['reserved_interact_attempts'] == 7440, 'actual prefix counters')
    need(proof['status'] == 'VERIFIED_RAM_STOP_PREFIX61_COMPLETE_F062_PARTIAL30_NOT_PRIMARY120'
         and proof['committed_cell_ids'] == [f'F{i:03}' for i in range(1, 62)]
         and proof['partial_cell'] == 'F062' and proof['partial_complete_responses'] == 30
         and (proof['raw_observables'], proof['raw_oracle'], proof['raw_endpoints'], proof['raw_ledger'], proof['initial_snapshots'])
             == (7350, 7350, 61, 123, 62)
         and len(proof['high_pairs']) == 20 and proof['shared_blocks'] == 10, 'verified partial population')
    references = {**plan['source_sha256'], **plan['inputs_sha256']}
    need(len(references) == 61 and worker['source_input_before_sha256'] == worker['source_input_after_sha256']
         == outer['source_input_before_sha256'] == outer['source_input_after_sha256'] == references, '61source/input bindings')
    native = proof['native_files_sha256_and_bytes']
    need(len(native) == 72 and {p.name for p in NATIVE.iterdir()} == set(native)
         and sum(row['bytes'] for row in native.values()) == 7954907, '72native inventory')
    for name, record in native.items():
        path = NATIVE/name
        need(sha(path) == record['sha256'] and path.stat().st_size == record['bytes'], 'native artifact drift '+name)
        references[path.relative_to(ROOT).as_posix()] = record['sha256']
    references['research_tracking/runs/owned-job-family-query-engineering-20261109-01/manifest.json'] = '6bbc8094c2849662668230e6283a627114c89eb49fe0f74cddcbfc644ee2f42d'
    references['research_tracking/runs/rq2-learned-graph-ability-20261109-01/manifest.json'] = '6d848a6bd8bbb4b26abd3f3caef4a8de2a1b80c9176cbaa4c3a8bce5164bf5a5'
    references['src/knowledge_tracing/evidence.py'] = '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
    for name, expected in references.items():
        need(sha(ROOT/name) == expected, 'reference drift '+name)
    return selected, references, native


NOTE = '''# Fresh120 attempt02 — RAM stop, chưa primary nghiệm thu

61complete +F062partial30,7350physical native policy.update calls, không0modelwork.
Chỉ operationalfailure/prefix preservation, không120worlds hoặc60Q/30K accepted.
Đọc report_draft.md, prefix_verification.json và continuation_proposal.md.
Continuation là đề nghị SOURCE-ONLY, chưa có dispatch/grant hoặc source implementation.

Native72file giữ nguyên tại scientificoutput experiments/simulator/results/
rq2-fresh-graph-source-robustness-20261109-02, SHA/size dẫn trong reference_sources.json.
Obs/oracle/endpoints và62initials không nhân đôi. Sharedinputs/seedfreeze copy nhỏ
được kiểm trước/sau. Rawverified20highpairs chỉ là controls của prefix40worlds.
Old19RSSscope worker+descendants khác02exactownedJob, không đo lại lịch sử.

Bảo toàn verifiermetadatafailure đầu (12counterkeys nhầm11), correctedverification
sau đó,0newmodel/world/RNG/Python calls. Không sửa nguồn hoặc bundle lịch sử.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--close', action='store_true')
    args = parser.parse_args()
    need(Path(sys.executable).absolute() == ROOT/'.venv/Scripts/python.exe', 'repository .venv required')
    selected, references, native = validate()
    names = sorted([*selected, *GENERATED])
    need(len(names) == 39 and len(set(names)) == 39, '39outputsexcludingmanifest')
    destination = ROOT/'research_tracking/runs'/RUN
    need(not destination.exists(), 'exclusive new evidence run')
    dry = dict(status='DRY_EXISTING_EVIDENCE_NO_COPY', run=RUN, output_count_excluding_manifest=39,
               output_names=names, selected=selected, reference_count=len(references),
               archiver_sha256=sha(Path(__file__)), parent_scope='RAM_STOP_NOT_PRIMARY120')
    if not args.close:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    before_path = PREP/'rq2_fresh120_attempt02_copy_inventory_before01.json'
    raw = json.dumps(dry, ensure_ascii=False, indent=2).encode()+b'\n'
    with before_path.open('xb') as stream:
        stream.write(raw)
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = {ROOT/row['source'] for row in selected.values()}
    sources.update(ROOT/name for name in references)
    sources.add(before_path)
    with record_evidence_run(ROOT, RUN, sources=sorted(sources), note=NOTE,
            metadata=dict(kind='operational_ram_stop_incomplete_research_prefix', completed_worlds=61,
                          partial_world='F062', partial_responses=30, actual_policy_updates=7350,
                          primary120_accepted=False, expected_output_count_excluding_manifest=39)) as directory:
        for alias, row in selected.items():
            data = (ROOT/row['source']).read_bytes()
            need(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], 'precopy drift')
            with (directory/alias).open('xb') as stream:
                stream.write(data)
            need(sha(directory/alias) == row['sha256'], 'copied SHA mismatch '+alias)
        (directory/'copy_inventory.json').write_bytes(raw)
        (directory/'reference_sources.json').write_bytes(json.dumps(dict(source_sha256=references,
            native_sha256_and_bytes=native, scope='Raw traces/initials kept native; no rerun/model read/deserialization'),
            ensure_ascii=False, indent=2).encode()+b'\n')
        need(inventory() == selected, 'source aftercopy drift')
        need(sorted(p.name for p in directory.iterdir() if p.name != 'manifest.json') == names, 'exact39output aliases')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == 39, 'closed39outputs')
    print(json.dumps(dict(status='CLOSED_EXISTING_RAM_FAILURE_EVIDENCE', verified=verified,
                         manifest_sha256=sha(destination/'manifest.json')), ensure_ascii=False))


if __name__ == '__main__':
    main()