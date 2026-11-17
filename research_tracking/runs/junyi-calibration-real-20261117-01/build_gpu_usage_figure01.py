"""Dựng bảng/figure telemetry đã ghim, không đọc model hoặc dataset."""
import csv
import hashlib
import json
import os
from pathlib import Path
import statistics

BUNDLE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    font_cache = BUNDLE.parents[2]/'artifacts/akt/runtime/figure-cache'
    font_cache.mkdir(parents=True,exist_ok=True)
    os.environ['MPLCONFIGDIR'] = str(font_cache)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows, pins = [], {}
    for variant in ('A0','A1','A2','A3'):
        telemetry = BUNDLE/f'{variant}_GPU_UTILIZATION_ORIGINAL.jsonl'
        result_path = BUNDLE/f'{variant}_GPU_RESULT01.json'
        meta_path = BUNDLE/f'{variant}_GPU_METADATA_DRIVE01.json'
        metadata = json.loads(meta_path.read_text())
        entries = [entry for batch in metadata['publications'] for entry in batch['files']
                   if entry['path'] == 'gpu-utilization.jsonl']
        assert len(entries) == 1
        entry = entries[0]
        assert sha(telemetry) == entry['sha256'] and telemetry.stat().st_size == entry['bytes']
        samples = [json.loads(line) for line in telemetry.read_text().splitlines() if line]
        outer = json.loads(result_path.read_text())
        result = outer['result']
        assert result['counts']['targets'] == 1621484 and result['counts']['oov_targets'] == 0
        values = [sample['gpu_utilization'] for sample in samples]
        assert all(0 <= value <= 100 for value in values)
        rows.append(dict(variant=variant, targets=result['counts']['targets'],
            gpu_worker_seconds=outer['worker_seconds'], numeric_worker_seconds=result['worker_seconds'],
            nvml_samples=len(samples), mean_nvml_percent=statistics.mean(values),
            peak_nvml_percent=max(values), peak_vram_mib=max(s['vram_used_mib'] for s in samples),
            total_vram_mib=max(s['vram_total_mib'] for s in samples),
            telemetry_seconds=samples[-1]['seconds']-samples[0]['seconds'],
            telemetry_drive_id=entry['file_id'], telemetry_sha256=entry['sha256']))
        pins.update({p.name:sha(p) for p in (telemetry,result_path,meta_path)})
    csv_path = BUNDLE/'GPU_USAGE_COMPARISON01.csv'
    with csv_path.open('x',newline='',encoding='utf-8') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
    figure, axes = plt.subplots(1,3,figsize=(11.7,4.5),layout='constrained')
    panels = [('gpu_worker_seconds','Thời gian GPU worker','giây',1),
              ('mean_nvml_percent','Mức sử dụng GPU trung bình','%',1),
              ('peak_vram_mib','VRAM cao nhất','GiB',1/1024)]
    colors = ['#416e80','#628b93','#937441','#806697']
    for axis,(field,title,unit,scale) in zip(axes,panels):
        values = [row[field]*scale for row in rows]
        bars = axis.bar([r['variant'] for r in rows],values,color=colors,width=.58)
        axis.bar_label(bars,labels=[f'{v:.1f}' for v in values],padding=5)
        axis.set_title(title,pad=14,fontsize=12)
        axis.set_ylabel(unit)
        axis.set_ylim(0,max(values)*1.28)
        axis.spines[['top','right']].set_visible(False)
        axis.grid(axis='y',alpha=.18)
        axis.set_axisbelow(True)
    figure.suptitle('Suy luận calibration Junyi · 1.621.484 target mỗi phiên bản',fontsize=14)
    figure.supxlabel('Một lượt mỗi model trên H100. Trung bình mẫu NVML gồm nạp model và I/O.\n'
                    'Đây là suy luận calibration, chưa phải đánh giá độc lập hoặc benchmark lặp.',fontsize=10)
    for suffix in ('svg','png'):
        path = BUNDLE/f'GPU_USAGE_COMPARISON01.{suffix}'
        assert not path.exists()
        figure.savefig(path,dpi=160)
    plt.close(figure)
    acceptance = dict(status='FOUR_VARIANT_TELEMETRY_RECEIPTS_VERIFIED',rows=rows,source_pins=pins,
        limits_vi='Một lượt suy luận calibration/model, không phải training hoặc đánh giá độc lập. '
        'Mean NVML là trung bình số học các mẫu gần1giây gồm load/I/O; chưa dùng làm causal benchmark.',
        output_pins={path.name:sha(path) for path in (csv_path,BUNDLE/'GPU_USAGE_COMPARISON01.svg',
                                                     BUNDLE/'GPU_USAGE_COMPARISON01.png')})
    with (BUNDLE/'GPU_USAGE_ACCEPTANCE01.json').open('x',encoding='utf-8') as stream:
        json.dump(acceptance,stream,ensure_ascii=False,indent=2)
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
