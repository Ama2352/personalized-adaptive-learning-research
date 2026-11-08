"""GPU-host audit CPU only, one target child; no install/device query/model."""
from __future__ import annotations
import argparse,base64,csv,hashlib,io,json,math,os,platform,re,signal,subprocess,sys,sysconfig,time,traceback,zipfile
from pathlib import Path,PurePosixPath

ROOT_TEXT='/content/KLTN_GPU08_20261108_01'
VENV_TEXT=ROOT_TEXT+'/.venv';TARGET_TEXT=VENV_TEXT+'/bin/python'
ROOT=Path(ROOT_TEXT)
VENV=ROOT/'.venv';TARGET=VENV/'bin/python'
MODE='GPU_HOST_CUDA_HIDDEN_AUDIT_ONLY'
BASELINE_SHA='b0032f9d556d0ca3655d4bafa6d010d30feca05e1d4d6c02ac8148757d8c4ec9'
PROFILE_SHA='0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228'
DISCOVERY_SOURCE_SHA='51c4b98053ba4eaac42b8c8be51ac29645c0b5fdcdf243b19d07c760a8a9db5f'
OLD_SOURCE_SHA='dd7738bfe06032ffaea6a921619767fd659e626ff53ee5a2a7203fb33f885132'
CHILD_SHA='a2b6bf03cb1c0a546a4d437525a80e869edfc6ed1abaca11fdc177b2c3991d98'
STARTUP_MANIFEST_SHA='fcd1175ddc46bb51a64d677d124e682545c32200b48cd9f589dfe64f00feb929'
OLD_PINS={'resolution-attempt01/pip-report.json': '92a2bbae1cdf285491bac1d67082d16c824aeb2ca9447d841a8182807be671dd', 'resolution-attempt01/candidate-linux-cuda.lock.txt': '60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a', 'install-attempt02/pip-install-report.json': 'a689302643eef8b3e6699a074ad6421933086195430614d88de81cc2b34a54ce', 'install-attempt02/result.json': '2ce1bb8efceb4baccab106565280b1a987a9989fcc2116ef4f803687f08b3918', 'install-attempt02/output-manifest.json': '1e449f86d8da250347ffe0ebbe2ab292b787466c57ba27a5fbcc737bc38282eb', 'install-attempt02/pip-check.stdout': '9261363b733079a641c2e4cc9bc46ffa1d8336945a87f807b6cf68847dbc9b09', 'install_stage_attempt02.py': '021dcbe8a4a4a994d56572eb0ac76743c9a1bb3854cb56ca205da7017cb1a21f', '.venv/pyvenv.cfg': '0b85377496947675cd146fc9bcdab419ca9ab7eb4ce40d9a05df459330043366'}
CHILD="import hashlib,importlib,importlib.metadata as m,json,platform,re,site,sys,sysconfig\nfrom email.parser import BytesParser\nfrom pathlib import Path,PurePosixPath\nexpected=EXPECTED_VERSIONS\ndef select_root_metadata(files,locate_file,venv,purelib):\n # Validate ALL RECORD origins, including nested vendored metadata and bin scripts.\n for item in files:\n  if not Path(locate_file(item)).resolve().is_relative_to(venv.resolve()):raise ValueError('record file origin outside venv')\n candidates=[]\n for item in files:\n  parts=PurePosixPath(str(item)).parts\n  if len(parts)==2 and parts[0].endswith('.dist-info') and parts[1]=='METADATA':candidates.append(item)\n if len(candidates)!=1:raise ValueError('exactly one top-level dist-info/METADATA required')\n p=Path(locate_file(candidates[0]))\n if p.resolve().parent.parent!=purelib.resolve() or not p.resolve().is_relative_to(venv.resolve()):raise ValueError('root metadata origin mismatch')\n return p\nnorm=lambda x:re.sub(r'[-_.]+','-',x).lower()\nv=Path('/content/KLTN_GPU08_20261108_01/.venv');pure=Path(sysconfig.get_path('purelib'))\nassert sys.prefix==str(v) and sys.base_prefix=='/usr' and sys.executable==str(v/'bin/python')\nassert platform.python_version()=='3.13.18' and platform.system()=='Linux' and platform.machine()=='x86_64'\nassert platform.libc_ver()==('glibc','2.39') and pure.resolve().is_relative_to(v.resolve()) and site.ENABLE_USER_SITE is False\nfor entry in sys.path:\n if ('site-packages' in entry or 'dist-packages' in entry) and not Path(entry).resolve().is_relative_to(v.resolve()):raise ValueError('external site path')\nrows={}\nfor d in m.distributions():\n name=norm(d.metadata['Name'])\n if name in rows:raise ValueError('duplicate distribution')\n assert name in expected and d.version==expected[name]\n files=list(d.files or ());assert files\n p=select_root_metadata(files,d.locate_file,v,pure);assert p.is_file()\n data=p.read_bytes();headers=BytesParser().parsebytes(data,headersonly=True)\n assert norm(headers['Name'])==name and headers['Version']==expected[name]\n all_depth=sum(str(f).endswith('.dist-info/METADATA') for f in files)\n rows[name]={'version':d.version,'metadata_file':str(p),'metadata_sha256':hashlib.sha256(data).hexdigest(),\n             'file_count':len(files),'all_depth_metadata_count':all_depth,'nested_metadata_ignored':all_depth-1}\nassert set(rows)==set(expected) and len(rows)==44\norigins={}\nfor name in ('torch','numpy','pandas','duckdb','sklearn','scipy','psutil','pytest'):\n module=importlib.import_module(name);p=Path(module.__file__)\n assert p.resolve().is_relative_to(v.resolve())\n origins[name]={'file':str(p),'version':str(getattr(module,'__version__','not_exposed'))}\nimport torch\nassert str(torch.__version__)=='2.7.1+cu126' and torch.version.cuda=='12.6'\nassert not torch.cuda.is_initialized()\nwith torch.device('cpu'):scalar=torch.zeros(1,device='cpu')\nassert scalar.device.type=='cpu' and scalar.item()==0. and not torch.cuda.is_initialized()\nprint(json.dumps({'prefix':sys.prefix,'executable':sys.executable,'python':platform.python_version(),\n 'distributions':rows,'package_count':len(rows),'external_distribution_origins':0,'origins':origins,\n 'torch_build':str(torch.__version__),'cuda_build_metadata':torch.version.cuda,'cuda_initialized':False,\n 'cpu_scalar_check':True,'gpu_device_queries':0,'gpu_model_steps':0,'optimizer_steps':0}))\n"
OLD_IMPORTS={'torch','numpy','pandas','duckdb','sklearn','scipy','psutil','pytest'}
HEX=re.compile('[a-f0-9]{64}')

def digest(b):return hashlib.sha256(b).hexdigest()
def bounded(p,cap=1024**2):
    with p.open('rb') as f:b=f.read(cap+1)
    if len(b)>cap:raise ValueError('input byte cap')
    return b
def strict_sha(v):return isinstance(v,str) and HEX.fullmatch(v) is not None
def current_abi():
    gil=sysconfig.get_config_var('Py_GIL_DISABLED')
    return {'platform_id':sys.platform,'implementation':sys.implementation.name,'python_version':platform.python_version(),
            'machine':platform.machine(),'libc':list(platform.libc_ver()),'cache_tag':sys.implementation.cache_tag,
            'soabi':sysconfig.get_config_var('SOABI'),'extension_suffix':sysconfig.get_config_var('EXT_SUFFIX'),
            'gil_disabled':0 if gil is None else gil}
def child_code(versions):
    if digest(CHILD.encode())!=CHILD_SHA or CHILD.count('EXPECTED_VERSIONS')!=1:raise ValueError('original CHILD template drift')
    return CHILD.replace('EXPECTED_VERSIONS',repr(versions))
def relative(text):
    if not isinstance(text,str) or not text or '\\' in text or ':' in text:raise ValueError('relative POSIX path required')
    p=PurePosixPath(text)
    if p.is_absolute() or '..' in p.parts or p.as_posix()!=text:raise ValueError('unsafe relative path')
    return p
def owned_file(text):
    p=ROOT.joinpath(*relative(text).parts)
    if not p.resolve().is_relative_to(ROOT) or not p.is_file():raise ValueError('missing/external input')
    for ancestor in (p,*p.parents):
        if ancestor.is_symlink():raise ValueError('symlink metadata input')
        if ancestor==ROOT:break
    return p
def normal(name):return re.sub('[-_.]+','-',name).lower()
def distribution_map(probe):
    out={}
    for row in probe['distributions']:
        name=normal(row['name'])
        if name in out or not strict_sha(row['metadata_sha256']) or not strict_sha(row['record_sha256']):raise ValueError('distribution fingerprints')
        out[name]={k:row[k] for k in ('version','root','metadata_sha256','record_sha256')}
    if len(out)!=44:raise ValueError('selected44 required')
    return out

def read_inputs(directory,expected_sha):
    rel=relative(directory)
    if len(rel.parts)!=4 or rel.parts[:3]!=('artifacts','akt','gpu10-hidden-inputs'):raise ValueError('dedicated relocation directory required')
    invpath=owned_file(directory+'/copy-inventory.json');raw=bounded(invpath)
    if not strict_sha(expected_sha) or digest(raw)!=expected_sha:raise ValueError('relocation inventory SHA mismatch')
    inv=json.loads(raw)
    if (type(inv.get('schema_version')) is not int or inv['schema_version']!=1
            or inv.get('role')!='EXACT_BYTE_DISCOVERY_RELOCATION_NOT_EXECUTION'
            or inv.get('copy_root')!=directory or inv.get('phase_auto_execution') is not False):raise ValueError('relocation role/schema')
    values={};hashes={};origins={};files={str(invpath):expected_sha};total_bytes=0
    for row in inv['copies']:
        label=row['label']
        if label in values or label not in {'baseline','fresh','launcher','acceptance','profile','startup_manifest'}:raise ValueError('relocation labels')
        if row['destination']!=directory+'/'+label+'.json' or not isinstance(row['original_locator'],str) or not row['original_locator']:raise ValueError('relocation locator/destination')
        expected_kind='LOCAL_DERIVED_RECEIPT_FROM_VERIFIED_RPC' if label=='acceptance' else None
        if expected_kind and row['origin_kind']!=expected_kind:raise ValueError('local acceptance origin must remain local-derived')
        if label=='fresh' and row['origin_kind']!='REMOTE_DISCOVERY_ARTIFACT':raise ValueError('fresh original source must retain remote-discovery provenance')
        if not isinstance(row['origin_kind'],str) or not row['origin_kind']:raise ValueError('origin kind required')
        p=owned_file(row['destination']);b=bounded(p)
        total_bytes+=len(b)
        if total_bytes>4*1024**2:raise ValueError('total relocation byte cap')
        if (type(row['bytes']) is not int or row['bytes']!=len(b) or not strict_sha(row['sha256_before_copy'])
                or digest(b)!=row['sha256_before_copy'] or digest(b)!=row['sha256_after_copy']):raise ValueError('relocation bytes/SHA')
        values[label]=json.loads(b);hashes[label]=digest(b);files[str(p)]=digest(b)
        origins[label]={k:row[k] for k in ('original_locator','origin_kind','destination')}
    if not {'baseline','fresh','launcher','acceptance','profile'}<=set(values):raise ValueError('missing relocation inputs')
    return values,hashes,origins,files

def validate_bindings(values,hashes):
    b,f,l,a,p=(values[n] for n in ('baseline','fresh','launcher','acceptance','profile'))
    if 'startup_manifest' in values and hashes.get('startup_manifest')!=STARTUP_MANIFEST_SHA:raise ValueError('exact parent-reviewed actual startup manifest required')
    if hashes['baseline']!=BASELINE_SHA or hashes['profile']!=PROFILE_SHA or hashes['fresh']==BASELINE_SHA:raise ValueError('CPU baseline cannot be fresh GPU evidence')
    if b.get('status')!='WARM_CANDIDATE_REQUIRES_AUDIT' or f.get('status')!='WARM_CANDIDATE_REQUIRES_AUDIT':raise ValueError('warm-only audit; cold/partial STOP')
    if (a.get('phase')!='GPU_HOST_READONLY_DISCOVERY'
            or a.get('status')!='VERIFIED_ACTUAL_WARM_GPU_HOST_DISCOVERY_NOT_GPU_READY'
            or a.get('result_sha256')!=hashes['fresh'] or a.get('launcher_sha256')!=hashes['launcher']
            or l.get('phase')!='GPU_HOST_READONLY_DISCOVERY'
            or l.get('status')!='COMPLETED_GPU_HOST_READONLY_DISCOVERY_NOT_GPU_READY'):raise ValueError('fresh generic GPU-host wrapper/acceptance required')
    if (l.get('result_sha256')!=hashes['fresh'] or not strict_sha(a.get('raw_rpc_sha256'))
            or not isinstance(a.get('parent_review_reference'),str) or not a['parent_review_reference'].strip()
            or a.get('launcher_cleanup') is not True or a.get('native_target_cleanup') is not True
            or type(l.get('project_source_file_count')) is not int or l['project_source_file_count']!=165
            or type(a.get('source_files')) is not int or a['source_files']!=165):raise ValueError('fresh accepted receipt lineage')
    signal=f['host_signals'];names=signal['nvidia_device_entry_names'];gpu=signal['COLAB_GPU']
    if (signal['TPU_present'] is not False or not isinstance(names,list) or any(not isinstance(n,str) or not re.fullmatch('nvidia[0-9]+',n) for n in names)
            or not (isinstance(gpu,str) and gpu not in ('','0') or names)):raise ValueError('fresh GPU-host indication required, not T4 proof')
    if f.get('approval_reference')==b.get('approval_reference') or not isinstance(f.get('approval_reference'),str) or not f['approval_reference'].strip():raise ValueError('fresh operation approval required')
    command=l.get('command')
    if not isinstance(command,list) or command[:4]!=['/usr/bin/python3','-I','-S','-B']:raise ValueError('fresh isolated discovery argv')
    def flag(name):
        if command.count(name)!=1 or command.index(name)+1>=len(command):raise ValueError('fresh required argv: '+name)
        return command[command.index(name)+1]
    attempt=flag('--attempt-id')
    expected_inputs='/content/KLTN_GPU10_DISCOVERY_20261108_01/'+attempt+'-inputs'
    if (not isinstance(attempt,str) or not re.fullmatch('gpu-host-[A-Za-z0-9_-]{1,36}',attempt)
            or command[4]!=expected_inputs+'/discovery02.py' or flag('--profile')!=expected_inputs+'/profile.json'
            or flag('--expected-source-sha256')!=DISCOVERY_SOURCE_SHA or flag('--profile-sha256')!=PROFILE_SHA
            or flag('--approval-reference')!=f['approval_reference'] or 'GPU_HOST' not in f['approval_reference']
            or l.get('result_path')!='/content/KLTN_GPU10_DISCOVERY_20261108_01/'+attempt+'/result.json'):
        raise ValueError('fresh generic GPU-host attempt/approval/source/profile labels required')
    expected={**p['source_files'],**{'artifacts/akt/dependencies/upstream/'+k:v for k,v in p['upstream_files'].items()},p['lock_relative']:p['lock_sha256']}
    snapshot=digest(json.dumps(expected,sort_keys=True).encode())
    if len(p['source_files'])!=161 or len(expected)!=165 or f['source_sha256']!=expected or b['source_sha256']!=expected:raise ValueError('source inventory mismatch')
    if l['project_source_snapshot_sha256_before']!=snapshot or l['project_source_snapshot_sha256_after']!=snapshot:raise ValueError('fresh source pre/post mismatch')
    if (f['controller_source_sha256_before']!=DISCOVERY_SOURCE_SHA or f['controller_source_sha256_after']!=DISCOVERY_SOURCE_SHA
            or f['profile_file_sha256_before']!=PROFILE_SHA or f['profile_file_sha256_after']!=PROFILE_SHA):raise ValueError('discovery source/profile mismatch')
    if (f['child']['cleanup_accepted'] is not True or l['cleanup_accepted'] is not True
            or type(f['child']['returncode']) is not int or f['child']['returncode']!=0
            or type(l['child_returncode']) is not int or l['child_returncode']!=0):raise ValueError('fresh child/launcher cleanup/RC')
    for obj,key in ((f,'elapsed_seconds'),(l,'launcher_seconds')):
        if type(obj[key]) not in (int,float) or not math.isfinite(obj[key]) or not 0<=obj[key]<=30:raise ValueError('fresh discovery budget')
    if f['host_abi']!=p['expected_host'] or f['target_probe']['abi']!=p['expected_host']:raise ValueError('fresh ABI differs')
    if type(f['host_abi']['gil_disabled']) is not int or type(f['target_probe']['abi']['gil_disabled']) is not int:raise ValueError('ABI strict types')
    if any(type(f[k]) is not int or f[k]!=0 for k in ('gpu_queries','model_imports','installs')) or type(l['model_gpu_install_calls']) is not int or l['model_gpu_install_calls']!=0:raise ValueError('fresh discovery call scope')
    q=f['target_probe']
    if q['prefix']!='/usr' or q['base_prefix']!='/usr' or type(q['no_site']) is not int or q['no_site']!=1 or type(q['isolated']) is not int or q['isolated']!=1:raise ValueError('no-site discovery expected, not normal prefix proof')
    if q['cuda_visible_devices']!='' or q['nvidia_visible_devices']!='' or q['heavy_modules_imported']!=[]:raise ValueError('fresh discovery scope')
    if distribution_map(q)!=distribution_map(b['target_probe']) or q['origins']!=b['target_probe']['origins'] or f['pyvenv_cfg_sha256']!=b['pyvenv_cfg_sha256']:raise ValueError('pre-switch fingerprint mismatch')
    versions={n:r['version'] for n,r in distribution_map(q).items()}
    if versions!=p['package_versions'] or sum(n.startswith('nvidia-') for n in versions)!=14:raise ValueError('selected44 versions')
    return expected,versions

def selected(report):
    rows={}
    for item in report['install']:
        n=normal(item['metadata']['name'])
        if n in rows:raise ValueError('duplicate selected wheel')
        rows[n]=(item['metadata']['version'],item['download_info']['url'],item['download_info']['archive_info']['hashes']['sha256'])
    if len(rows)!=44:raise ValueError('exact44 wheel report required')
    return rows

def historical_inputs(versions):
    files={};raw={}
    for name,h in {**OLD_PINS,'post_install_audit01.py':OLD_SOURCE_SHA}.items():
        p=owned_file(name);b=bounded(p)
        if digest(b)!=h:raise ValueError('historical provenance SHA mismatch: '+name)
        raw[name]=b;files[str(p)]=h
    planned=selected(json.loads(raw['resolution-attempt01/pip-report.json']))
    if selected(json.loads(raw['install-attempt02/pip-install-report.json']))!=planned or {n:v[0] for n,v in planned.items()}!=versions:raise ValueError('install report must equal original selected44')
    prior=json.loads(raw['install-attempt02/result.json'])
    if prior['status']!='FAILED_RETAIN_PARTIAL_NO_RETRY' or prior['error']!='distribution-origins failed; retain stdout/stderr':raise ValueError('retain original failed install02 verdict')
    if prior['owned_group_cleanup_accepted'] is not True or prior['resource_time_verdict']!='ACCEPTED':raise ValueError('historical install cleanup/budget')
    if [x['name'] for x in prior['children']]!=['probe-before','base-pip-before','pip-install','pip-check','distribution-origins'] or [x['returncode'] for x in prior['children']]!=[0,0,0,0,1]:raise ValueError('historical install lineage')
    if raw['install-attempt02/pip-check.stdout'].decode().strip()!='No broken requirements found.':raise ValueError('historical pip check only, no new pip invocation')
    return files

def startup_decision(facts,manifest,declared):
    """Bounded facts→decision; no hook evaluator or inferred canonical bytes."""
    if manifest is None:manifest={'schema_version':1,'role':'PARENT_REVIEWED_ACTUAL_STARTUP_ALLOWLIST','files':{},'environment':{}}
    if type(manifest.get('schema_version')) is not int or manifest['schema_version']!=1 or manifest.get('role')!='PARENT_REVIEWED_ACTUAL_STARTUP_ALLOWLIST':raise ValueError('startup review schema')
    allowed=manifest['files'];env=manifest['environment']
    if not isinstance(allowed,dict) or env not in ({},{'SETUPTOOLS_USE_DISTUTILS':'stdlib'}):raise ValueError('unreviewed startup environment')
    permitted='.venv/lib/python3.13/site-packages/distutils-precedence.pth'
    if set(allowed)-{permitted}:raise ValueError('only actual reviewed setuptools hook may be allowed')
    exception=manifest.get('reviewed_system_empty_symlink')
    unknown=[]
    for fact in facts:
        rel=fact['root_relative']
        if rel is None:
            reviewed=(isinstance(exception,dict) and fact['path']=='/usr/lib/python3.13/sitecustomize.py'
                      and exception.get('path')==fact['path'] and fact.get('is_symlink') is True
                      and fact.get('resolved_path')==exception.get('resolved_path')=='/etc/python3.13/sitecustomize.py'
                      and fact.get('target_is_symlink') is False
                      and type(fact.get('bytes')) is int and type(exception.get('bytes')) is int
                      and fact['bytes']==exception['bytes']==0
                      and fact.get('sha256')==exception.get('sha256')==digest(b''))
            if not reviewed:unknown.append(fact)
            continue
        entry=allowed.get(rel)
        if (not isinstance(entry,dict) or entry.get('sha256')!=fact['sha256'] or type(entry.get('bytes')) is not int
                or fact.get('is_symlink') is not False or entry['bytes']!=fact['bytes']
                or declared.get(rel)!=fact['sha256']):unknown.append(fact)
    if set(allowed)-{x['root_relative'] for x in facts}:raise ValueError('startup allowlist has absent/unsupported paths')
    if exception and not any(f['path']==exception.get('path') for f in facts):raise ValueError('reviewed system link now absent')
    return {'accepted':not unknown,'unknown':unknown,'environment':env,'facts':facts}

def startup_facts(fresh):
    q=fresh['target_probe'];pure=Path(q['purelib']);v=VENV.resolve()
    if pure.resolve()!=v/'lib/python3.13/site-packages':raise ValueError('explicit existing venv purelib required')
    declared={};files={}
    fingerprints=distribution_map(q);seen=set()
    for dist in pure.glob('*.dist-info'):
        if dist.is_symlink() or not dist.resolve().is_relative_to(v) or (dist/'METADATA').is_symlink() or (dist/'RECORD').is_symlink():raise ValueError('metadata source symlink')
        meta=bounded(dist/'METADATA');record=bounded(dist/'RECORD',8*1024**2)
        from email.parser import BytesParser
        name=normal(BytesParser().parsebytes(meta,headersonly=True)['Name'])
        if name in seen:raise ValueError('duplicate metadata directory')
        seen.add(name)
        if name not in fingerprints or digest(meta)!=fingerprints[name]['metadata_sha256'] or digest(record)!=fingerprints[name]['record_sha256']:raise ValueError('actual metadata/RECORD differs from fresh discovery')
        files[str(dist/'METADATA')]=digest(meta);files[str(dist/'RECORD')]=digest(record)
        for row in csv.reader(io.StringIO(record.decode())):
            if len(row)!=3 or not row[1].startswith('sha256='):continue
            target=(pure/row[0]).resolve()
            if target.is_relative_to(VENV) and target.suffix=='.pth':
                if name!='setuptools':continue
                value=base64.urlsafe_b64decode(row[1].split('=',1)[1]+'===')
                if len(value)!=32:raise ValueError('startup RECORD digest')
                key=target.relative_to(ROOT).as_posix()
                if key in declared and declared[key]!=value.hex():raise ValueError('conflicting startup RECORD hash')
                declared[key]=value.hex()
    if seen!=set(fingerprints):raise ValueError('missing selected44 metadata')
    candidates=set(pure.glob('*.pth'))
    for text in [*q['sys_path'],str(pure)]:
        path=Path(text)
        for name in ('sitecustomize','usercustomize'):
            if path.is_dir():
                for p in (path/(name+'.py'),path/name/'__init__.py'):
                    if p.is_file():candidates.add(p)
            elif path.is_file() and path.suffix=='.zip':
                with zipfile.ZipFile(path) as z:
                    if any(n in z.namelist() for n in (name+'.py',name+'/__init__.py')):raise ValueError('unknown customize in base ZIP; STOP_NO_CHILD')
    facts=[]
    for path in sorted(candidates):
        rel=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else None
        info={'path':str(path),'root_relative':rel,'is_symlink':path.is_symlink()}
        if path.is_symlink():
            target=path.resolve();info.update(resolved_path=str(target),target_is_symlink=target.is_symlink())
            if path!=Path('/usr/lib/python3.13/sitecustomize.py') or target!=Path('/etc/python3.13/sitecustomize.py') or target.is_symlink():
                facts.append({**info,'sha256':None,'bytes':None,'text':None});continue
        b=bounded(path,64*1024)
        info.update(sha256=digest(b),bytes=len(b),text=b.decode('utf-8',errors='replace') if len(b)<=4096 else None)
        facts.append(info)
        files[str(path)]=digest(b)
    if set(declared)-{f['root_relative'] for f in facts}:raise ValueError('declared startup hook missing; STOP_NO_CHILD')
    for entry in q['origins'].values():
        if entry is not None:
            p=Path(entry['path'])
            if not p.resolve().is_relative_to(v):raise ValueError('external entrypoint origin')
            b=bounded(p)
            if digest(b)!=entry['sha256'] or len(b)!=entry['bytes']:raise ValueError('actual entrypoint origin drift')
            files[str(p)]=digest(b)
    return facts,declared,files

def child_environment(stage,overrides):
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(stage/'home'),
         'TMPDIR':str(stage/'tmp'),'XDG_CACHE_HOME':str(stage/'cache'),'TORCH_HOME':str(stage/'cache'),
         'TRITON_CACHE_DIR':str(stage/'cache'),'CUDA_CACHE_PATH':str(stage/'cache'),
         'CUDA_VISIBLE_DEVICES':'','NVIDIA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1',
         'PYTHONNOUSERSITE':'1','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','PIP_CONFIG_FILE':os.devnull}
    if overrides not in ({},{'SETUPTOOLS_USE_DISTUTILS':'stdlib'}):raise ValueError('unreviewed env override')
    return {**env,**overrides}

def accept_payload(payload,versions,*,returncode,cleanup,elapsed,metadata_fingerprints):
    if type(returncode) is not int or returncode!=0 or cleanup is not True or type(elapsed) not in (int,float) or not math.isfinite(elapsed) or not 0<=elapsed<=90:raise ValueError('child/cleanup/post-exit budget failed')
    if (payload['prefix']!=VENV_TEXT or payload['executable']!=TARGET_TEXT or payload['python']!='3.13.18'
            or type(payload['package_count']) is not int or payload['package_count']!=44
            or set(payload['distributions'])!=set(versions) or set(payload['origins'])!=OLD_IMPORTS
            or payload['cuda_initialized'] is not False or payload['cpu_scalar_check'] is not True
            or payload['torch_build']!='2.7.1+cu126' or payload['cuda_build_metadata']!='12.6'):raise ValueError('normal-prefix/exact44/imports/CPU-scalar/CUDA-uninitialized required')
    for name,row in payload['distributions'].items():
        if row['version']!=versions[name] or row['metadata_sha256']!=metadata_fingerprints[name]['metadata_sha256']:raise ValueError('child distribution version/metadata')
    for name in ('external_distribution_origins','gpu_device_queries','gpu_model_steps','optimizer_steps'):
        if type(payload[name]) is not int or payload[name]!=0:raise ValueError('explicit child call/origin ledger')
    for row in payload['origins'].values():
        p=PurePosixPath(row['file'])
        if '..' in p.parts or not p.is_absolute() or not p.is_relative_to(PurePosixPath(VENV_TEXT)):raise ValueError('external imported origin')
    return True

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=(MODE,),required=True);p.add_argument('--expected-source-sha256',required=True)
    p.add_argument('--attempt-id',required=True);p.add_argument('--approval-reference',required=True)
    p.add_argument('--input-directory',required=True);p.add_argument('--input-inventory-sha256',required=True)
    return p

def main(argv=None):
    a=parser().parse_args(argv);start=time.monotonic()
    if (os.name!='posix' or sys.flags.no_site!=1 or sys.flags.isolated!=1
            or Path(sys.executable)!=Path('/usr/bin/python3') or sys.prefix!='/usr'
            or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,47}',a.attempt_id)
            or not a.approval_reference.strip() or not strict_sha(a.expected_source_sha256)):
        raise ValueError('explicit isolated-base/mode/source/attempt approval required')
    if not ROOT.is_dir() or ROOT.resolve()!=ROOT or ROOT.stat().st_uid!=os.getuid():raise ValueError('owned existing ROOT required')
    stage=ROOT/('gpu-host-hidden-audit-'+a.attempt_id);stage.mkdir(exist_ok=False)
    result={'status':'FAILED_HIDDEN_CPU_AUDIT_RETAIN_NO_RETRY','mode':MODE,'target_children':0,
            'install_pip_network_model_optimizer_explicit_device_query_calls':0,'CUDA_ready':False,
            'ledger_scope':'Our source explicit API calls only; not full dependency syscall or whole-host attestation.'}
    process=None;handled=False;cleanup_ok=False;cleanup=[];candidate=False;files={};after_files={};peak=0
    def check():
        nonlocal peak
        if time.monotonic()-start>90:raise TimeoutError('overall90s cap')
        if (stage/'CANCEL').exists():raise RuntimeError('cancelled')
        total=0
        for base,_,names in os.walk(ROOT,followlinks=False):
            for name in names:
                try:st=os.lstat(Path(base)/name)
                except FileNotFoundError:continue
                total+=max(st.st_size,getattr(st,'st_blocks',0)*512)
        peak=max(peak,total)
        import shutil
        if total>20*1024**3 or shutil.disk_usage(ROOT).free<30*1024**3:raise MemoryError('cooperative workspace/free disk guard')
        if sum(p.stat().st_size for p in stage.iterdir() if p.suffix in {'.stdout','.stderr'})>4*1024**2:raise MemoryError('audit log cap')
    def cleanup_once():
        nonlocal handled,cleanup_ok
        if process is None or handled:return
        handled=True;failed=False
        if process.pid<=1 or process.pid==os.getpgrp():cleanup.append('refuse global PGID');failed=True
        else:
            for sig in (signal.SIGTERM,signal.SIGKILL):
                try:os.killpg(process.pid,sig);cleanup.append({'signal':sig.name,'sent':True})
                except ProcessLookupError:cleanup.append({'signal':sig.name,'already_absent':True})
                except OSError as exc:failed=True;cleanup.append({'signal':sig.name,'error':str(exc)})
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:failed=True;cleanup.append('leader reap timeout')
        cleanup_ok=not failed
        result['child_returncode']=process.poll()
    try:
        source=Path(__file__).absolute()
        source=owned_file(source.relative_to(ROOT).as_posix());raw=bounded(source)
        if digest(raw)!=a.expected_source_sha256:raise ValueError('controller source SHA')
        files[str(source)]=digest(raw)
        values,hashes,origins,input_files=read_inputs(a.input_directory,a.input_inventory_sha256);files.update(input_files)
        expected,versions=validate_bindings(values,hashes)
        if origins['fresh']['original_locator']!=values['launcher']['result_path']:raise ValueError('relocation fresh original locator must remain actual external discovery path')
        if current_abi()!=values['profile']['expected_host']:raise ValueError('current controller ABI differs from approved fresh discovery')
        for name,h in expected.items():
            p=owned_file(name);b=bounded(p,64*1024**2)
            if digest(b)!=h:raise ValueError('actual source/lock differs from fresh discovery')
            files[str(p)]=h
        actual_gpu=bool(os.environ.get('COLAB_GPU') not in (None,'','0') or list(Path('/dev').glob('nvidia[0-9]*')))
        if not actual_gpu or os.environ.get('COLAB_TPU_ADDR'):raise ValueError('current host GPU indication required; no hardware queries')
        if not VENV.is_dir() or VENV.is_symlink() or not TARGET.is_file() or TARGET.resolve()!=Path(sys.executable).resolve():raise ValueError('existing isolated venv/current base required')
        files.update(historical_inputs(versions))
        facts,declared,startup_files=startup_facts(values['fresh']);files.update(startup_files)
        decision=startup_decision(facts,values.get('startup_manifest'),declared)
        result.update(input_origins=origins,input_sha256=hashes,startup_preflight=decision,
                      baseline_scope='Historical CPU pre-switch metadata only',fresh_scope='Parent-verified new generic GPU-host read-only discovery; not T4 hardware proof')
        (stage/'startup-preflight.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if not decision['accepted']:
            result['status']='STOP_UNKNOWN_STARTUP_HOOK_NO_CHILD'
        else:
            for name in ('home','tmp','cache'):(stage/name).mkdir()
            script=stage/'audit-child.py';script.write_text(child_code(versions),encoding='utf-8')
            check()
            with (stage/'audit.stdout').open('xb') as out,(stage/'audit.stderr').open('xb') as err:
                process=subprocess.Popen([str(TARGET),'-I','-B',str(script)],cwd=ROOT,env=child_environment(stage,decision['environment']),stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
                result['target_children']=1;result['child_pid']=process.pid
                try:
                    while process.poll() is None:
                        check()
                        try:process.wait(timeout=.25)
                        except subprocess.TimeoutExpired:pass
                finally:cleanup_once()
            payload=json.loads(bounded(stage/'audit.stdout'))
            accept_payload(payload,versions,returncode=process.returncode,cleanup=cleanup_ok,elapsed=time.monotonic()-start,
                           metadata_fingerprints=distribution_map(values['fresh']['target_probe']))
            result['audit']=payload;candidate=True
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
        (stage/'failure.log').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        cleanup_once()
        try:
            check()
            for fact in result.get('startup_preflight',{}).get('facts',[]):
                if fact.get('is_symlink') and fact['root_relative'] is None:
                    path=Path(fact['path'])
                    if not path.is_symlink() or str(path.resolve())!=fact['resolved_path']:raise ValueError('startup system link postcheck drift')
            for path,h in files.items():
                p=Path(path)
                if p!=Path('/usr/lib/python3.13/sitecustomize.py'):
                    startup_paths={f['path'] for f in result.get('startup_preflight',{}).get('facts',[])}
                    if not p.resolve().is_relative_to(ROOT) and str(p) not in startup_paths:raise ValueError('postcheck unexpected external source/input')
                    for ancestor in (p,*p.parents):
                        if ancestor.is_symlink():raise ValueError('postcheck source/input symlink')
                        if ancestor==ROOT:break
                actual=digest(bounded(p,64*1024**2));after_files[path]=actual
                if actual!=h:raise ValueError('post-audit source/input/startup hash drift')
            if candidate and cleanup_ok:result['status']='GPU_HOST_CUDA_HIDDEN_CPU_AUDIT_ACCEPTED_NOT_CUDA_READY'
        except Exception as exc:result.update(status='FAILED_HIDDEN_CPU_AUDIT_RETAIN_NO_RETRY',postcheck_error=str(exc))
        result.update(source_sha256=a.expected_source_sha256,child_template_sha256=CHILD_SHA,
                      approval_reference=a.approval_reference,cleanup_attempted=handled,cleanup_accepted=cleanup_ok,
                      cleanup=cleanup,elapsed_seconds=time.monotonic()-start,peak_workspace_bytes=peak,
                      workspace_guard_is_cooperative=True,input_file_sha256_before=files,input_file_sha256_after=after_files)
        (stage/'input-hashes.json').write_text(json.dumps({'before':files,'after':after_files},indent=2)+'\n',encoding='utf-8')
        (stage/'resources.json').write_text(json.dumps({'elapsed_seconds':time.monotonic()-start,'cap_seconds':90,
            'workspace_peak_bytes':peak,'workspace_cap_bytes':20*1024**3,'min_free_bytes':30*1024**3,
            'cooperative':True,'child_returncode':None if process is None else process.poll(),
            'cleanup_accepted':cleanup_ok},indent=2)+'\n',encoding='utf-8')
        # Budget verdict after bounded output hashing, not just after child exit.
        preliminary={p.name:{'sha256':digest(bounded(p,4*1024**2)),'bytes':p.stat().st_size} for p in stage.iterdir() if p.is_file()}
        result['elapsed_seconds']=time.monotonic()-start
        if result['elapsed_seconds']>90:result['status']='FAILED_HIDDEN_CPU_AUDIT_RETAIN_NO_RETRY';result['budget_rejected']=True
        (stage/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        manifest={**preliminary,'result.json':{'sha256':digest(bounded(stage/'result.json',4*1024**2)),'bytes':(stage/'result.json').stat().st_size}}
        (stage/'output-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':result['status'],'result':str(stage/'result.json'),'result_sha256':digest(bounded(stage/'result.json')),'target_children':result['target_children']}))
    return 0 if candidate and result['status'].startswith('GPU_HOST_CUDA_HIDDEN_CPU_AUDIT_ACCEPTED') else 1

if __name__=='__main__':raise SystemExit(main())
