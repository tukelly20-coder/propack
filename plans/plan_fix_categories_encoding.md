# Kế hoạch sửa lỗi Encoding trong Danh mục Categories

## Vấn đề
Danh sách CATEGORIES trong `client.py` có ký tự Trung Quốc bị hỏng (hiển thị là "?"). Ví dụ: "SJT散件图" bị thành "SJT散件?".

## Nguyên nhân
File encoding không đúng (UTF-8) dẫn đến ký tự Trung Quốc bị thay thế bằng "?".

## Format đúng (dựa trên thông tin người dùng cung cấp)
```
CODE-Tên-Tiêu mô tả
```

### Danh sách Categories đúng:
| STT | Category | Prefix |
|-----|----------|--------|
| 1 | SJT散件图-SJT散件图-拆解详图 | SJT |
| 2 | WLJ物料架-WLJ物料架-物料架 | WLJ |
| 3 | ZZC周转车-ZZC周转车-周转车 | ZZC |
| 4 | GZT工作台-GZT工作台-工作台 | GZT |
| 5 | WCP无尘棚-WCP无尘棚-无尘棚 | WCP |
| 6 | LSX流水线-LSX流水线-流水线 | LSX |
| 7 | ZWJ转弯机-ZWJ转弯机-转弯机 90,180 | ZWJ |
| 8 | GZL改造类-GZL改造类-改造类 | GZL |
| 9 | BSX倍速线-BSX倍速线-倍速链 | BSX |
| 10 | WLL围栏类-WLL围栏类-围栏 | WLL |
| 11 | GTX滚筒线-GTX滚筒线-滚筒线 | GTX |
| 12 | ZHT展会图-ZHT展会图-展会图 | ZHT |
| 13 | LHX老化线-LHX老化线-老化线 | LHX |

## Các bước thực hiện

### Bước 1: Sửa CATEGORIES trong client.py
- Thay thế danh sách CATEGORIES bằng danh sách đúng với encoding UTF-8

### Bước 2: Kiểm tra CATEGORY_PREFIXES trong server.py
- Đảm bảo CATEGORY_PREFIXES khớp với 3 ký tự đầu của mỗi category

### Bước 3: Kiểm tra tính nhất quán
- Đảm bảo client và server sử dụng cùng danh sách categories

## Lưu ý
- Category được chọn: **GZT工作台-GZT工作台-工作台**
- Prefix tương ứng: **GZT**
