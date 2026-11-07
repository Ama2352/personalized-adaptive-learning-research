"""Đối chiếu offline metadata/proposal; không resolver, install hoặc runtime import."""
from pathlib import Path
import email.parser
import hashlib
import html.parser
import json
import sys
from urllib.parse import urljoin, urldefrag, parse_qs

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.akt.config import load_config


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


proposal_path = ROOT / 'experiments/akt/configs/linux-cuda-runtime-proposal.json'
proposal = json.loads(proposal_path.read_text(encoding='utf-8'))
checks = []
for candidate, index_name, metadata_name in zip(proposal['candidate_wheels'],
        ('torch-cu126-index-02.html', 'triton-cu126-index-03.html'),
        ('torch-2.7.1-cu126-cp313.METADATA', 'triton-3.3.1-cp313.METADATA')):
    parser = Links()
    parser.feed((BASE / index_name).read_text(encoding='utf-8'))
    matches = [link for link in parser.links if urldefrag(urljoin(candidate['index_url'], link['href']))[0]
               == candidate['wheel_url']]
    assert len(matches) == 1
    link = matches[0]
    fragment = urldefrag(link['href'])[1]
    assert parse_qs(fragment)['sha256'][0] == candidate['sha256_from_official_index']
    for key in ('data-dist-info-metadata', 'data-core-metadata'):
        assert parse_qs(link[key])['sha256'][0] == sha(BASE / metadata_name) == candidate['metadata_sha256']
    parsed = email.parser.BytesParser().parsebytes((BASE / metadata_name).read_bytes())
    assert parsed['Name'] == candidate['name'] and parsed['Version'] == candidate['version']
    assert parsed.get_all('Requires-Dist', []) == candidate['requires_dist']
    assert candidate['wheel_downloaded'] is False and candidate['wheel_bytes_hash_verified'] is False
    checks.append({'name': candidate['name'], 'index_href_sha_verified': True,
                   'metadata_bytes_sha_verified': True, 'requires_dist_count': len(candidate['requires_dist'])})
receipts = [json.loads((BASE / f'fetch-{number:02d}.json').read_text(encoding='utf-8')) for number in (2, 3)]
requests = [request for receipt in receipts for request in receipt['requests']]
assert len(requests) == 4 and sum(item['bytes'] for item in requests) == 265132
for request in requests:
    assert request['bytes'] <= 1048576
    assert sha(BASE / request['saved_as']) == request['sha256']
    assert request['url'].endswith(('/', '.metadata'))
assert sum(item['bytes'] for item in requests) < 10485760
for name, record in proposal['local_input_inventory'].items():
    assert sha(ROOT / name) == record['sha256']
assert proposal['status'] == 'proposal_only' and proposal['lock_complete'] is False
assert proposal['execution_enabled'] is False and proposal['runnable_akt_config'] is False
assert proposal['actual_colab_v12_evidence']['torch'] == '2.14.1+cu130'
assert proposal['actual_colab_v12_evidence']['gate4_pass'] is False
assert proposal['candidate_profile']['torch_build_version'] == '2.7.1+cu126'
assert sum(req.startswith('nvidia-') for req in proposal['candidate_wheels'][0]['requires_dist']) == 14
try:
    load_config(proposal_path)
except TypeError as error:
    assert 'unexpected keyword argument' in str(error)
    rejection = str(error)
else:
    raise AssertionError('proposal was accepted as runnable AKTConfig')
assert 'torch' not in sys.modules and 'modal' not in sys.modules
result = {'status': 'PASS_OFFLINE_METADATA_CONSISTENCY_ONLY', 'checks': checks,
          'successful_http_responses': 4, 'metadata_response_bytes': 265132,
          'local_input_hashes_checked': len(proposal['local_input_inventory']),
          'proposal_sha256': sha(proposal_path), 'proposal_rejected_by_AKTConfig': rejection,
          'torch_modal_imported': False, 'resolver_install_model_gpu_cloud_executed': False,
          'lock_complete': False,
          'limits': ['Đây là consistency check local Windows, không phải Linux/GPU environment pass.',
                     'Wheel SHA mới đọc từ index; wheel bytes và full dependency closure chưa kiểm.']}
with (BASE / 'local-validation.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=True))
