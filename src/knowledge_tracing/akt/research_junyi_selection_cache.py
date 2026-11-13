"""Cache selection có window nhân quả và sidecar đáp án tách biệt, chỉ CPU.

Dùng lại window-cache đã kiểm, giữ nguyên iterator record/batch hiện hành.
Không cache xác suất hoặc logits của checkpoint khác.
"""
import hashlib
import json
import sqlite3
import time

import numpy as np

from .prediction_batch import _validate_learner
from .research_junyi_engineering import file_sha, write_json
from .research_junyi_window_cache import (
    _owned_root, build_junyi_window_cache, JunyiWindowCacheSession)
from .types import KTEvent, UnseenTarget
from .windows import iter_windows

KIND='JUNYI_SELECTION_WINDOW_SIDECAR_V1'


def _need(ok,message):
    if not ok:
        raise ValueError(message)


def _population_update(digest,event):
    key=(event.source_row,event.user_id,event.exercise,event.time_done,event.correct,event.suggested,event.fold)
    digest.update(json.dumps(key,separators=(',',':')).encode()+b'\n')


def _binding(view,encoding,source_sha):
    encoding.assert_for(view)
    _need(view.scope=='raw_selection10' and len(source_sha)==64, 'Selection-only pinned source required')
    return dict(kind=KIND,phase_sha256=view.identity,encoding_sha256=encoding.identity,
                source_sha256=source_sha,context=100,target_block=100)


def build_selection_cache(root,learners,*,view,encoding,source_sha256,expected_targets,
                          max_seconds,max_rss_bytes):
    """Chỉ công bố manifest gốc sau khi window và metadata đều đầy đủ."""
    import psutil
    root=_owned_root(root)
    binding=_binding(view,encoding,source_sha256)
    _need(type(expected_targets) is int and expected_targets>0 and max_seconds>0 and max_rss_bytes>0,
          'Bounded selection cache request required')
    root.mkdir(parents=True,exist_ok=False)
    write_json(root/'BUILD_REQUEST.json',dict(binding=binding,expected_targets=expected_targets,
        max_seconds=max_seconds,max_rss_bytes=max_rss_bytes))
    started=time.monotonic()
    process=psutil.Process()
    connection=sqlite3.connect(root/'events.sqlite')
    connection.execute('CREATE TABLE events (source_row INTEGER PRIMARY KEY,user_id TEXT NOT NULL,'
        'exercise TEXT NOT NULL,time_done INTEGER NOT NULL,correct INTEGER NOT NULL,'
        'suggested INTEGER NOT NULL,fold INTEGER NOT NULL)')
    count=0
    population=hashlib.sha256()

    def windows():
        nonlocal count
        previous=None
        seen=set()
        allowed=frozenset(view.users)
        for learner in learners:
            _need(time.monotonic()-started<=max_seconds and process.memory_info().rss<=max_rss_bytes,
                  'Selection cache resource limit')
            _validate_learner(learner,previous)
            _need(learner.user_id in allowed and learner.user_id not in seen and learner.fold in (0,1,2,3),
                  'Foreign/duplicate selection learner')
            rows=[]
            for event in learner.events:
                rows.append((event.source_row,event.user_id,event.exercise,event.time_done,
                             event.correct,event.suggested,event.fold))
                _population_update(population,event)
            connection.executemany('INSERT INTO events VALUES (?,?,?,?,?,?,?)',rows)
            count+=len(rows)
            _need(count<=expected_targets,'Selection cache target cap')
            seen.add(learner.user_id)
            previous=learner.user_id
            yield from iter_windows(learner,encoding.native,context=100,target_block=100,training=False)
        _need(seen==allowed and count==expected_targets,'Incomplete selection source coverage')

    try:
        result=build_junyi_window_cache(root/'windows',windows(),view=view,encoding=encoding,
            source_data_sha256=source_sha256,expected_target_rows=expected_targets,compressed=False)
        _need(binding==_binding(view,encoding,source_sha256),'Selection binding changed')
        _need(time.monotonic()-started<=max_seconds and process.memory_info().rss<=max_rss_bytes,
              'Selection cache resource limit')
        connection.commit()
        connection.close()
        manifest=dict(status='COMPLETE',binding=binding,targets=count,
            population_sha256=population.hexdigest(),events_sha256=file_sha(root/'events.sqlite'),
            window_manifest_sha256=result['manifest_sha256'])
        write_json(root/'manifest.json',manifest)
        receipt=dict(status='COMPLETE',manifest_sha256=file_sha(root/'manifest.json'),targets=count,
            population_sha256=population.hexdigest(),wall_seconds=time.monotonic()-started)
        write_json(root/'COMPLETE.json',dict(kind=KIND,manifest_sha256=receipt['manifest_sha256']))
        return receipt
    except BaseException as error:
        connection.close()
        write_json(root/'failure.json',dict(type=type(error).__name__,error=str(error)))
        raise


class SelectionCacheSession:
    """Strict admission một lần, replay từng shard và lookup metadata chỉ đọc."""
    def __init__(self,root,*,view,encoding,source_sha256,expected_targets,expected_manifest_sha256):
        self.root=_owned_root(root)
        self.view=view
        self.encoding=encoding
        self._binding=_binding(view,encoding,source_sha256)
        self._pin=expected_manifest_sha256
        self._check_control()
        self.manifest=json.loads((self.root/'manifest.json').read_text(encoding='utf-8'))
        self._manifest_json=json.dumps(self.manifest,sort_keys=True,separators=(',',':'))
        _need(self.manifest['status']=='COMPLETE' and self.manifest['binding']==self._binding
              and self.manifest['targets']==expected_targets,'Selection cache binding/population mismatch')
        self._events=self.root/'events.sqlite'
        _need(not self._events.is_symlink() and file_sha(self._events)==self.manifest['events_sha256'],
              'Selection metadata SHA mismatch')
        stat=self._events.stat()
        self._stat=(stat.st_size,stat.st_mtime_ns,stat.st_ino)
        self.windows=JunyiWindowCacheSession(self.root/'windows',view=view,encoding=encoding,
            source_data_sha256=source_sha256,expected_target_rows=expected_targets,
            expected_manifest_sha256=self.manifest['window_manifest_sha256'])
        # Kiểm join/coverage trước khi GPU dùng cache, không chỉ dựa COMPLETE marker.
        for _ in self.iter_prepared():
            pass

    @property
    def identity(self):
        return self._pin

    def _check_control(self):
        _need(file_sha(self.root/'manifest.json')==self._pin
              and json.loads((self.root/'COMPLETE.json').read_text())==dict(kind=KIND,manifest_sha256=self._pin),
              'Selection cache control changed/incomplete')

    def _check(self):
        self._check_control()
        _need(json.dumps(self.manifest,sort_keys=True,separators=(',',':'))==self._manifest_json,
              'Selection session manifest changed')
        _need(_binding(self.view,self.encoding,self._binding['source_sha256'])==self._binding,
              'Selection cache phase/encoding changed')
        stat=self._events.stat()
        _need((stat.st_size,stat.st_mtime_ns,stat.st_ino)==self._stat,'Selection metadata changed')

    def iter_prepared(self):
        self._check()
        population=hashlib.sha256()
        count=0
        connection=sqlite3.connect(self._events.as_uri()+'?mode=ro&immutable=1',uri=True)
        try:
            # Stream metadata theo đúng thứ tự learner/thời gian của builder.
            # Tránh hàng chục nghìn query IN và lookup ngẫu nhiên từng window.
            connection.execute('PRAGMA temp_store=MEMORY')
            _need(connection.execute('SELECT count(*) FROM events').fetchone()[0]==self.manifest['targets'],
                  'Selection metadata count differs')
            cursor=connection.execute('SELECT source_row,user_id,exercise,time_done,correct,suggested,fold '
                'FROM events ORDER BY user_id,time_done,source_row')
            for record in self.windows.iter_windows():
                if type(record) is UnseenTarget:
                    requested=(record.event.source_row,)
                else:
                    indices=np.flatnonzero(record.target_mask)
                    requested=tuple(int(record.inputs.source_rows[i]) for i in indices)
                rows=cursor.fetchmany(len(requested))
                _need(tuple(row[0] for row in rows)==requested,'Missing/out-of-order selection target metadata')
                events=tuple(KTEvent(row[1],row[2],row[3],row[0],row[4],row[5],row[6]) for row in rows)
                for event in events:
                    _population_update(population,event)
                count+=len(events)
                if type(record) is UnseenTarget:
                    _need(events==(record.event,),'OOV sidecar differs')
                    yield record
                else:
                    for index,event in zip(indices,events):
                        _need(event.user_id==record.inputs.user_ids[index]
                              and event.time_done==int(record.inputs.timestamps[index])
                              and event.exercise==self.encoding.native.vocabulary.values[int(record.inputs.item_ids[index])],
                              'Selection window/event join differs')
                    yield record,tuple((int(index),event) for index,event in zip(indices,events))
            _need(count==self.manifest['targets'] and population.hexdigest()==self.manifest['population_sha256'],
                  'Selection replay population differs')
            _need(cursor.fetchone() is None,'Extra selection metadata rows')
            self._check()
        finally:
            connection.close()
