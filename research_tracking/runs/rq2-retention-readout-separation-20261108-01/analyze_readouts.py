"""One predeclared constructed-state readout; stdlib, no native class execution."""
from pathlib import Path
import argparse,ast,hashlib,json,math,sys,time
START=time.perf_counter();ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
PREP=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
args=parser.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PLAN=PREP/'plan.json';assert sha(PLAN)==args.plan_sha256
plan=json.loads(PLAN.read_bytes());OUT=PREP/'analysis01';OUT.mkdir(exist_ok=False)
notebook=ROOT/plan['notebook'];assert sha(notebook)==plan['notebook_sha256']
nb=json.loads(notebook.read_bytes());pins=plan['method_pins'];excerpts={}
for name,pin in pins.items():
 text=''.join(nb['cells'][pin['cell']]['source'])
 nodes=[n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name==name]
 assert len(nodes)==1
 segment=ast.get_source_segment(text,nodes[0]);assert hashlib.sha256(segment.encode()).hexdigest()==pin['sha256']
 excerpts[name]={'cell':pin['cell'],'start_line':nodes[0].lineno,'end_line':nodes[0].end_lineno,'source':segment,**pin}
constants={}
for node in ast.parse(''.join(nb['cells'][3]['source'])).body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
  if node.targets[0].id in ('MASTERY_ELO','TRUE_FORGET_RATE','RETENTION_GAP_DAYS'):
   constants[node.targets[0].id]=ast.literal_eval(node.value)
assert constants=={'MASTERY_ELO':1250.,'TRUE_FORGET_RATE':.06,'RETENTION_GAP_DAYS':14.}
legacy=ROOT/plan['legacy_retention'];assert sha(legacy)==plan['legacy_retention_sha256']
old=json.loads(legacy.read_bytes())
factor=math.exp(-constants['TRUE_FORGET_RATE']*constants['RETENTION_GAP_DAYS'])
assert factor==old['scaling_factor']
base=plan['base'];gains=plan['gains'];assert len(base)==28 and set(gains)=={'A','B'}
assert base==[850.,1200.]+[1000.]*26
assert gains['A']==[0.,250.]+[0.]*26 and gains['B']==[450.,0.]+[0.]*26
def f(theta):
 return float(1.0/(1.0+10.0**((1250.0-theta)/400.0)))
def mean(values):return math.fsum(values)/28
def metrics(state):
 hard_count=sum(x>=1250 for x in state)
 return {'mean_theta':mean(state),'mean_theta_gain':mean(x-b for x,b in zip(state,base,strict=True)),
  'native_soft_mastery':mean(f(x) for x in state),'native_soft_mastery_gain':mean(f(x)-f(b) for x,b in zip(state,base,strict=True)),
  'native_hard_mastery_count':hard_count,'native_hard_mastery_rate':hard_count/28,
  'native_hard_mastery_gain':(hard_count-sum(b>=1250 for b in base))/28}
states={};residuals={}
for name,g in gains.items():
 assert len(g)==28 and all(x>=0 for x in g)
 final=[b+x for b,x in zip(base,g,strict=True)];retained=[b+factor*x for b,x in zip(base,g,strict=True)]
 assert all(x<=1600 for x in final) and all(b<=x<=1600 for b,x in zip(base,retained,strict=True))
 states[name]={'gain_vector':g,'T_state':final,'D14_state':retained,'T':metrics(final),'D14':metrics(retained)}
 residuals[name]={key:states[name]['D14'][key]-factor*states[name]['T'][key]
                  for key in ('mean_theta_gain','native_soft_mastery_gain','native_hard_mastery_gain')}
 assert abs(residuals[name]['mean_theta_gain'])<1e-12
differences={stage:{key:states['A'][stage][key]-states['B'][stage][key] for key in states['A'][stage]}
             for stage in ('T','D14')}
def order(delta):return 'A>B' if delta>1e-12 else 'A<B' if delta < -1e-12 else 'tie_within_1e-12'
orders={stage:{key:order(value) for key,value in differences[stage].items()}
        for stage in differences}
zero=metrics(base);assert all(abs(zero[k])<1e-15 for k in ('mean_theta_gain','native_soft_mastery_gain','native_hard_mastery_gain'))
assert metrics(states['A']['T_state'])==states['A']['T'] and metrics(states['A']['D14_state'])==states['A']['D14']
assert f(1250.)==.5
reversal=(differences['T']['native_soft_mastery_gain']*differences['D14']['native_soft_mastery_gain']<0
          and abs(differences['T']['native_soft_mastery_gain'])>1e-12
          and abs(differences['D14']['native_soft_mastery_gain'])>1e-12)
result={'status':'COMPUTED_FIXED_PREDECLARED_STATE_READOUT_NOT_TRAJECTORY','source_equations':excerpts,
 'constants':constants,'base':base,'states':states,'retention_factor':factor,'A_minus_B':differences,
 'orderings':orders,'linear_factor_residuals':residuals,'soft_gain_order_reversal':reversal,
 'negative_controls':{'zero_gain_all_readouts_gain_zero':True,'identical_state_same_readout':True,'threshold_readout_f1250_equals_half':True},
 'formulas':{'theta':'theta(T+D)=b+exp(-beta*D)*g',
  'linear':'mean(g14)=c*mean(gT)',
  'soft':'S(c)-S(0)=mean[f(b+c*g)-f(b)] generally not c*mean[f(b+g)-f(b)]',
  'curvature':'f_second(theta)=k^2*f(theta)*(1-f(theta))*(1-2*f(theta));k=ln(10)/400',
  'hard':'mean[1{b+c*g>=1250}-1{b>=1250}]; stepwise in c'},
 'limitations':['Constructed readout-domain states, not shown reachable from persona initialization or any policy/trajectory',
  'No environment/model/teacher/RNG or full trajectory execution','No graph/policy/ability treatment or learning-benefit inference',
  'Native soft/hard true-state metrics, not model mastery or protocol21 calibrated reference score',
  'Source-equation arithmetic uses stdlib fsum; not a bitwise native NumPy execution claim'],
 'environment_model_trajectory_calls':0,'parameter_search':False,'C08_rewritten':False}
assert time.perf_counter()-START<9
for name,value in [('readouts.json',result),('source_excerpts.json',{'notebook':plan['notebook'],'notebook_sha256':sha(notebook),'methods':excerpts})]:
 with (OUT/name).open('x',encoding='utf-8') as output:json.dump(value,output,ensure_ascii=False,indent=2);output.write('\n')
assert sha(notebook)==plan['notebook_sha256'] and sha(legacy)==plan['legacy_retention_sha256']
print(json.dumps({'status':result['status'],'soft_gain_order_reversal':reversal,'orders':orders,
                 'factor':factor,'A_T':states['A']['T'],'B_T':states['B']['T'],
                 'A_D14':states['A']['D14'],'B_D14':states['B']['D14']},ensure_ascii=False,indent=2))
