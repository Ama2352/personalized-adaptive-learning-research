"""Lập chỉ mục Drive và lấy JSON fit nhỏ, không tải raw/model/predictions."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
ACCOUNT = 'honguyenminhsang2005@gmail.com'
PARENT = '1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7'
RUN = 'junyi-calibration-real-20261117-01'
API = 'https://www.googleapis.com/drive/v3'
FOLDER = 'application/vnd.google-apps.folder'
MAX_FILE = 256*1024
MAX_TOTAL = 2*1024**2
NAMES = {'COMPLETE.json':'COMPLETE', 'config.json':'CONFIG', 'resource.json':'RESOURCE',
         'fit/temperature.json':'TEMPERATURE', 'fit/manifest.json':'FIT_MANIFEST'}
INDEX_ONLY = {'config.json', 'fit/manifest.json'}


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class MetadataDrive:
    def __init__(self, session):
        self.session = session
        self.downloaded = 0

    def get(self, path, **kwargs):
        response = self.session.get(API+path, timeout=30, allow_redirects=False, **kwargs)
        if response.status_code != 200:
            raise RuntimeError('Drive metadata request failed')
        return response

    def children(self, parent, name):
        rows, token = [], None
        while True:
            params = dict(q=f"'{parent}' in parents and name = '{name}' and trashed = false",
                fields='nextPageToken,files(id,name,mimeType,parents,size,sha256Checksum)', pageSize=100)
            if token:
                params['pageToken'] = token
            data = self.get('/files', params=params).json()
            rows.extend(data.get('files', []))
            token = data.get('nextPageToken')
            if not token:
                return rows

    def folder(self, parent, name):
        matches = self.children(parent, name)
        if not matches:
            return None
        if len(matches) != 1 or matches[0].get('mimeType') != FOLDER or parent not in matches[0]['parents']:
            raise ValueError('Ambiguous or foreign calibration folder')
        return matches[0]['id']

    def locate(self, parent, relative):
        parts = relative.split('/')
        for directory in parts[:-1]:
            parent = self.folder(parent, directory)
            if parent is None:
                return None
        matches = self.children(parent, parts[-1])
        if not matches:
            return None
        if len(matches) != 1 or parent not in matches[0]['parents']:
            raise ValueError('Ambiguous or foreign calibration metadata')
        return matches[0]

    def fetch(self, row, target):
        size = int(row.get('size', -1))
        if not 0 < size <= MAX_FILE or not row.get('sha256Checksum'):
            raise ValueError('Calibration JSON requires bounded size and server SHA')
        target = Path(target)
        if target.exists():
            raw = target.read_bytes()
        else:
            if self.downloaded+size > MAX_TOTAL:
                raise ValueError('Calibration metadata download budget exceeded')
            response = self.get('/files/'+row['id'], params={'alt':'media'}, stream=True)
            raw = b''
            try:
                for block in response.iter_content(4096):
                    raw += block
                    if len(raw) > size:
                        raise ValueError('Calibration JSON exceeded server byte pin')
            finally:
                response.close()
            self.downloaded += len(raw)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != row['sha256Checksum']:
            raise ValueError('Calibration JSON content SHA/byte mismatch')
        payload = json.loads(raw)
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(raw)
        return payload, dict(file_id=row['id'], bytes=size, sha256=row['sha256Checksum'],
                             local_file=target.name, drive_url='https://drive.google.com/file/d/'+row['id']+'/view')


def index_variants(session, output, variants=('A0','A1','A2','A3'), expected=None,
                   tranche_overrides=None, publication_receipts=None):
    tranche_overrides = {} if tranche_overrides is None else tranche_overrides
    publication_receipts = {} if publication_receipts is None else publication_receipts
    if not set(tranche_overrides) <= set(variants) or not set(publication_receipts) <= set(variants):
        raise ValueError('Tranche overrides require explicitly requested variants')
    drive = MetadataDrive(session)
    about = drive.get('/about', params={'fields':'user(emailAddress)'}).json()
    if about['user']['emailAddress'].lower() != ACCOUNT:
        raise ValueError('Calibration Drive account mismatch')
    run_folder = drive.folder(PARENT, RUN)
    results = []
    for variant in variants:
        if variant not in ('A0','A1','A2','A3'):
            raise ValueError('Explicit A0-A3 metadata only')
        tranche = tranche_overrides.get(variant, f'{variant.lower()}-fit-calibration-{variant.lower()}-join-20261117-01')
        if (not isinstance(tranche,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}',tranche)
                or not tranche.startswith(variant.lower()+'-fit-')):
            raise ValueError('Explicit same-variant fit tranche required')
        publication = publication_receipts.get(variant)
        if publication is not None and (publication['status'] != 'DRIVE_SHA256_VERIFIED'
                or publication['account'] != ACCOUNT or publication['parent_id'] != PARENT
                or publication['run_id'] != RUN or publication['tranche_id'] != tranche):
            raise ValueError('Frozen stage publication receipt mismatch')
        folder = None if run_folder is None else drive.folder(run_folder, tranche)
        complete_row = None if folder is None else drive.locate(folder, 'COMPLETE.json')
        if complete_row is None:
            results.append(dict(variant=variant, tranche=tranche, status='FIT_METADATA_NOT_PUBLISHED_YET'))
            continue
        if publication is not None and publication['folder_id'] != folder:
            raise ValueError('Drive folder differs from frozen publication receipt')
        payloads, files = {}, {}
        for relative, label in NAMES.items():
            row = complete_row if relative == 'COMPLETE.json' else drive.locate(folder, relative)
            if row is None:
                raise ValueError('Published calibration COMPLETE has missing metadata')
            if relative in INDEX_ONLY:
                size = int(row.get('size',-1))
                if size <= 0 or not row.get('sha256Checksum'):
                    raise ValueError('Index-only calibration metadata requires server SHA/byte')
                files[relative] = dict(file_id=row['id'],bytes=size,sha256=row['sha256Checksum'],
                    local_file=None,index_only=True,drive_url='https://drive.google.com/file/d/'+row['id']+'/view')
                continue
            payloads[relative], files[relative] = drive.fetch(row, Path(output)/f'{variant}_CALIBRATION_{label}01.json')
        if publication is not None:
            pins = {row['path']:row for row in publication['files']}
            if len(pins) != len(publication['files']) or set(pins) != set(NAMES):
                raise ValueError('Exact five-file calibration publication required')
            if any(files[name]['file_id'] != pin['file_id']
                   or any(files[name][field] != pin[field] for field in ('bytes','sha256'))
                   for name,pin in pins.items()):
                raise ValueError('Drive metadata differs from frozen stage publication')
        complete, temperature = payloads['COMPLETE.json'], payloads['fit/temperature.json']
        if (complete['status'] != 'JUNYI_CLOUD_CPU_CALIBRATION_FIT_COMPLETE'
                or complete['total_targets'] != 1621484 or complete['supported_targets'] != 1621484
                or temperature['total_targets'] != complete['total_targets']
                or temperature['supported_targets'] != complete['supported_targets']
                or complete['calibration_identity'] != identity(temperature)
                or temperature['binding']['model_id'] != variant+'_JUNYI_REFIT'
                or temperature['status'] != 'fitted_response_temperature'):
            raise ValueError('Calibration completion/temperature identity mismatch')
        if (temperature['recipe'] != 'response-temperature-reference-v1'
                or temperature['clip'] != 1e-6 or temperature['temperature_bounds'] != [.05,20.]
                or not math.isfinite(temperature['temperature']) or not .05 <= temperature['temperature'] <= 20.
                or not 0 < temperature['objective_evaluations'] <= 200
                or temperature['class_counts'] != [277836,1343648]
                or not all(math.isfinite(temperature[key]) and temperature[key] >= 0
                           for key in ('raw_log_loss','calibrated_log_loss'))
                or temperature['calibrated_log_loss'] > temperature['raw_log_loss']+1e-12):
            raise ValueError('Calibration V1 bounds or objective mismatch')
        for relative, pin in complete['files'].items():
            if relative not in files or any(files[relative][key] != pin[key] for key in ('bytes','sha256')):
                raise ValueError('Calibration COMPLETE inventory mismatch')
        if payloads['resource.json']['device'] != 'cpu':
            raise ValueError('Calibration fit resource device mismatch')
        if expected is not None:
            pin = expected[variant]
            if (any(temperature['binding'].get(key) != value for key,value in pin['binding'].items())
                    or ('calibration_identity' in pin and pin['calibration_identity'] != complete['calibration_identity'])):
                raise ValueError('Calibration metadata differs from frozen request/export')
        results.append(dict(variant=variant, status='CALIBRATION_DRIVE_METADATA_VERIFIED', tranche=tranche,
            folder_id=folder, folder_url='https://drive.google.com/drive/folders/'+folder, files=files,
            calibration_identity=complete['calibration_identity'], temperature=temperature['temperature'],
            targets=temperature['total_targets'], raw_log_loss=temperature['raw_log_loss'],
            calibrated_log_loss=temperature['calibrated_log_loss'],
            expected_population_identity=None if expected is None else expected[variant]['population_identity'],
            large_metadata_content_downloaded=False,
            cpu_fit_seconds=payloads['resource.json']['wall_seconds']))
    return dict(status='CALIBRATION_METADATA_INDEX', account=ACCOUNT, parent_id=PARENT, run_folder_id=run_folder,
        checked_at=datetime.now(timezone.utc).isoformat(), variants=results, downloaded_bytes=drive.downloaded,
        limits_vi='Log Loss trước/sau đo trên calibration đã dùng fit T, chưa phải đánh giá độc lập.')


def expected_local_bindings(variants):
    population_path = ROOT/'research_tracking/runs/junyi-calibration-data-20261117-01/POPULATION.json'
    population = json.loads(population_path.read_text())
    result = {}
    for variant in variants:
        request = json.loads((BUNDLE/f'REQUEST_{variant}_GPU01.json').read_text())
        index_path = ROOT/f'experiments/akt/results/model-export-{variant.lower()}-refit-20261114-01/MODEL_INDEX.json'
        if (hashlib.sha256(index_path.read_bytes()).hexdigest() != request['exports'][variant]['sha256']
                or hashlib.sha256(population_path.read_bytes()).hexdigest() != request['population']['sha256']):
            raise ValueError('Frozen metadata input pin mismatch')
        index = json.loads(index_path.read_text())
        support = index_path.parent/'SUPPORT.zip'
        if hashlib.sha256(support.read_bytes()).hexdigest() != index['support_sha256']:
            raise ValueError('Frozen encoding support archive pin mismatch')
        with zipfile.ZipFile(support) as archive:
            if archive.getinfo('inputs/encoding90.json').file_size > 1024**2:
                raise ValueError('Encoding metadata cap exceeded')
            values = json.loads(archive.read('inputs/encoding90.json'))['values']
        result[variant] = dict(binding=dict(model_id=variant+'_JUNYI_REFIT',
            checkpoint_sha256=index['checkpoint_sha256'],vocabulary_sha256=index['identity']['encoding'],
            split_sha256=population['roles_identity'],
            bank_sha256=identity(dict(domain='junyi_exercises',values=values)),
            reference_sha256=identity(dict(domain='junyi_logged_response',reference_bank='not_applicable')),
            model_source_sha256=request['source_identity'],
            domain_sha256=request['data_paths']['canonical']['sha256']),
            population_identity=population['identity'],source_pins=request['source_pins'])
    return result



def stage_publications(entries, expected, variants):
    """Lấy tranche/pins từ stage result local đã lưu, không tạo cloud calls."""
    tranches, publications = {}, {}
    for variant, filename in entries:
        if variant not in variants or variant in publications:
            raise ValueError('One stage result per requested variant required')
        path = Path(filename)
        if path.stat().st_size > 1024**2:
            raise ValueError('Small stage result required')
        document = json.loads(path.read_text(encoding='utf-8'))
        if document['status'] != 'STAGE_COMMITTED':
            raise ValueError('Completed stage result required')
        rows = [row for row in document['result']['publish_receipts']
                if row['tranche_id'].startswith(variant.lower()+'-fit-')]
        if len(rows) != 1:
            raise ValueError('One fit publication in frozen stage result required')
        publications[variant] = rows[0]
        tranches[variant] = rows[0]['tranche_id']
        expected[variant]['calibration_identity'] = document['result']['calibration_identity']
    return tranches, publications


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--variants', nargs='+', choices=['A0','A1','A2','A3'], default=['A0','A1','A2','A3'])
    parser.add_argument('--stage-result', action='append', default=[], metavar='A0=PATH')
    args = parser.parse_args()
    if args.output.resolve().parent != BUNDLE or args.output.exists():
        parser.error('New metadata index required inside current run bundle')
    credentials = Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'),
        ['https://www.googleapis.com/auth/drive'])
    expected = expected_local_bindings(args.variants)
    entries = [entry.split('=',1) for entry in args.stage_result]
    if any(len(entry) != 2 for entry in entries):
        parser.error('Stage result format is VARIANT=PATH')
    tranches, publications = stage_publications(entries, expected, args.variants)
    with AuthorizedSession(credentials) as session:
        result = index_variants(session, BUNDLE, args.variants, expected,
                                tranche_overrides=tranches, publication_receipts=publications)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(dict(index=str(args.output), statuses={r['variant']:r['status'] for r in result['variants']},
                         downloaded_bytes=result['downloaded_bytes'])))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit('Calibration metadata retrieval stopped: '+type(error).__name__) from None
