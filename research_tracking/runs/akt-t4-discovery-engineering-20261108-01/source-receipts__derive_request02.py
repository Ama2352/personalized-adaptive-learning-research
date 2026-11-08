"""Sinh producer02 mới; giữ producer/request01 nguyên bytes, không dispatch."""
import ast,difflib,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent
old=W/'prepare_request01.py';raw=old.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)=='d625690ae6c9b9dad4436393ef1f7b771d5fac149e6b979a04c3bff1a203cc0c'
text=raw.decode().replace('c176c85ad5e93c6daf229f9f7f884b277aa11c1ae99a259389059292784d0b75','51c4b98053ba4eaac42b8c8be51ac29645c0b5fdcdf243b19d07c760a8a9db5f')
text=text.replace('discovery.py','discovery02.py').replace('cpu-readonly01','cpu-readonly02')
text=text.replace('cpu-discovery01-cell.py','cpu-discovery02-cell.py').replace('request-add-cpu-discovery01.json','request-add-cpu-discovery02.json').replace('request-contract01.json','request-contract02.json')
text=text.replace("result['inline_result_included']=True", "result['inline_result_included']='inline_result_text' in result")
needle="result['inline_result_included']='inline_result_text' in result"
addition="""for label in ('target.stdout','target.stderr'):
    p=ATTEMPT/label
    if p.is_file():
        with p.open('rb') as f:b=f.read(512*1024+1)
        row={'bytes_captured':len(b),'sha256_captured':sha(b),'capture_cap_exceeded':len(b)>512*1024}
        if len(b)<=4096:row['text']=b.decode('utf-8',errors='replace')
        result[label]=row
"""
assert text.count(needle)==1;text=text.replace(needle,addition+needle)
text=text.replace(".open('x',encoding='utf-8').write(code)",".open('x',encoding='utf-8',newline='\\n').write(code)")
ast.parse(text)
target=W/'prepare_request02.py';target.open('xb').write(text.encode());assert old.read_bytes()==raw
record={'status':'EXCLUSIVE_REQUEST_PRODUCER02_SOURCE_DERIVED_NOT_DISPATCHED','producer01_sha256_before_after':sha(raw),'producer02_sha256':sha(target.read_bytes()),'source02_sha256':'51c4b98053ba4eaac42b8c8be51ac29645c0b5fdcdf243b19d07c760a8a9db5f','profile_sha256_unchanged':'0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228','new_attempt':'cpu-readonly02','changes':['source02 pin/path','exclusive02 attempt/request/output','inline bounded target logs on failure/success','honest inline_result_included flag','LF cell file matches request code SHA'],'diff':''.join(difflib.unified_diff(raw.decode().splitlines(True),text.splitlines(True),fromfile='prepare_request01.py',tofile='prepare_request02.py'))}
(W/'request-producer02-copy-inventory.json').open('x',encoding='utf-8').write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='diff'}))
