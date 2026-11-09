# Review Root cho cadence monitor hữu hạn

Attempt04 bị monitor terminate tại4.001samples sau127,82giây, trước thời hạn180giây. Family peak167,6MB và RAM khả dụng tối thiểu3,22GB còn trong bounds. Owned cleanup đạt Job0. Chỉ có reservation và native metadata, nên actual estimator calls được ghi UNKNOWN trong giới hạn đã reserve. Không nhận partial truth/parity.

Đã review derivative cuối outer05a8ea7c8c với monitor cadence0,1giây thay0,025giây. Loop chờ trước mỗi sample và thêm một terminalsample. Trong whole180giây số lần lấy mẫu không vượt1.800, dưới cap4.000 và journal4MiB. Giữ peak RSS process lifetime khi hệ điều hành cung cấp, family/free-floor observation và Job termination. Đây là phép đo hợp tác ở cadence được ghi rõ, không cam kết quan sát mọi dip RAM tức thời.

Worker04f262 chỉ đổi contract literal. Contract042976 chỉ đổi worker/output namespace so contract03. Helper source và các phương trình mô hình giữ nguyên, pure12 và adapter5 receipts vẫn giữ scope nguồn cũ đã thực chạy. Một lượt cuối này theo packet4f336a1c dùng fresh outputattempt04/outer05/owned05,180/177/173giây và1GiB/free2GiB. Giữ đủ bốn failure trước.

Nếu lượt này không hoàn tất trong bounds, dừng dispatch lane này để thiết kế partition/observer-cost riêng. Không thêm retry hoặc tăng thời hạn chỉ để đạt kết quả. Không dùng failure để kết luận mô hình hoặc RQ.
