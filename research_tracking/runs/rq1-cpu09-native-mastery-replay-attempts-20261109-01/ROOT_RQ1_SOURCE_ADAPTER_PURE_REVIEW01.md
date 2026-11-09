# Review Root cho năm canary source adapter

Đã đọc helper3650769e, tests285079be và controller72fb6029. Cho phép đúng5canary stdlib theo packetda267102,30giây whole/18owned/15worker/3cleanup,1GiB/free2GiB. Tests dựng source nhỏ trong TemporaryDirectory bên trong prep, rồi dọn đúng thư mục do chúng sở hữu. Không thay source production, dataset hoặc cache có sẵn.

Mục tiêu kiểm actual source compilation vào đúng module namespace, dataclass string annotations, metadata package/parent, và từ chối wronghash/preexistingmodule/missingparent/pathdrift. Fixture thay ROOT của helper vào thư mục dựng tay để kiểm source adapter, không thay mô hình khoa học. TearDown phải phục hồi sys.modules/parentattrs. Expected helper12calls,7compiled bodies và5rejects, không neural imports hoặc cache nghiên cứu.

Chỉ native worker sau này mới có thể chứng minh source adapter nạp được Paper2 thật. Các failure01–03 và nguyên nhân logcap/UTC/PYC phải giữ nguyên. Không nới filesystem allowlist sang projectPYC hoặc xoá cache để đạt canary.
