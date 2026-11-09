"""Root dry/closure RQ2 learned19, không chạy lại world/model hoặc sửa raw."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/simulator/results/rq2-learned-graph-ability-20261109-01'
RUN = 'rq2-learned-graph-ability-20261109-01'
REPORT_SHA = '5d1b8592d2933a8e9afc100325d15f64e658dccac9eab4528b8f3d6437554687'
FILES = (
    ("worker.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/worker_rq2_learned_graph_ability01.py", "c1f1c4cd11cb16e236c4acc09725ab9a4b523135ec8a80a23f62c63f42831e94"),
    ("outer.py", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/run_rq2_learned_graph_ability01.py", "829437c4fc8268cc1750bb5be2fadff13cd6a06628ac6281b9a114b1f6c8fecd"),
    ("plan.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_learned_graph_ability01_plan.json", "26302c3b74649ae67340866e502c3853d373eb2f23b31f946bd567ce8a4ea7fd"),
    ("handoff.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_LEARNED_GRAPH_ABILITY_HANDOFF01.md", "a463de782a8e171be299e5a8283527cd44ae1057d270cf64084e1ab4117e47ee"),
    ("adversarial_review.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_LEARNED19_ADVERSARIAL_REVIEW01.md", "b7fd779416f5cdb6361b9a8574b88d79bf5a3ee2292ffaabf40c0da3bc9dd889"),
    ("root_dispatch_review.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_LEARNED19_ROOT_DISPATCH_REVIEW01.md", "4b4bbc1648623ff2ccb60f27f7209f5122c4bb0d3fefc29edb898ce8f1510088"),
    ("verify_results.ps1", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/verify_rq2_learned19_results01.ps1", "679c7b94d2d815eb2a17d86d2691043b7818fb65e965308884a386356fe08272"),
    ("independent_verification.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2_learned19_independent_verification01.json", "5d83fbad61f8f562d44ea0cd9d539684e71534f871ae7d0ecddfc36c4b199808"),
    ("prior_design_source_review.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_NEXT_EVIDENCE_SOURCE_REVIEW01.md", "4f547c0fd3ed9040e1b7b0e5b95e67da5c9e565f09f79a40adb2f49c94d57ead"),
    ("report_draft.md", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ2_LEARNED_GRAPH_ABILITY_RESULTS_DRAFT01.md", "5d1b8592d2933a8e9afc100325d15f64e658dccac9eab4528b8f3d6437554687"),
    ("native__admission.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/admission.json", "77db1e5bfc4304bdbbdc9416b895e7251eb5b43143114b539104b1afd6fdc0af"),
    ("native__cell_ledger.jsonl", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/cell_ledger.jsonl", "448776c1f05f0f7b603094675b1285f01d558fb203880d75c107f0a1843bd5e6"),
    ("native__conditional_lambda_contrasts.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/conditional_lambda_contrasts.json", "7939645bdb9a11cae01d254d4d1135d32ed1c9c218eb57ccd589b8221bdf4529"),
    ("native__dispatch.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/dispatch.json", "b0dd08ca56e7e0f31fd6888fd85c60fe0dfb497140f716877a6e5c1712de763e"),
    ("native__graph_source_contrasts.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/graph_source_contrasts.json", "643f202b212e62fd5dd295bce46cf44a761eab3bf892045dfd7772459a39504a"),
    ("native__high_controls.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/high_controls.json", "7c43072aaad8620e457219de2d1bd9b8cce617cf6a2ef90bdc0e4674ed3fa93f"),
    ("native__outcomes.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/outcomes.json", "b4563418607f9421e3d78b0e2a92ca28bd113b2afa5932c2ebe1aa164acbf3e7"),
    ("native__sentinel.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/sentinel.json", "16aba34daeeeff37403b542534676b729a92bb23ed5212a56f37f4b6ec6c50e0"),
    ("native__summary.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/summary.json", "af6f13e1afa7ff49858b5c018e992ad3c55602bb9cf381da394d0df6693220eb"),
    ("native__worker_run.json", ROOT/"experiments/simulator/results/rq2-learned-graph-ability-20261109-01/worker_run.json", "86974b5a1a4be7f7278a52d19a48677135f52429264ae6f7680b55be092ef540"),
    ("owned__GO.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-learned-graph-ability01-owned/GO.json", "8ff0b33dbbd89795a769ab501a11c6c30fb3a0971e8b6fb80e91ae748eba9d22"),
    ("owned__launch.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-learned-graph-ability01-owned/launch.json", "fc7290d0a5a4434083b9eae7953d3ca42bedcf042e34d4ebb9c6f0cd376d503b"),
    ("owned__ready.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-learned-graph-ability01-owned/ready.json", "054e830897cb2b0159d9c115dc11f9fd690ecdf2dd1f89068228db15cc8ecafd"),
    ("owned__receipt.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-learned-graph-ability01-owned/receipt.json", "4ad92bbff2df6d20d052275f126fe5c95fd9b00546dcb08bc2a18c4e14064ac8"),
    ("owned__stderr.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-learned-graph-ability01-owned/stderr.log", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("owned__stdout.log", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-learned-graph-ability01-owned/stdout.log", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("outer_final.json", ROOT/"artifacts/akt/local-tests/akt-research-runner-20261108-01/rq2-learned-graph-ability01-outer/final.json", "55be940503c2f09cc5b2baf4966a14c3ac039a6ed6918d130792ef9c57b8625b"),
)
REFERENCES = json.loads('{"scripts/research/windows_owned_worker.py":"0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1","src/knowledge_tracing/paper2_reference.py":"a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1","src/knowledge_tracing/gam_kt/simulator_mechanisms.py":"0cbfaf1b4735c188e04ed822197121118dcb65849b582af7413e157fd8d847fa","src/knowledge_tracing/gam_kt/simulator_pathways.py":"33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560","src/knowledge_tracing/experimental_controls.py":"099a02e9182d2357f0abcd1fc25816c7cc4b5425ec16106245a738d028631aa4","src/knowledge_tracing/akt/resources.py":"8c1e5970efb6aa9966a8f583e11172632426f3318d396c3e28d24b5d16b9c5ba","src/knowledge_tracing/__init__.py":"b84a9a4118d8b3476daae25a7981c97909524ace7ef93860bba7e6ec9e5bccb8","src/knowledge_tracing/akt/__init__.py":"03a3e9c1a2030b62b050c846fccb4349066ff247864484683f4acf8f5b725986","src/knowledge_tracing/gam_kt/__init__.py":"ce054ddb34933abbe8e156e2471fa3c504cf8e914ee82dd1a6aadcc0c22781c6","paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb":"353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f","paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/nodes.csv":"6db464d1fd3df5d4215d51c9f90dc0f7e24f252517252784c80bdb5fa6291650","paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/edges.csv":"ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb","paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/question_bank.csv":"fb5924ac0d19049ef1a5be23352592e30dfa3a4bde3e3fa07f10979fe0887e4d","paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/concept_to_chapter_map.csv":"aa99cffb251ce6757258d2e87fe707455bc74b6b3917ead1acf48c5e96ee0a17","artifacts/akt/local-tests/akt-research-runner-20261108-01/worker_rq2_learned_graph_ability01.py":"c1f1c4cd11cb16e236c4acc09725ab9a4b523135ec8a80a23f62c63f42831e94","artifacts/akt/local-tests/akt-research-runner-20261108-01/run_rq2_learned_graph_ability01.py":"829437c4fc8268cc1750bb5be2fadff13cd6a06628ac6281b9a114b1f6c8fecd","artifacts/akt/local-tests/akt-research-runner-20261108-01/method24_worker01.py":"ffb0c5307f5130164ac59f2e70959cf49505b3b59bc8e1afc29dca6f08126505","src/knowledge_tracing/edge_confidence_artifact.py":"ecc313c5a52c3fbb56e06e84bbd1c0808191b956a35bad1ffced200728e01746","src/knowledge_tracing/simulator_bridge.py":"b29105acd8de84b060ca27573bb7f7cf8e85599a4596e50e4a21ab63c82329d2","src/knowledge_tracing/shared_kt.py":"06922d5a6bfd6c806fd1abb61232f58a9ccd63826e30cefaf87ce3d3b36dffa8","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/manifest.json":"a910612fdb0b3c728a715a3f5250eb9736016fdd9e691bc8fd29cdc89a146f57","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/worker.py":"973a1973da7982aac9a44b4112786915a127447ac57c6bce07f51c06e381f119","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/plan.json":"fce29998c3a94c8c1a499fc43ff9e8aed77f68d62544de82bd4c3d9d66d15c72","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__shared_inputs.json":"11caeb463d6f7f4d686f3b969d43e15f971a27813179d333fc34e0a0ef22ab6e","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__outcomes.json":"76ddbdff68fb0ea592762c4feaaf4d39b112df35ac834fa576da7219c861d88d","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__observables.jsonl":"ca6ac8467c1e7735b08effc7d2ac93e1ac29da3fccb6baa5cafaa85092f0a0ae","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__oracle.jsonl":"cff2f744be6569e5dc80a690aa2fba69ab22548fe4f40b31970014b7c82bce02","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__oracle_endpoints.jsonl":"66cf25f9d8381b9d7e7af610ab1d6d89e0a61d48c732f8f8a759758e18ccc664","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__high_controls.json":"6f86868d07994271abb0b193fd414f3ab035f8a3ea63ea9fcb8dda9966aebd46","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__worker_run.json":"4b8f917da1df9c6fabc7d86b1d513d305ee6546be4be7255001d94109f3e8554","research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__admission.json":"6ecff33cf1f7905620271aa4a3101bcc855b279fa4eadcd3ae8ebb03ac77264a","artifacts/akt/local-tests/akt-research-runner-20261108-01/edge_artifact_native03_expectation.json":"fe968b7c87aa868e7d98fc29dcacc5fa6ddd5ec20fd21d517eda4ac75e35ce20","artifacts/simulator/corpora/grade10-development-lifecycle01-20261108/bank.json":"4ef02907ee9071ba2ed6b4bba4d4dab728d390e9bbff8218a4e39bbb32f48034","research_tracking/runs/edge-confidence-windows-bootstrap-20261108-01/manifest.json":"6e0cbe7129e52752fe2457ca44c04a9c942b6c2d660b0e10e164ec7c2088e270","research_tracking/runs/edge-confidence-artifact-integration-20261109-01/manifest.json":"f19c2243a663f07c48ee45f5d5b21e71cd2248c5ce1fe115e10b19d0d094bc9d","artifacts/akt/local-tests/akt-research-runner-20261108-01/edge-artifact-native03/summary.json":"4b6d91b0e0b4c9b9fdf82ace8efc1f5e2640992c9042e133847ef7449d588305","artifacts/akt/local-tests/akt-research-runner-20261108-01/edge-artifact-native03/result.json":"0b5de848f8f50b214cf5038641d2d71c9c5b21ba96c3409bcdbe3dfcf21089f6",".venv/Lib/site-packages/joblib-1.6.0.dist-info/METADATA":"c5fd6509906c5795fd6724d97bc1709d1f266b78aff92c0156d6cf5ad7c045e3",".venv/Lib/site-packages/joblib-1.6.0.dist-info/RECORD":"8afc819ab0ca1981144bea4ac64ee3a4043f577f9fd3d01037909b3ea246898f",".venv/Lib/site-packages/joblib/__init__.py":"eafd927d03aad93ac1e7eb14d38307a0db0dca9754c4a19726be439209138ddf",".venv/Lib/site-packages/numpy-2.5.4.dist-info/METADATA":"e2b909d6a37d76c2bc130f528d7fed0c517322bce16dc7846b6a6df30e200403",".venv/Lib/site-packages/numpy-2.5.4.dist-info/RECORD":"93c39ea75948c53a86da219e67e4775db845e0d1f1678a40b44266b03335c605",".venv/Lib/site-packages/numpy/__init__.py":"a6958cb364663b7acce81ccfd58eeb65a2b34d5376157f924777b97211a73be4",".venv/Lib/site-packages/pandas-3.0.6.dist-info/METADATA":"9eb4d20fc21b7851d6f782bd5186ded152fce80a48ac93120bf88e03c89ebc39",".venv/Lib/site-packages/pandas-3.0.6.dist-info/RECORD":"3ab2a0afc28a48668e314ea5a61b29c1780cd5b81f6efb4e8b6d02d172b6431d",".venv/Lib/site-packages/pandas/__init__.py":"384f08537ab666fc8252604ad72d26499c5110cdab70e2257e715ed0113104a7",".venv/Lib/site-packages/psutil-7.2.2.dist-info/METADATA":"a263a40220d921d9cb963fc636d34f817aa2eb72c2696e3e3465d088cdb1976b",".venv/Lib/site-packages/psutil-7.2.2.dist-info/RECORD":"6dbb9a261c6a358d5d37f84ca6bd2ac4f10f600376c038538e2685a95d2cb2a3",".venv/Lib/site-packages/psutil/__init__.py":"7b6a0675824eb1fa2ff0cb1eb36e358dc454703e51dfa4e9a0e6ccd26a159f0c",".venv/Lib/site-packages/scikit_learn-1.9.1.dist-info/METADATA":"32e503c710a61e4e04be4edb450f9f8141233ac6af3f3db59a877667538fa4ec",".venv/Lib/site-packages/scikit_learn-1.9.1.dist-info/RECORD":"02979e0e85d8b021871c47e54d417d00a108c2d016bd440cb63e241c346b3c59",".venv/Lib/site-packages/scipy-1.18.1.dist-info/METADATA":"c8313d18ca0168ff291fe0a3b50532f3a18b14547695e9aa7ca1c1ce6eca92dc",".venv/Lib/site-packages/scipy-1.18.1.dist-info/RECORD":"d0350965cceed1dfc69c1261b8f87a02845bf01f1b55e18cf7d426b5e3588e03",".venv/Lib/site-packages/scipy/__init__.py":"a11ad8a1eaf423d32a0d3dd6c9be6c7be86068321f043dacd2d555a49418b92f",".venv/Lib/site-packages/sklearn/__init__.py":"4ca68db4b3be340b1ef586b6c6d1cbf394bf1e5c0b2a998f997f02800a50c2c9",".venv/Lib/site-packages/sklearn/linear_model/_logistic.py":"80fb5439089025c955f032464d5c9540c5e1f2c0f0d31f80c7d8417b0169806f",".venv/Lib/site-packages/threadpoolctl-3.7.0.dist-info/METADATA":"09b19e721560cd12246402d44e53c1ede5194b8398ef60822f02cab86ccf8d1f",".venv/Lib/site-packages/threadpoolctl-3.7.0.dist-info/RECORD":"04201bedd765fa1852bc41735c6764e362cc156e5fd0bb92ef9eb22d8403dd57",".venv/Lib/site-packages/threadpoolctl.py":"e5f119e394193e206655bec4b993ef0bb40b0fbb2f22c92bd5b2d70a622bb518",".venv/Scripts/python.exe":"935016795f3e6908e75acbc2040a01e2e4cdb494a57c42f63a0d6eedb2372256",".venv/pyvenv.cfg":"e6ce18340141206a9176f045f8dce3d0da8de284d916dccfa4279c445f87ea33","docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md":"c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6","requirements-akt.lock.txt":"3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/admission.json":"77db1e5bfc4304bdbbdc9416b895e7251eb5b43143114b539104b1afd6fdc0af","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/cell_ledger.jsonl":"448776c1f05f0f7b603094675b1285f01d558fb203880d75c107f0a1843bd5e6","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/conditional_lambda_contrasts.json":"7939645bdb9a11cae01d254d4d1135d32ed1c9c218eb57ccd589b8221bdf4529","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/dispatch.json":"b0dd08ca56e7e0f31fd6888fd85c60fe0dfb497140f716877a6e5c1712de763e","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/graph_source_contrasts.json":"643f202b212e62fd5dd295bce46cf44a761eab3bf892045dfd7772459a39504a","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/high_controls.json":"7c43072aaad8620e457219de2d1bd9b8cce617cf6a2ef90bdc0e4674ed3fa93f","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L01.json":"59860237c85af2c820e1d39dc2ae3a98646d6f3cb31704920288ba87837ecf79","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L02.json":"ae1ef524518c6af6bad9066c079cba08b03a3de0409b7dd01a1fd191934018e9","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L03.json":"238337d97588a8de6f310813f0775df5ec18caa6e079264e1231e9915ab9ae49","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L04.json":"3713d428945d2cd9d8655f8cada974b6290aee081e8ac832f1aa94f4e01092c6","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L05.json":"7e305bd5ca090d11c2140a0897d2395ec84b9805297a24e865bc0b8e505aa2a6","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L06.json":"4f3e28b48f7074d28c59f019a5489b3aa920b5f5869bc10026dd2f0c092682a0","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L07.json":"5e8a292f8c95f59bee68bc3e7b7759f653af00c4a69277582bbb328bfcc74a61","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L08.json":"e559594d5c455199465b1c9920c53f30be987c31111468c02d90cae8666e4f61","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L09.json":"23fee5492ad373347c65986e55e5c494da64b8901712db44c62da8783fec9b09","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L10.json":"af9af814202bbf8569ee5101f88d74a384c27418df615866e0212312e2a2d3d9","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L11.json":"40f534a3441a97d6baa3f4ecd17fd143f97821cc2680e99037d5ce3607924976","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L12.json":"a0bd15d3febdb73bad6581d3eb2326654c682ddd0b70af16c86bc0814a0a45f5","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L13.json":"edc7658c3ea16fa71e501d5ec7f4fe93f8e662669f2e430ada97db21151b47eb","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L14.json":"1af750d9da4d15c8696db554fde706140671fd959e2def6cffcf4691f75302c2","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L15.json":"41f38e9e4b6960be1d08d0a202096c9f79c7b766be63fdad0d275e181b3c0e08","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L16.json":"df07518b1ad551fbc2ac995cee7043c597783049ab8a155f287c3525a3d3fa41","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L17.json":"07fc21c7100d31f5644119ddc9814349fd9df48487b4def816a741b6a5b9de39","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-L18.json":"bca04b443a8aed9f964799694688e336ad2800346f7ede11617b782a595f41a4","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/initial-S01.json":"e9a2c9d181ba59902e51907372fb21679cf52ce998c5979bf8817ccdcba9cd75","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/observables.jsonl":"e8c3997cebfd1494273864cb8399e7361fd1eccca0d2f9ce911d2095a2a5b2ba","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/oracle_endpoints.jsonl":"424770c53a8911dbc3e2de515860380c3c4d79801bedec71683c86ca3501e35c","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/oracle.jsonl":"031bb1c9600a66b9fd99a2bace7a395acd5636f5cb5d8f4436037a72282aa131","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/outcomes.json":"b4563418607f9421e3d78b0e2a92ca28bd113b2afa5932c2ebe1aa164acbf3e7","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/sentinel.json":"16aba34daeeeff37403b542534676b729a92bb23ed5212a56f37f4b6ec6c50e0","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/summary.json":"af6f13e1afa7ff49858b5c018e992ad3c55602bb9cf381da394d0df6693220eb","experiments/simulator/results/rq2-learned-graph-ability-20261109-01/worker_run.json":"86974b5a1a4be7f7278a52d19a48677135f52429264ae6f7680b55be092ef540","src/knowledge_tracing/evidence.py":"414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49"}')
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inventory():
    selected = {alias: {'source': path.relative_to(ROOT).as_posix(),
                        'sha256': sha(path), 'bytes': path.stat().st_size}
                for alias, path, expected in FILES}
    require(len(selected) == 27, '27 selected copies required')
    for alias, path, expected in FILES:
        require(selected[alias]['sha256'] == expected, f'selected source drift {alias}')
    selected['archiver.py'] = {'source': Path(__file__).resolve().relative_to(ROOT).as_posix(),
                              'sha256': sha(Path(__file__)),
                              'bytes': Path(__file__).stat().st_size}
    for name, expected in REFERENCES.items():
        require(sha(ROOT / name) == expected, f'reference drift {name}')
    return selected


def validate():
    selected = inventory()
    outer = read(PREP / 'rq2-learned-graph-ability01-outer/final.json')
    require(outer['status'] == 'ACCEPTED19_FINITE_LEARNED_GRAPH_SOURCE_EXTENSION', 'outer status')
    require(outer['elapsed_seconds'] < 60 and outer['automatic_retry'] is False, 'outer budget/retry')
    owned = outer['owned_receipt']
    require(owned['accepted'] is True and owned['returncode'] == 0
            and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup'] == 0
            and owned['popen_handle_closed'] is True
            and owned['actual_worker_in_job_before_GO'] is True
            and not owned['errors'] and not owned['cleanup_errors'], 'owned cleanup')
    worker = read(NATIVE / 'worker_run.json')
    counts = {'environment_constructor': 19, 'policy_builder': 19, 'snapshot': 19,
              'interact': 2280, 'oracle_probability_probe': 2280, 'oracle_theta_probe': 2280,
              'predict': 2280, 'select': 2280, 'update': 2280}
    require(worker['status'] == 'COMPLETE19_PENDING_OUTER'
            and worker['direct_attempts'] == worker['direct_returns'] == counts, 'actual call counts')
    require(worker['completed_cells'] == 19 and worker['worker_seconds'] < 50
            and worker['monitor_stopped'] is True and not worker['monitor_errors'], 'worker completion')
    require(worker['actual_online_policy_update_returns'] == 2280
            and worker['new_graph_offline_neural_solver_fits'] == 0
            and worker['new_solver_calls'] == 0 and worker['nn_optimizer_calls'] == 0, 'update/fit scope')
    bindings = outer['source_input_before_sha256']
    require(len(bindings) == 63 and bindings == outer['source_input_after_sha256']
            == worker['source_input_before_sha256'] == worker['source_input_after_sha256'], '63 bindings')
    require(all(REFERENCES[name] == digest for name, digest in bindings.items()), 'source/reference bindings')
    resources = worker['resources']
    require(len(resources) == 563
            and max(row['family_rss_bytes'] for row in resources) <= 512 * 1024**2
            and min(row['available_bytes'] for row in resources) >= 1536 * 1024**2, 'resource bounds')
    summary = read(NATIVE / 'summary.json')
    require((summary['worlds'], summary['new_learned_cells'], summary['sentinel_duplicate'],
             summary['interactions'], summary['components'], summary['contrasts'])
            == (19, 18, 1, 2280, 18, 9), 'scientific population')
    require(summary['new_independent_seed_blocks'] == 0
            and summary['old_initial_policy_hash_logged'] is False
            and summary['confidence_probability_claim'] is False
            and summary['causal_human_ability_claim'] is False, 'scientific limits')
    sentinel = read(NATIVE / 'sentinel.json')
    require(sentinel['status'] == 'EXACT_120_ROWS_AND_ENDPOINT_MATCH'
            and sentinel['observable_rows'] == sentinel['oracle_rows'] == 120
            and sentinel['old_cell'] == 'c26', 'sentinel')
    high = read(NATIVE / 'high_controls.json')
    require(len(high) == 3 and {row['block'] for row in high} == {21000, 21001, 21002}
            and all(row['trace_exact'] is True and row['endpoint_exact'] is True for row in high), 'high controls')
    admission = read(NATIVE / 'admission.json')
    prior = read(PREP / 'edge-artifact-native03/summary.json')
    require(admission['learned_artifact_identity'] == prior['identity']
            and admission['confidence_used_as_GAM_weight'] is False, 'typed artifact provenance')
    proof = read(PREP / 'rq2_learned19_independent_verification01.json')
    require(proof['status'] == 'VERIFIED_CACHED19_Q18_K9_AND_TRAJECTORY_PAIRS_NO_MODEL_CALLS'
            and proof['outer_sha256'] == sha(PREP / 'rq2-learned-graph-ability01-outer/final.json')
            and proof['exact_q_components_and_binary64_subtractions'] == 18
            and proof['exact_k_binary64_subtractions'] == 9
            and proof['sentinel_raw_endpoint_exact'] is True, 'independent verification')
    native = proof['native_output_before_after']
    require(len(native) == 32 and {path.name for path in NATIVE.iterdir()} == set(native), '32 native files')
    for name, record in native.items():
        path = NATIVE / name
        require(path.stat().st_size == record['bytes'] and sha(path) == record['sha256'], f'native drift {name}')
    qrows = read(NATIVE / 'graph_source_contrasts.json')
    krows = read(NATIVE / 'conditional_lambda_contrasts.json')
    require(len(qrows) == 18 and len(krows) == 9, 'Q/K rows')
    qmap = {(row['block'], row['ability'], row['mechanism_strength']): row for row in qrows}
    require(len(qmap) == 18 and all(row['expert'] - row['learned'] == row['expert_minus_learned']
                                   for row in qrows), 'Q arithmetic')
    for row in krows:
        key = (row['block'], row['ability'])
        require(qmap[(*key, .55)]['expert_minus_learned'] - qmap[(*key, 0.)]['expert_minus_learned']
                == row['lambda_difference'], 'K arithmetic')
    trajectories = proof['trajectory_pairs']
    require(len(trajectories) == 18
            and sum(row['question_id_differences'] for row in trajectories) == 1409
            and all(row['ordinal_rows'] == 120 and row['question_id_differences'] > 0
                    and row['labels_equal_before_first_question_difference'] is True
                    and row['question_id_difference_fraction'] == row['question_id_differences'] / 120
                    for row in trajectories), 'trajectory description')
    return selected, native, prior['verified_artifacts_sha256']


NOTE = '''# RQ2 — nguồn đồ thị learned trong controlled ability world

19 world hoàn tất gồm18 learned và1 expert sentinel. Ba seedblocks được dùng lại,
new independent N bằng0. Q18/K9 giữ toàn bộ dấu và zero. Scope là native GAM,
không neural fit hoặc hoàn tất RQ2/RQ3. Có2280 adaptive policy updates thực tế.

Đọc report_draft.md, native__graph_source_contrasts.json,
native__conditional_lambda_contrasts.json và independent_verification.json.
19 initial snapshots cùng raw observables/oracle/endpoints giữ ở scientific output,
được dẫn bằng SHA/size trong reference_sources.json. Oracle chỉ là evaluator/world.

Old initial state có scope SOURCE_RECONSTRUCTED_INITIAL_STATE, không có raw old
initial-policy hash. Sentinel120rows và endpoint exact là điều kiện ghép. Learned
confidence không P(edge true), không được dùng làm GAM weights. Không causal/human,
CI/p-value, graph-quality ranking hoặc true-graph recovery claim.

verify_results.ps1 là mã kiểm metadata sau run, không phải preregistration.
Archiver chỉ đóng bằng chứng có sẵn, không chạy lại world/model.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--canonical-report', type=Path)
    args = parser.parse_args()
    require(Path(sys.executable).absolute() == ROOT / '.venv/Scripts/python.exe', 'repository .venv required')
    selected, native, provider = validate()
    expected = sorted([*selected, *GENERATED])
    require(len(expected) == 32 and len(set(expected)) == 32, '32 output aliases')
    destination = ROOT / 'research_tracking/runs' / RUN
    require(not destination.exists(), 'exclusive new bundle required')
    report = args.canonical_report
    if report is not None:
        report = report.resolve()
        require(report == ROOT / 'research_tracking/reports/rq2_learned_graph_source_ability_results_20261109.md'
                and sha(report) == REPORT_SHA, 'exact canonical report bytes required')
    dry = {'status': 'DRY_ONLY_NO_COPY', 'run': RUN, 'copies': len(selected),
           'generated': sorted(GENERATED), 'output_count_excluding_manifest': len(expected),
           'outputs': expected, 'selected': selected, 'reference_count': len(REFERENCES),
           'archiver_sha256': sha(Path(__file__)), 'report_sha256': REPORT_SHA}
    if not args.close:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    before_path = PREP / 'rq2_learned19_archive_copy_inventory_before01.json'
    before = json.dumps(dry, ensure_ascii=False, indent=2).encode('utf-8') + b'\n'
    with before_path.open('xb') as stream:
        stream.write(before)
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    paths = {ROOT / row['source'] for row in selected.values()}
    paths.update(ROOT / name for name in REFERENCES)
    paths.add(before_path)
    if report is not None:
        paths.add(report)
    with record_evidence_run(ROOT, RUN, sources=sorted(paths), note=NOTE,
            metadata={'kind': 'finite_paired_graph_source_research_diagnostic',
                      'worlds': 19, 'reused_seed_blocks': 3, 'new_independent_seed_blocks': 0,
                      'interactions': 2280, 'new_graph_offline_neural_solver_fits': 0,
                      'expected_output_count_excluding_manifest': 32,
                      'report_source_sha256': REPORT_SHA}) as directory:
        for alias, row in selected.items():
            source = ROOT / row['source']
            data = source.read_bytes()
            require(hashlib.sha256(data).hexdigest() == row['sha256'] and len(data) == row['bytes'], 'precopy drift')
            with (directory / alias).open('xb') as stream:
                stream.write(data)
            require(sha(directory / alias) == row['sha256'], f'copy mismatch {alias}')
        references = {'source_sha256': REFERENCES, 'native_sha256_and_bytes': native,
                      'historical_provider_verified_artifacts_sha256': provider,
                      'scope': 'Provider exports referenced from accepted typed consumer; not recopied or independently re-solved.'}
        (directory / 'reference_sources.json').write_bytes(json.dumps(references, ensure_ascii=False, indent=2).encode('utf-8') + b'\n')
        (directory / 'copy_inventory.json').write_bytes(before)
        require(inventory() == selected, 'postcopy source drift')
        require(sorted(path.name for path in directory.iterdir() if path.name != 'manifest.json') == expected, 'output membership')
    verified = verify_evidence_bundle(destination)
    require(verified['artifacts'] == 32, 'closed output count')
    print(json.dumps({'status': 'CLOSED_EXISTING_EVIDENCE_ONLY', 'verified': verified,
                      'manifest_sha256': sha(destination / 'manifest.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()