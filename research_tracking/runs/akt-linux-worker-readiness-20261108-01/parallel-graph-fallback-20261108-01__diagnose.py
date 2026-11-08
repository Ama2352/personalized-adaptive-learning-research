from pathlib import Path
import sys,os,json,runpy,hashlib,platform
root=Path.cwd();sys.path[:0]=[str(root/'src'),str(root/'third_party')]
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=(root/'artifacts/akt/dependencies/upstream').as_posix())
import torch
from dataclasses import replace
m=runpy.run_path(str(root/'tests/akt/test_graph_prototype.py'))
cfg,train,selection,encoding,graph,baseline,proto,original=m['bundle'].__wrapped__()
t=selection.trajectories[0];shard=replace(selection,trajectories=(replace(t,observations=tuple(replace(o,query=replace(o.query,item_id='c')) for o in t.observations)),))
batch=m['graph_proto'].prepare_graph_batch(shard,encoding,config=cfg,graph=graph);target=m['labels'](batch,shard)
threads=[]
def record(label):
 return lambda model,args:threads.append({'model':label,'threads':torch.get_num_threads(),'shape':list(args[0].shape),'training':model.training})
a=baseline.register_forward_pre_hook(record('baseline'));b=proto.native.register_forward_pre_hook(record('proto.native'))
def summary(x,y):
 return [{'shape':list(v.shape),'dtype':str(v.dtype),'equal':torch.equal(v,w),'max_abs_delta':float((v-w).abs().max()),'left_values':v.detach().reshape(-1).tolist(),'right_values':w.detach().reshape(-1).tolist(),'left_bits':v.detach().view(torch.int32).reshape(-1).tolist() if v.dtype==torch.float32 else None,'right_bits':w.detach().view(torch.int32).reshape(-1).tolist() if w.dtype==torch.float32 else None} for v,w in zip(x,y,strict=True)]
rows=[];state=m['native_hash'](proto.native)
for ambient in (1,2,1,2):
 torch.set_num_threads(ambient)
 details=proto.forward_details(batch,target)
 expected=baseline(batch.base.q_data,batch.base.qa_data,target)
 direct=proto.native(batch.base.q_data,batch.base.qa_data,target)
 with torch.device('cpu'):
  torch.set_num_threads(2);matched=baseline(batch.base.q_data,batch.base.qa_data,target)
 torch.set_num_threads(ambient)
 rows.append({'ambient':ambient,'after_proto_threads':torch.get_num_threads(),'applied_mask':details.applied_mask.tolist(),'hidden_is_none':details.hidden is None,'baseline_vs_proto':summary(expected,details.native_result),'proto_direct_ambient_vs_wrapper':summary(direct,details.native_result),'matched_threads2_baseline_vs_proto':summary(matched,details.native_result)})
assert state==m['native_hash'](proto.native)==m['native_hash'](baseline)
a.remove();b.remove()
result={'torch':torch.__version__,'torch_config':torch.__config__.show(),'platform':platform.platform(),'initial_backbone_states_equal':True,'final_backbone_states_equal':True,'optimizer_steps':0,'config_threads':cfg.threads,'input_shape':list(batch.base.q_data.shape),'q':batch.base.q_data.tolist(),'qa':batch.base.qa_data.tolist(),'targets':target.tolist(),'parent_supports':[[[p.support for p in q.evidence.parents] if q else None for q in row] for row in batch.contexts],'hooks':threads,'comparisons':rows}
p=root/'artifacts/akt/local-tests/parallel-graph-fallback-20261108-01/diagnostic.json';p.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'result':str(p),'torch':torch.__version__,'shape':result['input_shape'],'rows':[{'ambient':x['ambient'],'base_vs_proto_equal':[v['equal'] for v in x['baseline_vs_proto']],'max_abs':[v['max_abs_delta'] for v in x['baseline_vs_proto']],'matched_equal':[v['equal'] for v in x['matched_threads2_baseline_vs_proto']]} for x in rows],'optimizer_steps':0}))
