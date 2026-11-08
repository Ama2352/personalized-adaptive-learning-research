"""Observer thu actual arguments; không thêm RNG/scoring hoặc thay native methods."""
import copy
import hashlib
import json
import math
import struct


def exact(left,right):
    if type(left) is not type(right):return False
    if isinstance(left,float):return struct.pack('>d',left)==struct.pack('>d',right)
    if isinstance(left,dict):return set(left)==set(right) and all(exact(left[k],right[k]) for k in left)
    if isinstance(left,(list,tuple)):return len(left)==len(right) and all(exact(a,b) for a,b in zip(left,right))
    return left==right


def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def row_sha(value):return hashlib.sha256(canonical(value).encode()).hexdigest()


def query_tuple(cid,qid,difficulty,timestamp):
    if type(cid) is not str or not cid or type(qid) is not str or not qid or not math.isfinite(difficulty):
        raise ValueError('native query identity invalid')
    return {'concept':cid,'question':qid,'difficulty':float(difficulty),
            'timestamp_iso':timestamp.isoformat(),'timestamp_ns':int(timestamp.value)}


class Context:
    def __init__(self,seed,profile,sink):
        self.seed=seed;self.profile=profile;self.sink=sink
        self.pending={};self.started={};self.completed={};self.rows=[]

    def begin(self,variant,query):
        if variant in self.pending:raise ValueError('previous event incomplete')
        event=str(self.started.get(variant,0));self.started[variant]=int(event)+1
        row={'seed':self.seed,'profile':self.profile,'learner_id':f'{self.seed}-{self.profile}',
             'event_id':event,'variant':variant,'query':query,'query_capture_phase':'before_delegate_predict',
             'phases':['before_predict']}
        self.pending[variant]=row
        return (variant,event)

    def current(self,key):
        variant,event=key;row=self.pending.get(variant)
        if row is None or row['event_id']!=event:raise ValueError('event key mismatch')
        return row

    def prediction(self,key,value):
        row=self.current(key)
        if row['phases']!=['before_predict']:raise ValueError('prediction phase mismatch')
        row['probability']=value;row['phases'].append('after_predict')

    def copied(self,key):
        row=self.current(key)
        if row['phases']!=['before_predict','after_predict']:raise ValueError('duplicate or out-of-order deepcopy')
        row['phases'].append('preview_deepcopy')

    def preview(self,key,result):
        row=self.current(key)
        if row['phases']!=['before_predict','after_predict','preview_deepcopy']:raise ValueError('preview phase mismatch')
        if type(result) is not tuple or len(result)!=3:raise ValueError('native select tuple required')
        cid,qid,difficulty=result
        if type(cid) is not str or type(qid) is not str or not math.isfinite(difficulty):raise ValueError('preview identity invalid')
        row['preview']={'concept':cid,'question':qid,'difficulty':float(difficulty)}
        row.update(preview_capture_phase='after_native_preview_select',preview_is_served=False,preview_timestamp_argument=None)
        row['phases'].append('after_preview_select')

    def legacy(self,value):
        row=self.pending.get(value['variant'])
        if row is None or (row['event_id'],row['learner_id'])!=(value['event_id'],value['learner_id']):raise ValueError('legacy key mismatch')
        if row['phases'][-1]!='after_preview_select':raise ValueError('missing preview before trace')
        if not exact(row['probability'],value['probability']) or row['preview']['concept']!=value['action']:
            raise ValueError('prediction/preview disagrees with legacy trace')
        row['correct']=value['correct'];row['legacy_row_sha256']=row_sha(value);row['phases'].append('legacy_pre_update')

    def before_update(self,key,query,y,probability):
        row=self.current(key)
        if row['phases'][-1]!='legacy_pre_update' or not exact(query,row['query']):raise ValueError('update query pairing mismatch')
        if not exact(y,row['correct']) or not exact(probability,row['probability']):raise ValueError('update label/probability pairing mismatch')
        row['phases'].append('before_update_pairing_verified')

    def after_update(self,key):
        row=self.current(key)
        if row['phases'][-1]!='before_update_pairing_verified':raise ValueError('update phase mismatch')
        row['phases'].append('after_update');row['update_pairing_verified']=True
        self.sink.write(canonical(row)+'\n');self.rows.append(row)
        variant=key[0];self.completed[variant]=self.completed.get(variant,0)+1;del self.pending[variant]


class PolicyObserver:
    def __init__(self,delegate,variant,context,*,preview=False,event_key=None):
        object.__setattr__(self,'_delegate',delegate);object.__setattr__(self,'_variant',variant)
        object.__setattr__(self,'_context',context);object.__setattr__(self,'_preview',preview)
        object.__setattr__(self,'_event_key',event_key)

    def __getattr__(self,name):return getattr(self._delegate,name)
    def __setattr__(self,name,value):
        if name.startswith('_'):object.__setattr__(self,name,value)
        else:setattr(self._delegate,name,value)

    def predict(self,cid,qid,difficulty,timestamp):
        if self._preview:raise ValueError('preview predict not part of fixed stream')
        key=self._context.begin(self._variant,query_tuple(cid,qid,difficulty,timestamp))
        object.__setattr__(self,'_event_key',key)
        value=self._delegate.predict(cid,qid,difficulty,timestamp)
        self._context.prediction(key,value)
        return value

    def __deepcopy__(self,memo):
        if self._preview or self._event_key is None:raise ValueError('preview copy requires current prediction')
        copied=copy.deepcopy(self._delegate,memo)
        self._context.copied(self._event_key)
        proxy=type(self)(copied,self._variant,self._context,preview=True,event_key=self._event_key)
        memo[id(self)]=proxy
        return proxy

    def select(self):
        if not self._preview:raise ValueError('real policy selection forbidden in fixed stream observer')
        result=self._delegate.select();self._context.preview(self._event_key,result)
        return result

    def update(self,cid,qid,difficulty,timestamp,y,p_pred):
        if self._preview or self._event_key is None:raise ValueError('update without current prediction')
        self._context.before_update(self._event_key,query_tuple(cid,qid,difficulty,timestamp),y,p_pred)
        result=self._delegate.update(cid,qid,difficulty,timestamp,y,p_pred)
        self._context.after_update(self._event_key);object.__setattr__(self,'_event_key',None)
        return result
