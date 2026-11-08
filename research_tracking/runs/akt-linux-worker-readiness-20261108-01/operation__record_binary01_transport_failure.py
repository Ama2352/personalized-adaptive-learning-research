"""Chuẩn hóa tín hiệu lỗi WSS từ log riêng; không xuất raw log/nonce/secret."""
import hashlib,json
from pathlib import Path
w=Path(__file__).resolve().parent
p=w.parents[1]/'private/colab-bridge/session-a67c8207b6224b9398ad00cfa0876435/private-server.log'
raw=p.read_bytes();text=raw.decode('utf-8',errors='replace').lower()
signals={key:text.count(key) for key in ('1009','message too big','max_size')}
assert signals['1009']>=1 and signals['message too big']>=1 and signals['max_size']>=1
sha=lambda b:hashlib.sha256(b).hexdigest()
result={'status':'CONFIRMED_WSS_MESSAGE_SIZE_TRANSPORT_FAILURE_NOT_MODEL_FAILURE',
 'source_private_log_prefix_bytes':len(raw),'source_private_log_prefix_sha256':sha(raw),
 'normalized_signal_counts':signals,'raw_private_log_exported':False,
 'operation_source_sha256':sha((w/'cpu_worker_binary_preservation01.py').read_bytes()),
 'request_sha256':sha((w.parent/'requests/gpu09-add-cpu-worker-binary-export01.json').read_bytes()),
 'observed_client_timeout_and_disconnect':'Parent observed tool TimeoutError and connected=false after binary01; these client events are not raw server-log fields.',
 'scope_vi':'Lỗi transport khi xuất4binary cùngmộtJSON; worker/Gate/artifact gốc không chạy lại hoặc thay đổi. Sửa bằng8frame48KB/ZIPCRC/SHA, không tăng giới hạn WSS. Không xuất rawMCP/log/token.'}
with (w/'binary01-transport-failure-normalized.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
