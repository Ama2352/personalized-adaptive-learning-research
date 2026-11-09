"""Nối E11 từ fresh120 đã nghiệm thu, giữ prefix cũ và đơn vị suy luận."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03'
BUNDLE = ROOT/'research_tracking/runs/thesis-rq2-e11-writing-20261110-01'
DRAFT = ROOT/'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


stats_path = ROOT/'research_tracking/runs/rq2-fresh-graph-source-analysis-20261110-01/descriptive_statistics.json'
stats = json.loads(stats_path.read_bytes())
summary = json.loads((NATIVE/'summary.json').read_bytes())
assert summary['primary_worlds']==120 and summary['primary_responses']==14400
assert summary['components']==60 and summary['contrasts']==30
assert stats['groups']['1000']['positive']==6 and stats['groups']['1000']['negative']==4
assert stats['groups']['1150']['positive']==8 and stats['groups']['1150']['negative']==2
assert stats['groups']['1300']['zero']==10
assert stats['trajectory_question_differences']==4936 and stats['trajectory_positions']==7200
section = '''

## 14. Bổ sung E11 về tái kiểm nguồn đồ thị trên mười khối mô phỏng mới

### Từ dấu hiệu ở ba khối đến một phép kiểm mới

E9 đã cho thấy đồ thị trong bộ ước lượng có thể đổi đường đi ngay cả khi cơ chế phạt thiếu tiên quyết của world không hoạt động. Ba khối cũ vẫn còn ít, dùng lại trạng thái đã lưu và có giới hạn về chứng minh trạng thái khởi đầu. Vì vậy, bước tiếp theo giữ cùng câu hỏi nhưng dùng mười khối khởi tạo mới đã định trước, đồng thời lưu trạng thái ban đầu thực tế của từng ca. Không chọn lại seed theo dấu của kết quả. [E11a]

Thiết kế gồm các block21010–21019. Mỗi block có ba mức khởi tạo1000,1150,1300, hai nguồn đồ thị trong bộ ước lượng và hai mức cơ chế phạt0/0,55. Đồ thị của môi trường và bộ chọn bài cùng giữ expert31. Chỉ đồ thị trong bộ ước lượng thay giữa expert31 và một learned31 đã có từ TRAIN. Hai đường tín hiệu và điều chỉnh theo cha cùng bật, điều chỉnh cục bộ tắt. Đây là mười block dùng một learned artifact cố định, chưa có mười đồ thị học độc lập. [E11a]

### Đại lượng được đối chiếu trả lời câu hỏi nào

Gọi Y là trung bình trên28 khái niệm của latent cuối trừ mức nền ban đầu. Trước hết lấy Y của expert trừ Y của learned tại cùng block, mức khởi tạo và mức cơ chế, được chênh lệch Q. Sau đó lấy Q khi bật cơ chế trừ Q khi tắt, được K. Phép trừ thứ hai giúp nhận diện sự tương tác giữa đổi nguồn đồ thị và cơ chế phạt trong chính simulator đang kiểm. Nó chưa tách riêng mọi mediator của đường đi. [E11b]

Không dùng nhóm năng lực cao làm một nhóm người học đối chứng giả định có parallel trends. Các mức khởi tạo là can thiệp được dựng trong mô phỏng. Các trạng thái và chuỗi uniform được ghép trong từng block. Diễn giải chính dựa vào các can thiệp đã kiểm soát và phương trình simulator. Thiết kế chưa cung cấp tác động nhân quả của prerequisite instruction trên người học thật.

| Mức khởi tạo | K trung bình | K nhỏ nhất đến lớn nhất | Block dương / âm / bằng0 |
|---|---:|---|---|
|1000|+0,004496|−0,069250 đến+0,095294|6 /4 /0|
|1150|+0,024530|−0,004716 đến+0,079790|8 /2 /0|
|1300|0|0 đến0|0 /0 /10|

Các giá trị dùng thang điểm latent Elo của world. Ở hai mức thấp hơn, K đổi dấu giữa các block. Trung bình dương cần được đọc cùng các trường hợp âm. Đây là thống kê mô tả, chưa có CI hoặc kiểm định xác lập ưu thế ổn định. Đơn vị độc lập được dự kiến là block, không phải120 world hoặc14.400 lần trả lời. [E11b]

### Đối chứng bất hoạt và thay đổi đường đi

Ở mức1300, K bằng0 ở cả mười block, phù hợp với20 cặp high-control đã khớp semantic trace và endpoint giữa hai mức cơ chế. Zero này là hành vi được dự kiến từ điều kiện bất hoạt của penalty. Nó chưa phải mười bằng chứng độc lập rằng mọi tác dụng của graph đều biến mất khi năng lực cao. Chênh lệch Q ở mức1300 vẫn khác0 tại cả20 điều kiện, có cả dấu dương lẫn âm. Như vậy, tác động của đổi nguồn đồ thị còn đi qua các đường ngoài riêng penalty. Phép kiểm hiện tại chưa phân rã signal, parent adaptation và challenge thành các tác động riêng. [E11c]

Cả60 cặp expert–learned có ít nhất một câu hỏi khác nhau, tổng cộng4936/7200 vị trí ordinal khác question ID. Nhãn trước lần phân kỳ đầu khớp trong từng cặp. Sau phân kỳ, cùng ordinal chưa bảo đảm cùng câu và cùng history. Vì vậy, các vị trí đó chưa là shared-target population để đối chiếu Log Loss của hai model. Thay đổi hành động đã được quan sát, còn chất lượng dự báo trên cùng dòng cần một phép kiểm riêng. [E11c]

### Điều được củng cố và điều cần giữ mở

Mười block mới duy trì chẩn đoán rằng khác biệt giữa đồ thị có thể tồn tại khi đường penalty bất hoạt. Dấu hiệu theo mức khởi tạo cũng cần kiểm lại. Chẳng hạn, K ở mức1150 có tám block dương và hai âm, còn cả ba block cũ của E9 đều âm. Sự khác nhau về dấu chưa là một kết luận đảo chiều có ý nghĩa thống kê. Hai tập block có population và bằng chứng initial state khác nhau, nên chưa pooling thành một mẫu13block. [E11d]

E11 bổ sung đối chứng có trạng thái khởi đầu được lưu thực và khả năng lặp lại trên các block mới. RQ1 vẫn cần đo chuỗi dự báo, hiệu chỉnh, quyết định và hành động trên quần thể phù hợp. RQ2 vẫn còn graph noise/quality conditions cùng thống kê theo block. RQ3 tiếp tục cần các biến thể neural đã huấn luyện, so sánh công bằng và closed-loop outcomes. Các kết quả mô tả hiện tại chưa hoàn tất một RQ.

### Nguồn bổ sung E11

- **E11a** dùng [acceptance recovery](../runs/rq2-fresh-graph-recovery-20261110-01/acceptance.json), public plan và initial-state hashes. Logical120/14.400 được tách khỏi physical121/14.430 có30lượt replay, giữ parent failure.
- **E11b** dùng [thống kê mô tả đã lưu](../runs/rq2-fresh-graph-source-analysis-20261110-01/descriptive_statistics.json), đủ60 Q và30 K đã kiểm số học. Công thức Y nằm trong source worker được đóng cùng recovery bundle.
- **E11c** dùng20highcontrols,60trajectory pairs và [review độc lập](../runs/rq2-fresh-graph-source-analysis-20261110-01/independent_review.md), có exact pointers để kiểm lại từng giá trị.
- **E11d** đối chiếu nguồn E9 đã nghiệm thu với [báo cáo fresh120](rq2_fresh_graph_source_replication_20261110.md). Việc viết E11 không thực hiện thêm tương tác hoặc tăng cỡ mẫu của bất kỳ phép kiểm nào.

[Bundle viết E11](../runs/thesis-rq2-e11-writing-20261110-01/README.md) giữ before/after và source map. Toàn bộ phần trước E11 được bảo toàn byte.
'''
original = DRAFT.read_bytes()
assert b'## 14.' not in original
BUNDLE.mkdir(exist_ok=False)
write(BUNDLE/'inventory_before_copy.json',{DRAFT.relative_to(ROOT).as_posix():sha(DRAFT)})
shutil.copyfile(DRAFT,BUNDLE/'before.md')
assert (BUNDLE/'before.md').read_bytes()==original
with DRAFT.open('ab') as stream:
    stream.write(section.encode('utf-8'))
assert DRAFT.read_bytes()[:len(original)]==original
shutil.copyfile(DRAFT,BUNDLE/'after.md')
inputs = [stats_path,NATIVE/'summary.json',NATIVE/'graph_source_contrasts.json',
    NATIVE/'conditional_lambda_contrasts.json',NATIVE/'trajectory_pairs.json',NATIVE/'high_controls.json',
    ROOT/'research_tracking/runs/rq2-fresh-graph-source-analysis-20261110-01/independent_review.md']
write(BUNDLE/'source_map.json',dict(input_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in inputs},
    original_prefix_bytes=len(original),prefix_preserved=True,
    checked_claims=dict(blocks=10,worlds=120,responses=14400,Q=60,K=30,
        signs_1000=[6,4,0],signs_1150=[8,2,0],signs_1300=[0,0,10],
        trajectory_pairs=60,different_question_positions=4936,total_positions=7200),
    pending='Independent prose review before commit.',new_model_calls=0))
shutil.copyfile(Path(__file__).resolve(),BUNDLE/Path(__file__).name)
(BUNDLE/'README.md').write_text('# Viết E11 từ fresh120 đã nghiệm thu\n\n'
    'Bổ sung phần14 sau E10, bảo toàn byte prefix. Có source map và số liệu đã kiểm, '
    'giải thích đối chứng bất hoạt, đơn vị block và giới hạn so E9. '
    'Không CI/pvalue, pooling13blocks hoặcmodelcall mới. Independent prose review còn chờ.\n',encoding='utf-8')
write(BUNDLE/'manifest.json',dict(kind='thesis_writing_from_fresh120_closed_results',
    outputs_sha256={p.relative_to(BUNDLE).as_posix():sha(p) for p in BUNDLE.rglob('*') if p.is_file()}))
print('E11_PUBLISHED_NUMERIC_PREFIX_CHECKED_PENDING_INDEPENDENT_REVIEW',len(original))
