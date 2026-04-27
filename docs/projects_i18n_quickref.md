# Projects Module i18n Keys → Database Columns
## (新建项目 - New Project)

File này là reference nhanh ánh xạ **từng key i18n** sang **tên cột trong database** (`db.db`)

---

## Legend

| Symbol | Ý nghĩa |
|--------|---------|
| 🔑 **PK** | PRIMARY KEY (khóa chính) |
| 📅 **DT** | Date/Datetime |
| 🔗 **FK** | Foreign Key |
| 💬 **TXT** | Text/VARCHAR |
| 🔢 **INT** | Integer |
| ✅ **UI** | Chỉ hiển thị, không lưu DB |

---

## Complete Mapping Table

| # | Key i18n | Column trong DB | Kiểu | R/W | Ghi chú |
|---|----------|----------------|------|-----|---------|
| 1 | `col_stt` | *(calculated)* | INT | R | STT tự động (không có trong DB) |
| 2 | `col_tracking_id` | `tracking_id` 🔑 | INTEGER | R | Mã dự án (PK) |
| 3 | `col_ngay` | `Created_Date` 📅 | DATE | R/W | Ngày tạo |
| 4 | `col_khachhang` | `khach_hang` 💬 | VARCHAR(200) | R/W | Khách hàng |
| 5 | `col_nhanvienkd` | `nhan_vien_kinh_doanh` 💬 | VARCHAR(100) | R/W | Nhân viên KD |
| 6 | `col_tensanpham` | `ten_san_pham` 💬 | VARCHAR(200) | R/W | Tên sản phẩm |
| 7 | `col_quycach` | `quy_cach` 💬 | TEXT | R/W | Quy cách |
| 8 | `col_lienhe_kh` | `nguoi_lien_he_kh` 💬 | VARCHAR(100) | R/W | Người liên hệ KH |
| 9 | `col_soluong` | `so_luong` 🔢 | INTEGER | R/W | Số lượng |
| 10 | `col_mapo` | `ma_po` 💬 | VARCHAR(50) | R/W | Mã PO |
| 11 | `col_mabave` | `ma_ban_ve` 💬 | VARCHAR(50) | R/W | Mã bản vẽ chính |
| 12 | `col_mabavkythuat` | `ma_ban_ve_ky_thuat` 💬 | VARCHAR(50) | R/W | Mã bản vẽ kỹ thuật |
| 13 | `col_mame` | `ma_me` 💬 | VARCHAR(50) | R/W | Mã mẹ |
| 14 | `col_loaisanpham` | `loai_san_pham` 💬 | VARCHAR(100) | R/W | Loại sản phẩm (13 loại) |
| 15 | `col_kysu` | `nhan_vien_thiet_ke` 💬 | VARCHAR(100) | R/W | Kỹ sư thiết kế |
| 16 | `col_tinhtrang` | `tinh_trang_hoan_thanh` 💬 | VARCHAR(100) | R/W | Tình trạng hoàn thành |
| 17 | `col_dokhan` | `urgency_level` 💬 | VARCHAR(20) | R/W | Độ khẩn: normal/urgent/very_urgent |
| 18 | `col_tg_mongmuon` | `thoi_gian_mong_muon_ban_ve` 📅 | TEXT | R/W | TG mong muốn có bản vẽ |
| 19 | `col_tg_hoanthanh` | `thoi_gian_hoan_thanh_ke_hoach` 📅 | TEXT | R/W | TG hoàn thành kế hoạch |
| 20 | `col_trangthai` | `is_pending` 💬 | VARCHAR(10) | R | Trạng thái: 'yes'/'no' |
| 21 | `col_nguoinhan` | `accepted_by` 💬 | VARCHAR(100) | R | Người nhận (kỹ sư) |
| 22 | `col_actions` | *(UI only)* ✅ | - | - | Cột nút hành động |

---

## Form Fields Mapping

| Form Field Key | Database Column | Input Type | Required? |
|----------------|-----------------|------------|-----------|
| `form_ngay_khoitao` | `Created_Date` | datetime-local | ✅ |
| `form_khachhang` | `khach_hang` | text (dropdown + input) | ✅ |
| `form_nhanvienkd` | `nhan_vien_kinh_doanh` | text | ✅ (auto-fill) |
| `form_tensanpham` | `ten_san_pham` | text | ✅ |
| `form_quycach` | `quy_cach` | text | ❌ |
| `form_lienhe_kh` | `nguoi_lien_he_kh` | text | ✅ |
| `form_soluong` | `so_luong` | number | ❌ |
| `form_mapo` | `ma_po` | text | ❌ |
| `form_mabave_chinh` | `ma_ban_ve` | text | ❌ |
| `form_mabave` | `ma_ban_ve` | text | ❌ (alias) |
| `form_mabavkythuat` | `ma_ban_ve_ky_thuat` | text | ❌ |
| `form_mame` | `ma_me` | text | ❌ |
| `form_loaisanpham` | `loai_san_pham` | select (14 loại) | ❌ |
| `form_kysu` | `nhan_vien_thiet_ke` | text | ❌ |
| `form_tinhtrang` | `tinh_trang_hoan_thanh` | text | ❌ |
| `form_capbach` | `urgency_level` | select (3 levels) | ❌ |
| `form_tg_mongmuon` | `thoi_gian_mong_muon_ban_ve` | datetime-local | ❌ |
| `form_tg_hoanthanh` | `thoi_gian_hoan_thanh_ke_hoach` | datetime-local | ❌ |

**Required fields (bắt buộc):** `khach_hang`, `ten_san_pham`, `nguoi_lien_he_kh`

---

## Filter Values Mapping

| Filter UI | Database Column | Giá trị |
|-----------|-----------------|---------|
| `status_pending` | `is_pending` | `'yes'` |
| `status_in_progress` | *(UI state)* | - |
| `status_completed` | *(UI state)* | - |
| `urgency_normal` | `urgency_level` | `'normal'` |
| `urgency_urgent` | `urgency_level` | `'urgent'` |
| `urgency_very_urgent` | `urgency_level` | `'very_urgent'` |

---

## Mã Sản Phẩm (Loại sản phẩm) - 14 loại

| Key i18n | Mã (DB) | Tên Việt | Tên Trung |
|----------|---------|----------|-----------|
| `loaisanpham_sjt` | `SJT` | Bản vẽ tách chi tiết | 散件图 |
| `loaisanpham_wlj` | `WLJ` | Giá đựng vật liệu | 物料架 |
| `loaisanpham_zzc` | `ZZC` | Xe trung chuyển | 周转车 |
| `loaisanpham_gzt` | `GZT` | Bàn thao tác | 工作台 |
| `loaisanpham_wcp` | `WCP` | Phòng sạch | 无尘棚 |
| `loaisanpham_lsx` | `LSX` | Băng tải | 流水线 |
| `loaisanpham_zwj` | `ZWJ` | Băng tải chuyển hướng | 转弯机 |
| `loaisanpham_gzl` | `GZL` | Cải tạo | 改造类 |
| `loaisanpham_bsx` | `BSX` | Băng chuyền xích | 倍速线 |
| `loaisanpham_wll` | `WLL` | Hàng rào | 围栏类 |
| `loaisanpham_gtx` | `GTX` | Băng chuyền con lăn | 滚筒线 |
| `loaisanpham_zht` | `ZHT` | Bản vẽ mặt bằng | 展会图 |
| `loaisanpham_lhx` | `LHX` | Băng chuyền lão hóa | 老化线 |

---

## Urgency Levels (Độ khẩn)

| Key i18n | DB Value | Mô tả |
|----------|----------|-------|
| `urgency_normal_option` | `'normal'` | Bình thường |
| `urgency_urgent_option` | `'urgent'` | Khẩn cấp |
| `urgency_very_urgent_option` | `'very_urgent'` | Rất khẩn cấp |

---

## Trạng Thái (`is_pending`)

| DB Value | Mô tả | Hiển thị `col_trangthai` |
|----------|-------|------------------------|
| `'yes'` | Chờ xử lý | "Chờ xử lý" / "待处理" |
| `'no'` | Đã xử lý/hoàn thành | "Hoàn thành" / "已完成" (từ `status_completed`) |
| `NULL` | Chưa set | Mặc định: "Chờ xử lý" |

---

## Quick Reference: Tất cả Key i18n cho Projects

```txt
# Toolbar
add_project, edit_project, delete_project, refresh_projects,
toggle_columns, export_excel, export_csv,
btn_add, btn_edit, btn_delete, btn_refresh, btn_toggle_columns, btn_export

# Filters
filter_status, filter_urgency, all_status, all_urgency,
status_pending, status_in_progress, status_completed,
urgency_normal, urgency_urgent, urgency_very_urgent,
search_placeholder, clear_search

# Table Headers (22 columns)
col_stt, col_tracking_id, col_ngay, col_khachhang,
col_nhanvienkd, col_tensanpham, col_quycach, col_lienhe_kh,
col_soluong, col_mapo, col_mabavkythuat, col_mabave, col_mame,
col_loaisanpham, col_dokhan, col_tinhtrang, col_kysu,
col_tg_mongmuon, col_tg_hoanthanh, col_trangthai, col_nguoinhan,
col_actions, col_select

# Column Selector
column_selector_title, column_reset, column_apply

# Modals
add_project_title, edit_project_title, view_project_title,
confirm_delete, confirm_delete_message

# Form - Basic Info
form_ngay_khoitao, form_khachhang, form_khachhang_required,
select_customer, liveSearch_placeholder, form_nhanvienkd

# Form - Product Info
product_info, form_tensanpham, form_tensanpham_required,
form_quycach, form_lienhe_kh, form_soluong, form_mapo

# Form - Drawing Codes
drawing_codes, form_mabave_chinh, form_mabave, form_mabavkythuat, form_mame

# Form - Technical
form_loaisanpham, select_loaisanpham, loaisanpham_* (14 keys),
form_kysu, form_tinhtrang

# Form - Time & Urgency
form_capbach, form_tg_mongmuon, form_tg_hoanthanh,
urgency_normal_option, urgency_urgent_option, urgency_very_urgent_option

# Quick Actions
quick_view, quick_edit, quick_delete, quick_accept

# Toast & Messages
toast_project_created, toast_project_updated, toast_project_deleted,
toast_export_success, toast_no_data_export,
validation_khachhang_required, validation_tensanpham_required,
validation_lienhe_required, validation_invalid_page

# Pagination
page, page_info, jump_to_page, per_page
```

---

## Lưu ý quan trọng

1. **`tracking_id`** là INTEGER PRIMARY KEY (tăng dần tự động)
2. **`Created_Date`** lưu dạng DATE (YYYY-MM-DD)
3. **Các trường thời gian** (`thoi_gian_mong_muon_ban_ve`, `thoi_gian_hoan_thanh_ke_hoach`) lưu dạng TEXT ISO 8601 (có thể chứa timezone)
4. **`is_pending`** chỉ có 2 giá trị: `'yes'` (chờ) hoặc `'no'` (đã xử lý)
5. **`loai_san_pham`** lưu mã 3 ký tự (SJT, WLJ, ...) - hiển thị dạng bilingual "SJT散件图 - Bản vẽ tách chi tiết"
6. **`urgency_level`** lưu lowercase: `'normal'`, `'urgent'`, `'very_urgent'`
7. **`col_stt`** không phải cột DB, là STT tính toán trên frontend: `(page-1)*pageSize + index + 1`
8. **`col_actions`** là UI column, không có trong DB

---

## Data Flow

```
Database (db.db) 
    ↓ [API GET /api/projects]
JSON Response (REST API)
    ↓ [api.js → projects.js loadProjects()]
ProjectsState.projects[] array
    ↓ [renderProjectsTable()]
HTML Table with data-i18n attributes
    ↓ [translatePage()]
Translated UI (VI/zh)
```

**Mỗi row data:**

```javascript
{
  tracking_id: 123,           // ↔ col_tracking_id
  Created_Date: "2025-01-15", // ↔ col_ngay
  khach_hang: "ABC公司",       // ↔ col_khachhang
  // ... all 25 columns
}
```

---

**File gốc:** `docs/projects_i18n_keys.md`  
**Schema DB:** `DB.db` → table `projects`  
**Code Reference:** `web/js/modules/projects.js`, `src/db_helper.py`
