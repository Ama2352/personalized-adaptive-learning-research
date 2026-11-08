"""Chunked retrieval of EXISTING4small CPU artifacts; no model/job rerun.

One owned ZIP, 48000-byte frames. Finish reuses unchanged receiver01 copy guards.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import stat
import zipfile

ROOT_TEXT='/content/KLTN_GPU08_20261108_01'
ROOT=Path(ROOT_TEXT)
REMOTE=ROOT/'cpu-worker-binary-transfer02'
ARCHIVE='cpu-worker-binary-preservation02.zip'
MANIFEST='TRANSFER_MANIFEST.json'
CHUNK=48000
CAP=1024**2
SOURCE01_SHA='331e46d711327350915b400e69f91e18492d8881df3774cccf45cb0c0e662095'
TEXT_ACCEPTANCE_SHA='dd7c9864c74a9f8fd9584fa24c14b37fb1ac3e665488372ce10be2df0bd3d874'
RUN_ID='ctx-linux-20261108-01'
OUT='experiments/akt/results/'+RUN_ID+'/'
DATA='artifacts/akt/synthetic/'+RUN_ID+'/'
MAP={DATA+'assignments.parquet':'inputs/assignments.parquet',DATA+'canonical/events.parquet':'inputs/events.parquet',
     OUT+'inner-best-epoch-1.pt':'inner-best-epoch-1.pt',OUT+'predictions/part-00000.parquet':'predictions/part-00000.parquet'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')
def work():return Path(__file__).resolve().parent
def local():return work()/'transfer-cpu-worker-binary02'
def old_receiver():
    path=work()/'cpu_worker_binary_preservation01.py'
    if sha(path.read_bytes())!=SOURCE01_SHA:raise ValueError('preserved receiver01 source changed')
    return runpy.run_path(str(path)) # Definitions only; no model/receive operation.
def expected():return old_receiver()['expected']()[0]
def validate_rows(rows):
    if set(rows)!=set(MAP):raise ValueError('four source paths required')
    for name,row in rows.items():
        if (row['destination']!=MAP[name] or type(row['bytes']) is not int or not 0<row['bytes']<=CAP
                or re.fullmatch('[a-f0-9]{64}',row['sha256']) is None):raise ValueError('exact mapping/size/SHA')
    if sum(r['bytes'] for r in rows.values())>CAP:raise ValueError('raw1MiB cap')
def read_source(name,size):
    if name not in MAP:raise ValueError('source path unavailable')
    path=ROOT/name
    for part in (path,*path.parents):
        if part.is_symlink():raise ValueError('source link forbidden')
        if part==ROOT:break
    if not stat.S_ISREG(path.stat().st_mode):raise ValueError('regular source required')
    with path.open('rb') as stream:raw=stream.read(size+1)
    if len(raw)!=size:raise ValueError('source size changed')
    return raw
def zip_checked(raw,rows):
    if len(raw)>CAP:raise ValueError('ZIP1MiB cap')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        if len(names)!=5 or set(names)!={*MAP.values(),MANIFEST}:raise ValueError('exact5ZIP members/no duplicates')
        if any(stat.S_ISLNK(i.external_attr>>16) for i in infos):raise ValueError('ZIP symlink forbidden')
        if archive.testzip() is not None:raise ValueError('ZIP CRC failure')
        manifest=json.loads(archive.read(MANIFEST))
        if manifest['rows']!=rows or manifest['source_text_acceptance_sha256']!=TEXT_ACCEPTANCE_SHA:raise ValueError('ZIP manifest identity')
        result={}
        for name,row in rows.items():
            info=archive.getinfo(row['destination'])
            if info.file_size!=row['bytes']:raise ValueError('ZIP declared binary size')
            data=archive.read(info)
            if len(data)!=row['bytes'] or sha(data)!=row['sha256']:raise ValueError('ZIP member SHA/size')
            result[name]=data
        return result
def first(rows):
    validate_rows(rows)
    if ROOT.resolve()!=ROOT or ROOT.is_symlink():raise ValueError('physical existing ROOT')
    if REMOTE.exists():
        plan_raw=(REMOTE/'plan.json').read_bytes();plan=json.loads(plan_raw)
        raw=(REMOTE/ARCHIVE).read_bytes()
        if plan['rows']!=rows or sha(raw)!=plan['archive_sha256'] or len(raw)!=plan['archive_bytes']:raise ValueError('existing transfer drift')
        zip_checked(raw,rows)
        print(canonical({'plan':plan,'plan_sha256':sha(plan_raw),'existing_archive_reused':True}).decode());return
    if REMOTE.is_symlink():raise ValueError('transfer path link')
    data={name:read_source(name,row['bytes']) for name,row in rows.items()}
    if any(sha(data[n])!=rows[n]['sha256'] for n in rows):raise ValueError('source SHA before ZIP')
    REMOTE.mkdir(exist_ok=False)
    with zipfile.ZipFile(REMOTE/ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,raw in data.items():archive.writestr(rows[name]['destination'],raw)
        after={n:sha(read_source(n,rows[n]['bytes'])) for n in rows}
        if any(after[n]!=rows[n]['sha256'] for n in rows):raise ValueError('source SHA after ZIP snapshot')
        manifest={'source_origin':'EXISTING_COMPLETED_SYNTHETIC_CPU_COLAB_JOB_NOT_LOCAL_FIT','root':ROOT_TEXT,
                  'source_text_acceptance_sha256':TEXT_ACCEPTANCE_SHA,'rows':rows,
                  'source_sha256_before':{n:sha(b) for n,b in data.items()},'source_sha256_after':after,'model_or_Parquet_loads':0}
        archive.writestr(MANIFEST,canonical(manifest))
    raw=(REMOTE/ARCHIVE).read_bytes();zip_checked(raw,rows)
    plan={'kind':'CPU_DUMMY_BINARY_CHUNKED_ZIP_V2','root':ROOT_TEXT,'archive':ARCHIVE,'archive_sha256':sha(raw),
          'archive_bytes':len(raw),'chunk_bytes':CHUNK,'chunks':(len(raw)+CHUNK-1)//CHUNK,'rows':rows,
          'raw_bytes':sum(len(b) for b in data.values()),'zip_crc_checked':True,'source_text_acceptance_sha256':TEXT_ACCEPTANCE_SHA}
    plan_raw=canonical(plan)+b'\n'
    with (REMOTE/'plan.json').open('xb') as stream:stream.write(plan_raw)
    print(canonical({'plan':plan,'plan_sha256':sha(plan_raw),'existing_archive_reused':False}).decode())
def chunk(index,plan_sha):
    plan_raw=(REMOTE/'plan.json').read_bytes();plan=json.loads(plan_raw)
    if sha(plan_raw)!=plan_sha or type(index) is not int or not 0<=index<plan['chunks']:raise ValueError('chunk index/plan pin')
    path=REMOTE/ARCHIVE;raw=path.read_bytes()
    if len(raw)!=plan['archive_bytes'] or sha(raw)!=plan['archive_sha256']:raise ValueError('archive drift')
    data=raw[index*CHUNK:(index+1)*CHUNK]
    row={'kind':'CPU_BINARY_FRAME_48000_V2','plan_sha256':plan_sha,'archive_sha256':plan['archive_sha256'],
         'index':index,'offset':index*CHUNK,'bytes':len(data),'sha256':sha(data),'base64':base64.b64encode(data).decode('ascii')}
    if sha(path.read_bytes())!=plan['archive_sha256']:raise ValueError('archive changed after frame')
    wire=canonical(row)
    if len(wire)>65000:raise ValueError('frame stdout65k cap; fullywrapped target<200k')
    print(wire.decode())
def rpc(input_path,cap=256*1024):
    with input_path.open('rb') as stream:raw=stream.read(cap+1)
    if len(raw)>cap:raise ValueError('bounded frame RPC input')
    obj=json.loads(raw)
    if 'plan' in obj or obj.get('kind')=='CPU_BINARY_FRAME_48000_V2':return obj,sha(raw)
    data=obj.get('structured_content') or obj.get('data');outputs=data['outputs']
    if any(o.get('output_type')=='error' for o in outputs):raise ValueError('RPC output error')
    def text(row):
        value=row.get('text','');return value if isinstance(value,str) else ''.join(value)
    stdout=''.join(text(o) for o in outputs if o.get('name')=='stdout')
    return json.loads(stdout),sha(raw)
def request(label,call):
    raw=Path(__file__).read_bytes()
    code=("namespace={'__name__':'bounded_existing_binary_transfer02'}\n"
          f"exec(compile({raw.decode('utf-8')!r},'cpu_worker_binary_chunk02.py','exec'),namespace)\n"+call+'\n')
    path=work().parent/'requests'/('gpu09-add-cpu-binary02-'+label+'.json')
    with path.open('x',encoding='utf-8') as stream:json.dump({'cellIndex':0,'language':'python','code':code},stream)
    return {'request':str(path),'sha256':sha(path.read_bytes())}
def prepare_first():
    rows=expected();validate_rows(rows)
    print(json.dumps({**request('first',f"namespace['first']({rows!r})"),'executed':False,'chunk_bytes':CHUNK,'raw_bytes':sum(r['bytes'] for r in rows.values())}))
def receive_first(path):
    obj,transport_sha=rpc(path);plan=obj['plan'];rows=expected()
    if (plan['kind']!='CPU_DUMMY_BINARY_CHUNKED_ZIP_V2' or plan['root']!=ROOT_TEXT or plan['archive']!=ARCHIVE
            or plan['rows']!=rows or plan['chunk_bytes']!=CHUNK or not 0<plan['archive_bytes']<=CAP
            or plan['chunks']!=(plan['archive_bytes']+CHUNK-1)//CHUNK or plan['zip_crc_checked'] is not True
            or plan['source_text_acceptance_sha256']!=TEXT_ACCEPTANCE_SHA):raise ValueError('first exact plan identity/bounds')
    if sha(canonical(plan)+b'\n')!=obj['plan_sha256']:raise ValueError('remote plan SHA')
    if local().exists() or local().is_symlink():raise FileExistsError('local transfer already exists; no overwrite')
    local().mkdir(exist_ok=False)
    with (local()/'plan.json').open('x',encoding='utf-8') as stream:json.dump(obj,stream,indent=2);stream.write('\n')
    with (local()/'first-receipt.json').open('x',encoding='utf-8') as stream:json.dump({'transport_sha256':transport_sha,'remote_plan_sha256':obj['plan_sha256']},stream)
    print(json.dumps({'received_plan':str(local()/'plan.json'),'chunks':plan['chunks'],'archive_bytes':plan['archive_bytes']}))
def prepare_chunks():
    obj=json.loads((local()/'plan.json').read_text());items=[]
    for index in range(obj['plan']['chunks']):items.append(request('chunk-'+str(index).zfill(4),f"namespace['chunk']({index},{obj['plan_sha256']!r})"))
    with (local()/'chunk-requests.json').open('x',encoding='utf-8') as stream:json.dump(items,stream,indent=2)
    print(json.dumps({'requests':items,'executed':False}))
def receive_chunk(path):
    row,transport_sha=rpc(path);obj=json.loads((local()/'plan.json').read_text());plan=obj['plan'];index=row['index']
    if (row['kind']!='CPU_BINARY_FRAME_48000_V2' or type(index) is not int or not 0<=index<plan['chunks']
            or row['plan_sha256']!=obj['plan_sha256'] or row['archive_sha256']!=plan['archive_sha256']
            or row['offset']!=index*CHUNK):raise ValueError('frame identity/offset')
    data=base64.b64decode(row['base64'],validate=True);size=min(CHUNK,plan['archive_bytes']-index*CHUNK)
    if len(data)!=size or row['bytes']!=size or sha(data)!=row['sha256']:raise ValueError('frame exact size/SHA')
    target=local()/('chunk-'+str(index).zfill(4)+'.bin')
    with target.open('xb') as stream:stream.write(data)
    if sha(target.read_bytes())!=row['sha256']:raise ValueError('frame postcopy SHA')
    with target.with_suffix('.receipt.json').open('x',encoding='utf-8') as stream:json.dump({'index':index,'bytes':size,'sha256':row['sha256'],'transport_sha256':transport_sha},stream)
    print(json.dumps({'chunk_received':index,'bytes':size,'sha256':row['sha256']}))
def finish():
    obj=json.loads((local()/'plan.json').read_text());plan=obj['plan'];parts=[]
    for index in range(plan['chunks']):
        path=local()/('chunk-'+str(index).zfill(4)+'.bin');data=path.read_bytes();receipt=json.loads(path.with_suffix('.receipt.json').read_text())
        if sha(data)!=receipt['sha256'] or len(data)!=min(CHUNK,plan['archive_bytes']-index*CHUNK):raise ValueError('stored frame drift/gap')
        parts.append(data)
    raw=b''.join(parts)
    if len(raw)!=plan['archive_bytes'] or sha(raw)!=plan['archive_sha256']:raise ValueError('assembled archive exact SHA/size')
    rows=expected();binaries=zip_checked(raw,rows)
    with (local()/ARCHIVE).open('xb') as stream:stream.write(raw)
    # Reuse receiver01 ONLY LOCALLY; its unchanged canonical path/no-overwrite/text copy contracts apply.
    files=[{'path':name,**rows[name],'sha256_before':sha(data),'sha256_after':sha(data),
            'base64':base64.b64encode(data).decode('ascii')} for name,data in binaries.items()]
    payload={'kind':'SYNTHETIC_CPU_COLAB_BINARY_PRESERVATION_V1','root':ROOT_TEXT,'run_id':RUN_ID,
             'source_text_acceptance_sha256':TEXT_ACCEPTANCE_SHA,'total_raw_bytes':sum(map(len,binaries.values())),
             'files':files,'model_or_Parquet_loads':0,'remote_mutation':False,'zip_used':True}
    envelope=canonical({'payload':payload,'payload_sha256':sha(canonical(payload))})
    packet=local()/'local-receiver01-envelope.json'
    with packet.open('xb') as stream:stream.write(envelope)
    old_receiver()['receive'](packet)
    run=work().parents[3]/'experiments/akt/results'/RUN_ID;inventory=run/'transfer-copy-inventory.json'
    acceptance={'status':'PRESERVED_CHUNKED_CPU_DUMMY_BYTES','archive_sha256':sha(raw),'archive_bytes':len(raw),
                'chunks':plan['chunks'],'zip_crc_checked':True,'binary_files':4,'binary_raw_bytes':sum(map(len,binaries.values())),
                'canonical_inventory':str(inventory),'canonical_inventory_sha256':sha(inventory.read_bytes()),
                'model_or_Parquet_loads':0,'local_or_remote_fit_reruns':0,'original_receiver01_sha256':SOURCE01_SHA}
    with (local()/'acceptance.json').open('x',encoding='utf-8') as stream:json.dump(acceptance,stream,indent=2);stream.write('\n')
    print(json.dumps(acceptance))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('prepare-first','receive-first','prepare-chunks','receive-chunk','finish'))
    parser.add_argument('input_json',nargs='?',type=Path);args=parser.parse_args()
    if args.operation=='prepare-first':prepare_first()
    elif args.operation=='prepare-chunks':prepare_chunks()
    elif args.operation=='finish':finish()
    elif args.input_json is None:parser.error('explicit RPC JSON is required')
    elif args.operation=='receive-first':receive_first(args.input_json)
    else:receive_chunk(args.input_json)
