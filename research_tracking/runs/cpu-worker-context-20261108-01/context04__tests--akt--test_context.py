"""Context sidecar: chỉ synthetic inputs, không sửa config/hash CPU lịch sử."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.context import load_worker_context, context_from_options
from knowledge_tracing.akt.authorization import config_hash
from knowledge_tracing.akt import runner, watchdog


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def context_fixture(tmp_path):
    root=tmp_path/'r';dataset=root/'artifacts/akt/synthetic/a'
    dataset.mkdir(parents=True)
    (dataset/'c').mkdir()
    # Payload bytes chỉ hash/role fixture, chưa phải Parquet để execute worker.
    for name,data in [('c/a.parquet',b'synthetic parquet placeholder'),('a.parquet',b'assignments placeholder'),
                      ('cm.json',b'{}'),('sm.json',b'{}'),
                      ('SYNTHETIC_ONLY.json',b'{"synthetic_only":true,"real_data_authorized":false}')]:
        (dataset/name).write_bytes(data)
    value={'schema_version':1,'scope':'synthetic-development-only',
        'runtime_report':'artifacts/akt/preflight/runtime.json','lock_file':'requirements-akt-linux.txt',
        'gate2_report':'artifacts/akt/preflight/gate2-current.json','dataset_root':'artifacts/akt/synthetic/a',
        'canonical':'artifacts/akt/synthetic/a/c','assignments':'artifacts/akt/synthetic/a/a.parquet',
        'canonical_manifest':'artifacts/akt/synthetic/a/cm.json','split_manifest':'artifacts/akt/synthetic/a/sm.json',
        'input_hashes':{p.relative_to(root).as_posix():sha(p) for p in dataset.rglob('*') if p.is_file()}}
    path=root/'artifacts/akt/context.json'
    def write():path.write_text(json.dumps(value),encoding='utf-8');return sha(path)
    write()
    return root,dataset,path,value,write


def test_context_loads_and_preserves_config_hash(context_fixture):
    root,dataset,path,value,write=context_fixture
    config=AKTConfig(project_root=root)
    before=config_hash(config)
    context=load_worker_context(path,expected_sha256=sha(path),project_root=root)
    assert context.data_paths.canonical==dataset/'c'
    assert context.identity['worker_context_scope']=='synthetic-development-only'
    assert context.revalidate(root)==context
    assert config_hash(config)==before
    with pytest.raises(ValueError,match='fold'):
        context.validate_for(replace(config,phase='fold'))


@pytest.mark.parametrize('field,value',[
    ('schema_version',True),('schema_version',2),('scope','holdout'),
    ('canonical','dataset/a.parquet'),('assignments','artifacts/bkt_baseline/a.parquet'),
    ('lock_file','artifacts/akt/private/modal.toml'),('runtime_report','docs/runtime.json'),
    ('dataset_root','artifacts/akt'),('canonical','../escape.parquet'),
    ('canonical','artifacts/akt/synthetic/a/**/*.parquet'),('canonical',r'C:\dataset\a.parquet')])
def test_context_rejects_invalid_schema_paths_and_scopes(context_fixture,field,value):
    root,dataset,path,payload,write=context_fixture
    payload[field]=value;digest=write()
    with pytest.raises(ValueError):load_worker_context(path,expected_sha256=digest,project_root=root)


def test_context_sha_and_input_inventory_are_bound(context_fixture):
    root,dataset,path,value,write=context_fixture
    context=load_worker_context(path,expected_sha256=sha(path),project_root=root)
    with pytest.raises(ValueError,match='SHA'):
        load_worker_context(path,expected_sha256='0'*64,project_root=root)
    (dataset/'c/a.parquet').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hashes'):context.revalidate(root)


def test_context_rejects_extra_parquet_not_in_inventory(context_fixture):
    root,dataset,path,value,write=context_fixture
    (dataset/'c/extra.parquet').write_bytes(b'new')
    with pytest.raises(ValueError,match='hashes'):
        load_worker_context(path,expected_sha256=sha(path),project_root=root)


def test_context_rejects_false_marker_even_with_matching_hash(context_fixture):
    root,dataset,path,value,write=context_fixture
    marker=dataset/'SYNTHETIC_ONLY.json'
    marker.write_text('{"synthetic_only":false,"real_data_authorized":true}')
    value['input_hashes'][marker.relative_to(root).as_posix()]=sha(marker)
    with pytest.raises(ValueError,match='declared'):
        load_worker_context(path,expected_sha256=write(),project_root=root)


@pytest.mark.parametrize('path,sha_value',[(None,'a'*64),('context.json',None)])
def test_context_cli_requires_both_flags(path,sha_value):
    with pytest.raises(ValueError,match='both'):
        context_from_options(SimpleNamespace(context_file=path,context_sha256=sha_value),AKTConfig())


def test_legacy_call_shape_and_child_context_flags_are_preserved():
    assert runner._with_context(lambda value:value+1,3)==4
    parsed=watchdog._parse_worker_args(['smoke','--config','config.json','--context-file','ctx.json',
                                       '--context-sha256','a'*64])
    assert parsed.context_file==Path('ctx.json') and parsed.context_sha256=='a'*64
    assert watchdog._worker_args(['smoke','--config','config.json'])==('smoke',Path('config.json'),None)


def test_cuda_context_requires_explicit_allocator_limits(context_fixture):
    root,dataset,path,value,write=context_fixture
    config=AKTConfig(project_root=root,phase='cuda-smoke',device='cuda')
    context=load_worker_context(path,expected_sha256=sha(path),project_root=root)
    with pytest.raises(ValueError,match='CUDA'):context.validate_for(config)
    value['cuda_limits']={'max_vram_bytes':2*1024**3,'visible_devices':1}
    context=load_worker_context(path,expected_sha256=write(),project_root=root)
    assert context.validate_for(config).cuda_limits.visible_devices==1
    with pytest.raises(ValueError,match='CUDA'):context.validate_for(replace(config,phase='smoke',device='cpu'))
