# Kiểm guard local bằng fake subprocess/JUnit; không chạy Colab hoặc GPU.
import hashlib,json,subprocess,types,uuid
from pathlib import Path

def exercise_guards(root, notebook):
    base=root/'artifacts/akt/local-tests'/('colab-guards-'+uuid.uuid4().hex[:12])
    base.mkdir(parents=True)
    cpu=''.join(notebook['cells'][3]['source'])
    gpu=''.join(notebook['cells'][4]['source'])
    records=[]
    for case in ('pass','zero','failure','error','skip','exit_nonzero','missing_junit'):
        directory=base/case;directory.mkdir();output=directory/'output';output.mkdir()
        calls=[]
        def fake_run(command,**kwargs):
            calls.append(command)
            assert kwargs['timeout']==600 and kwargs['env']['CUDA_VISIBLE_DEVICES']==''
            kwargs['stdout'].write('MOCK CPU run; không là actual pytest execution\n')
            if case!='missing_junit':
                counts={'tests':3,'failures':0,'errors':0,'skipped':0}
                for label,key in [('zero','tests'),('failure','failures'),('error','errors'),('skip','skipped')]:
                    if case==label:counts[key]=0 if label=='zero' else 1
                attrs=' '.join(f'{key}="{value}"' for key,value in counts.items())
                (output/'cpu-tests.xml').write_text(f'<testsuites><testsuite {attrs}/></testsuites>')
            return subprocess.CompletedProcess(command,1 if case=='exit_nonzero' else 0)
        fake=types.SimpleNamespace(run=fake_run,STDOUT=subprocess.STDOUT)
        namespace={'ROOT':directory,'OUTPUT':output,'ENV':{},'AKT_PY':'MOCK_ONLY','subprocess':fake,'json':json}
        failed=False
        try:exec(compile(cpu,'<CPU-notebook-cell>','exec'),namespace)
        except (RuntimeError,subprocess.CalledProcessError,FileNotFoundError):failed=True
        assert namespace['CPU_PORTABILITY_OK']==(case=='pass')
        assert failed==(case!='pass')
        if case!='pass':
            before=len(calls)
            try:exec(compile(gpu,'<GPU-notebook-cell>','exec'),namespace)
            except RuntimeError as error:assert 'CPU portability' in str(error)
            else:raise AssertionError('GPU cell ran despite rejected CPU gate')
            assert len(calls)==before
        records.append({'case':case,'guard_pass':True,'actual_gpu_subprocess_invoked':False})
    directory=base/'source_tamper';directory.mkdir();(directory/'code.py').write_text('changed')
    calls=[]
    fake=types.SimpleNamespace(run=lambda *a,**k:calls.append(a))
    namespace={'ROOT':directory,'CPU_PORTABILITY_OK':True,'manifest':{'files':{'code.py':hashlib.sha256(b'original').hexdigest()}},'hashlib':hashlib,'subprocess':fake}
    try:exec(compile(gpu,'<GPU-notebook-cell>','exec'),namespace)
    except ValueError as error:assert 'Source' in str(error)
    else:raise AssertionError('GPU cell accepted changed source')
    assert not calls
    records.append({'case':'source_tamper','guard_pass':True,'actual_gpu_subprocess_invoked':False})
    return records
