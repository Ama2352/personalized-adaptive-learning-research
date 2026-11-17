"""Fit V1 trên CPU local với SQLite, giữ nguyên solver lấy từ source V1.

Đây là adapter biểu diễn dữ liệu, không thay nguồn KT hoặc guard fitter cũ.
Receipt riêng ghi source V1, source adapter và tài nguyên thực đo.
"""
import ast
from dataclasses import asdict, dataclass
import hashlib
import inspect
import json
import math
from pathlib import Path
import sqlite3
import time

import psutil
from knowledge_tracing import response_calibration as v1


@dataclass(frozen=True)
class LocalCalibrationBudget:
    max_targets: int
    max_rss_bytes: int = 512 * 1024**2
    max_database_bytes: int = 2 * 1024**3
    max_seconds: float = 90

    def __post_init__(self):
        for name in ('max_targets','max_rss_bytes','max_database_bytes'):
            if type(getattr(self,name)) is not int or getattr(self,name) <= 0:
                raise ValueError('explicit positive local calibration budget required')
        if isinstance(self.max_seconds,bool) or not isinstance(self.max_seconds,(int,float)) or not math.isfinite(self.max_seconds) or not 0 < self.max_seconds <= 86400:
            raise ValueError('bounded local calibration wall time required')


class _Monitor:
    def __init__(self,budget,database):
        self.budget=budget
        self.database=database
        self.started=time.monotonic()
        self.process=psutil.Process()
        self.peak_rss=0
        self.check()

    def check(self):
        rss=self.process.memory_info().rss
        self.peak_rss=max(self.peak_rss,rss)
        if rss > self.budget.max_rss_bytes:
            raise MemoryError('local calibration RSS budget exceeded')
        if time.monotonic()-self.started > self.budget.max_seconds:
            raise TimeoutError('local calibration wall budget exceeded')
        if self.database.exists() and self.database.stat().st_size > self.budget.max_database_bytes:
            raise MemoryError('local calibration database budget exceeded')


def _solver():
    """Biên dịch nguyên phần loss và golden search từ hàm public V1 hiện hành."""
    tree=ast.parse(inspect.getsource(v1.fit_temperature))
    body=tree.body[0].body
    start=next(i for i,node in enumerate(body) if isinstance(node,ast.FunctionDef) and node.name=='loss')
    arguments=ast.arguments(posonlyargs=[],args=[ast.arg(arg=name) for name in ('logits','common','max_evaluations')],
        kwonlyargs=[],kw_defaults=[],defaults=[])
    function=ast.FunctionDef(name='_original_solver',args=arguments,body=body[start:],decorator_list=[])
    module=ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[]))
    namespace=dict(vars(v1))
    exec(compile(module,'<unchanged-public-V1-solver>','exec'),namespace)
    digest=hashlib.sha256(ast.dump(module,include_attributes=False).encode()).hexdigest()
    return namespace['_original_solver'],digest


class _Logits:
    def __init__(self,connection,count,monitor):
        self.connection,self.count,self.monitor=connection,count,monitor

    def __len__(self):
        return self.count

    def __iter__(self):
        cursor=self.connection.execute('SELECT logit,correct FROM targets WHERE probability IS NOT NULL ORDER BY learner,event,item,history')
        for index,row in enumerate(cursor):
            if index%1024==0:
                self.monitor.check()
            yield row


def _database(path):
    path=Path(path).absolute()
    if path.resolve()!=path or path.exists() or not path.parent.is_dir():
        raise ValueError('new physical calibration database required')
    if any(part.is_symlink() or getattr(part,'is_junction',lambda:False)() for part in (path,*path.parents)):
        raise ValueError('new physical calibration database required')
    connection=sqlite3.connect(path)
    connection.execute('PRAGMA cache_size=-8192')
    connection.execute('PRAGMA mmap_size=0')
    connection.execute('PRAGMA temp_store=FILE')
    connection.execute('CREATE TABLE targets(learner TEXT NOT NULL,event TEXT NOT NULL,item TEXT NOT NULL,history TEXT NOT NULL,payload TEXT NOT NULL,correct INTEGER NOT NULL,probability REAL,reason TEXT NOT NULL,logit REAL, PRIMARY KEY(learner,event,item,history),UNIQUE(learner,event)) WITHOUT ROWID')
    connection.execute('CREATE TABLE expected(learner TEXT NOT NULL,event TEXT NOT NULL,item TEXT NOT NULL,history TEXT NOT NULL,PRIMARY KEY(learner,event,item,history)) WITHOUT ROWID')
    connection.execute('CREATE INDEX unsupported_reasons ON targets(reason) WHERE probability IS NULL')
    return path,connection


def fit_temperature_spooled(targets, *, binding, partition, expected_target_keys,
        database, budget, max_evaluations=200):
    """Trả payload V1 như fitter public, dữ liệu trung gian được giữ trên đĩa.

    Caller vẫn phải kiểm raw/prefix/population trước API này. Database và receipt
    là đầu ra mới, không sửa checkpoint hoặc calibrator đã tồn tại.
    """
    if type(binding) is not v1.PredictionBinding or type(partition) is not v1.CalibrationPartition or binding.split_sha256!=partition.split_sha256:
        raise ValueError('calibration partition/binding mismatch')
    if type(max_evaluations) is not int or not 4<=max_evaluations<=200:
        raise ValueError('objective evaluation budget 4..200')
    if type(budget) is not LocalCalibrationBudget:
        raise ValueError('explicit local calibration budget required')
    receipt=Path(database).with_suffix('.receipt.json')
    if receipt.exists():
        raise ValueError('new physical calibration receipt required')
    database,connection=_database(database)
    try:
        monitor=_Monitor(budget,database)
        with connection:
            count=0
            for count,row in enumerate(targets,1):
                if type(row) is not v1.CalibrationTarget:
                    raise ValueError('calibration target schema')
                if count>budget.max_targets:
                    raise MemoryError('local calibration target budget exceeded')
                payload=json.dumps(asdict(row),sort_keys=True,separators=(',',':'),allow_nan=False)
                if len(payload)>1024**2:
                    raise ValueError('bounded calibration target required')
                connection.execute('INSERT INTO targets VALUES(?,?,?,?,?,?,?,?,?)',
                    (row.learner_id,row.event_id,row.item_id,row.history_sha256,payload,row.correct,
                     row.probability,row.support_reason,None if row.probability is None else v1._logit(row.probability)))
                if count%1024==0:
                    monitor.check()
            expected_count=0
            for expected_count,key in enumerate(expected_target_keys,1):
                key=tuple(key)
                if expected_count>budget.max_targets:
                    raise MemoryError('local calibration expected target budget exceeded')
                if len(key)!=4 or any(type(value) is not str for value in key):
                    raise ValueError('calibration target key schema')
                connection.execute('INSERT INTO expected VALUES(?,?,?,?)',key)
                if expected_count%1024==0:
                    monitor.check()
        missing=connection.execute('SELECT 1 FROM expected LEFT JOIN targets USING(learner,event,item,history) WHERE targets.learner IS NULL LIMIT 1').fetchone()
        extra=connection.execute('SELECT 1 FROM targets LEFT JOIN expected USING(learner,event,item,history) WHERE expected.learner IS NULL LIMIT 1').fetchone()
        learners={row[0] for row in connection.execute('SELECT DISTINCT learner FROM targets')}
        if count!=expected_count or missing or extra or learners!=set(partition.calibration_learners):
            raise ValueError('missing/extra/duplicate calibration population or wrong-role learner')
        digest=hashlib.sha256(b'[')
        for index,(payload,) in enumerate(connection.execute('SELECT payload FROM targets ORDER BY learner,event,item,history')):
            if index:
                digest.update(b',')
            digest.update(payload.encode())
            if index%1024==0:
                monitor.check()
        digest.update(b']')
        counts=tuple(connection.execute('SELECT COUNT(*) FROM targets WHERE probability IS NOT NULL AND correct=?',(correct,)).fetchone()[0] for correct in (0,1))
        unsupported=tuple(connection.execute('SELECT reason,COUNT(*) FROM targets INDEXED BY unsupported_reasons WHERE probability IS NULL GROUP BY reason ORDER BY reason'))
        common=dict(binding=binding,partition_sha256=partition.identity,targets_sha256=digest.hexdigest(),
            implementation_sha256=v1.implementation_identity(),total_targets=count,
            supported_targets=sum(counts),class_counts=counts,unsupported_counts=unsupported)
        solve,solver_sha=_solver()
        if not sum(counts) or min(counts)==0:
            result=v1.TemperatureCalibration(**common,status='unsupported_no_predictions' if not sum(counts) else 'unsupported_two_class_labels_required',
                temperature=None,objective_evaluations=0,raw_log_loss=None,calibrated_log_loss=None)
        else:
            result=solve(_Logits(connection,sum(counts),monitor),common,max_evaluations)
        monitor.check()
        receipt.write_text(json.dumps(dict(status='SPOOLED_V1_CALIBRATION_COMPLETE',
            adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            original_v1_identity=v1.implementation_identity(),solver_ast_sha256=solver_sha,
            budget=asdict(budget),sampled_peak_rss_bytes=monitor.peak_rss,
            wall_seconds=time.monotonic()-monitor.started,database_bytes=database.stat().st_size,
            targets=count,calibration_identity=result.identity,
            resource_semantics='RSS checked every1024rows; not OS hard limit'),indent=2)+'\n',encoding='utf-8')
        return result
    except sqlite3.IntegrityError as error:
        raise ValueError('missing/extra/duplicate calibration population or wrong-role learner') from error
    finally:
        connection.close()
