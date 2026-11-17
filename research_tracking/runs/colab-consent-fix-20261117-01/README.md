# Xử lý xác nhận thiếu quyền Colab

## Nguyên nhân đã đối chiếu

Lần đăng nhập thật do root theo dõi dừng với `Warning` sau khi người dùng bỏ sót một quyền trong hộp xác nhận. Token Colab chưa được lưu. Mã `oauthlib` đang cài cho thấy khi scope trả về khác scope yêu cầu, thư viện đặt `token`, `new_scope`, `old_scope` lên đối tượng Warning rồi raise trước khi `requests_oauthlib` gắn response vào `session.token`.

Google helper dựng `Credentials.scopes` từ `session.scope`, trong khi `granted_scopes` lấy từ token response. Vì vậy kiểm `has_scopes` trên scope được yêu cầu chưa đủ để khẳng định người dùng đã cấp từng quyền.

## Sửa tối thiểu

`scripts/akt/colab_session.py` đọc quyền thực được cấp. Ba quyền bắt buộc là identity OpenID, email và Colab runtime. `email` được chuẩn hóa thành scope `userinfo.email` tương đương. Thiếu quyền nào thì báo tên quyền an toàn và dừng trước khi ghi token. Không in Warning gốc, token hoặc OAuth URL.

Với scope Warning nhưng toàn bộ quyền bắt buộc đã được cấp, client chỉ phục hồi khi có token response thật trên Warning/session và tập scope response khớp `new_scope`. Sau đó dựng lại Credentials với `scopes` bằng tập quyền thực. Extra scopes hợp lệ được giữ đúng, không giả định chúng được cấp từ scope yêu cầu.

Helper `save_credentials` cũng kiểm quyền thực sau refresh tự động của AuthorizedSession trước mọi lần persist. Nếu refresh trả thiếu quyền, không ghi lại scope cũ như thể còn đầy đủ. Không đặt `OAUTHLIB_RELAX_TOKEN_SCOPE` hoặc thay kiểm quyền bằng một quy tắc bỏ qua lỗi.

Đường login giữ Edge, callback localhost và timeout600giây. Token Colab dùng file riêng trên D, token Drive và client secret cũ được giữ nguyên.

## Đã kiểm

16kiểm thử offline đạt trong0,57giây. Chúng bao gồm thiếu quyền có/không có Warning, đủ quyền kèm extra-scope Warning, alias email, refresh tự động bị giảm quyền, không persist token thiếu quyền, cùng các kiểm proxy/private/error cũ.

Logs nằm tại `../colab-persistent-session-20261117-01/consent-red01.txt`, `consent-refresh-red01.txt`, `consent01.txt/xml`, `consent02.txt/xml`. Hai lượt red cho thấy các regression mới thất bại trước sửa. Các chuỗi SECRET/URL trong logs red là fixture giả để kiểm không lộ nội dung lỗi, không phải credential thật.

Chưa chạy lại đăng nhập thật trong nhánh này. Root cần mở lại login và người dùng chọn đủ quyền, rồi mới xác nhận được read-only API hoạt động. Không tạo runtime, chạy code từ xa hoặc dùng compute trong gói sửa.

Nguồn đối chiếu local gồm `oauthlib/oauth2/rfc6749/parameters.py`, `requests_oauthlib/oauth2_session.py`, `google_auth_oauthlib/helpers.py`. Manifest giữ SHA các source library và source/tests mới.
