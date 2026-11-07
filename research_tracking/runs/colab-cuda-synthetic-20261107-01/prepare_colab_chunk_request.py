import json
from pathlib import Path

root=Path.cwd()
code='''# Chỉ đọc ZIP synthetic bất biến; mỗi lần tối đa200000bytes, không optimizer.
import base64, math
TRANSFER_CHUNK_SIZE=200000
if 'KLTN_TRANSFER_INDEX03' not in globals():KLTN_TRANSFER_INDEX03=0
assert archive_path.name=='akt-colab-results-b82b6de2333a4c5a85ef98491ad5c6b1.zip'
assert archive_path.stat().st_size==28657701
count=math.ceil(archive_path.stat().st_size/TRANSFER_CHUNK_SIZE)
assert count==144 and 0<=KLTN_TRANSFER_INDEX03<count
with archive_path.open('rb') as stream:
    stream.seek(KLTN_TRANSFER_INDEX03*TRANSFER_CHUNK_SIZE)
    chunk=stream.read(TRANSFER_CHUNK_SIZE)
print(json.dumps({'status':'SYNTHETIC_ARTIFACT_CHUNK03','index':KLTN_TRANSFER_INDEX03,'count':count,'bytes':len(chunk),'sha256':hashlib.sha256(chunk).hexdigest(),'archive_sha256':'64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188','base64':base64.b64encode(chunk).decode()}))
KLTN_TRANSFER_INDEX03+=1
'''
path=root/'artifacts/akt/colab/requests/add-artifact-chunks03.json'
path.write_text(json.dumps({'cellIndex':14,'language':'python','code':code}),encoding='utf-8')
print(json.dumps({'chunk_bytes':200000,'maximum_calls':144,'total_archive_bytes':28657701,'scope':'Transfer only; no new training, no paid service'}))
