# Kế hoạch bổ sung đa ngôn ngữ cho taomabanve.html

## Mục tiêu
Bổ sung đa ngôn ngữ (tiếng Trung và tiếng Việt) cho file `taomabanve.html`

## Các bước thực hiện

### 1. Xác định text cần dịch
Tất cả các text tĩnh trong file HTML và JavaScript:
- Tiêu đề trang
- Labels của form
- Nút bấm
- Thông báo lỗi/thành công
- Table headers
- Phân trang
- Toast messages

### 2. Tạo cấu trúc translations
```javascript
const translations = {
    vi: { /* tiếng Việt */ },
    zh: { /* tiếng Trung */ }
};
```

### 3. Thêm UI chọn ngôn ngữ
- Thêm dropdown/chọn ngôn ngữ trong header
- Lưu preference vào localStorage

### 4. Cập nhật JavaScript
- Tạo hàm `t(key)` để lấy text theo ngôn ngữ hiện tại
- Cập nhật tất cả hardcoded text sử dụng hàm `t()`

### 5. Danh sách text cần dịch

| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| page_title | Tạo Mã Bản Vẽ | 生成图纸代码 |
| create_code | Tạo Mã Bản Vẽ | 生成图纸代码 |
| requester_name | Tên người xin mã | 申请人姓名 |
| employee_code | Mã nhân viên công trình | 工程人员工号 |
| category | Hạng mục | 类别 |
| create_btn | Tạo Mã | 生成代码 |
| history | Lịch Sử Tạo Mã | 创建历史 |
| refresh | Làm mới | 刷新 |
| export_excel | Xuất Excel | 导出Excel |
| stt | STT | 序号 |
| name | Tên | 姓名 |
| drawing_code | Mã bản vẽ | 图纸代码 |
| mother_code | Mã mẹ | 母码 |
| time | Thời gian | 时间 |
| action | Thao tác | 操作 |
| total | Tổng | 合计 |
| today | Hôm nay | 今天 |
| week | Tuần | 本周 |
| latest | Mới nhất | 最新 |
| page_info | Hiển thị {start} - {end} của {total} bản ghi | 显示 {start} - {end}，共 {total} 条 |
| no_history | Chưa có lịch sử tạo mã | 暂无创建历史 |
| loading | Đang tải... | 加载中... |
| creating | Đang tạo mã bản vẽ... | 正在生成图纸代码... |
| success | Thành công | 成功 |
| error | Lỗi | 错误 |
| warning | Cảnh báo | 警告 |

### 6. Hạng mục (Categories)
| Value | Tiếng Việt | Tiếng Trung |
|-------|------------|-------------|
| SJT | SJT散件图 - Bản vẽ tách chi tiết | SJT散件图 - 拆解详图 |
| WLJ | WLJ物料架 - Giá đựng vật liệu | WLJ物料架 - 料架 |
| ZZC | ZZC周转车 - Xe trung chuyển | ZZC周转车 - 周转车 |
| GZT | GZT工作台 - Bàn thao tác | GZT工作台 - 工作台 |
| WCP | WCP无尘棚 - Phòng sạch | WCP无尘棚 - 无尘棚 |
| LSX | LSX流水线 - Băng tải | LSX流水线 - 流水线 |
| ZWJ | ZWJ转弯机 - Băng tải chuyển hướng | ZWJ转弯机 - 转弯机 |
| GZL | GZL改造类 - Cải tạo | GZL改造类 - 改造类 |
| BSX | BSX倍速线 - Băng chuyền xích | BSX倍速线 - 倍速链 |
| WLL | WLL围栏类 - Hàng rào | WLL围栏类 - 围栏类 |
| GTX | GTX滚筒线 - Băng chuyền con lăn | GTX滚筒线 - 滚筒线 |
| ZHT | ZHT展会图 - Bản vẽ mặt bằng | ZHT展会图 - 展会图 |
| LHX | LHX老化线 - Băng chuyền lão hóa | LHX老化线 - 老化线 |

### 7. Validation messages
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| emp_code_required | Mã nhân viên phải có 3 chữ số | 员工工号必须为3位数字 |
| emp_code_invalid | Mã nhân viên không được là 000 | 员工工号不能为000 |
| emp_code_numbers | Mã nhân viên chỉ được chứa số | 员工工号只能包含数字 |
| name_required | Vui lòng nhập tên người xin mã | 请输入申请人姓名 |
| category_required | Vui lòng chọn hạng mục | 请选择类别 |
| copy_success | Đã copy mã vào clipboard | 已复制到剪贴板 |
| copy_failed | Không thể copy mã | 无法复制代码 |
| delete_confirm | Nhập mật khẩu để xóa mã {code}: | 输入密码删除代码 {code}: |
| delete_wrong | Mật khẩu không đúng | 密码错误 |
| no_data_export | Không có dữ liệu để xuất | 没有数据可导出 |
| export_success | Đã xuất file Excel | 已导出Excel文件 |
