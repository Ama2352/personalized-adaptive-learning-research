import hashlib,json,os,runpy,subprocess,time,traceback,xml.etree.ElementTree as ET
try:
    INTEGRATION_OUTPUT=ROOT/'integration-evidence02'
    INTEGRATION_OUTPUT.mkdir(exist_ok=False)
    before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in manifest['files']}
    assert before==manifest['files']
    partition=runpy.run_path(str(ROOT/'scripts/akt/refresh_gate2.py'))['test_partition'](ROOT)
    assert sum(len(paths) for _,paths in partition)==92
    env=dict(ENV,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    started=time.monotonic()
    status={'status':'FAILED','scope':'Scoped Linux CPU integration, inherited runtime; explicit isolated-runtime test deselection; no fresh Gate','groups':[],'excluded_node':'tests/akt/test_runtime.py::test_native_akt_import_cpu','exclusion_reason':'Inherited Colab Torch/NumPy are outside .venv; isolated runtime readiness remains unverified'}
    (INTEGRATION_OUTPUT/'sources.json').write_text(json.dumps(manifest,indent=2))
    (INTEGRATION_OUTPUT/'STARTED.json').write_text(json.dumps({'timeout_seconds':600,'modules':92,'groups':partition}))
    for name,modules in partition:
        remaining=600-(time.monotonic()-started)
        assert remaining>0,'integration global deadline'
        command=[AKT_PY,'-B','-m','pytest',*modules,'-q','-o','addopts=','-p','no:cacheprovider',
            '--deselect=tests/akt/test_runtime.py::test_native_akt_import_cpu',
            '--basetemp',str(ROOT/'artifacts/akt/tmp'/('integration02-'+name)),
            '--junitxml',str(INTEGRATION_OUTPUT/(name+'.xml'))]
        entry={'name':name,'command':command,'module_count':len(modules)}
        status['groups'].append(entry)
        (INTEGRATION_OUTPUT/'status.json').write_text(json.dumps(status,indent=2))
        try:
            with (INTEGRATION_OUTPUT/(name+'.log')).open('xb') as log:
                result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
            cases=list(ET.parse(INTEGRATION_OUTPUT/(name+'.xml')).getroot().iter('testcase'))
            entry.update(returncode=result.returncode,tests=len(cases),counts={tag:sum(c.find(tag) is not None for c in cases) for tag in ('failure','error','skipped')})
        except BaseException as exc:
            entry.update(error_type=type(exc).__name__,error=str(exc))
        (INTEGRATION_OUTPUT/'status.json').write_text(json.dumps(status,indent=2))
        print('GROUP_DONE',json.dumps(entry),flush=True)
    after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in manifest['files']}
    status['source_unchanged']=before==after
    status['elapsed_seconds']=time.monotonic()-started
    if status['source_unchanged'] and status['elapsed_seconds']<=600 and all(g.get('returncode')==0 and g.get('tests',0)>0 and not any(g['counts'].values()) for g in status['groups']):
        status['status']='PASS_SCOPED_PORTABILITY_ONLY'
    (INTEGRATION_OUTPUT/'status.json').write_text(json.dumps(status,indent=2))
    print('INTEGRATION_FINAL',json.dumps(status),flush=True)
except BaseException:
    print(traceback.format_exc(),flush=True)
