"""Dựng bảng tiến độ từ artifact đã lưu, không nạp mô hình hoặc chạy cloud."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
NATIVE = ROOT / "experiments/akt/results/modal-junyi-main-selected-t4-20261112-02"
receipt = json.loads((NATIVE / "remote-receipt.json").read_text())
archive = NATIVE / "artifacts.zip"
digest = hashlib.sha256()
with archive.open("rb") as stream:
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        digest.update(block)
assert digest.hexdigest() == receipt["archive_sha256"]
assert archive.stat().st_size == receipt["archive_bytes"]
guard = json.loads((NATIVE / "app-budget-guard.json").read_text())
assert guard["stop_acknowledged"] is True
history = receipt["worker_result"]["terminal"]["history"]
epochs = []
with zipfile.ZipFile(archive) as bundle:
    for name in bundle.namelist():
        if name.endswith("-training.json"):
            stats = json.loads(bundle.read(name))
            number = int(Path(name).name.split("-")[1])
            epochs.append({
                "epoch": number,
                "complete": stats["complete"],
                "targets": stats["valid_targets"],
                "optimizer_steps": stats["optimizer_steps"],
                "train_seconds": stats["resource"]["wall_seconds"],
                "archive_member": name,
            })
epochs.sort(key=lambda entry: entry["epoch"])
assert [entry["epoch"] for entry in epochs if entry["complete"]] == [1, 2]
assert all(entry["targets"] == 13347331 for entry in epochs[:2])
assert [entry["epoch"] for entry in history] == [1, 2]
assert all(entry["validation"]["targets"] == 1600343 for entry in history)
snapshot = {
    "as_of_date": "2026-11-12",
    "status": receipt["status"],
    "archive_sha256_verified": digest.hexdigest(),
    "archive_bytes": archive.stat().st_size,
    "app_stop_acknowledged": True,
    "epochs": epochs,
    "validation_history": history,
    "limitations": "Hai epoch hoàn tất, epoch3 dở dang. Chưa selected cuối, refit, calibration hoặc đánh giá độc lập.",
}
(BUNDLE / "training-status-20261112.json").write_text(
    json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({"status": "PASS", "epochs": epochs, "archive_verified": True}, ensure_ascii=False))
