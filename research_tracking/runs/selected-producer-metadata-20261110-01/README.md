# Nối metadata producer với checkpoint và quần thể

Ngày10/11/2026,39tests thực đạt trong `.venv`, gồm7ca metadata mới và32ca hồi quy. Fixtures kiểm cả9ID, ba schema thực, sai context/nguồn/runtime, selected epoch, flags refit, coverage, bytes và bảng kê COMPLETE. Lượt01 đạt39ca; sau review bổ sung đối chiếu full_selection của terminal AKT với coverage, lượt02 chạy lại39ca và4producer đều đạt. Không cộng hai lượt thành78ca độc lập.

## Đã đạt

A0, A1 expert, SAKT và GKT trên corpus engineering cùng84target đã qua đối chiếu invocation→claim→terminal→coverage→checkpoint. Các source file thực còn khớp exact vector của producer, được hash trước–sau qua reader bounded. Result02 ghi số file từng producer, SHA/size/path và thời gian. Runtime dùng đúng file đã pin. Raw invocation chứa spec được pin riêng với semantic spec/config identity, không đồng nhất hai loại hash.

Hai layouts baseline giữ population hash trung tính độc lập. AKT giữ scheme riêng, không gán nhãn nó thành K/y hash. Full K/y và336dòng được kiểm ở bundle selected-row-normalization-20261110-01, không nhân đôi exports/checkpoints ở đây.

## Phần còn thiếu

Expected claim/checkpoint identity của rehearsal này lấy từ snapshot đầu vào trước kiểm, chưa là request độc lập được review để chọn mô hình. Caller phải xác minh bytes/source snapshots trước gọi adapter thuần. Hàm trả typed claim và không cấp quyền thực thi. Chưa nối accepted-operation receipts/late-failure markers, chưa admission đủ9candidate, chưa freeze hoặc refit. Hash checkpoint không chứng minh nội dung tensor hoặc lịch sử optimizer.

Source193 cần refresh Gate sau khi ổn định tích hợp. Đây là bằng chứng phần mềm, chưa kết quả Main60/Junyi hoặc hiệu quả RQ3. Không thêm training/Holdout/Modal hoặc thay kết luận báo cáo GVHD. Gốc experiments và các bundle trước giữ nguyên.
