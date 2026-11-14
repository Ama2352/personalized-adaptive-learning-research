"""Đọc receipt private, chỉ xuất trạng thái và hash artifact đã xác minh."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
current=json.loads((ROOT/'artifacts/akt/private/colab-bridge/current.json').read_text())
directory=ROOT/current['directory']
plan=json.loads((HERE/'upload-plan.json').read_text())
expected={row['index']:row for row in plan['chunks']}
received={};errors=[];events=[]
for path in sorted(directory.glob('result-*.json'),key=lambda value:value.stat().st_mtime_ns):
    payload=json.loads(path.read_text())
    if payload.get('is_error'):
        errors.append('MCP_CALL_ERROR')
    for output in (payload.get('structured_content') or {}).get('outputs',[]):
        if output.get('output_type')=='error':
            errors.append(dict(type=output.get('ename'),message=output.get('evalue')))
        text=output.get('text',[])
        if isinstance(text,list):text=''.join(text)
        for line in text.splitlines():
            try:record=json.loads(line)
            except (ValueError,TypeError):continue
            if not isinstance(record,dict):continue
            if record.get('phase')=='UPLOAD_CHUNK':
                row=expected[record['index']]
                assert record['sha256']==row['sha256'] and record['end']==row['offset']+row['bytes']
                received[record['index']]=record
            else:
                # Dữ liệu nhị phân tải về được kiểm riêng, không nhân đôi vào log.
                events.append({key:value for key,value in record.items() if key!='data'})
result=dict(received_chunks=len(received),last_chunk=max(received,default=-1),errors=errors,
            recent_events=events[-3:])
print(json.dumps(result))
if not (HERE/'MANIFEST.json').exists():
    (HERE/'mcp-verified-progress.json').write_text(json.dumps(result,indent=2)+'\n')
