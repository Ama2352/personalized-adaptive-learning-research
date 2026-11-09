"""Root dry/closure GKT data bridge, không rerun/import model hoặc sửa evidence cũ."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'gkt-research-data-engineering-20261109-01'
REPORT_SHA = '22e86e07e449b1eceaae85baa6073876ff0d096281fd15eda086a8e77b5b1d56'
FILES = (
    ("research_data.py", ROOT/"src/knowledge_tracing/gkt/research_data.py", "1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873"),
    ("test_research_data.py", ROOT/"tests/gkt/test_research_data.py", "e426e42e82c34319ed04214c2248656b08c94e60eaf52579188a22650de41b89"),
    ("gkt_init.py", ROOT/"src/knowledge_tracing/gkt/__init__.py", "80fd45e6176831f00be7496b1549d3a98485d6b1addd26113130e3c1fcd7fd3f"),
    ("test_candidate01.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/test_gkt_research_data_candidate01.py", "88cfd7f85ab90f2be08fb0eafcd2a92fceda03f80614a521f247c40125c89189"),
    ("test_candidate02.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/test_gkt_research_data_candidate02.py", "ec6b4248828ff0aaaf39a6a9fee1bb4c4ce8fe15e6894ffe66d221881b91d69a"),
    ("test_normal_pre_lazy17_SOURCE_ONLY.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt_research_data_canonical_test03.py", "86473903eb30dadd3c95830399fad3cacdd82ab6697dcc3666aa188507e23c19"),
    ("controller01.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gkt_research_data_candidate01.py", "abc1fd34d29cbf56482b30d072adce192fa20ba18ca45e541714298b9c0ab456"),
    ("packet01.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt_research_data_candidate01_packet.json", "b958b96441e2ae911a78c0c2e418fc0ec0131d0cf5fdf46e902e99354b19a5f6"),
    ("controller02.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gkt_research_data_candidate02.py", "c58019ee3e391beecbdc13de77da6868e3094703b626e869e616633f694ec5d9"),
    ("packet02.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt_research_data_candidate02_packet.json", "f963e4ac852834dd9046ba0be82410a79e3a06323d31157d220b41edd5cb645a"),
    ("controller03.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gkt_research_data_normal03.py", "57389885199cdb33cd440323d14799947feef3daaff5e2ec63a34bf8998a6efe"),
    ("packet03.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt_research_data_normal03_packet.json", "89ba3b5c4e61f6896061a30e842946ddb9f723a58ff4c7029777a0d2c3276d5d"),
    ("apply_helper03_SOURCE_ONLY.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/apply_gkt_research_data03.py", "d04071c61064f5b7974ed623247f43de0eabab3751058f5e1581fc740a15ea45"),
    ("apply_helper04.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/apply_gkt_research_data04.py", "885d752b5730eb47dfe844bc557da75f329a5def697db743e51a9bb8138ad740"),
    ("prepare_atomic_apply04.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/prepare_atomic_gkt_apply04.py", "a36fdcba242209692dd999fcfe55dd911172a512086ba1ab2bd644c491deaa39"),
    ("apply04__before_gkt_init.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-apply04/before_gkt_init.py", "90c9db6ea986694aa9e5b7a9aa6bf1c54f7afa9f8e449d3a6d30880d24c3a1aa"),
    ("apply04__inventory_before_copy.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-apply04/inventory_before_copy.json", "ea1cb1746e65c363c9c13d2c5072fc7ff7311474875ab7f7189f1f437d69714c"),
    ("apply04__receipt.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-apply04/receipt.json", "89198b6d2053ddc09fc1fa4cc1fd6ab6ab2a83165917f3bd75d8a571e15b9f05"),
    ("independent_review01.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/GKT_RESEARCH_DATA_INDEPENDENT_REVIEW01.md", "605fdc53c5fad0347436fd9f390b44ff032a7dc93875125dc007f5a0f9a6f513"),
    ("handoff01.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/GKT_RESEARCH_DATA_CANDIDATE_HANDOFF01.md", "6e3389fb75dc9e010662777c1d15f149f5cde1e7855633cca3bcfa6aca9f9bd7"),
    ("handoff02.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/GKT_RESEARCH_DATA_CANDIDATE_HANDOFF02.md", "420911b56bfa9b3cde2a5135f703f2c9055d3f5338e5c9ecdb5e12a841997414"),
    ("handoff03.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/GKT_RESEARCH_DATA_NORMAL_ENTRY_HANDOFF03.md", "d0041618ca4c853f31bed6a61a1fa5dc9fe7890d037473f996fe76fa67c287f5"),
    ("attempt01__result.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01/result.json", "957758df1172f08ccf44afd2edd9e8936cc13fdf63f6a83b86d07d0e15af8986"),
    ("attempt01__source_before.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01/source_before.json", "326305d0670938fee747fea3c4906ef62dceaa42a46e9cf6068ba32869d56a6c"),
    ("attempt01__unittest.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01/unittest.log", "500ea93fdc684ebcb0a815fbe76368838e87b59c1a552fe47c0d3888cd18bafb"),
    ("attempt01__owned__GO.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01-owned/GO.json", "1ff13a9b7dacd9b162394ffe9d416725f9e0d4d17ac052b8bc242f40fb0ee74f"),
    ("attempt01__owned__launch.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01-owned/launch.json", "8360985a4549d4bbc5f9c1b53372a20cb1b36e6ed4e28ac7e11c312ed868495e"),
    ("attempt01__owned__ready.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01-owned/ready.json", "918d39ead26833147f48933e418cc9df67abe55eba6131112f05b090ab61c097"),
    ("attempt01__owned__receipt.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01-owned/receipt.json", "2509c0a2cf708c55afb88c7d6930339ea434e30ed6df14c483200263f86442fd"),
    ("attempt01__owned__stderr.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01-owned/stderr.log", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("attempt01__owned__stdout.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01-owned/stdout.log", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("attempt01__outer_final.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01-outer/final.json", "edbbb77fac8cc1e04db80cf8ed1fb1dc29a2c6ee27cf1cb4f583c54140a5a09e"),
    ("attempt02__result.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02/result.json", "5be419689816d4b8622da7a87e1c357a97f8e243d63525b62ae9f6fc090606c6"),
    ("attempt02__source_before.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02/source_before.json", "82f55856d416e4aa7acb2f2c5cbf285409ac5bfcc3e6ba6517c7fa0ce1e37fa9"),
    ("attempt02__unittest.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02/unittest.log", "c3e6c24378bc4ffdf2292a49c0589da20cb84c3ad819ebc5f75a922b686abaf7"),
    ("attempt02__owned__GO.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02-owned/GO.json", "37c66b489bf853944ffad7120f2a1a87ad473079f77869f57784499521f60d45"),
    ("attempt02__owned__launch.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02-owned/launch.json", "33f0683e239e502dc18f62910ba34638349c275f011913fd6a85067d7c163384"),
    ("attempt02__owned__ready.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02-owned/ready.json", "5fadf5cbbd0077677a8f923c0a1d0478312c6945158d4efcc55fea1f5f16e77a"),
    ("attempt02__owned__receipt.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02-owned/receipt.json", "15858741220d22e042ed460309522dc8983f7a0a101811f767520329e8057607"),
    ("attempt02__owned__stderr.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02-owned/stderr.log", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("attempt02__owned__stdout.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02-owned/stdout.log", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("attempt02__outer_final.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02-outer/final.json", "42f75a5055fb5f4ee45f67f24a834db507956357a5eb4fb130807c5529ec9ccd"),
    ("attempt03__result.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03/result.json", "a4def4d2c8c5c20239858edb68e2457c90c81022c990ddb88b4397ee1dcb79bc"),
    ("attempt03__source_before.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03/source_before.json", "a4eef2170461a0b42c9b866b0aa9e3c6919db99d7ef582d1ec7f5fab5795239c"),
    ("attempt03__unittest.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03/unittest.log", "6ead578a2c12ce6fee0348dbf60a83467acbf41b8a95d59dd0f308ad1f1be527"),
    ("attempt03__owned__GO.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03-owned/GO.json", "6fcb3a1319df53a99964994c3b132cd75ca91e79fdf39b918af5430a928dee27"),
    ("attempt03__owned__launch.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03-owned/launch.json", "bab5b3c83e41138de9f65e27a500c0d29eee4bc43dec1f62b7c4295be401abab"),
    ("attempt03__owned__ready.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03-owned/ready.json", "78c057bf816b35ffa5eed4970111875ae3cdb9847e37c4521315c5108baa8231"),
    ("attempt03__owned__receipt.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03-owned/receipt.json", "aee21efe291b4750aacfa66a7666e0a39e39b6636fc0fefec078a54b27b6c001"),
    ("attempt03__owned__stderr.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03-owned/stderr.log", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("attempt03__owned__stdout.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03-owned/stdout.log", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("attempt03__outer_final.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-normal03-outer/final.json", "ad009df879870ffd0153ec916f2fb359328782decfbff77176a96e2ecb0983f4"),
    ("readiness_report.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/GKT_RESEARCH_DATA_READINESS_REPORT01.md", "22e86e07e449b1eceaae85baa6073876ff0d096281fd15eda086a8e77b5b1d56"),
)
REFERENCES = json.loads('{"src/knowledge_tracing/__init__.py":"b84a9a4118d8b3476daae25a7981c97909524ace7ef93860bba7e6ec9e5bccb8","src/knowledge_tracing/akt/__init__.py":"03a3e9c1a2030b62b050c846fccb4349066ff247864484683f4acf8f5b725986","src/knowledge_tracing/shared_kt.py":"06922d5a6bfd6c806fd1abb61232f58a9ccd63826e30cefaf87ce3d3b36dffa8","src/knowledge_tracing/simulator_bridge.py":"b29105acd8de84b060ca27573bb7f7cf8e85599a4596e50e4a21ab63c82329d2","src/knowledge_tracing/simulator_data.py":"79e28c1a8fc9b3bd5f3283868d7aba1a5bbc7c76764725a8b01098b2ae33cd9f","src/knowledge_tracing/simulator_research_data.py":"51eb7275a6a4a6b26b763a21a8fe6dc15b0973fc19b3c5557175eaa298db7e53","src/knowledge_tracing/simulator_corpus_reader.py":"e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90","src/knowledge_tracing/akt/research_simulator_data.py":"9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b","src/knowledge_tracing/akt/windows.py":"e8d00ea0f8b9d07bdc979575109c1f1fc22498d55410bff05a12559bebdb2068","src/knowledge_tracing/akt/types.py":"312e57e4fa507f12b449841969b3a9c2b35c592909178b3040102b254aa20304","src/knowledge_tracing/akt/encoding.py":"4b8288b9e50fd0763f9ee15db39775a8d3b7b42bb72540a644cbf8a177d351f8","src/knowledge_tracing/akt/provenance.py":"493d82af749baefcacec9ece0a7abe3297e64398eb4cd93c1d639ca41752cb59","src/knowledge_tracing/akt/config.py":"472b1b08d5270a1f2f07b214d5bf2658443265400828f6d66d1a802c1f92083d","artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt_research_data_candidate01.py":"1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873","artifacts/akt/local-tests/akt-research-runner-20261108-01/test_gkt_research_data_candidate01.py":"88cfd7f85ab90f2be08fb0eafcd2a92fceda03f80614a521f247c40125c89189",".venv/pyvenv.cfg":"e6ce18340141206a9176f045f8dce3d0da8de284d916dccfa4279c445f87ea33","artifacts/akt/local-tests/akt-research-runner-20261108-01/test_gkt_research_data_candidate02.py":"ec6b4248828ff0aaaf39a6a9fee1bb4c4ce8fe15e6894ffe66d221881b91d69a","artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gkt_research_data_candidate01.py":"abc1fd34d29cbf56482b30d072adce192fa20ba18ca45e541714298b9c0ab456","artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt_research_data_candidate01_packet.json":"b958b96441e2ae911a78c0c2e418fc0ec0131d0cf5fdf46e902e99354b19a5f6","artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01-outer/final.json":"edbbb77fac8cc1e04db80cf8ed1fb1dc29a2c6ee27cf1cb4f583c54140a5a09e","artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure01/result.json":"957758df1172f08ccf44afd2edd9e8936cc13fdf63f6a83b86d07d0e15af8986","artifacts/akt/local-tests/akt-research-runner-20261108-01/GKT_RESEARCH_DATA_INDEPENDENT_REVIEW01.md":"605fdc53c5fad0347436fd9f390b44ff032a7dc93875125dc007f5a0f9a6f513","src/knowledge_tracing/gkt/research_data.py":"1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873","tests/gkt/test_research_data.py":"e426e42e82c34319ed04214c2248656b08c94e60eaf52579188a22650de41b89","src/knowledge_tracing/gkt/__init__.py":"80fd45e6176831f00be7496b1549d3a98485d6b1addd26113130e3c1fcd7fd3f","src/knowledge_tracing/gkt/config.py":"8785a608e017ed4f6f77f8bd027ed3b3ee8a57d6e5b34bbb6d787acd9952c5d2","src/knowledge_tracing/gkt/core.py":"4663e25d158a08d344d2f5f85735d8db927f96e14199b5d16f40b8e32701b3e1","artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02-outer/final.json":"42f75a5055fb5f4ee45f67f24a834db507956357a5eb4fb130807c5529ec9ccd","artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt-research-data-candidate-pure02/result.json":"5be419689816d4b8622da7a87e1c357a97f8e243d63525b62ae9f6fc090606c6","artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gkt_research_data_candidate02.py":"c58019ee3e391beecbdc13de77da6868e3094703b626e869e616633f694ec5d9","artifacts/akt/local-tests/akt-research-runner-20261108-01/gkt_research_data_candidate02_packet.json":"f963e4ac852834dd9046ba0be82410a79e3a06323d31157d220b41edd5cb645a","scripts/research/windows_owned_worker.py":"0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1","src/knowledge_tracing/evidence.py":"414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49","docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md":"c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6","docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md":"96858efc6d99915390d841f45144d2e2be29e244e825b58cee993a148f05f3d1"}')
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(path):
    return json.loads(path.read_bytes())


def validate_runs():
    roots = ('gkt-research-data-candidate-pure01', 'gkt-research-data-candidate-pure02', 'gkt-research-data-normal03')
    expected_counts = ((17, 1), (17, 0), (20, 0))
    for number, (directory, (tests, errors)) in enumerate(zip(roots, expected_counts, strict=True), 1):
        outer = parse(PREP/(directory+'-outer/final.json'))
        worker = parse(PREP/(directory+'/result.json'))
        owned = parse(PREP/(directory+'-owned/receipt.json'))
        need(worker == outer['worker_result'] and owned == outer['owned_receipt'], 'Raw receipts must equal embedded originals')
        need(worker['counts'] == dict(tests=tests, failures=0, errors=errors, skipped=0,
            expected_failures=0, unexpected_successes=0), 'Honest actual test counts')
        need(worker['collected_ids'] == worker['started_ids'] == worker['completed_ids']
             and len(set(worker['collected_ids'])) == tests, 'Exact complete ID population')
        need(worker['source_before'] == worker['source_after'] == outer['source_before'] == outer['source_after']
             == parse(PREP/(directory+'/source_before.json')), 'Actual pre/post source inventories')
        need(owned['returncode'] == (1 if errors else 0) and owned['cleanup_accepted']
             and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed']
             and owned['actual_worker_in_job_before_GO'] and owned['GO_released'], 'Terminal native owned Job evidence')
        need(owned['accepted'] is (errors == 0) and outer['status'].startswith('REJECTED' if errors else 'ACCEPTED'),
             'Failed01 must remain rejected')
        need(0 <= outer['elapsed_seconds'] < outer['whole_cap_seconds'] == 30
             and 0 <= worker['elapsed_seconds'] < 20 and worker['monitor_stopped'] and worker['platform_restored']
             and not worker['denied'] and not worker['heavy_modules'] and worker['error'] is None,
             'Execution/source/data-only scope')
        resource = worker['resources']
        need(not resource['errors'] and resource['samples'] > 0
             and max(resource['peak_family_rss_bytes'], resource['peak_worker_rss_bytes']) <= 512*1024**2
             and resource['min_available_bytes'] >= 1536*1024**2
             and outer['prelaunch_available_bytes'] >= 2*1024**3, 'Actual resource floors unchanged')
        for suffix in ('', '-outer'):
            need(not (PREP/(directory+suffix)/'postwrite-rejection.json').exists(), 'No late-publication rejection')
        packet_name = ('gkt_research_data_candidate'+str(number).zfill(2) if number < 3
                       else 'gkt_research_data_normal03')+'_packet.json'
        need(sha(PREP/packet_name) == outer['packet_sha256'], 'Actual packet source')
    applied = parse(PREP/'gkt-research-data-apply04/receipt.json')
    expected = {path.relative_to(ROOT).as_posix(): pin for _, path, pin in FILES[:3]}
    need(applied['status'] == 'APPLIED_THREE_SOURCE_FILES_NOT_RUNTIME_TESTED'
         and applied['after_sha256'] == expected and applied['tests_executed'] is False,
         'Atomic apply is separate from later normal-entry acceptance')
    need(sha(PREP/'apply_gkt_research_data04.py') == applied['helper_sha256']
         and sha(PREP/'gkt-research-data-apply04/before_gkt_init.py') == applied['files']['src/knowledge_tracing/gkt/__init__.py']['prior_sha256'],
         'Actual atomic helper and preserved old initializer')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry', action='store_true')
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--canonical-report', action='store_true')
    args = parser.parse_args()
    need(not (args.dry and args.close), 'Choose dry or explicit closure')
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'Repository .venv only')
    destination = ROOT/'research_tracking/runs'/RUN
    need(not destination.exists(), 'Exclusive fresh bundle')
    copies = {alias: (path, pin) for alias, path, pin in FILES}
    need(len(copies) == 53, 'Exact selected53 input copies')
    copies['archiver.py'] = (Path(__file__).resolve(), sha(Path(__file__)))
    references = dict(REFERENCES)
    if args.canonical_report:
        references['research_tracking/reports/gkt_research_data_readiness_20261109.md'] = REPORT_SHA
    before = {}
    for alias, (path, pin) in copies.items():
        need(path.resolve() == path and path.is_relative_to(ROOT) and path.is_file() and sha(path) == pin,
             'Selected input SHA '+alias)
        before[alias] = dict(source=path.relative_to(ROOT).as_posix(), sha256=pin, bytes=path.stat().st_size)
    for relative, pin in references.items():
        need(sha(ROOT/relative) == pin, 'Reference source changed '+relative)
    validate_runs()
    outputs = sorted((*copies, *GENERATED))
    need(len(outputs) == len(set(outputs)) == 58, 'Exact58outputs, no case-count inflation')
    dry = dict(status='DRY_INPUTS_VERIFIED_NOT_CLOSED', run_id=RUN, copies=54, outputs_excluding_manifest=58,
        outputs=outputs, copy_inventory=before, reference_sources=references,
        actual_cases=dict(failed01='16PASS1ERROR', candidate02='17PASS', canonical03='20PASS'),
        model_fit=False, corpus_publication=False, tests_rerun=False)
    if not args.close:
        print(json.dumps(dry, ensure_ascii=False, indent=2)); return
    # Inventory đóng băng trước copy đầu tiên, không ghi đè lần closure cũ.
    with (PREP/'gkt_research_data_copy_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(dry, stream, ensure_ascii=False, indent=2); stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(dict.fromkeys([path for path, _ in copies.values()]+[ROOT/name for name in references]))
    note = ('# GKT research data bridge, engineering\n\n'
        'Giữ01 16PASS/1ERROR,02 candidate17PASS và03 canonical20PASS. '
        'Ba source canonical đã apply bằng helper04 nguyên tử; no-Torch normal data import, '
        '3lazy-export cases dùng explicit stub, không native kernel proof. '
        'Fixtures không corpus publication hoặc fitted GKT.58files là số outputs, không58testcases. '
        'Core/config/dependencies chỉ reference SHA, không copy runtime/corpus.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='GKT_RESEARCH_DATA_ENGINEERING_ONLY',
        canonical_methods=20, data_methods=17, lazy_package_methods=3,
        failure01_preserved=True, model_fit=False, new_research_efficacy=False), sources=sources, note=note) as directory:
        checked = {}
        for alias, (path, pin) in copies.items():
            raw = path.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == pin, 'Input drift before copy '+alias)
            with (directory/alias).open('xb') as stream:
                stream.write(raw)
            need(sha(directory/alias) == sha(path) == pin
                 and (directory/alias).stat().st_size == before[alias]['bytes'], 'After-copy SHA/size '+alias)
            checked[alias] = dict(before[alias], copied_sha256=pin, source_after_sha256=sha(path))
        for relative, pin in references.items():
            need(sha(ROOT/relative) == pin, 'Reference drift during closure '+relative)
        (directory/'copy_inventory.json').write_bytes((json.dumps(checked, ensure_ascii=False, indent=2)+'\n').encode())
        (directory/'reference_sources.json').write_bytes((json.dumps(references, indent=2)+'\n').encode())
        need(sorted(p.name for p in directory.iterdir() if p.name != 'manifest.json') == outputs, 'Exact selected output membership')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == 58, 'Closed58outputs verification')
    print(json.dumps(dict(verification=verified, manifest_sha256=sha(destination/'manifest.json'))))


if __name__ == '__main__':
    main()
