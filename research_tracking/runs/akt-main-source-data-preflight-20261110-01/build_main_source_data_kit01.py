"""Đóng source/public corpus giữ provenance thật, không quyền training."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'main-source-data-kit01'
ZIP = ROOT / 'artifacts/akt/colab/akt-main-source-data-20261110-01.zip'
NOTEBOOK = ('paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/'
            'source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb')
CORPORA = ('grade10-development-lifecycle01-20261108',
           'grade10-main-lifecycle-engineering10x84-20261109-01')
PUBLIC = ('bank.json', 'corpus.json', 'DONE.json', 'plan.json', 'train.jsonl',
    'train.manifest.json', 'selection.jsonl', 'selection.manifest.json',
    'calibration.jsonl', 'calibration.manifest.json')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


started = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
assert not OUT.exists() and not ZIP.exists()
builder = ROOT / 'scripts/akt/build_colab_bundle.py'
spec = importlib.util.spec_from_file_location('source_bundle_definitions', builder)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
contents, transforms = module.bundle_contents()
original = (ROOT / NOTEBOOK).read_bytes()
notebook = json.loads(original)
assert all(not cell.get('outputs') for cell in notebook['cells'])
assert sha(contents[NOTEBOOK]) != sha(original), 'Record the actual default transform mismatch'
mismatch = dict(path=NOTEBOOK, original_sha256=sha(original),
    default_synthetic_copy_sha256=sha(contents[NOTEBOOK]), original_output_blocks=0,
    default_profile_transformation=transforms[NOTEBOOK],
    resolution='Preserve original bytes for this output-free source dependency in the new data package.')
contents[NOTEBOOK] = original
transforms.pop(NOTEBOOK)
for name in ('28_CUDA_EXECUTION_PROFILE_V1.md', '29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md',
             '30_SAKT_RESEARCH_NUMERICAL_RECIPE_V1.md'):
    relative = 'docs/thesis_recovery/' + name
    contents[relative] = (ROOT / relative).read_bytes()
corpus_pins = {}
for corpus_id in CORPORA:
    base = f'artifacts/simulator/corpora/{corpus_id}/'
    for name in PUBLIC:
        contents[base + name] = (ROOT / base / name).read_bytes()
    inventory = json.loads(contents[base + 'corpus.json'])['source_inventory']
    for name, digest in inventory.items():
        assert name in contents and sha(contents[name]) == digest, name
    corpus_pins[corpus_id] = dict(corpus_sha256=sha(contents[base + 'corpus.json']),
        done_sha256=sha(contents[base + 'DONE.json']))
assert all(not name.startswith(('dataset/', 'artifacts/bkt_baseline/')) for name in contents)
assert all('/oracle' not in name and '/authorizations/' not in name for name in contents)
assert all(not name.endswith(('.pt', '.pth', '.toml', '.pem')) for name in contents)
assert max(map(len, contents.values())) <= 2 * 1024**2
assert sum(map(len, contents.values())) <= 16 * 1024**2
manifest = dict(schema_version=3, scope='SOURCE_AND_PUBLIC_SYNTHETIC_DATA_PREFLIGHT_ONLY',
    neural_training_authorized=False, runtime_or_Linux_CUDA_verified=False,
    upstream_Git_and_runtime_Gates_included=False, Method24_large_artifact_included=False,
    source_notebook_bytes_preserved=NOTEBOOK, notebook_copy_transforms=transforms,
    corpora=corpus_pins, files={name: sha(raw) for name, raw in contents.items()})
OUT.mkdir()
write('input_inventory_before_package.json', manifest['files'])
write('default_profile_mismatch_and_resolution.json', mismatch)
ZIP.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(ZIP, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, raw in sorted(contents.items()):
        archive.writestr(name, raw)
    archive.writestr('MAIN_DATA_PACKAGE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
assert ZIP.stat().st_size <= 8 * 1024**2
stage = OUT / 'relocated'
stage.mkdir()
with zipfile.ZipFile(ZIP) as archive:
    assert len(archive.namelist()) == len(set(archive.namelist())) == len(contents) + 1
    for member in archive.infolist():
        name = member.filename
        assert '\\' not in name and not Path(name).is_absolute() and '..' not in Path(name).parts
        raw = archive.read(name)
        if name in contents:
            assert sha(raw) == manifest['files'][name]
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
child = r'''
import sys,json,hashlib
from pathlib import Path
stage=Path(sys.argv[1]);sys.path.insert(0,str(stage/'src'))
def audit(event,args):
    if event=='import' and str(args[0]).split('.')[0] in {'torch','modal','boto3','pyBKT'}:raise RuntimeError('No model/runtime allocation in relocated data check')
sys.addaudithook(audit)
from knowledge_tracing import simulator_corpus_reader as reader
assert reader.ROOT==stage
manifest=json.loads((stage/'MAIN_DATA_PACKAGE_MANIFEST.json').read_bytes());results={}
for corpus_id,pins in manifest['corpora'].items():
    corpus=reader.read_public_research_corpus(corpus_id,expected_corpus_sha256=pins['corpus_sha256'],
        expected_done_sha256=pins['done_sha256'],limits=reader.CorpusReadLimits(2*1024**2,4*1024**2,256*1024,48,210,12600,20.))
    results[corpus_id]={role:{'learners':len(corpus.role_data(role).trajectories),'targets':corpus.role_data(role).audit['audit']['targets']} for role in ('train','selection','calibration')}
assert 'torch' not in sys.modules
print(json.dumps({'accepted':True,'reader_origin':reader.__file__,'results':results,'scope':'Windows relocated reader only; no Linux/CUDA/runtime or training proof'}))
'''
process = subprocess.run([sys.executable, '-B', '-c', child, str(stage.resolve())], cwd=ROOT,
    capture_output=True, timeout=45)
for name, raw in [('stdout.log', process.stdout), ('stderr.log', process.stderr)]:
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
accepted = process.returncode == 0 and time.perf_counter() - started < 60
write('package_manifest.json', manifest)
write('result.json', dict(accepted=accepted, returncode=process.returncode,
    package_path=ZIP.relative_to(ROOT).as_posix(), package_sha256=sha(ZIP.read_bytes()),
    package_bytes=ZIP.stat().st_size, source_members=len(contents),
    original_notebook_sha256=sha(original), relocated_data_check=json.loads(process.stdout) if process.returncode == 0 else None,
    elapsed_seconds=time.perf_counter()-started, training_or_device_authority=False))
print(json.dumps(dict(accepted=accepted, returncode=process.returncode, zip_bytes=ZIP.stat().st_size)))
raise SystemExit(0 if accepted else 1)
