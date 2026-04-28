# Kế hoạch: Hoàn thiện Tiếng Trung cho trang 大日程 (Projects)

## Mục tiêu
Cập nhật đầy đủ translation tiếng Trung cho trang "大日程" (Projects/Dự án) để khi người dùng chuyển sang tiếng Trung, tất cả label và text hiển thị đúng tiếng Trung.

## Danh sách label cần cập nhật (trong projects.js)

### 1. Toolbar & Actions
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| btn_add | Thêm | 新建 |
| btn_edit | Sửa | 编辑 |
| btn_delete | Xóa | 删除 |
| btn_refresh | Làm mới dữ liệu | 刷新数据 |
| btn_toggle_columns | Cột | 列 |
| btn_export | Xuất | 导出 |

### 2. Filter Options
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| all_status | Tất cả trạng thái | 全部状态 |
| all_urgency | Tất cả độ khẩn | 全部紧急程度 |
| search_placeholder | Tìm kiếm... | 搜索... |

### 3. Table Headers
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| col_stt | STT | 序号 |
| col_tracking_id | Tracking ID | Tracking ID |
| col_ngay | Ngày | 日期 |
| col_khachhang | Khách hàng | 客户 |
| col_nhanvienkd | Nhân viên KD | 业务员 |
| col_tensanpham | Tên sản phẩm | 产品名称 |
| col_quycach | Quy cách | 规格 |
| col_lienhe | Người liên hệ | 联系人 |
| col_soluong | Số lượng | 数量 |
| col_mapo | Mã PO | PO号 |
| col_mabave | Mã bản vẽ | 图纸编码 |
| col_mabavkythuat | Mã bản vẽ KT | 方案图编码 |
| col_mame | Mã mẹ | 母码 |
| col_loaisanpham | Loại sản phẩm | 产品类型 |
| col_kysu | Kỹ sư | 工程师 |
| col_tinhtrang | Tình trạng | 状态 |
| col_dokhan | Độ khẩn | 紧急程度 |
| col_tg_mongmuon | TG mong muốn | 期望时间 |
| col_tg_hoanthanh | TG hoàn thành | 完成时间 |
| col_trangthai | Trạng thái | 状态 |
| col_nguoinhan | Người nhận | 接收人 |
| col_actions | Hành động | 操作 |

### 4. Form Labels (Modal)
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| basic_info | Thông tin cơ bản | 基本信息 |
| product_info | Thông tin sản phẩm | 产品信息 |
| drawing_codes | Mã bản vẽ | 图纸编码 |
| technical_info | Thông tin kỹ thuật | 技术信息 |
| time_urgency | Thời gian & Độ khẩn | 时间与紧急程度 |
| form_ngay_khoitao | Ngày khởi tạo | 创建日期 |
| form_khachhang_required | Khách hàng * | 客户 * |
| form_nhanvienkd | Nhân viên kinh doanh | 业务员 |
| form_tensanpham_required | Tên sản phẩm * | 产品名称 * |
| form_quycach | Quy cách | 规格 |
| form_lienhe_kh | Người liên hệ (KH) | 联系人(客户) |
| form_soluong | Số lượng | 数量 |
| form_mapo | Mã PO | PO号 |
| form_mabave | Mã bản vẽ (phương án) | 图纸编码(方案) |
| form_mabavkythuat | Mã bản vẽ kỹ thuật | 技术图纸编码 |
| form_mame | Mã mẹ | 母码 |
| form_loaisanpham | Loại sản phẩm | 产品类型 |
| form_kysu | Nhân viên thiết kế | 设计人员 |
| form_tinhtrang | Tình trạng hoàn thành | 完成状态 |
| form_capbach | Tính cấp bách | 紧急程度 |
| form_tg_mongmuon | Thời gian mong muốn có bản vẽ | 期望收到图纸时间 |
| form_tg_hoanthanh | Thời gian hoàn thành kế hoạch | 计划完成时间 |

### 5. Urgency Options
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| urgency_normal_option | Bình thường | 普通 |
| urgency_urgent_option | Khẩn cấp | 紧急 |
| urgency_very_urgent_option | Rất khẩn cấp | 非常紧急 |

### 6. Quick Actions (Dropdown)
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| quick_view | Xem chi tiết | 查看详情 |
| quick_edit | Sửa | 编辑 |
| quick_delete | Xóa | 删除 |

### 7. Column Selector
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| column_selector_title | Chọn cột hiển thị | 选择显示列 |
| column_reset | Mặc định | 默认 |
| column_apply | Áp dụng | 应用 |

### 8. Messages
| Key | Tiếng Việt | Tiếng Trung |
|-----|------------|-------------|
| no_data | Không có dữ liệu dự án | 暂无项目数据 |
| load_error | Lỗi tải dữ liệu | 加载数据出错 |

## Thứ tự thực hiện

### Bước 1: Cập nhật i18n.js
- Thêm tất cả translation keys mới vào phần `zh:` trong file i18n.js

### Bước 2: Cập nhật projects.js
- Thay thế các label cứng trong HTML bằng `data-i18n` attribute
- Cập nhật hàm `updateProjectFormLabels()` để sử dụng `t()` function

### Bước 3: Kiểm tra
- Chạy ứng dụng
- Chuyển sang tiếng Trung
- Kiểm tra tất cả label trong trang Projects