# Ghim SHA riêng của plan bên trong ZIP

Root đã xác định nguyên nhân thực của ValueError ở lượt stage01. File INPUT_PLAN04.json local dùng CRLF, còn CLOUD_INPUT_PLAN.json trong ZIP dùng LF. Hai bản JSON bằng nhau về nội dung nhưng byte khác nhau. ZIP, model và dữ liệu không đổi.

- Embedded plan có 33.831 byte, SHA-256 `0a5aea93f57206d04ee3094f1c13ae6d64aaa0864c95cf67f4e9ebcca7a7baef`.
- Plan local có 34.758 byte, SHA-256 `a552518a231ee5d432e88080220e22ab161c196150b42addea08f0f94aed64dc`.
- ZIP giữ SHA-256 `a34cee8e961baf7056e8f16159d2b9a25afcca72f3c19b3a37bd0d711aab2d6a`.

Worker hiện ghim đúng raw SHA của embedded plan. Pin file local được ghi riêng trong STAGED.json. Không chuẩn hóa newline để vượt kiểm, không thay raw check bằng so sánh JSON. Root giữ đối chiếu binding thực trong bundle input.

`tests06.txt` đạt **19/19** trong 0,54 giây. Ca hồi quy dựng LF embedded và CRLF local, xác nhận JSON bằng nhau, SHA khác nhau, từ chối raw pin local và chỉ chấp nhận pin đúng của embedded. MANIFEST04.json ghi bản nguồn mới. Root thực hiện retry CPU riêng sau review.
