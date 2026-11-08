"""Đóng một bundle exact bytes; không execute source/model/RNG, không Git mutation."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];PREP=Path(__file__).resolve().parent
RUN='rq2-controlled-ability-prerequisite-20261108-01';DEST=ROOT/'research_tracking/runs'/RUN
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def write(p,value):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
assert not DEST.exists(),'exclusive new bundle only'
provenance=read(PREP/'source_provenance.json')
report=ROOT/provenance['report']
assert sha(report)==provenance['report_sha256']=='5bd3f075bf3a352ad84ce3cf259a4420ba1d7194bf39cf1895fc5e2197da8e23'
expected=dict(provenance['sources_sha256'])
for p in (PREP/'source_provenance.json',PREP/'assemble_report.py',Path(__file__),report):expected[p.relative_to(ROOT).as_posix()]=sha(p)
assert all(sha(ROOT/n)==d for n,d in expected.items()),'source drift'
pairs=[]
for i,(name,digest) in enumerate(expected.items(),1):
    src=ROOT/name
    if src.is_relative_to(PREP/'attempt01'):alias='native__'+src.relative_to(PREP/'attempt01').as_posix().replace('/','__')
    elif src.parent==PREP:alias=src.name
    elif src==report:alias='report.md'
    else:alias=f'bound_{i:02d}__'+src.name
    assert not re.search(r'[\t\r\n]',name+alias) and Path(alias).name==alias
    pairs.append({'source':name,'copy':alias,'sha256':digest,'bytes':src.stat().st_size})
assert len({x['copy'] for x in pairs})==len(pairs)
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
note='''# RQ2: controlled ability × prerequisite — bằng chứng hữu hạn\n\nMột native attempt đã accepted36worlds/4320interactions,3reusedblocks,0newindependentseed/NNoptimizer. Y/Delta/Psi/Omega là điểm Elo net trung bình28concepts tạiT41ngày. Giữ đủ36endpoints/18delta/9psi/6omega và negatives. HighPsi0 design-knownD0; high graphDelta vẫn positive. Không p/CI, external ability/learning generalization hoặc fitted research model/RQcompletion.\n\nCanonical [báo cáo](../../reports/rq2_controlled_ability_prerequisite_results_20261108.md). report.md giữ nguyên bytes và đường dẫn theo vị trí canonical, không rewrite nội dung snapshot. native__* là exactcopies từ attempt01, observable/oracle tách riêng. Raw counters do frozen worker ghi; independent stdlib verifier không chạy native/RNG. Pre-normalization là source preparation versions, không fake failed trial. Root dispatch observation không raw stdout/full toolwall. Copy inventory giữ exactsourcepaths/prepostSHA; không sửa original notebook/world/history.\n\nmetadata.status completed của manifest chỉ là archiver; native acceptance được giữ riêng trong native__run.json. Không Gitmutation/modelcalls trong archive. Parent xử lý indices/state/commit.\n'''
metadata={'kind':'RQ2_FINITE_CONTROLLED_ABILITY_PREREQUISITE_SIMULATOR','evidence_status':'ACCEPTED_NATIVE36_4320_WITH_SAVED_RAW_INDEPENDENT_VERIFICATION','native_run_sha256':sha(PREP/'attempt01/run.json'),'native_elapsed_seconds':12.361254453659058,'max_native_batch_seconds':60,'new_independent_seed_blocks':0,'nn_optimizer_calls':0,'units_vi':'mean net theta/Elo points across28concepts atT41days','role':'Finite simulator factorial; not population inference/model research-fit/RQcompletion','copy_count':len(pairs)}
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=[ROOT/n for n in expected],note=note) as out:
    write(out/'copy_inventory_before.json',{'sources_sha256':expected,'copy_pairs':pairs,'all_sources_checked_before_copy':True})
    for row in pairs:
        payload=(ROOT/row['source']).read_bytes()
        assert hashlib.sha256(payload).hexdigest()==row['sha256'] and len(payload)==row['bytes']
        with (out/row['copy']).open('xb') as f:f.write(payload)
    after={n:sha(ROOT/n) for n in expected}
    copied={row['copy']:sha(out/row['copy']) for row in pairs}
    assert after==expected and all(copied[x['copy']]==x['sha256'] for x in pairs)
    write(out/'copy_inventory_after.json',{'source_after_sha256':after,'copy_sha256':copied,'all_exact':True,'copy_pairs':pairs})
    write(out/'source_bindings.json',{'sources_sha256':expected,'before_equals_after':True,'scientific_inputs25':read(PREP/'attempt01/run.json')['source_input_before_sha256']})
    whitespace={}
    for row in pairs:
        payload=(out/row['copy']).read_bytes()
        bad=[i for i,line in enumerate(payload.splitlines(),1) if line.endswith((b' ',b'\t'))]
        if bad:whitespace[row['copy']]=bad
    write(out/'raw_whitespace_inventory.json',{'raw_exact_bytes_not_normalized':True,'trailing_whitespace_lines':whitespace})
    extras=['copy_inventory_before.json','copy_inventory_after.json','source_bindings.json','raw_whitespace_inventory.json','ignored_log_paths.json','stage_paths.json','README.md','execution.log','manifest.json']
    stage=[(out/x).relative_to(ROOT).as_posix() for x in [r['copy'] for r in pairs]+extras]
    proc=subprocess.run(['git','check-ignore','--',*stage],cwd=ROOT,capture_output=True,text=True)
    if proc.returncode not in (0,1):
        (out/'git_check_ignore_error.txt').write_text(proc.stderr,encoding='utf-8');raise RuntimeError('readonly check-ignore failed')
    ignored=proc.stdout.splitlines();assert set(ignored)<=set(stage)
    write(out/'ignored_log_paths.json',{'command':'git check-ignore -- <exact argv paths>, no -z','returncode':proc.returncode,'force_add_exact_paths':ignored,'stderr':proc.stderr})
    write(out/'stage_paths.json',{'paths':stage,'binary_models_or_data':False,'parent_only_git_stage':True})
verified=verify_evidence_bundle(DEST)
manifest=read(DEST/'manifest.json');assert set(manifest['outputs_sha256'])=={p.name for p in DEST.iterdir() if p.name!='manifest.json'}
public_links=re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8'))
assert all((report.parent/link).resolve().exists() for link in public_links),'public canonical links must materialize'
result={'status':'CLOSED_VERIFIED_NO_RESEARCH_EXECUTION','run':DEST.relative_to(ROOT).as_posix(),'manifest_sha256':sha(DEST/'manifest.json'),'verified':verified,'copies':len(pairs),'sources':len(expected),'copy_bytes':sum(r['bytes'] for r in pairs),'canonical_report_sha256':sha(report),'canonical_links':len(public_links),'force_add_exact_paths':ignored,'all_sources_unchanged_after_closure':all(sha(ROOT/n)==d for n,d in expected.items())}
write(PREP/'closure_verification01.json',result)
print(json.dumps(result,ensure_ascii=False))
