"""Readonly4small binary transfer; bytes/SHA only, no model/Parquet loading.

Local destination must be a NEW absent run directory. Native text originals
remain byte-identical; a copy inventory records relocation, not a local fit.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat

ROOT_TEXT='/content/KLTN_GPU08_20261108_01'
ROOT=Path(ROOT_TEXT)
RUN_ID='ctx-linux-20261108-01'
NATIVE='experiments/akt/results/'+RUN_ID+'/'
DATA='artifacts/akt/synthetic/'+RUN_ID+'/'
TEXT_ACCEPTANCE_SHA='dd7c9864c74a9f8fd9584fa24c14b37fb1ac3e665488372ce10be2df0bd3d874'
MAP={DATA+'assignments.parquet':'inputs/assignments.parquet',
     DATA+'canonical/events.parquet':'inputs/events.parquet',
     NATIVE+'inner-best-epoch-1.pt':'inner-best-epoch-1.pt',
     NATIVE+'predictions/part-00000.parquet':'predictions/part-00000.parquet'}
RAW_CAP=1024**2
WIRE_CAP=2*1024**2
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')
def work():return Path(__file__).resolve().parent
def expected():
    path=work()/'received-cpu-worker-evidence01/acceptance.json';raw=path.read_bytes()
    if sha(raw)!=TEXT_ACCEPTANCE_SHA:raise ValueError('verified text acceptance bytes changed')
    receipt=json.loads(raw);rows={}
    for row in receipt['binary_omissions']:
        name=row['path'];value=row['expected_sha256'];size=row['bytes']
        if (name not in MAP or name in rows or not isinstance(value,str) or not re.fullmatch('[a-f0-9]{64}',value)
                or value!=row['sha256_before'] or value!=row['sha256_after'] or type(size) is not int or not 0<size<=RAW_CAP):
            raise ValueError('four actual omission metadata/SHA/size required')
        rows[name]={'sha256':value,'bytes':size,'destination':MAP[name]}
    if set(rows)!=set(MAP) or sum(r['bytes'] for r in rows.values())>RAW_CAP:raise ValueError('four files/raw1MiB bound')
    return rows,receipt
def validate_rows(rows):
    if set(rows)!=set(MAP):raise ValueError('exact four source paths')
    for name,row in rows.items():
        if row['destination']!=MAP[name] or not re.fullmatch('[a-f0-9]{64}',row['sha256']):raise ValueError('fixed relocation/hash identity')
    if sum(r['bytes'] for r in rows.values())>RAW_CAP:raise ValueError('raw1MiB cap')
def read_remote(name,size):
    if name not in MAP:raise ValueError('nonallowlisted source')
    path=ROOT/name
    for part in (path,*path.parents):
        if part.is_symlink():raise ValueError('symlink source forbidden')
        if part==ROOT:break
    if not stat.S_ISREG(path.stat().st_mode):raise ValueError('regular source required')
    with path.open('rb') as stream:raw=stream.read(size+1)
    if len(raw)!=size:raise ValueError('actual source size mismatch')
    return raw
def export(rows):
    validate_rows(rows)
    if ROOT.resolve()!=ROOT or ROOT.is_symlink():raise ValueError('physical existing remote ROOT required')
    raw={name:read_remote(name,row['bytes']) for name,row in rows.items()}
    if any(sha(raw[name])!=row['sha256'] for name,row in rows.items()):raise ValueError('original binary SHA mismatch')
    files=[{'path':name,**rows[name],'sha256_before':sha(data),'base64':base64.b64encode(data).decode('ascii')} for name,data in raw.items()]
    for row in files:
        row['sha256_after']=sha(read_remote(row['path'],row['bytes']))
        if row['sha256_after']!=row['sha256_before']:raise ValueError('source drift after readonly transfer snapshot')
    payload={'kind':'SYNTHETIC_CPU_COLAB_BINARY_PRESERVATION_V1','root':ROOT_TEXT,'run_id':RUN_ID,
             'source_text_acceptance_sha256':TEXT_ACCEPTANCE_SHA,'total_raw_bytes':sum(map(len,raw.values())),
             'files':files,'model_or_Parquet_loads':0,'remote_mutation':False,'zip_used':False}
    wire=canonical({'payload':payload,'payload_sha256':sha(canonical(payload))})
    if len(wire)>WIRE_CAP:raise ValueError('wire2MiB cap')
    print(wire.decode('utf-8'))
def prepare():
    rows,_=expected();source=Path(__file__).resolve();raw=source.read_bytes()
    code=("namespace={'__name__':'readonly_completed_cpu_binary_export'}\n"
          f"exec(compile({raw.decode('utf-8')!r},'cpu_worker_binary_preservation01.py','exec'),namespace)\n"
          f"namespace['export']({rows!r})\n")
    target=work().parent/'requests/gpu09-add-cpu-worker-binary-export01.json'
    with target.open('x',encoding='utf-8') as stream:json.dump({'cellIndex':0,'language':'python','code':code},stream)
    contract={'status':'PREPARED_OFFLINE_NOT_DISPATCHED','source_sha256':sha(raw),'request_sha256':sha(target.read_bytes()),
              'rows':rows,'total_raw_bytes':sum(r['bytes'] for r in rows.values()),'raw_cap_bytes':RAW_CAP,'wire_cap_bytes':WIRE_CAP,
              'readonly':True,'model_Parquet_Git_pip_calls':0,'zip_used':False,'MCP_timeout_seconds':60}
    with (work()/'cpu-worker-binary-export01-contract.json').open('x',encoding='utf-8') as stream:json.dump(contract,stream,indent=2);stream.write('\n')
    print(json.dumps({'request':str(target),**contract}))
def receive(input_path):
    rows,text_receipt=expected();validate_rows(rows)
    with input_path.open('rb') as stream:transport=stream.read(2*WIRE_CAP+1)
    if len(transport)>2*WIRE_CAP:raise ValueError('wrapper4MiB cap')
    obj=json.loads(transport)
    if 'payload_sha256' in obj:stdout=transport.decode('utf-8')
    else:
        data=obj.get('structured_content') or obj.get('data');outputs=data['outputs']
        if len(outputs)>32 or any(o.get('output_type')=='error' for o in outputs):raise ValueError('MCP output error/bound')
        def text(row):
            value=row.get('text','');return value if isinstance(value,str) else ''.join(value)
        stdout=''.join(text(o) for o in outputs if o.get('name')=='stdout')
    if len(stdout.encode('utf-8'))>WIRE_CAP:raise ValueError('wire2MiB cap')
    obj=json.loads(stdout);payload=obj['payload']
    if (sha(canonical(payload))!=obj['payload_sha256'] or payload['kind']!='SYNTHETIC_CPU_COLAB_BINARY_PRESERVATION_V1'
            or payload['root']!=ROOT_TEXT or payload['run_id']!=RUN_ID or payload['source_text_acceptance_sha256']!=TEXT_ACCEPTANCE_SHA):
        raise ValueError('payload source/run identity')
    binaries={}
    for row in payload['files']:
        name=row['path']
        if name not in rows or name in binaries or any(row[k]!=rows[name][k] for k in ('sha256','bytes','destination')):
            raise ValueError('unexpected/duplicate binary mapping')
        raw=base64.b64decode(row['base64'],validate=True)
        if len(raw)!=rows[name]['bytes'] or sha(raw)!=rows[name]['sha256'] or row['sha256_before']!=sha(raw) or row['sha256_after']!=sha(raw):
            raise ValueError('binary exact bytes/SHA')
        binaries[name]=raw
    if set(binaries)!=set(rows) or sum(map(len,binaries.values()))!=payload['total_raw_bytes']:raise ValueError('complete4binary closure')
    repo=work().parents[3];base=(repo/'experiments/akt/results').resolve();destination=base/RUN_ID
    if destination.resolve()!=destination or not destination.is_relative_to(base) or destination.exists() or destination.is_symlink():
        raise FileExistsError('resolved new RunID directory must be absent; no overwrite')
    for parent in destination.parents:
        if parent.is_symlink():raise ValueError('local destination ancestor symlink')
    # Prevalidate all already-received native JSON/logs before any RunID write.
    native_text={};text_rows={}
    for row in text_receipt['copies']:
        name=row['path']
        if not name.startswith(NATIVE):continue
        relative=PurePosixPath(name[len(NATIVE):])
        if relative.is_absolute() or '..' in relative.parts or relative.suffix not in {'.json','.log','.stdout','.stderr'}:
            raise ValueError('native text relocation path')
        raw=(work()/'received-cpu-worker-evidence01'/name).read_bytes()
        if sha(raw)!=row['sha256_before_copy'] or sha(raw)!=row['sha256_after_copy'] or len(raw)!=row['bytes']:
            raise ValueError('verified native text source drift')
        native_text[name]=raw;text_rows[name]=row
    planned=[{'original_ROOT_relative':n,'local_destination':str(destination/MAP[n]),'sha256_before_copy':rows[n]['sha256'],
              'bytes':len(b),'kind':'binary'} for n,b in binaries.items()]
    planned += [{'original_ROOT_relative':n,'local_destination':str(destination/n[len(NATIVE):]),'sha256_before_copy':sha(b),
                 'bytes':len(b),'kind':'native_text'} for n,b in native_text.items()]
    before={'source_origin':'EXISTING_COMPLETED_SYNTHETIC_CPU_COLAB_JOB_NOT_LOCAL_FIT','root':ROOT_TEXT,'run_id':RUN_ID,
            'payload_sha256':obj['payload_sha256'],'transport_sha256':sha(transport),'planned_copies':planned}
    before_path=work()/'cpu-worker-binary-preservation01-before.json'
    with before_path.open('x',encoding='utf-8') as stream:json.dump(before,stream,indent=2);stream.write('\n')
    destination.mkdir(exist_ok=False);copied=[]
    # Preserve binaries first, each post-copy digest checked before native text copy.
    for name,raw in binaries.items():
        target=destination/MAP[name];target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(raw)
        after=sha(target.read_bytes())
        if after!=rows[name]['sha256']:raise ValueError('binary post-copy SHA')
        copied.append({'original_ROOT_relative':name,'local_destination':str(target),'bytes':len(raw),
                       'sha256_before_copy':rows[name]['sha256'],'sha256_after_copy':after,'kind':'binary'})
    for name,raw in native_text.items():
        target=destination/name[len(NATIVE):];target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(raw)
        after=sha(target.read_bytes())
        if after!=sha(raw) or sha((work()/'received-cpu-worker-evidence01'/name).read_bytes())!=after:
            raise ValueError('native text source/destination SHA drift')
        copied.append({'original_ROOT_relative':name,'local_destination':str(target),'bytes':len(raw),
                       'sha256_before_copy':sha(raw),'sha256_after_copy':after,'kind':'native_text'})
    receipt={**before,'status':'PRESERVED_EXACT_CPU_COLAB_DUMMY_ARTIFACT_BYTES','copies':copied,
             'before_inventory_sha256':sha(before_path.read_bytes()),'binary_files':4,'binary_bytes':sum(map(len,binaries.values())),
             'native_text_files':len(native_text),'model_or_Parquet_loads':0,'local_fit_executions':0,
             'limits_vi':'Lưu bytes từ CPU Colab synthetic; không local fit/resume/CUDA/research fitted efficacy. Native manifest giữ nguyên paths và bytes; mapping chỉ ở inventory. Không stage binary Git.'}
    inventory=destination/'transfer-copy-inventory.json'
    with inventory.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
    with (destination/'README.md').open('x',encoding='utf-8') as stream:
        stream.write('# Bản lưu CPU dummy Colab\n\nNguồn là job synthetic CPU đã hoàn tất trên Colab; không phải một lần fit local. Checkpoint/Parquet chỉ được copy và kiểm bytes/SHA, không nạp model hay đọc bảng.\n\nNative JSON/logs giữ nguyên nội dung và đường dẫn gốc remote. `transfer-copy-inventory.json` ánh xạ nguồn–đích, giữ SHA trước/sau. Bản lưu không tự chứng minh resume, CUDA hoặc hiệu quả nghiên cứu; binary không thuộc Git staging.\n')
    print(json.dumps({'destination':str(destination),'binary_files':4,'binary_bytes':receipt['binary_bytes'],
                      'native_text_files':len(native_text),'inventory_sha256':sha(inventory.read_bytes()),'model_loads':0}))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('prepare','receive'))
    parser.add_argument('input_json',nargs='?',type=Path);args=parser.parse_args()
    if args.operation=='prepare':prepare()
    elif args.input_json is None:parser.error('receive requires explicit existing RPC/raw envelope JSON')
    else:receive(args.input_json)
