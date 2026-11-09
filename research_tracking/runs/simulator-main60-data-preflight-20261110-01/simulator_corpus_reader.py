"""Đọc public corpus V1, tái dựng observable types; không execution authority.

Chỉ9modelinputfiles + DONE, không oracle/final/source paths từ metadata. Reader
không import publisher/collector/AKT/Torch/NumPy và không gọi generator/model.
SHA/provenance kiểm consistency hợp tác; current source/Gate và model admission
thuộc research entry riêng. DONE logical, không chống adversarial/crash races.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import time

from .simulator_bridge import SimulatorBank, SimulatorItem, identity_hash
from .simulator_data import ObservableTrajectory
from .simulator_research_data import (DEVELOPMENT_ROLES, PROTOCOL_ID, ResearchSplitPlan,
    ResearchProvenance, ShardLimits, audit_research_shard)

ROOT=Path(__file__).resolve().parents[2]
PUBLIC_FILES=('corpus.json','bank.json','plan.json','train.jsonl','train.manifest.json',
              'selection.jsonl','selection.manifest.json','calibration.jsonl','calibration.manifest.json')
SOURCE_ROW_STRIDE=1000000  # Public V1 collector address formula; not horizon/default.
COLLECTOR_PATH='src/knowledge_tracing/simulator_research_collection.py'


def _require(ok,message):
    if not ok:raise ValueError(message)


def _sha(value):
    _require(type(value) is str and re.fullmatch('[0-9a-f]{64}',value),'lowercase SHA256 required')


def _text(value):
    _require(type(value) is str and bool(value.strip()),'nonempty identifier required')


def _same(left,right):
    return identity_hash(left)==identity_hash(right)


def _json(raw):
    def unique(pairs):
        result={}
        for key,value in pairs:
            _require(key not in result,'duplicate JSON key')
            result[key]=value
        return result
    def bad_constant(value):raise ValueError('nonfinite JSON constant: '+value)
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=bad_constant)
    _require(type(value) is dict,'JSON object required')
    return value


def _sealed(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def _alias(path):
    return path.is_symlink() or getattr(path,'is_junction',lambda:False)()


def _path(corpus_id,name=None):
    _require(type(corpus_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}',corpus_id),'safe corpus ID required')
    _require(name is None or name in (*PUBLIC_FILES,'DONE.json','failure.json'),'fixed public filename required')
    _require(ROOT.is_dir() and not _alias(ROOT) and ROOT.resolve()==ROOT.absolute(),'physical fixed ROOT required')
    cursor=ROOT
    parts=('artifacts','simulator','corpora',corpus_id)+(() if name is None else (name,))
    for part in parts:
        cursor=cursor/part
        _require(not _alias(cursor),'corpus path symlink/junction forbidden')
    return cursor


@dataclass(frozen=True)
class CorpusReadLimits:
    max_file_bytes: int
    max_total_bytes: int
    max_line_bytes: int
    max_trajectories_per_role: int
    max_events_per_learner: int
    max_total_events: int
    max_wall_seconds: float

    def __post_init__(self):
        for name,value in asdict(self).items():
            if name=='max_wall_seconds':
                _require(type(value) in (int,float) and math.isfinite(value) and 0<value<=600,'explicit finite read wall limit required')
            else:_require(type(value) is int and 0<value<2**63,'explicit positive read byte/count limit required')
        _require(self.max_line_bytes<=self.max_file_bytes<=self.max_total_bytes,'line/file/total limits inconsistent')

    @property
    def shard_limits(self):
        return ShardLimits(self.max_trajectories_per_role,self.max_events_per_learner,self.max_total_events)


@dataclass(frozen=True)
class PublicRoleData:
    role: str
    provenance: ResearchProvenance
    trajectories: tuple[ObservableTrajectory,...]
    manifest_json: str
    audit_json: str
    class_counts: tuple[int,int]

    @property
    def manifest(self):return json.loads(self.manifest_json)

    @property
    def audit(self):return json.loads(self.audit_json)

    @property
    def reference_complete(self):return self.audit['reference_complete']

    @property
    def two_class_support(self):return min(self.class_counts)>0


@dataclass(frozen=True)
class PublicResearchCorpus:
    corpus_id: str
    plan: ResearchSplitPlan
    bank: SimulatorBank
    roles: tuple[PublicRoleData,...]
    corpus_manifest_json: str
    files_sha256: tuple[tuple[str,str,int],...]
    done_sha256: str
    source_bindings: tuple[tuple[str,str],...]
    limits: CorpusReadLimits
    input_bytes: int
    elapsed_seconds: float
    content_sha256: str

    @property
    def manifest(self):return json.loads(self.corpus_manifest_json)

    def role_data(self,role):
        _require(role in DEVELOPMENT_ROLES,'final/unknown role events are not loaded')
        return next(value for value in self.roles if value.role==role)

    def _payload(self):
        return dict(corpus_id=self.corpus_id,plan=asdict(self.plan),bank=asdict(self.bank),
            roles=[asdict(r) for r in self.roles],corpus_manifest_json=self.corpus_manifest_json,
            files_sha256=self.files_sha256,done_sha256=self.done_sha256,source_bindings=self.source_bindings)

    def assert_integrity(self):
        _require(identity_hash(self._payload())==self.content_sha256,'loaded observable result changed')

    @property
    def identity(self):
        self.assert_integrity();return self.content_sha256


class _Read:
    def __init__(self,corpus_id,limits):
        self.corpus_id,self.limits=corpus_id,limits
        self.start,self.wall=time.monotonic(),time.time()
        self.records={};self.total=0;self.events=0

    def guard(self):
        _require(max(time.monotonic()-self.start,time.time()-self.wall)<=self.limits.max_wall_seconds,'reader wall limit exceeded')
        _require(not _path(self.corpus_id,'failure.json').exists(),'failed/partial corpus cannot be consumed')

    def open(self,name):
        self.guard();path=_path(self.corpus_id,name)
        _require(path.is_file(),'regular public file required')
        s=path.stat();_require(s.st_size<=self.limits.max_file_bytes,'public file byte limit exceeded')
        _require(self.total+s.st_size<=self.limits.max_total_bytes,'total public input byte limit exceeded')
        return path,(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)

    def commit(self,name,path,before,digest,size):
        s=path.stat();after=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
        _require(not _alias(path) and before==after and size==s.st_size,'public input changed during read')
        _require(name not in self.records,'duplicate public file read')
        self.records[name]=(digest,size,before);self.total+=size;self.guard()

    def metadata(self,name):
        path,before=self.open(name);parts=[];digest=hashlib.sha256();size=0
        with path.open('rb') as stream:
            while chunk:=stream.read(65536):
                size+=len(chunk);_require(size<=self.limits.max_file_bytes and self.total+size<=self.limits.max_total_bytes,'growing metadata byte limit')
                parts.append(chunk);digest.update(chunk);self.guard()
        self.commit(name,path,before,digest.hexdigest(),size)
        return _json(b''.join(parts))

    def trajectories(self,name):
        path,before=self.open(name);digest=hashlib.sha256();size=0;result=[];events=0
        with path.open('rb') as stream:
            while raw:=stream.readline(self.limits.max_line_bytes+1):
                _require(len(raw)<=self.limits.max_line_bytes,'JSONL line byte limit exceeded')
                size+=len(raw);_require(size<=self.limits.max_file_bytes and self.total+size<=self.limits.max_total_bytes,'growing JSONL byte limit')
                _require(len(result)<self.limits.max_trajectories_per_role,'JSONL trajectory count limit exceeded')
                payload=_json(raw);observations=payload.get('observations')
                _require(type(observations) is list and 0<len(observations)<=self.limits.max_events_per_learner,'JSONL event count/schema limit')
                events+=len(observations);_require(events<=self.limits.max_total_events,'role event limit exceeded')
                self.events+=len(observations);_require(self.events<=self.limits.max_total_events,'whole corpus event limit exceeded before constructing records')
                result.append(ObservableTrajectory.from_payload(payload));digest.update(raw);self.guard()
        self.commit(name,path,before,digest.hexdigest(),size)
        return tuple(result)

    def check_hash(self,name,expected):
        _sha(expected);_require(self.records[name][0]==expected,'public input raw SHA mismatch: '+name)

    def verify_after(self):
        self.guard()
        _require(set(self.records)==set(PUBLIC_FILES)|{'DONE.json'},'incomplete fixed public input population')
        for name,(expected,size,before) in self.records.items():
            path=_path(self.corpus_id,name);s=path.stat()
            _require((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==before,'public input metadata changed after parse')
            digest=hashlib.sha256();count=0
            with path.open('rb') as stream:
                while chunk:=stream.read(65536):
                    count+=len(chunk);_require(count<=size,'public input grew after parse')
                    digest.update(chunk);self.guard()
            _require(count==size and digest.hexdigest()==expected,'public input changed after parse')
            s=path.stat();_require((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==before,'public input changed during final verification')
        self.guard()


def _descriptor(value):
    keys={'schema_version','domain','no_junyi_fold','protocol_id','protocol_sha256','bank_sha256','domain_sha256',
          'plan_sha256','research_plan_sha256','environment_graph_sha256','normalized_recipe','normalized_recipe_sha256',
          'source_inventory','roles'}
    _require(set(value)==keys and type(value['schema_version']) is int and value['schema_version']==1
             and value['domain']=='simulator' and value['no_junyi_fold'] is True,'closed simulator corpus schema required')
    _require(value['protocol_id']==PROTOCOL_ID,'unsupported research protocol')
    for k in ('protocol_sha256','bank_sha256','domain_sha256','plan_sha256','research_plan_sha256','environment_graph_sha256','normalized_recipe_sha256'):_sha(value[k])
    recipe=value['normalized_recipe']
    _require(type(recipe) is dict and set(recipe)=={'collector_version','policy','events_per_learner','start_unix_seconds','gap_seconds','timestamp_unit','timezone'},'normalized recipe schema')
    _text(recipe['collector_version']);_text(recipe['policy'])
    _require(type(recipe['events_per_learner']) is int and recipe['events_per_learner']>0
             and type(recipe['gap_seconds']) is int and recipe['gap_seconds']>0
             and type(recipe['start_unix_seconds']) is int and recipe['start_unix_seconds']>=0
             and recipe['timestamp_unit']=='unix_seconds_utc' and recipe['timezone']=='UTC'
             and identity_hash(recipe)==value['normalized_recipe_sha256'],'recipe/clock identity mismatch')
    _require(recipe['events_per_learner']<=SOURCE_ROW_STRIDE
             and recipe['start_unix_seconds']+recipe['events_per_learner']*recipe['gap_seconds']<2**63,
             'recipe exceeds V1 source-row slots or signed clock representation')
    sources=value['source_inventory'];_require(type(sources) is dict and sources,'source bindings required')
    for name,digest in sources.items():
        _text(name);_sha(digest);p=PurePosixPath(name)
        _require('\\' not in name and ':' not in name and not p.is_absolute() and p.parts
                 and p.as_posix()==name and '..' not in p.parts,'source binding must be relative; never opened')
    _require(type(value['roles']) is dict and set(value['roles'])==set(DEVELOPMENT_ROLES),'development roles only; no final input')


def _typed_plan(value,corpus):
    _require(set(value)=={'schema_version','recipe','manifest'} and type(value['schema_version']) is int
             and value['schema_version']==1 and type(value['recipe']) is dict,'restartable plan schema required')
    _require(set(value['recipe'])=={'namespace','root_seed','development_learners','final_learners','protocol_sha256'},'plan constructor fields required')
    plan=ResearchSplitPlan(**value['recipe'])
    _require(_same(plan.manifest(),value['manifest']) and plan.identity==corpus['research_plan_sha256']
             and plan.protocol_sha256==corpus['protocol_sha256'],'reconstructed plan/manifest/protocol mismatch')
    return plan


def _typed_bank(value,corpus):
    _require(set(value)=={'schema_version','environment_id','items'} and type(value['schema_version']) is int
             and value['schema_version']==1 and type(value['items']) is list and len(value['items'])==84,'bank schema/84reference items required')
    items=[]
    for row in value['items']:
        _require(type(row) is dict and set(row)=={'item_id','concept_id','difficulty'},'bank item schema')
        items.append(SimulatorItem(**row))
    bank=SimulatorBank(value['environment_id'],tuple(items))
    _require(identity_hash(bank.identity)==corpus['domain_sha256'],'bank semantic domain mismatch')
    return bank


def _provenance(manifest,entry,corpus,plan,bank,role):
    expected=dict(schema_version=1,role=role,research_plan_sha256=plan.identity,domain_sha256=identity_hash(bank.identity),
        environment_graph_sha256=corpus['environment_graph_sha256'],normalized_recipe_sha256=corpus['normalized_recipe_sha256'],
        source_inventory_sha256=identity_hash(corpus['source_inventory']),profile_sha256=entry['profile_sha256'],
        learner_ids=sorted(a.learner_id for a in plan.split_plan.assignments(role)),targets=entry['targets'],
        observable_sha256=entry['observable_sha256'],timestamp_unit='unix_seconds_utc',timezone='UTC',logging_policy_oracle_access=False)
    _require(set(manifest)==set(expected)|{'provenance','provenance_sha256'}
             and _same({k:manifest[k] for k in expected},expected),'role manifest summary/schema mismatch')
    fields=manifest['provenance'];_require(type(fields) is dict and set(fields)==set(ResearchProvenance.__dataclass_fields__),'provenance schema')
    fields=dict(fields);bindings=fields['source_bindings']
    _require(type(bindings) is list and all(type(row) is list and len(row)==2 for row in bindings),'source binding schema')
    fields['source_bindings']=tuple(tuple(row) for row in bindings);provenance=ResearchProvenance(**fields)
    _require(provenance.identity==manifest['provenance_sha256'],'provenance identity mismatch')
    recipe=corpus['normalized_recipe'];raw={k:recipe[k] for k in ('policy','events_per_learner','start_unix_seconds','gap_seconds')}
    raw_sha=identity_hash({'collector':recipe['collector_version'],'clock':'unix_seconds_utc',**raw})
    composite=identity_hash(dict(recipe=raw,recipe_sha256=raw_sha,profile_metadata_sha256=entry['profile_sha256']))
    checks=dict(role=role,research_plan_sha256=plan.identity,split_plan_sha256=plan.split_plan.identity,
        bank_sha256=identity_hash(bank.identity),environment_graph_sha256=corpus['environment_graph_sha256'],
        collection_recipe_sha256=composite,collection_policy_id=recipe['collector_version']+':'+recipe['policy'],
        timestamp_unit='unix_seconds_utc',timezone='UTC',logging_policy_oracle_access=False)
    _require(all(_same(getattr(provenance,k),v) for k,v in checks.items()),'provenance role/source/world/recipe mismatch')
    bound=dict(provenance.source_bindings);sources=corpus['source_inventory']
    _require(set(bound)=={'collector','environment','source_inventory'} and COLLECTOR_PATH in sources
             and bound['collector']==sources[COLLECTOR_PATH] and bound['source_inventory']==identity_hash(sources),'collector/source inventory provenance mismatch')
    return provenance,bound['environment']


def read_public_research_corpus(corpus_id,*,expected_corpus_sha256,expected_done_sha256,limits):
    """Read-only fixed corpus path. Không nguồn/model/authority hoặc readiness claim.

    Missingreference/two-class support được báo đúng audit, không biến thành
    calibrated/fitted success. Research entry chịu trách nhiệm admission policy.
    """
    _require(type(limits) is CorpusReadLimits,'explicit typed read limits required')
    _sha(expected_corpus_sha256);_sha(expected_done_sha256);_path(corpus_id)
    read=_Read(corpus_id,limits)
    done=read.metadata('DONE.json');read.check_hash('DONE.json',expected_done_sha256)
    _require(set(done)=={'schema_version','status','corpus_sha256','files_sha256'}
             and type(done['schema_version']) is int and done['schema_version']==1
             and done['status']=='COMPLETE_SIMULATOR_CORPUS' and done['corpus_sha256']==expected_corpus_sha256
             and type(done['files_sha256']) is dict and set(done['files_sha256'])==set(PUBLIC_FILES),'DONE exact public inventory required')
    for digest in done['files_sha256'].values():_sha(digest)
    corpus=read.metadata('corpus.json');read.check_hash('corpus.json',expected_corpus_sha256);_descriptor(corpus)
    bank_raw=read.metadata('bank.json');read.check_hash('bank.json',corpus['bank_sha256']);bank=_typed_bank(bank_raw,corpus)
    plan_raw=read.metadata('plan.json');read.check_hash('plan.json',corpus['plan_sha256']);plan=_typed_plan(plan_raw,corpus)
    counts=dict(plan.split_plan.role_counts);all_assignments=plan.split_plan.assignments()
    ordinals={a.learner_id:i for i,a in enumerate(all_assignments)}
    seen_rows=set();event_count=0;semantics=None;roles=[]
    for role in DEVELOPMENT_ROLES:
        entry=corpus['roles'][role]
        _require(type(entry) is dict and set(entry)=={'observable_file','observable_sha256','manifest_file','manifest_sha256','learners','targets','profile_sha256'},'role entry schema')
        _require(entry['observable_file']==role+'.jsonl' and entry['manifest_file']==role+'.manifest.json','fixed role filenames required')
        for k in ('observable_sha256','manifest_sha256','profile_sha256'):_sha(entry[k])
        _require(type(entry['learners']) is int and entry['learners']==counts[role]
                 and type(entry['targets']) is int and entry['targets']==entry['learners']*corpus['normalized_recipe']['events_per_learner'],'declared role counts/recipe mismatch')
        manifest=read.metadata(role+'.manifest.json');read.check_hash(role+'.manifest.json',entry['manifest_sha256'])
        provenance,current_semantics=_provenance(manifest,entry,corpus,plan,bank,role)
        if semantics is None:semantics=current_semantics
        _require(semantics==current_semantics,'cross-role environment semantics mismatch')
        trajectories=read.trajectories(role+'.jsonl');read.check_hash(role+'.jsonl',entry['observable_sha256'])
        class_counts=[0,0]
        for trajectory in trajectories:
            _require(trajectory.learner_id in ordinals,'foreign observable learner')
            _require(len(trajectory.observations)==corpus['normalized_recipe']['events_per_learner'],'actual learner length differs from recipe')
            for rank,observation in enumerate(trajectory.observations):
                q=observation.query
                _require(q.timestamp==corpus['normalized_recipe']['start_unix_seconds']+(rank+1)*corpus['normalized_recipe']['gap_seconds']
                         and q.source_row==ordinals[trajectory.learner_id]*SOURCE_ROW_STRIDE+rank+1
                         and q.source_row not in seen_rows,'query clock/source-row/global identity mismatch')
                seen_rows.add(q.source_row);event_count+=1;class_counts[observation.correct]+=1
                _require(event_count<=limits.max_total_events,'whole corpus event limit exceeded')
        audit=audit_research_shard(trajectories,plan=plan,bank=bank,role=role,provenance=provenance,
            expected_provenance_sha256=manifest['provenance_sha256'],limits=limits.shard_limits,reference_items=bank.item_ids)
        _require(audit['audit']['learners']==entry['learners'] and audit['audit']['targets']==entry['targets'],'actual vs published role population mismatch')
        roles.append(PublicRoleData(role,provenance,trajectories,_sealed(manifest),_sealed(audit),tuple(class_counts)))
    for name in PUBLIC_FILES:read.check_hash(name,done['files_sha256'][name])
    read.verify_after()
    values=dict(corpus_id=corpus_id,plan=plan,bank=bank,roles=tuple(roles),corpus_manifest_json=_sealed(corpus),
        files_sha256=tuple((n,v[0],v[1]) for n,v in sorted(read.records.items()) if n!='DONE.json'),done_sha256=expected_done_sha256,
        source_bindings=tuple(sorted(corpus['source_inventory'].items())),limits=limits,input_bytes=read.total,
        elapsed_seconds=max(time.monotonic()-read.start,time.time()-read.wall),content_sha256='')
    result=PublicResearchCorpus(**values)
    values['content_sha256']=identity_hash(result._payload());result=PublicResearchCorpus(**values)
    result.assert_integrity();read.guard()
    return result
