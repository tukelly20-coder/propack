# i18n Keys cho Module "新建项目" (Projects Module)

> **Cập nhật lần cuối:** 2026-04-27
> **Trạng thái:** ✅ Đã triển khai đầy đủ trong `web/js/i18n.js`
>
> **Lưu ý:** Trong quá trình kiểm tra, phát hiện 2 key thiếu đã được bổ sung:
> - `search_placeholder` (placeholder cho ô tìm kiếm)
> - `btn_toggle_columns` (text nút "Chọn cột" responsive)

## Thông tin chung
- **Module**: Projects (Dự Án)
- **Tên Trung**: 新建项目 (Tạo dự án mới)
- **File chính**: `web/js/modules/projects.js`
- **File i18n**: `web/js/i18n.js`

---

## Các Key Được Sử Dụng

### 1. Toolbar Actions (Thanh công cụ)

| Key | Tiếng Việt | Tiếng Trung | Ghi chú |
|-----|-----------|-------------|---------|
| `add_project` | Thêm mới | 新建 | Title nút "Thêm dự án" |
| `add` | Thêm | 新建 | Text nút "Thêm" (span) |
| `edit_project` | Sửa | 编辑 | Title nút "Sửa" |
| `edit` | Sửa | 编辑 | Text nút "Sửa" |
| `delete_project` | Xóa | 删除 | Title nút "Xóa" |
| `delete` | Xóa | 删除 | Text nút "Xóa" |
| `refresh_projects` | Làm mới dữ liệu | 刷新数据 | Title nút refresh (icon only) |
| `toggle_columns` | Chọn cột hiển thị | 选择显示列 | Title nút column selector |
| `btn_toggle_columns` | Chọn cột | 列 | Text nút column selector (responsive) |
| `export` | Xuất | 导出 | Text dropdown toggle |
| `export_excel` | Xuất Excel | 导出Excel | Excel export |
| `export_csv` | Xuất CSV | 导出CSV | CSV export |

### 2. Filters & Search (Bộ lọc & Tìm kiếm)

| Key | Tiếng Việt | Tiếng Trung | Ghi chú |
|-----|-----------|-------------|---------|
| `filter_status` | Lọc theo trạng thái | 按状态筛选 | Label filter status |
| `filter_urgency` | Lọc theo độ khẩn | 按紧急程度筛选 | Label filter urgency |
| `all_status` | Tất cả trạng thái | 全部状态 | Option "All" |
| `all_urgency` | Tất cả độ khẩn | 全部紧急程度 | Option "All" |
| `status_pending` | Chờ xử lý | 待处理 | Status pending |
| `status_in_progress` | Đang làm | 进行中 | Status in progress |
| `status_completed` | Hoàn thành | 已完成 | Status completed |
| `urgency_normal` | Bình thường | 正常 | Urgency normal |
| `urgency_urgent` | Khẩn cấp | 紧急 | Urgency urgent |
| `urgency_very_urgent` | Rất khẩn | 非常紧急 | Urgency very urgent |
| `search_placeholder` | Tìm kiếm... | 搜索... | Placeholder search input |
| `clear_search` | Xóa tìm kiếm | 清除搜索 | Nút xóa search |

### 2.1 Pagination (Phân trang)

| Key | Tiếng Việt | Tiếng Trung | Database Column | Ghi chú |
|-----|-----------|-------------|-----------------|---------|
| `page` | Trang | 页 | N/A | Placeholder "Nhảy đến trang" |
| `page_info` | Hiển thị {start} - {end} của {total} bản ghi | 显示 {start} - {end}，共 {total} 条 | N/A | Text "Đang xem 1-50 của 200" |
| `jump_to_page` | Nhảy đến trang | 跳转到页 | N/A | Title button |
| `per_page` | trang | 页 | N/A | Label "50 / trang" |

### 3. Table Headers (Tiêu đề bảng)

| Key i18n | Tiếng Việt | Tiếng Trung | Database Column (db.db) | Kiểu dữ liệu |
|----------|-----------|-------------|------------------------|---------------|
| `col_stt` | STT | 序号 | *(calculated)* | INT (auto) |
| `col_tracking_id` | Tracking ID | Tracking ID | `tracking_id` | INTEGER PK |
| `col_ngay` | Ngày | 创建日期 | `Created_Date` | DATE |
| `col_khachhang` | Khách hàng | 客户公司名称 | `khach_hang` | VARCHAR(200) |
| `col_nhanvienkd` | Nhân viên KD | 业务员 | `nhan_vien_kinh_doanh` | VARCHAR(100) |
| `col_tensanpham` | Tên sản phẩm | 产品名称 | `ten_san_pham` | VARCHAR(200) |
| `col_quycach` | Quy cách | 规格 | `quy_cach` | TEXT |
| `col_lienhe_kh` | Người liên hệ (KH) | 客户联系人 | `nguoi_lien_he_kh` | VARCHAR(100) |
| `col_soluong` | Số lượng | 数量 | `so_luong` | INTEGER |
| `col_mapo` | Mã PO | PO号 | `ma_po` | VARCHAR(50) |
| `col_mabave` | Mã bản vẽ | 图纸编码 | `ma_ban_ve` | VARCHAR(50) |
| `col_mabavkythuat` | Mã bản vẽ phương án | 方案图号 | `ma_ban_ve_ky_thuat` | VARCHAR(50) |
| `col_mame` | Mã mẹ | 母料号 | `ma_me` | VARCHAR(50) |
| `col_loaisanpham` | Loại sản phẩm | 产品类型 | `loai_san_pham` | VARCHAR(100) |
| `col_kysu` | Kỹ sư | 工程师 | `nhan_vien_thiet_ke` | VARCHAR(100) |
| `col_tinhtrang` | Tình trạng nhận dự án | 接受方案状态 | `tinh_trang_hoan_thanh` | VARCHAR(100) |
| `col_dokhan` | Độ khẩn | 紧急程度 | `urgency_level` | VARCHAR(20) |
| `col_tg_mongmuon` | TG mong muốn | 期望时间 | `thoi_gian_mong_muon_ban_ve` | TEXT |
| `col_tg_hoanthanh` | TG hoàn thành | 完成时间 | `thoi_gian_hoan_thanh_ke_hoach` | TEXT |
| `col_trangthai` | Trạng thái | 状态 | `is_pending` | VARCHAR(10) |
| `col_nguoinhan` | Người nhận | 接收人 | `accepted_by` | VARCHAR(100) |
| `col_actions` | Hành động | 操作 | *(UI only)* | - |

### 4. Column Selector (Chọn cột)

| Key | Tiếng Việt | Tiếng Trung | Mô tả |
|-----|-----------|-------------|--------|
| `column_selector_title` | Chọn cột hiển thị | 选择显示列 | Tiêu đề popup |
| `column_reset` | Mặc định | 默认 | Nút reset |
| `column_apply` | Áp dụng | 应用 | Nút apply |

### 5. Modal - Add/Edit Project (Modal Thêm/Sửa)

| Key | Tiếng Việt | Tiếng Trung | Mô tả |
|-----|-----------|-------------|--------|
| `add_project_title` | Thêm dự án mới | 新建项目 | Title modal thêm |
| `edit_project_title` | Sửa dự án | 编辑项目 | Title modal sửa |
| `view_project_title` | Chi tiết dự án | 项目详情 | Title modal xem |
| `cancel` | Hủy | 取消 | Nút cancel |

### 6. Form - Basic Info (Thông tin cơ bản)

| Key | Tiếng Việt | Tiếng Trung | Element Type |
|-----|-----------|-------------|--------------|
| `form_ngay_khoitao` | Ngày khởi tạo | 创建日期 | Label input datetime |
| `form_khachhang` | Khách hàng | 客户公司名称 | Label field khách hàng |
| `form_khachhang_required` | Khách hàng * | 客户 * | Label required |
| `select_customer` | -- Chọn khách hàng -- | -- 选择客户 -- | Option dropdown |
| `liveSearch_placeholder` | Tìm kiếm khách hàng... | 搜索客户... | Placeholder search |
| `form_nhanvienkd` | Nhân viên kinh doanh | 业务员 | Label input |

### 7. Form - Product Info (Thông tin sản phẩm)

| Key | Tiếng Việt | Tiếng Trung | Element Type |
|-----|-----------|-------------|--------------|
| `product_info` | Thông tin sản phẩm | 产品信息 | Section header |
| `form_tensanpham` | Tên sản phẩm | 产品名称 | Label input |
| `form_tensanpham_required` | Tên sản phẩm * | 产品名称 * | Label required |
| `form_quycach` | Quy cách | 规格 | Label input |
| `form_lienhe_kh` | Người liên hệ (KH) | 联系人(客户) | Label input |
| `form_soluong` | Số lượng | 数量 | Label input number |
| `form_mapo` | Mã PO | PO号 | Label input |

### 8. Form - Drawing Codes (Mã bản vẽ)

| Key | Tiếng Việt | Tiếng Trung | Element Type |
|-----|-----------|-------------|--------------|
| `drawing_codes` | Mã bản vẽ | 图纸编码 | Section header |
| `form_mabave_chinh` | Mã bản vẽ chính | 图纸编码 | Label input |
| `form_mabave` | Mã bản vẽ (phương án) | 图纸编码(方案) | Label input |
| `form_mabavkythuat` | Mã bản vẽ kỹ thuật | 技术图纸编码 | Label input |
| `form_mame` | Mã mẹ | 母料号 | Label input |

### 9. Form - Technical Info (Thông tin kỹ thuật)

| Key | Tiếng Việt | Tiếng Trung | Element Type |
|-----|-----------|-------------|--------------|
| `form_loaisanpham` | Loại sản phẩm | 产品类型 | Label select |
| `select_loaisanpham` | -- Chọn loại sản phẩm -- | -- 选择产品类型 -- | Default option |
| `loaisanpham_sjt` | SJT - Bản vẽ tách chi tiết | 散件图 | Option SJT |
| `loaisanpham_wlj` | WLJ - Giá đựng vật liệu | 物料架 | Option WLJ |
| `loaisanpham_zzc` | ZZC - Xe trung chuyển | 周转车 | Option ZZC |
| `loaisanpham_gzt` | GZT - Bàn thao tác | 工作台 | Option GZT |
| `loaisanpham_wcp` | WCP - Phòng sạch | 无尘棚 | Option WCP |
| `loaisanpham_lsx` | LSX - Băng tải | 流水线 | Option LSX |
| `loaisanpham_zwj` | ZWJ - Băng tải chuyển hướng | 转弯机 | Option ZWJ |
| `loaisanpham_gzl` | GZL - Cải tạo | 改造类 | Option GZL |
| `loaisanpham_bsx` | BSX - Băng chuyền xích | 倍速线 | Option BSX |
| `loaisanpham_wll` | WLL - Hàng rào | 围栏类 | Option WLL |
| `loaisanpham_gtx` | GTX - Băng chuyền con lăn | 滚筒线 | Option GTX |
| `loaisanpham_zht` | ZHT - Bản vẽ mặt bằng | 展会图 | Option ZHT |
| `loaisanpham_lhx` | LHX - Băng chuyền lão hóa | 老化线 | Option LHX |
| `form_kysu` | Nhân viên thiết kế | 设计人员 | Label input |
| `form_tinhtrang` | Tình trạng hoàn thành | 完成状态 | Label input |

### 10. Form - Time & Urgency (Thời gian & Độ khẩn)

| Key | Tiếng Việt | Tiếng Trung | Element Type |
|-----|-----------|-------------|--------------|
| `form_capbach` | Tính cấp bách | 紧急程度 | Label select |
| `form_tg_mongmuon` | Thời gian mong muốn có bản vẽ | 期望收到图纸时间 | Label datetime |
| `form_tg_hoanthanh` | Thời gian hoàn thành kế hoạch | 计划完成时间 | Label datetime |
| `urgency_normal_option` | Bình thường | 普通 | Option normal |
| `urgency_urgent_option` | Khẩn cấp | 紧急 | Option urgent |
| `urgency_very_urgent_option` | Rất khẩn cấp | 非常紧急 | Option very urgent |

### 11. Quick Actions (Hành động nhanh)

| Key | Tiếng Việt | Tiếng Trung | Ghi chú |
|-----|-----------|-------------|---------|
| `quick_view` | Xem chi tiết | 查看详情 | Dropdown item |
| `quick_edit` | Sửa | 编辑 | Dropdown item |
| `quick_delete` | Xóa | 删除 | Dropdown item |

### 12. Toast Messages (Thông báo)

| Key | Tiếng Việt | Tiếng Trung | Ghi chú |
|-----|-----------|-------------|---------|
| `toast_project_created` | Tạo dự án thành công | 创建项目成功 | Success message |
| `toast_project_updated` | Cập nhật dự án thành công | 更新项目成功 | Success message |
| `toast_project_deleted` | Đã xóa {count} dự án | 已删除 {count} 个项目 | Success message |

### 13. Validation (Xác thực)

| Key | Tiếng Việt | Tiếng Trung | Ghi chú |
|-----|-----------|-------------|---------|
| `validation_khachhang_required` | Vui lòng nhập tên khách hàng | 请输入客户名称 | Required field |
| `validation_tensanpham_required` | Vui lòng nhập tên sản phẩm | 请输入产品名称 | Required field |
| `validation_lienhe_required` | Vui lòng nhập người liên hệ | Vui lòng nhập người liên hệ | Required field |
| `validation_invalid_page` | Vui lòng nhập trang từ 1 đến {max} | 请输入1到{max}之间的页码 | Page validation |

### 14. Pagination (Phân trang)

| Key | Tiếng Việt | Tiếng Trung | Ghi chú |
|-----|-----------|-------------|---------|
| `page_info` | Hiển thị {start} - {end} của {total} bản ghi | 显示 {start} - {end}，共 {total} 条 | Page info text |
| `jump_to_page` | Nhảy đến trang | 跳转到页 | Jump to page button |

### 15. Confirmation (Xác nhận)

| Key | Tiếng Việt | Tiếng Trung | Ghi chú |
|-----|-----------|-------------|---------|
| `confirm_delete` | Xác nhận xóa | 确认删除 | Modal title |
| `confirm_delete_message` | Bạn có chắc chắn muốn xóa {count} item đã chọn không? | 确定要删除选中的 {count} 项吗？ | Modal body |

---

## Schema Database (`db.db`)

**File:** `DB.db` (SQLite database)
**Schema Version:** V2 (normalized - các cột riêng biệt)
**Table:** `projects`

### Cấu trúc đầy đủ:

```sql
CREATE TABLE IF NOT EXISTS projects (
    tracking_id INTEGER PRIMARY KEY,
    Created_Date DATE,
    khach_hang VARCHAR(200),
    nhan_vien_kinh_doanh VARCHAR(100),
    ten_san_pham VARCHAR(200),
    quy_cach TEXT,
    nguoi_lien_he_kh VARCHAR(100),
    so_luong INTEGER,
    ma_po VARCHAR(50),
    ma_ban_ve VARCHAR(50),
    ma_ban_ve_ky_thuat VARCHAR(50),
    ma_me VARCHAR(50),
    loai_san_pham VARCHAR(100),
    nhan_vien_thiet_ke VARCHAR(100),
    tinh_trang_hoan_thanh VARCHAR(100),
    urgency_level VARCHAR(20),
    thoi_gian_mong_muon_ban_ve TEXT,
    thoi_gian_hoan_thanh_ke_hoach TEXT,
    sales_name VARCHAR(100),
    user_id INTEGER,
    is_pending VARCHAR(10) DEFAULT 'no',
    accepted_by VARCHAR(100),
    accepted_at TEXT,
    desired_solution_time TEXT,
    sales_id INTEGER
);
```

### Indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)
CREATE INDEX IF NOT EXISTS idx_projects_ma_po ON projects(ma_po)
CREATE INDEX IF NOT EXISTS idx_projects_ten_san_pham ON projects(ten_san_pham)
```

### Migration History:

- **V1 (cũ):** Dùng JSON blob trong cột `data` + `tracking_id`, `sales_name`, `user_id`, `is_pending`, `accepted_by`, `accepted_at`
- **V2 (hiện tại):** Normalized với 25 cột riêng biệt (đã migrate tự động bằng `migrate_ngay_to_created_date()`)

### Cột đặc biệt:

| Column | Mô tả | Giá trị |
|--------|-------|---------|
| `tracking_id` | PK, tự động tăng | INTEGER (1, 2, 3...) |
| `is_pending` | Trạng thái nhận việc | `'yes'` / `'no'` |
| `urgency_level` | Độ khẩn | `'normal'`, `'urgent'`, `'very_urgent'` |
| `so_luong` | Số lượng | INTEGER |

---

## API Endpoints liên quan

| Endpoint | Method | Mô tả | Trả về |
|----------|--------|-------|--------|
| `/api/projects` | GET | Lấy danh sách dự án (có phân trang) | `{data: [...], total: N}` |
| `/api/projects/search` | GET/POST | Tìm kiếm dự án | `{data: [...], total: N}` |
| `/api/projects` | POST | Tạo dự án mới | `{success: true, tracking_id: N}` |
| `/api/projects/:id` | PUT | Cập nhật dự án | `{success: true}` |
| `/api/projects/:id` | DELETE | Xóa dự án | `{success: true}` |
| `/api/customers` | GET | Lấy danh sách khách hàng (dropdown) | `[{name: ...}]` |

**Chi tiết response object từ `/api/projects`:**

```javascript
{
  tracking_id: 123,           // INTEGER → string trong JSON
  Created_Date: "2025-01-15", // DATE → string
  khach_hang: "Công ty ABC",  // VARCHAR
  nhan_vien_kinh_doanh: "Nguyễn Văn A",
  ten_san_pham: "Máy móc A",
  quy_cach: "250x500mm",
  nguoi_lien_he_kh: "Trần Thị B",
  so_luong: 100,              // INTEGER
  ma_po: "PO-2025-001",
  ma_ban_ve: "SJT001",
  ma_ban_ve_ky_thuat: "SJT-ABC",
  ma_me: "SJT-ME-001",
  loai_san_pham: "SJT散件图",
  nhan_vien_thiet_ke: "Lê Văn C",
  tinh_trang_hoan_thanh: "Đang thiết kế",
  urgency_level: "urgent",    // "normal" | "urgent" | "very_urgent"
  thoi_gian_mong_muon_ban_ve: "2025-02-01T00:00:00",
  thoi_gian_hoan_thanh_ke_hoach: "2025-02-15T00:00:00",
  is_pending: "yes",          // "yes" | "no"
  accepted_by: "Phạm Văn D",  // null nếu chưa nhận
  sales_name: "Nguyễn Văn A", // redundant
  user_id: 5,
  accepted_at: null,
  desired_solution_time: null,
  sales_id: 5
}
```

---

## Cấu trúc State trong `projects.js`

## Danh sách Column trong Database (db.db)

Bảng `projects` trong database sử dụng schema **V2 (normalized)** với các cột riêng biệt:

| Column Name | Kiểu dữ liệu | Mô tả | Null? | Default |
|-------------|--------------|-------|-------|---------|
| `tracking_id` | INTEGER | **PRIMARY KEY** - Mã theo dõi dự án | NOT NULL | - |
| `Created_Date` | DATE | Ngày khởi tạo dự án | YES | NULL |
| `khach_hang` | VARCHAR(200) | Tên khách hàng | YES | NULL |
| `nhan_vien_kinh_doanh` | VARCHAR(100) | Nhân viên kinh doanh (sales) | YES | NULL |
| `ten_san_pham` | VARCHAR(200) | Tên sản phẩm | YES | NULL |
| `quy_cach` | TEXT | Quy cách sản phẩm | YES | NULL |
| `nguoi_lien_he_kh` | VARCHAR(100) | Người liên hệ bên khách hàng | YES | NULL |
| `so_luong` | INTEGER | Số lượng | YES | NULL |
| `ma_po` | VARCHAR(50) | Mã Purchase Order | YES | NULL |
| `ma_ban_ve` | VARCHAR(50) | Mã bản vẽ chính | YES | NULL |
| `ma_ban_ve_ky_thuat` | VARCHAR(50) | Mã bản vẽ kỹ thuật/phương án | YES | NULL |
| `ma_me` | VARCHAR(50) | Mã mẹ (parent code) | YES | NULL |
| `loai_san_pham` | VARCHAR(100) | Loại sản phẩm (category) | YES | NULL |
| `nhan_vien_thiet_ke` | VARCHAR(100) | Kỹ sư thiết kế | YES | NULL |
| `tinh_trang_hoan_thanh` | VARCHAR(100) | Tình trạng hoàn thành | YES | NULL |
| `urgency_level` | VARCHAR(20) | Độ khẩn (normal/urgent/very_urgent) | YES | NULL |
| `thoi_gian_mong_muon_ban_ve` | TEXT | Thời gian mong muốn có bản vẽ | YES | NULL |
| `thoi_gian_hoan_thanh_ke_hoach` | TEXT | Thời gian hoàn thành kế hoạch | YES | NULL |
| `sales_name` | VARCHAR(100) | Tên sales (redundant, có thể lấy từ users) | YES | NULL |
| `user_id` | INTEGER | Foreign key đến bảng users | YES | NULL |
| `is_pending` | VARCHAR(10) | Trạng thái pending ('yes'/'no') | YES | 'no' |
| `accepted_by` | VARCHAR(100) | Người nhận (kỹ sư accepts) | YES | NULL |
| `accepted_at` | TEXT | Thời gian nhận | YES | NULL |
| `desired_solution_time` | TEXT | Thời gian giải quyết mong muốn | YES | NULL |
| `sales_id` | INTEGER | Foreign key đến bảng users (sales) | YES | NULL |

**Indexes:**
- `PRIMARY KEY (tracking_id)`
- `idx_projects_user_id (user_id)`
- `idx_projects_ma_po (ma_po)`
- `idx_projects_ten_san_pham (ten_san_pham)`

**Lưu ý:**
- `tracking_id` là INTEGER PRIMARY KEY (trước đây có thể là TEXT, đã migrate)
- Các cột `Created_Date`, `thoi_gian_mong_muon_ban_ve`, `thoi_gian_hoan_thanh_ke_hoach`, `accepted_at` lưu dạng TEXT (ISO 8601 string) hoặc DATE
- `is_pending` lưu giá trị `'yes'` hoặc `'no'` (VARCHAR), hiển thị trong col `col_trangthai`
- `urgency_level` có thể là: `'normal'`, `'urgent'`, `'very_urgent'`
- Trước đây (schema V1), tất cả data được lưu trong cột `data` (JSON blob). Đã migrate sang V2 với các cột riêng biệt.

---

## API Endpoints liên quan

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/projects` | GET | Lấy danh sách dự án (có phân trang) |
| `/api/projects/search` | GET/ POST | Tìm kiếm dự án |
| `/api/projects` | POST | Tạo dự án mới |
| `/api/projects/:id` | PUT | Cập nhật dự án |
| `/api/projects/:id` | DELETE | Xóa dự án |
| `/api/customers` | GET | Lấy danh sách khách hàng (dropdown) |

---

## Lời gọi hàm t(key)

Trong file `projects.js`, hàm `t()` được gọi nhiều lần để lấy translation:

```javascript
// Ví dụ:
const title = t('add_project_title');  // "Thêm dự án mới"
const btnText = t('add');             // "Thêm"
```

Các element sử dụng `data-i18n` attribute sẽ tự động được dịch bởi `translatePage()`.

---

## Cách Thêm Key Mới

1. **Thêm vào i18n.js**:
```javascript
vi: {
    new_key: 'Giá trị tiếng Việt',
    ...
},
zh: {
    new_key: 'Giá trị tiếng Trung',
    ...
}
```

2. **Sử dụng trong code**:
```javascript
// Trong HTML
<span data-i18n="new_key">Default text</span>

// Trong JS
const text = t('new_key');
```

---

**Lưu ý**: Tất cả các key ở trên phải có mặt trong cả 2 ngôn ngữ (vi & zh) để đảm bảo đa ngôn ngữ hoạt động đúng.
