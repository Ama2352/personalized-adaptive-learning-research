"""Surrogate confidence Junyi theo native window và crossfit người học train80.

Tái dùng solver và bootstrap Method24. Dữ liệu được phát từng target, fitter
nhận một child để caller có thể spool trên D thay vì giữ mọi feature vào RAM.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import time

from ..edge_confidence import (EdgeConfidenceRecipe, OOFRow, _fit_one, _loss,
    _probabilities, _summarize_edge)
from .research_junyi_graph import JunyiGraphPhaseSession
from .research_junyi_data import JunyiPhaseView
from .types import TrainingWindow, UnseenTarget

FEATURE_RECIPE='junyi-effective-native-window-surrogate-v1'
FOLD_RECIPE='junyi-train80-surrogate-learner-rank-v1'


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


@dataclass(frozen=True,slots=True)
class JunyiSurrogateRow:
    learner_id: str
    child_id: str
    source_row: int
    global_rank: int
    correct: int
    base: tuple[float,...]
    # Một entry cho mỗi declared parent, kể cả parent chưa quan sát.
    parents: tuple[tuple[str,int,int],...]


def surrogate_fold_assignments(view,recipe):
    if type(view) is not JunyiPhaseView or view.scope!='select_train80' or type(recipe) is not EdgeConfidenceRecipe:
        raise ValueError('TRAIN80 view and approved confidence recipe required')
    if view.roles.identity!=view.expected_roles_identity:
        raise ValueError('Frozen TRAIN80 roles changed')
    users=view.users
    if tuple(sorted(set(users)))!=users:
        raise ValueError('Canonical TRAIN80 learners required')
    population=_digest(users)
    ranked=sorted(users,key=lambda user:(_digest([FOLD_RECIPE,recipe.seed,view.identity,population,user]),user))
    return tuple(sorted((user,index%recipe.folds) for index,user in enumerate(ranked)))


def iter_surrogate_rows(windows,session,*,max_targets,max_windows,max_seconds):
    """Feature tại t chỉ đọc responses trước t, label lấy riêng từ target loss."""
    if type(session) is not JunyiGraphPhaseSession or session.view.scope!='select_train80':
        raise ValueError('TRAIN80 graph session required')
    if (type(max_targets) is not int or max_targets<=0 or type(max_windows) is not int
            or max_windows<=0 or not math.isfinite(max_seconds) or max_seconds<=0):
        raise ValueError('Explicit positive preparation caps required')
    started=time.monotonic()
    previous=None
    targets=window_count=0
    vocabulary=session.condition.encoding.native.vocabulary.values
    for entry in windows:
        if time.monotonic()-started>max_seconds:
            raise TimeoutError('Junyi confidence preparation time cap')
        if type(entry) is UnseenTarget:
            # OOV barrier/reset đã được iter_windows áp dụng vào window tiếp theo.
            continue
        if type(entry) is not TrainingWindow:
            raise ValueError('Typed native training windows required')
        window_count+=1
        if window_count>max_windows:
            raise ValueError('Junyi confidence window cap')
        window=entry.window
        evidence=session.prefix_evidence(window)
        if len(entry.targets)!=len(window.inputs.item_ids):
            raise ValueError('Target/window geometry mismatch')
        counts,successes={},{}
        total_successes=0
        for local,item_id in enumerate(window.inputs.item_ids):
            if local:
                prior=vocabulary[int(window.inputs.item_ids[local-1])]
                response=int(window.inputs.prior_responses[local])
                counts[prior]=counts.get(prior,0)+1
                successes[prior]=successes.get(prior,0)+response
                total_successes+=response
            if not window.target_mask[local]:
                continue
            label=entry.targets[local]
            if label not in (0,1):
                raise ValueError('Binary surrogate target required')
            query=evidence[local]
            key=(query.learner_id,query.global_rank)
            if previous is not None and key<=previous:
                raise ValueError('Duplicate or unordered surrogate targets')
            previous=key
            targets+=1
            if targets>max_targets:
                raise ValueError('Junyi confidence target cap')
            child=vocabulary[int(item_id)]
            n=counts.get(child,0)
            base=((successes.get(child,0)+1.)/(n+2.),n/(n+5.),
                  (total_successes+1.)/(local+2.),local/(local+5.))
            parents=tuple((parent.parent,parent.support,successes.get(parent.parent,0))
                          for parent in query.audit.parents)
            yield JunyiSurrogateRow(query.learner_id,child,query.source_row,query.global_rank,
                int(label),base,parents)
    session.assert_boundary()


def fit_child_confidence(rows,*,child,parents,view,recipe,runtime,max_rows,max_fits,max_seconds):
    """Fit một child và các parent bằng Method24, giữ OOF và ledger để kiểm."""
    if (type(recipe) is not EdgeConfidenceRecipe or type(parents) is not tuple
            or parents!=tuple(sorted(set(parents))) or child in parents):
        raise ValueError('Approved recipe and canonical nonself parents required')
    if (type(max_rows) is not int or max_rows<=0 or type(max_fits) is not int
            or max_fits<recipe.folds*(1+len(parents)) or not math.isfinite(max_seconds) or max_seconds<=0):
        raise ValueError('Explicit fit row/count/time caps required')
    started=time.monotonic()
    fold_of=dict(surrogate_fold_assignments(view,recipe))
    stored=[]
    previous=None
    for row in rows:
        if time.monotonic()-started>max_seconds:
            raise TimeoutError('Junyi child confidence fit time cap')
        if type(row) is not JunyiSurrogateRow or row.child_id!=child or row.learner_id not in fold_of:
            raise ValueError('One child and TRAIN80 learners required')
        key=(row.learner_id,row.global_rank)
        if previous is not None and key<=previous:
            raise ValueError('Duplicate or unordered child targets')
        previous=key
        if (type(row.correct) is not int or row.correct not in (0,1)
                or type(row.source_row) is not int or row.source_row<=0
                or type(row.global_rank) is not int or row.global_rank<0 or len(row.base)!=4
                or any(not math.isfinite(value) or not 0<=value<=1 for value in row.base)
                or tuple(parent for parent,_,_ in row.parents)!=parents
                or any(type(n) is not int or type(s) is not int or not 0<=s<=n for _,n,s in row.parents)):
            raise ValueError('Invalid surrogate features or parent geometry')
        stored.append(row)
        if len(stored)>max_rows:
            raise ValueError('Junyi child confidence row cap')
    if not stored:
        raise ValueError('Nonempty child population required')
    ledger=[]

    def fitted(kind,parent,fold,training,features):
        if time.monotonic()-started>max_seconds:
            raise TimeoutError('Junyi child confidence fit time cap')
        fit=_fit_one(tuple(features(row) for row in training),tuple(row.correct for row in training),recipe,runtime)
        ledger.append(dict(kind=kind,parent=parent,child=child,heldout_fold=fold,
            training_targets=len(training),training_learners_sha256=_digest(sorted({row.learner_id for row in training})),
            training_rows_sha256=_digest([(row.learner_id,row.source_row) for row in training]),
            solver_called=fit.solver_called,supported=fit.model is not None,reason=fit.reason,
            coefficients=fit.coefficients,intercept=fit.intercept,iterations=fit.iterations))
        if time.monotonic()-started>max_seconds:
            raise TimeoutError('Junyi child confidence fit time cap')
        return fit

    partitions={fold:(tuple(row for row in stored if fold_of[row.learner_id]!=fold),
        tuple(row for row in stored if fold_of[row.learner_id]==fold)) for fold in range(recipe.folds)}
    baseline={}
    for fold,(training,heldout) in partitions.items():
        fit=fitted('baseline',None,fold,training,lambda row:row.base)
        baseline[fold]=_probabilities(fit,tuple(row.base for row in heldout))
    summaries=[]
    oof=[]
    for position,parent in enumerate(parents):
        edge_rows=[]
        supported=True

        def augmented(row):
            _,n,s=row.parents[position]
            return row.base+((s+1.)/(n+2.),n/(n+5.))

        for fold,(training,heldout) in partitions.items():
            fit=fitted('augmented',parent,fold,training,augmented)
            probabilities=_probabilities(fit,tuple(augmented(row) for row in heldout))
            base=baseline[fold]
            supported=supported and base is not None and probabilities is not None
            for index,row in enumerate(heldout):
                eligible=row.parents[position][1]>0
                b=base[index] if base is not None else None
                p=probabilities[index] if probabilities is not None else None
                delta=None
                if eligible and b is not None and p is not None:
                    delta=_loss(row.correct,b,recipe.clip)-_loss(row.correct,p,recipe.clip)
                edge_rows.append(OOFRow(parent,child,row.learner_id,row.source_row,fold,row.correct,
                    eligible,b,p,delta,'PARENT_NOT_PAST' if not eligible else (None if delta is not None else 'FIT_UNSUPPORTED')))
        seed=int(_digest([FEATURE_RECIPE,recipe.seed,view.identity,parent,child])[:16],16)
        summaries.append(_summarize_edge(tuple(edge_rows),recipe,seed,supported))
        oof.extend(edge_rows)
    if len(ledger)!=recipe.folds*(1+len(parents)):
        raise ValueError('Incomplete surrogate fit population')
    if time.monotonic()-started>max_seconds:
        raise TimeoutError('Junyi child confidence fit time cap')
    return dict(feature_recipe=FEATURE_RECIPE,fold_recipe=FOLD_RECIPE,
        train_view_identity=view.identity,recipe_identity=recipe.identity,
        child=child,edges=tuple(summaries),oof=tuple(oof),fit_ledger=tuple(ledger))
