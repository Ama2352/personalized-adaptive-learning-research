"""Sink artifact cloud-first: Volume bền vững, Drive kiểm SHA-256 từng file.

Root worker cấp Modal Volume.commit và OAuth qua Secret. Module không tạo
Modal resource hoặc ghi token. API có session-injection dành cho kiểm offline.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re

CORE_PATH=Path(__file__).with_name('drive_resumable_upload.py')
_spec=importlib.util.spec_from_file_location('kltn_drive_upload_core',CORE_PATH)
core=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)

DRIVE_ACCOUNT='honguyenminhsang2005@gmail.com'
DRIVE_PARENT='1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7'
TOKEN_ENV='KLTN_DRIVE_OAUTH_JSON'
CLOUD_ROOT=Path('/artifacts')


class ArtifactSinkError(RuntimeError):
    """Chỉ dùng thông báo kiểm soát được, giữ URI/OAuth ngoài log công khai."""


def _identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}',value):
        raise ArtifactSinkError('Tên run/tranche không hợp lệ.')
    return value


def _relative(value):
    if not isinstance(value,str) or '\\' in value:
        raise ArtifactSinkError('Artifact cần đường dẫn POSIX tương đối.')
    path=PurePosixPath(value)
    forbidden={'.drive-state','drive-evidence','private','.private','.git'}
    names={'client_secret.json','credentials.json','token.json','modal.toml','id_rsa','id_ed25519'}
    if (path.is_absolute() or not path.parts or '..' in path.parts or str(path)!=value
            or any(part.lower() in forbidden for part in path.parts)
            or path.name.lower() in names or path.name.lower().startswith('.env')):
        raise ArtifactSinkError('Artifact path nằm ngoài phạm vi payload được phép.')
    return path


def _physical(path):
    path=Path(path).absolute()
    for ancestor in (path,*path.parents):
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():
            raise ArtifactSinkError('Artifact/state path có alias, cần nguồn vật lý rõ ràng.')
    if path.resolve()!=path:
        raise ArtifactSinkError('Artifact/state path không canonical.')
    return path


def build_artifact_plan(source_root,files,*,run_id,tranche_id,max_total_bytes,max_files=256):
    """Pin đúng filelist rõ ràng; không glob private hoặc đòi MANIFEST archive cũ."""
    _identifier(run_id)
    _identifier(tranche_id)
    source=_physical(source_root)
    if (type(max_total_bytes) is not int or max_total_bytes<=0
            or type(max_files) is not int or not 1<=max_files<=256
            or not isinstance(files,(list,tuple)) or not 1<=len(files)<=max_files
            or not all(isinstance(name,str) for name in files)
            or len(set(files))!=len(files)):
        raise ArtifactSinkError('Cần filelist duy nhất và ngân sách byte/file hữu hạn.')
    rows=[]
    total=0
    for name in sorted(files):
        relative=_relative(name)
        path=_physical(source/relative)
        if not path.is_file() or not path.is_relative_to(source):
            raise ArtifactSinkError('Artifact source không phải file payload hợp lệ.')
        size=path.stat().st_size
        if size==0:
            raise ArtifactSinkError('Artifact rỗng cần biểu diễn trong manifest trước khi dùng sink này.')
        total+=size
        if total>max_total_bytes:
            raise ArtifactSinkError('Artifact batch vượt ngân sách byte.')
        info=core.hashes(path)
        rows.append(dict(path=relative.as_posix(),**info))
    return dict(kind='KLTN_CLOUD_ARTIFACT_PLAN_V1',source=str(source),files=rows,bytes=total,
                run_id=run_id,tranche_id=tranche_id,folder_name=tranche_id,
                parent_id=DRIVE_PARENT,account=DRIVE_ACCOUNT)


def content_plan(plan):
    """Identity payload giữ theo byte; mtime chỉ phục vụ kiểm file đang đọc."""
    return dict(plan,files=[{key:value for key,value in row.items() if key!='mtime_ns'}
                            for row in plan['files']])


class DurableDriveUploader(core.Uploader):
    def __init__(self,*args,volume_commit,**kwargs):
        if not callable(volume_commit):
            raise ArtifactSinkError('Cần callback commit Volume bền vững.')
        self.volume_commit=volume_commit
        super().__init__(*args,**kwargs)
        if self.plan['parent_id']!=DRIVE_PARENT or self.plan['account']!=DRIVE_ACCOUNT:
            raise ArtifactSinkError('Đích Drive phải giữ tài khoản và parent KLTN đã chốt.')

    def save(self):
        super().save()
        self.volume_commit()

    def event(self,action,**fields):
        super().event(action,**fields)
        self.volume_commit()

    def complete(self,relative,entry,meta,row,parent):
        if not self.matches(meta,row,parent) or meta.get('sha256Checksum')!=row['sha256']:
            entry['strict_verified']=False
            self.save()
            raise ArtifactSinkError('Drive chưa xác nhận SHA-256 đúng của artifact.')
        entry['strict_verified']=True
        entry['strict_parent_id']=parent
        super().complete(relative,entry,meta,row,parent)

    def send_file(self,row,parent):
        # Cùng namespace/tranche là snapshot bất biến, không tạo bản cùng tên
        # khác nội dung khi phát hiện conflict từ một lượt trước hoặc writer khác.
        entry=self.state['files'].setdefault(row['path'],{})
        if 'remote_id' not in entry:
            candidates=self.children(parent,Path(row['path']).name)
            if candidates:
                if len(candidates)!=1 or not self.matches(candidates[0],row,parent):
                    raise ArtifactSinkError('Drive artifact path có nội dung xung đột hoặc trùng tên.')
                entry['remote_id']=candidates[0]['id']
                self.save()
        super().send_file(row,parent)

    def run(self,login_only=False):
        self.state['strict_batch_verified']=False
        self.save()
        super().run(login_only=True)
        if login_only:
            return None
        run_parent=self.folder('namespace/run',DRIVE_PARENT,self.plan['run_id'])
        tranche_parent=self.folder('namespace/tranche',run_parent,self.plan['tranche_id'])
        for row in self.plan['files']:
            parent=tranche_parent
            current=PurePosixPath()
            for part in PurePosixPath(row['path']).parent.parts:
                current/=part
                parent=self.folder('payload/'+current.as_posix(),parent,part)
            self.send_file(row,parent)
        receipts=[]
        for row in self.plan['files']:
            entry=self.state['files'][row['path']]
            meta=self.metadata(entry['remote_id'])
            if (not entry.get('strict_verified') or not entry.get('complete')
                    or not self.matches(meta,row,entry['strict_parent_id'])
                    or meta.get('sha256Checksum')!=row['sha256']):
                entry['strict_verified']=False
                self.save()
                raise ArtifactSinkError('Drive strict readback chưa khớp toàn batch.')
            receipts.append(dict(path=row['path'],file_id=meta['id'],bytes=row['bytes'],sha256=row['sha256']))
        self.state['strict_batch_verified']=True
        self.save()
        result=dict(status='DRIVE_SHA256_VERIFIED',run_id=self.plan['run_id'],tranche_id=self.plan['tranche_id'],
                    account=DRIVE_ACCOUNT,parent_id=DRIVE_PARENT,folder_id=tranche_parent,
                    plan_identity=hashlib.sha256(json.dumps(content_plan(self.plan),sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                    files=receipts,bytes=self.plan['bytes'],verified_at=core.now())
        core.atomic_json(self.evidence/'STRICT_ACCEPTANCE.json',result)
        self.volume_commit()
        self.event('STRICT_BATCH_VERIFIED',files=len(receipts),bytes=self.plan['bytes'],folder_id=tranche_parent)
        return result


def publish_with_session(session,*,source_root,files,run_id,tranche_id,volume_commit,max_total_bytes,
                         cloud_root=CLOUD_ROOT,chunk_bytes=32*1024**2,retries=6,sleep=core.time.sleep,
                         lock_root=None):
    """Worker có session sẵn hoặc fake test, state/evidence chỉ dưới cloudroot."""
    base=_physical(cloud_root)
    batch=_physical(base/_identifier(run_id)/_identifier(tranche_id))
    private=_physical(batch/'.drive-state')
    evidence=_physical(batch/'drive-evidence')
    private.mkdir(parents=True,exist_ok=True)
    if os.name!='nt':
        private.chmod(0o700)
    # Volume không có distributed locks. Root serialize một writer/tranche;
    # khóa scratch này chỉ ngăn hai process trong cùng container.
    if lock_root is None:
        lock_root=Path('/tmp/kltn-drive-locks') if os.name=='posix' else private
    lock_path=Path(lock_root)/(hashlib.sha256(str(batch).encode()).hexdigest()+'.lock')
    with core.single_writer(lock_path):
        plan=build_artifact_plan(source_root,files,run_id=run_id,tranche_id=tranche_id,max_total_bytes=max_total_bytes)
        source=Path(plan['source'])
        if not source.is_relative_to(base) and not source.is_relative_to(Path('/tmp').resolve()):
            raise ArtifactSinkError('Payload cần nằm trên Volume hoặc cloud scratch /tmp.')
        if (source.is_relative_to(private) or source.is_relative_to(evidence)
                or any((source/row['path']).is_relative_to(private) or (source/row['path']).is_relative_to(evidence)
                       for row in plan['files'])):
            raise ArtifactSinkError('Private state/evidence không phải payload source.')
        plan_path=batch/'ARTIFACT_PLAN.json'
        immutable_plan=content_plan(plan)
        if plan_path.exists():
            if core.read_json(plan_path)!=immutable_plan:
                raise ArtifactSinkError('Plan tranche đã có và thay đổi. Giữ tranche cũ, cần snapshot mới.')
        else:
            core.atomic_json(plan_path,immutable_plan)
        volume_commit()
        state_path=private/'state.json'
        metadata_rebound=False
        if state_path.exists():
            state=core.read_json(state_path)
            if content_plan(state['plan'])!=immutable_plan:
                raise ArtifactSinkError('State tranche không khớp content plan bất biến.')
            if state['plan']!=plan:
                # build_artifact_plan đã hash lại toàn file. Chỉ metadata mtime
                # khác sau remount/restage mới được gắn lại, giữ URI/offset cũ.
                state['plan']=plan
                for entry in state['files'].values():
                    entry.pop('local',None)
                state['strict_batch_verified']=False
                core.atomic_json(state_path,state)
                volume_commit()
                metadata_rebound=True
        uploader=DurableDriveUploader(session,plan,state_path,evidence,
            volume_commit=volume_commit,chunk_bytes=chunk_bytes,retries=retries,sleep=sleep)
        if metadata_rebound:
            uploader.event('SOURCE_METADATA_REBOUND_AFTER_CONTENT_REHASH')
        result=uploader.run()
        result['plan_sha256']=hashlib.sha256(plan_path.read_bytes()).hexdigest()
        result['receipt_sha256']=hashlib.sha256((evidence/'STRICT_ACCEPTANCE.json').read_bytes()).hexdigest()
        return result


def publish_from_environment(*,source_root,files,run_id,tranche_id,volume_commit,max_total_bytes,
                             chunk_bytes=32*1024**2,retries=6):
    """Entrypoint CPU Linux cloud, OAuth chỉ đọc Secret env, return ID/SHA nhỏ."""
    if platform.system()!='Linux' or not CLOUD_ROOT.is_dir():
        raise ArtifactSinkError('Sink này cần Linux cloud worker và Volume /artifacts.')
    try:
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2.credentials import Credentials
        raw=os.environ.get(TOKEN_ENV)
        info=json.loads(raw) if raw else None
        if (not isinstance(info,dict) or not all(info.get(k) for k in ('client_id','client_secret','refresh_token'))
                or info.get('token_uri','https://oauth2.googleapis.com/token')!='https://oauth2.googleapis.com/token'):
            raise ArtifactSinkError('Drive OAuth Secret chưa hợp lệ.')
        credentials=Credentials.from_authorized_user_info(info,[core.SCOPE])
        with AuthorizedSession(credentials) as session:
            return publish_with_session(session,source_root=source_root,files=files,run_id=run_id,
                tranche_id=tranche_id,volume_commit=volume_commit,max_total_bytes=max_total_bytes,
                chunk_bytes=chunk_bytes,retries=retries,cloud_root=CLOUD_ROOT)
    except ArtifactSinkError:
        raise
    except Exception as error:
        raise ArtifactSinkError(f'Drive sink dừng do {type(error).__name__}; state remote được giữ để tiếp tục.') from None
