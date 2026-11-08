"""Observer local: baseline trước patch, restore toàn bộ rồi mới final-check.

Chỉ phục vụ bounded engineering workers, không monkeypatch thuật toán/optimizer.
Inherited targets phải capture trước patch đầu tiên; dynamic own methods mới
được capture muộn (AKT/Architecture class vừa load thật trong provenance phase).
"""


def label(obj):
    if isinstance(obj, type):
        return obj.__module__+'.'+obj.__qualname__
    return getattr(obj, '__name__', type(obj).__name__)


class MethodPatches:
    def __init__(self):
        self._snapshots = {}
        self._order = []
        self._started = False
        self._restored = False

    def capture(self, obj, name):
        key = (id(obj), name)
        if key in self._snapshots:
            return
        if self._restored:
            raise RuntimeError('restored observer is closed')
        own = name in vars(obj)
        if self._started and not own:
            raise RuntimeError('inherited baseline must be captured before any patch')
        inherited_from = None
        if isinstance(obj, type) and not own:
            inherited_from = next((label(base) for base in obj.__mro__[1:] if name in vars(base)), None)
        self._snapshots[key] = dict(obj=obj, name=name, resolved=getattr(obj, name), own=own,
            own_value=vars(obj).get(name), inherited_from=inherited_from)

    def capture_many(self, targets):
        if self._started:
            raise RuntimeError('all static baselines precede patches')
        for obj, name in targets:
            self.capture(obj, name)

    def patch(self, obj, name, value):
        if self._restored:
            raise RuntimeError('restored observer is closed')
        self.capture(obj, name)
        key = (id(obj), name)
        if key in self._order:
            raise RuntimeError('target patched twice by observer')
        # Register before assignment so assignment failure still has a baseline.
        self._order.append(key)
        self._started = True
        setattr(obj, name, value)

    def restore(self):
        if self._restored:
            raise RuntimeError('restore is one-shot')
        self._restored = True
        errors = []
        # Pass1: no resolved-attribute comparison while parents remain patched.
        for key in reversed(self._order):
            row = self._snapshots[key]; obj, name = row['obj'], row['name']
            try:
                if row['own']:
                    setattr(obj, name, row['own_value'])
                elif name in vars(obj):
                    delattr(obj, name)
            except BaseException as error:
                errors.append(dict(owner=label(obj), name=name, type=type(error).__name__, message=str(error)))
        # Pass2: every entry checked against TRUE pre-patch baseline, including
        # inherited resolution and exact own-attribute presence/value identity.
        checks = []
        for key in self._order:
            row = self._snapshots[key]; obj, name = row['obj'], row['name']
            try:
                own_now = name in vars(obj)
                check = dict(owner=label(obj), name=name, expected_own=row['own'], actual_own=own_now,
                    baseline_inherited_from=row['inherited_from'],
                    own_presence_matches=own_now == row['own'],
                    own_value_matches=not row['own'] or vars(obj).get(name) is row['own_value'],
                    resolved_identity_matches=getattr(obj, name) is row['resolved'])
                check['restored'] = all(check[field] for field in
                    ('own_presence_matches','own_value_matches','resolved_identity_matches'))
            except BaseException as error:
                check = dict(owner=label(obj), name=name, restored=False,
                    error_type=type(error).__name__, error=str(error))
            checks.append(check)
        return dict(accepted=bool(checks) and not errors and all(row['restored'] for row in checks),
                    patched_targets=len(self._order), restore_errors=errors, final_checks=checks)
