"""Đóng gói allowlist source và synthetic tests cho notebook Colab."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
RESEARCH_CONTRACT_FILES = (
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
    'docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md',
    'docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md',
    'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md',
    'docs/thesis_recovery/28_CUDA_EXECUTION_PROFILE_V1.md',
    'docs/thesis_recovery/29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md',
    'docs/thesis_recovery/30_SAKT_RESEARCH_NUMERICAL_RECIPE_V1.md',
    'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json',
)


def bundle_contents():
    paths = sorted((ROOT / 'src/knowledge_tracing').rglob('*.py'))
    paths += sorted((ROOT / 'tests/akt').glob('*.py'))
    paths += sorted((ROOT / 'tests/shared_kt').glob('*.py'))
    paths += sorted((ROOT / 'tests/gam_kt').glob('*.py'))
    paths += sorted((ROOT / 'scripts/akt').glob('*.py'))
    paths += sorted((ROOT / 'scripts/research').glob('*.py'))
    paths += [ROOT / 'experiments/akt/configs' / name for name in ('smoke.json', 'pilot.json', 'fold0.json')]
    paths += [ROOT/'requirements-akt.in', ROOT/'requirements-akt.lock.txt']
    # Fixed public contract dependencies read by graph/stage/driver source;
    # no docs glob, runtime credentials, authorization or execution grant.
    paths += [ROOT/name for name in RESEARCH_CONTRACT_FILES]
    paper = ROOT / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
    paths += [ROOT/'paper1/AdaptiveEngineSimulation_Enhanced.ipynb']
    paths += [paper/'source'/name for name in ('adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb',
                                             'junyi_cycle_corrected_ablation_confirmation.ipynb')]
    paths += [paper/'data/simulator_inputs'/name for name in
              ('nodes.csv','edges.csv','edges_baseline.csv','question_bank.csv','concept_to_chapter_map.csv')]
    contents, transforms = {}, {}
    for path in sorted(set(paths)):
        name = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        if path.suffix == '.ipynb':
            original_hash = hashlib.sha256(data).hexdigest()
            notebook = json.loads(data)
            notebook['metadata'] = {}
            for cell in notebook['cells']:
                cell['metadata'] = {}
                if cell['cell_type'] == 'code':
                    cell['outputs'] = []
                    cell['execution_count'] = None
            data = (json.dumps(notebook,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
            transforms[name] = {'original_sha256':original_hash,'transform':'strip notebook outputs/execution metadata in bundle copy'}
        contents[name] = data
    return contents, transforms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    allowed = (ROOT / 'artifacts/akt/colab').resolve()
    if not output.is_relative_to(allowed) or output.suffix != '.zip':
        parser.error('output must be a new .zip under artifacts/akt/colab')
    contents, transforms = bundle_contents()
    manifest = {'schema_version': 2, 'scope': 'source_and_bounded_test_fixtures',
                'notebook_copy_transforms': transforms,
                'windows_lock_role': 'hash fixture only; Colab uses its own runtime and project venv',
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
        archive.writestr('BUNDLE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(json.dumps({'bundle': str(output), 'files': len(contents), 'sha256': digest}))


if __name__ == '__main__':
    main()
