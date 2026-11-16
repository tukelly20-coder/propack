# Kế hoạch thêm tính năng Copy mã liệu trong list_matches

## 1. Mô tả yêu cầu

**Vấn đề hiện tại:**
- Giao diện có phần "Chọn các mã liên quan (Ctrl+Click)" sử dụng QListWidget
- Người dùng có thể Ctrl+Click để chọn nhiều mã
- Tuy nhiên, sau khi chọn, người dùng KHÔNG THỂ COPY được các mã đã chọn bằng chuột

**Yêu cầu:**
- Tại vị trí danh sách kết quả (`list_matches`), có thể dùng chuột để copy các mã đã chọn
- Copy được cInvCode (phần sau dấu mũi tên →)

---

## 2. Phân tích code hiện tại

### File: `Mở mã liệu UI.py`

**Dòng 370-373: Khởi tạo list_matches**
```python
self.list_matches = QListWidget()
self.list_matches.setSelectionMode(QAbstractItemView.ExtendedSelection)
self.list_matches.setVisible(False)
left_layout.addWidget(self.list_matches, stretch=1)
```

**Dòng 648-651: Hiển thị dữ liệu trong list**
```python
for i, m in enumerate(matches, 1):
    eng_fig = m['cEngineerFigNo']
    cinv = m['cInvCode']
    self.list_matches.addItem(f"{i}. {eng_fig}  →  {cinv}")
```

**Dòng 635-646: Lưu cache matches**
```python
self.cached_matches = matches
```

---

## 3. Giải pháp đề xuất

### 3.1. Thêm context menu cho list_matches

Thêm context menu (chuột phải) với các tùy chọn:
- "📋 Copy mã đã chọn (cInvCode)" - Copy các cInvCode đã chọn
- "📋 Copy tất cả cInvCode" - Copy tất cả cInvCode trong list
- "📄 Copy dòng đã chọn" - Copy nguyên dòng text hiển thị

### 3.2. Thêm phím tắt Ctrl+C

Xử lý sự kiện Ctrl+C để copy nhanh các cInvCode đã chọn.

### 3.3. Định dạng output khi copy

**Khi copy 1 mã:**
```
100301000761
```

**Khi copy nhiều mã (mỗi mã một dòng):**
```
100301000761
300101002754
300101002755
300101002756
```

---

## 4. Các bước thực hiện

### Bước 1: Thêm context menu policy cho list_matches
- Thêm dòng: `self.list_matches.setContextMenuPolicy(Qt.CustomContextMenu)`
- Kết nối signal: `self.list_matches.customContextMenuRequested.connect(self.show_list_matches_context_menu)`

### Bước 2: Tạo hàm xử lý context menu
Tạo hàm `show_list_matches_context_menu(self, pos)`:
- Kiểm tra có items được chọn không
- Hiển thị QMenu với các tùy chọn copy
- Xử lý sự kiện click cho từng tùy chọn

### Bước 3: Tạo hàm copy logic
Tạo hàm `copy_selected_codes(self)`:
- Lấy các indices được chọn từ `list_matches.selectedItems()`
- Lấy cInvCode tương ứng từ `self.cached_matches`
- Copy vào clipboard bằng `QApplication.clipboard().setText()`

### Bước 4: Thêm phím tắt Ctrl+C
- Override keyPressEvent hoặc sử dụng QShortcut
- Xử lý Ctrl+C để gọi hàm copy

---

## 5. Sơ đồ luồng xử lý

```
Người dùng Ctrl+Click để chọn các mã
         ↓
Người dùng Click chuột phải / Ctrl+C
         ↓
Kiểm tra có item nào được chọn không?
    ├── Có → Lấy các cInvCode tương ứng từ cached_matches
    │         ↓
    │    Format thành text (mỗi mã một dòng)
    │         ↓
    │    Copy vào clipboard
    │         ↓
    │    Hiển thị thông báo "Đã copy X mã"
    │
    └── Không → Hiển thị thông báo "Vui lòng chọn mã trước"
```

---

## 6. File cần sửa đổi

| File | Thay đổi |
|------|----------|
| `Mở mã liệu UI.py` | Thêm context menu và phím tắt cho list_matches |

---

## 7. Demo giao diện sau khi thay đổi

```
┌─────────────────────────────────────────────────────────┐
│ CÔNG CỤ TRA CỨU MÃ LIỆU                                │
├─────────────────────────────────────────────────────────┤
│ [Nhập Mã / Code                    ] [Tra cứu] [▼] [🗑] │
├─────────────────────────────────────────────────────────┤
│ Chọn các mã liên quan (Ctrl+Click):                    │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ☑ 1. PLSX048-0000-00-A0 → 100301000761             │ │
│ │ ☑ 2. PLSX048-0000-01-A0 → 300101002754             │ │
│ │ ☐ 3. PLSX048-0000-02-A0 → 300101002755             │ │
│ │ ☐ 4. PLSX048-0000-04-A0 → 300101002756             │ │
│ └─────────────────────────────────────────────────────┘ │
│ Tổng: 25 kết quả | Mã duy nhất: 25                      │
│                                                         │
│ [Open Selected] [Open All Files]                       │
├─────────────────────────────────────────────────────────┤
│ NHẬT KÝ HỆ THỐNG / LOGS                                 │
│ ...                                                     │
└─────────────────────────────────────────────────────────┘

[Click chuột phải vào danh sách]
┌────────────────────────────────┐
│ 📋 Copy mã đã chọn (cInvCode) │
│ 📋 Copy tất cả cInvCode        │
│ 📄 Copy dòng đã chọn           │
└────────────────────────────────┘
```

---

## 8. Ghi chú

- QListWidget mặc định đã hỗ trợ Ctrl+Click để chọn nhiều (ExtendedSelection)
- Tuy nhiên, QListWidget không có sẵn chức năng copy vào clipboard khi bấm Ctrl+C
- Cần xử lý thủ công sự kiện keyboard và context menu
