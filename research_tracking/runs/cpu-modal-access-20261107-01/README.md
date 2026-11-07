# Kiểm kết nối Modal chỉ đọc

User báo đã login/token thành công và yêu cầu kiểm kỹ, không dùng credits tùy tiện. Probe dùng SDK1.6.3 với projectprivateconfig/profilekltn. Chỉ handshake xác thực, TokenInfoGet và WorkspaceSettings nếu đúng workspace. Không gọi app/function/image/Volume, không thay account settings. Không lưu token ID/secret, raw SDKstdout/stderr hoặc hash privateconfig. Source probe và kết quả whitelist được lưu để audit.

Tên workspace/expiry/settings được xác minh từ API nếu thành công. Credits30, grosscap30/netcap0 là user-reported; thông tin này không có trong TokenInfoGet/WorkspaceSettings. User đã báo hoàn tất bước1 đặt limits; chưa kiểm dashboard/APIbilling. Không dùng CLIbillingreport đặc quyền để suy credits hoặc khẳng định job GPU ready.
