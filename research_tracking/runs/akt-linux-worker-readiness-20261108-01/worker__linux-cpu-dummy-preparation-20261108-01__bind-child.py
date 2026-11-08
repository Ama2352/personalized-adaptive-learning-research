
import hashlib,json,sys
from pathlib import Path
root=Path('/content/KLTN_GPU08_20261108_01');sys.path.insert(0,str(root/'src'))
from knowledge_tracing.akt.config import load_config
from knowledge_tracing.akt.context import load_worker_context,context_authorization_identity
from knowledge_tracing.akt.authorization import config_hash,require_authorization
prep=root/'linux-cpu-dummy-preparation-20261108-01';execution=root/'linux-cpu-dummy-execution-20261108-01'
data=root/'artifacts/akt/synthetic/ctx-linux-20261108-01'
def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def w(path,value):
 with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write(chr(10))
config_path=prep/'execution-config.json';context_path=data/'worker-context.json'
config=load_config(config_path);context=load_worker_context(context_path,expected_sha256='42cc79d8c1fee18b1f4908de5a9c2f406a2f898b769aa2b81f9ab156e6959c4c')
context.validate_for(config);identity=context_authorization_identity(config,context)
caps={name:getattr(config,name) for name in ('max_train_users', 'max_val_users', 'max_targets_per_side', 'max_steps', 'max_seconds', 'max_wall_seconds', 'max_rss_bytes', 'min_available_ram_bytes')}
if 'prepare'=='prepare':
 authorization={'approved':False,'scope':'development-inner-only','phase':'smoke','run_id':config.run_id,
  'source_commit':config.source_commit,'config_sha256':config_hash(config),'identity':identity,'caps':caps,
  'approval_reference':'PENDING_PARENT_REVIEW; preparation does not authorize execution'}
 w(prep/'proposed-authorization.json',authorization)
else:
 proposal=json.loads((prep/'proposed-authorization.json').read_text())
 assert proposal['approved'] is False and proposal['identity']==identity and proposal['config_sha256']==config_hash(config)
 authorization={**proposal,'approved':True,'approval_reference':''}
 require_authorization(config,authorization,identity_fn=lambda cfg:context_authorization_identity(cfg,context))
 w(execution/'authorization.json',authorization)
print(json.dumps({'identity':identity,'context_sha256':h(context_path),'config_sha256':config_hash(config),
 'execution_config_file_sha256':h(config_path),'caps':caps,'model_execution':False,'mode':'prepare'}))
