# Kế hoạch sửa lỗi Wrap cho màn Log bên phải

## Vấn đề
- Màn log bên phải hiện tại đang sử dụng `QTextEdit.NoWrap`
- Link dài hiện ngang ra ngoài màn hình, không tự động xuống dòng

## Giải pháp
Thay đổi chế độ wrap từ `NoWrap` sang `WrapAtWordBoundary` để:
- Link dài tự động xuống dòng tại ranh giới từ
- Không cắt giữa các từ
- Giao diện hiển thị đẹp hơn

## Thay đổi cần thực hiện

### File: `Mở mã liệu UI.py`
- Dòng 406: Thay `self.txt_log.setLineWrapMode(QTextEdit.NoWrap)` 
  thành `self.txt_log.setLineWrapMode(QTextEdit.WrapAtWordBoundary)`

## Các tùy chọn Wrap trong QTextEdit
| Chế độ | Mô tả |
|--------|-------|
| NoWrap | Không xuống dòng (hiện tại) |
| WidgetWidth | Tự động xuống dòng theo chiều rộng widget |
| WrapAtWordBoundary | Xuống dòng tại ranh giới từ |
| WrapAnywhere | Xuống dòng bất kỳ chỗ nào |

Chọn `WrapAtWordBoundary` vì phù hợp nhất cho hiển thị link.
