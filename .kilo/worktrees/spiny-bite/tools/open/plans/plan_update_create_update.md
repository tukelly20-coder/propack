# Kế hoạch cập nhật create_update.py và updater.py

## Mục tiêu
Đồng bộ danh sách file cần đóng gói giữa `create_update.py` và `updater.py` với **5 file**:

1. `Mở mã liệu UI.py`
2. `Mở mã liệu 打开链接VP.py`
3. `add_query_all.py`
4. `create_update.py`
5. `network_update_template.txt`

**Lưu ý:** Các file trong thư mục `Khac/` thuộc dự án khác, không cần đóng gói.

## Các bước thực hiện

### Bước 1: Cập nhật create_update.py
- Cập nhật danh sách `UPDATE_FILES` (dòng 19-22) - thêm 3 file: `add_query_all.py`, `create_update.py`, `network_update_template.txt`
- Cập nhật thông báo hướng dẫn (dòng 133) từ "Copy 2 file" thành "Copy 5 file"

### Bước 2: Cập nhật updater.py
- Cập nhật danh sách `UPDATE_FILES` (dòng 47-58) - loại bỏ các file trong thư mục `Khac/`
- Chỉ giữ lại 5 file như trên

## Files cần chỉnh sửa
- `create_update.py`
- `updater.py`
