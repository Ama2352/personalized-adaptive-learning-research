"""Prepared one remote CPU numerical diagnostic only; <=30s/0optimizer.
No production writes/assertion changes. Parent dispatches separately after review.
"""
import argparse,hashlib,json,math,os,runpy,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path('/content/KLTN_GPU08_20261108_01')
STAGE=ROOT/'graph-fallback-diagnostic01'
HELPER_SHA='f33c9d50dbde6a354c03c0f9d702f239a70a9d298f3ee0214718d0daadd9db90'
sha=lambda b:hashlib.sha256(b).hexdigest()
BODY="from pathlib import Path\nimport sys,os,json,runpy,hashlib,platform\nroot=Path('/content/KLTN_GPU08_20261108_01');sys.path[:0]=[str(root/'src'),str(root/'third_party')]\n\nimport torch\nfrom dataclasses import replace\nassert hashlib.sha256((root/'tests/akt/test_graph_prototype.py').read_bytes()).hexdigest()=='5e2aae220d1b862c337951182efab417a3ed81dd5eb6899f84af710a3cfd76ae'\nassert hashlib.sha256((root/'src/knowledge_tracing/akt/graph_prototype.py').read_bytes()).hexdigest()=='c7e9ce13a6225d60c550640b48c173275a6d5b353959eec133cd20b8c08afc84'\nm=runpy.run_path(str(root/'tests/akt/test_graph_prototype.py'))\ncfg,train,selection,encoding,graph,baseline,proto,original=m['bundle'].__wrapped__()\npredecessors=[]\nfor name in ('test_fresh_backbone_initialization_identity_and_thin_visible_output_parity','test_disabled_exact_native_outputs_and_backbone_gradients','test_active_joint_gradients_and_same_forward_mixed_inactive_probabilities'):\n try:\n  m[name]((cfg,train,selection,encoding,graph,baseline,proto,original));predecessors.append({'test':name,'result':'PASS'})\n except Exception as error:predecessors.append({'test':name,'error_type':type(error).__name__,'error':str(error)})\nt=selection.trajectories[0];shard=replace(selection,trajectories=(replace(t,observations=tuple(replace(o,query=replace(o.query,item_id='c')) for o in t.observations)),))\nbatch=m['graph_proto'].prepare_graph_batch(shard,encoding,config=cfg,graph=graph);target=m['labels'](batch,shard)\nthreads=[]\ndef record(label):\n return lambda model,args:threads.append({'model':label,'threads':torch.get_num_threads(),'shape':list(args[0].shape),'training':model.training})\na=baseline.register_forward_pre_hook(record('baseline'));b=proto.native.register_forward_pre_hook(record('proto.native'))\ndef summary(x,y):\n return [{'shape':list(v.shape),'dtype':str(v.dtype),'equal':torch.equal(v,w),'max_abs_delta':float((v-w).abs().max()),'left_values':v.detach().reshape(-1).tolist(),'right_values':w.detach().reshape(-1).tolist(),'left_bits':v.detach().view(torch.int32).reshape(-1).tolist() if v.dtype==torch.float32 else None,'right_bits':w.detach().view(torch.int32).reshape(-1).tolist() if w.dtype==torch.float32 else None} for v,w in zip(x,y,strict=True)]\nrows=[];state=m['native_hash'](proto.native)\nfor ambient in (1,2,1,2):\n torch.set_num_threads(ambient)\n details=proto.forward_details(batch,target)\n expected=baseline(batch.base.q_data,batch.base.qa_data,target)\n direct=proto.native(batch.base.q_data,batch.base.qa_data,target)\n with torch.device('cpu'):\n  torch.set_num_threads(2);matched=baseline(batch.base.q_data,batch.base.qa_data,target)\n torch.set_num_threads(ambient)\n rows.append({'ambient':ambient,'after_proto_threads':torch.get_num_threads(),'applied_mask':details.applied_mask.tolist(),'hidden_is_none':details.hidden is None,'baseline_vs_proto':summary(expected,details.native_result),'proto_direct_ambient_vs_wrapper':summary(direct,details.native_result),'matched_threads2_baseline_vs_proto':summary(matched,details.native_result)})\nassert state==m['native_hash'](proto.native)==m['native_hash'](baseline)\na.remove();b.remove()\nresult={'predecessor_test_observations':predecessors,'torch':torch.__version__,'torch_config':torch.__config__.show(),'platform':platform.platform(),'initial_backbone_states_equal':True,'final_backbone_states_equal':True,'optimizer_steps':0,'config_threads':cfg.threads,'input_shape':list(batch.base.q_data.shape),'q':batch.base.q_data.tolist(),'qa':batch.base.qa_data.tolist(),'targets':target.tolist(),'parent_supports':[[[p.support for p in q.evidence.parents] if q else None for q in row] for row in batch.contexts],'hooks':threads,'comparisons':rows}\nprint(json.dumps(result))\n"

def main():
 p=argparse.ArgumentParser();p.add_argument('--expected-source-sha256',required=True);args=p.parse_args()
 start=time.monotonic();wall=time.time();process=None;helper=None;state={'attempted':False,'accepted':False,'events':[]}
 assert os.name=='posix' and ROOT.resolve()==ROOT and ROOT.is_dir() and not ROOT.is_symlink()
 assert not STAGE.exists() and not STAGE.is_symlink();STAGE.mkdir(exist_ok=False)
 result={'status':'FAILED_NUMERICAL_DIAGNOSTIC','optimizer_steps':0,'source_edits':False}
 def check():
  assert all(math.isfinite(v) and 0<=v<=30 for v in (time.monotonic()-start,time.time()-wall)), '30s cap'
  assert not (STAGE/'CANCEL').exists()
  assert sum(q.stat().st_size for q in STAGE.iterdir() if q.is_file())<=4*1024**2
 try:
  source=Path(__file__).absolute();assert source==ROOT/'graph_fallback_diagnostic01.py' and sha(source.read_bytes())==args.expected_source_sha256
  assert os.environ.get('COLAB_GPU') in (None,'','0') and not os.environ.get('COLAB_TPU_ADDR') and not list(Path('/dev').glob('nvidia[0-9]*'))
  hp=ROOT/'upstream_checkout01.py';assert not hp.is_symlink() and sha(hp.read_bytes())==HELPER_SHA
  helper=runpy.run_path(str(hp));kit_sha=helper['verify_kit']()
  script=STAGE/'diagnostic-child.py'
  with script.open('x',encoding='utf-8') as f:f.write(BODY)
  env={k:v for k,v in os.environ.items() if not k.upper().startswith(('GIT_','GH_','GITHUB_','SSH_','PYTHON','PIP_','UV_','CONDA_')) and not any(s in k.upper() for s in ('TOKEN','PASSWORD','CREDENTIAL','SECRET','AUTH','PROXY')) and k not in {'HOME','XDG_CONFIG_HOME','LD_PRELOAD','LD_LIBRARY_PATH'}}
  (STAGE/'home').mkdir();env.update(HOME=str(STAGE/'home'),XDG_CONFIG_HOME=str(STAGE/'home'),PATH='/usr/bin:/bin',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=(ROOT/'artifacts/akt/dependencies/upstream').as_posix(),CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
  with (STAGE/'child.stdout').open('xb') as stdout,(STAGE/'child.stderr').open('xb') as stderr:
   process=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-I','-B',str(script)],cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
   try:
    while process.poll() is None:
     check()
     if time.monotonic()-start>25:raise TimeoutError('reserve cleanup')
     try:process.wait(timeout=.1)
     except subprocess.TimeoutExpired:pass
   finally:helper['cleanup_once'](process,state)
  assert state['accepted'] and state['returncode']==0
  payload=json.loads(helper['read_regular'](STAGE/'child.stdout'))
  assert payload['optimizer_steps']==0 and payload['initial_backbone_states_equal'] and payload['final_backbone_states_equal']
  assert helper['verify_kit']()==kit_sha and sha(source.read_bytes())==args.expected_source_sha256
  result.update(status='COMPLETED_NUMERICAL_OBSERVATION_NOT_GATE',diagnostic=payload,source_sha256=args.expected_source_sha256);check()
 except Exception as error:
  result.update(error_type=type(error).__name__,error=str(error))
  with (STAGE/'failure.log').open('x',encoding='utf-8') as f:f.write(traceback.format_exc())
 finally:
  if helper is not None:helper['cleanup_once'](process,state)
  result.update(elapsed_seconds=time.monotonic()-start,elapsed_wall_seconds=time.time()-wall,cleanup=state)
  if not all(math.isfinite(v) and 0<=v<=30 for v in (result['elapsed_seconds'],result['elapsed_wall_seconds'])):result['status']='REJECTED_30S_BOUND'
  with (STAGE/'result.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
  outputs={q.name:{'sha256':sha(q.read_bytes()),'bytes':q.stat().st_size} for q in STAGE.iterdir() if q.is_file()}
  with (STAGE/'output-manifest.json').open('x',encoding='utf-8') as f:json.dump({'status':result['status'],'outputs':outputs},f,indent=2);f.write('\n')
  print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'result_sha256':sha((STAGE/'result.json').read_bytes()),'manifest_sha256':sha((STAGE/'output-manifest.json').read_bytes())}))
 return 0 if result['status']=='COMPLETED_NUMERICAL_OBSERVATION_NOT_GATE' else 1
if __name__=='__main__':raise SystemExit(main())
