"""Đo lại physical parents sau materialize/guard, không gán ngược thời điểm."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent


def main():
    rows = []
    for path in (ROOT / 'experiments/akt/configs', ROOT / 'experiments/akt/authorizations', PREP):
        checks = []
        for ancestor in (*reversed(path.parents), path):
            if ancestor.is_absolute():
                assert ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction()
                assert ancestor.resolve() == ancestor.absolute()
                checks.append(dict(path=str(ancestor), directory=True, symlink=False, junction=False))
        rows.append(dict(path=path.relative_to(ROOT).as_posix(), ancestors=checks))
    record = dict(kind='POST_MATERIALIZATION_AND_GUARD_PHYSICAL_PARENT_RECHECK',
                  observed_utc=datetime.now(timezone.utc).isoformat(), parents=rows,
                  earlier_precheck_origin='Root tool006417/g2:3402 transcript, separate from this later measurement',
                  recipe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope_vi='Kiểm trạng thái vật lý hiện tại sau guard, không backdate thành receipt trước materialize.')
    target = PREP / 'main_guard_parent_postcheck01.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status='PHYSICAL_PARENT_RECHECK_ACCEPTED', sha256=hashlib.sha256(target.read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
