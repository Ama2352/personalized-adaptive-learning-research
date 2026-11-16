"""Kiểm Drive thật bằng file tổng hợp ~1 MiB, tách hai process dừng/phục hồi."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent / 'real-probe'
SOURCE = ROOT / 'artifacts/akt/runtime/drive-upload-recovery-check-20261116-01/KLTN_UPLOAD_RECOVERY_CHECK_20261116'
PRIVATE = ROOT / 'artifacts/akt/private/drive-upload'
spec = importlib.util.spec_from_file_location('drive_upload', ROOT / 'scripts/akt/drive_resumable_upload.py')
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)


class ObservedSession:
    def __init__(self, session, stage):
        self.session = session
        self.stage = stage

    def request(self, method, url, **kwargs):
        response = self.session.request(method, url, **kwargs)
        if method == 'PUT':
            row = dict(stage=self.stage, status=response.status_code,
                       sent_range=kwargs.get('headers', {}).get('Content-Range'),
                       server_range=response.headers.get('Range'))
            HERE.mkdir(parents=True, exist_ok=True)
            with (HERE / 'NETWORK.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row) + '\n')
            if self.stage == 'interrupt' and kwargs.get('data') and response.status_code == 308:
                marker = dict(status='INTERRUPTED_AFTER_SERVER_ACK',
                              acknowledged_bytes=upload.checked_offset(response, 1048593),
                              note_vi='Process dừng sau server ack, trước khi client lưu offset chunk.')
                upload.atomic_json(HERE / 'INTERRUPTED.json', marker)
                raise KeyboardInterrupt
        return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['interrupt', 'resume'])
    args = parser.parse_args()
    if args.stage == 'interrupt':
        if (PRIVATE / 'probe-state.json').exists():
            raise RuntimeError('Lượt probe đã có state, cần rà trước khi tạo lại.')
        SOURCE.mkdir(parents=True, exist_ok=True)
        payload = bytes(range(256)) * 4096 + b'KLTN_RECOVERY_01!'
        assert len(payload) == 1048593
        (SOURCE / 'resume_probe.bin').write_bytes(payload)
        manifest = dict(files=[dict(upload_path='resume_probe.bin', bytes=len(payload),
                                    sha256=hashlib.sha256(payload).hexdigest())])
        upload.atomic_json(SOURCE / 'MANIFEST.json', manifest)
    elif not (HERE / 'INTERRUPTED.json').exists():
        raise RuntimeError('Chưa có dấu vết ngắt có chủ ý.')
    plan = upload.build_plan(SOURCE, '1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7', 'honguyenminhsang2005@gmail.com')
    plan_path = HERE / 'PLAN.json'
    if plan_path.exists() and upload.read_json(plan_path) != plan:
        raise RuntimeError('Kế hoạch probe đã đổi.')
    upload.atomic_json(plan_path, plan)
    credentials = Credentials.from_authorized_user_file(str(PRIVATE / 'token.json'), [upload.SCOPE])
    with upload.single_writer(PRIVATE / 'upload.lock'):
        try:
            with AuthorizedSession(credentials) as session:
                observed = ObservedSession(session, args.stage)
                worker = upload.Uploader(observed, plan, PRIVATE / 'probe-state.json', HERE,
                                         chunk_bytes=256 * 1024, retries=2)
                try:
                    worker.run()
                except KeyboardInterrupt:
                    if args.stage != 'interrupt' or not (HERE / 'INTERRUPTED.json').exists():
                        raise
                    print('Đã ngắt có chủ ý sau Drive nhận chunk. State đã giữ riêng trên D.')
                    return
        finally:
            upload.atomic_json(PRIVATE / 'token.json', json.loads(credentials.to_json()))
    if args.stage == 'interrupt':
        raise RuntimeError('Probe chưa ngắt được theo thiết kế.')
    marker = upload.read_json(HERE / 'INTERRUPTED.json')
    network = [json.loads(line) for line in (HERE / 'NETWORK.jsonl').read_text().splitlines()]
    sent = [row for row in network if row['stage'] == 'resume'
            and row['sent_range'] and not row['sent_range'].startswith('bytes */')]
    assert sent and sent[0]['sent_range'].startswith(f"bytes {marker['acknowledged_bytes']}-")
    result = dict(status='LIVE_RECOVERY_VERIFIED', interrupted_after_bytes=marker['acknowledged_bytes'],
                  first_resumed_range=sent[0]['sent_range'], files=2, probe_bytes=1048593,
                  validation_vi='Drive thật, hai process riêng, ngắt client có chủ ý sau server ack; checksum server khớp nguồn.',
                  limit_vi='Chưa thực hiện cắt kết nối mạng vật lý hoặc thử file hàng GB.')
    upload.atomic_json(HERE / 'RECOVERY_ACCEPTANCE.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        print(str(error))
        raise SystemExit(1)
    except Exception as error:
        print(f'Probe dừng do {type(error).__name__}, giữ state để kiểm.')
        raise SystemExit(1)
