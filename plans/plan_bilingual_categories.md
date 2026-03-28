# Kế hoạch: Hiển thị Categories Song ngữ trong Tạo Mã Bản Vẽ

## Mục tiêu
Không để i18n.js dịch Categories. Luôn hiển thị song ngữ theo định dạng:
```
CODE + Tiếng Trung - Tiếng Việt
```
Ví dụ: `GZT工作台 - Bàn thao tác`

## Vấn đề hiện tại
1. **Dropdown Category** - Sử dụng `<span data-i18n="cat_gzt">` nên bị dịch theo ngôn ngữ
2. **Cột Category trong bảng** - Hàm `getCategoryDisplayName()` gọi `t(i18nKey)` nên bị dịch
3. Khi chuyển sang tiếng Trung, Categories bị dịch mất tiếng Việt

## Giải pháp

### 1. Sửa taomabanve.js
- Sửa **dropdown Category** (dòng 102-117): Thay đổi cách hiển thị
- Sửa hàm **getCategoryDisplayName()** (dòng 780-805): Trả về định dạng song ngữ cố định
- Sửa hàm **translateCategoryDropdown()** (dòng 807-820): Bỏ qua dịch

### 2. Giữ nguyên i18n.js
- Giữ nguyên các translation keys `cat_sjt`, `cat_wlj`, ... để dropdown hiển thị đúng

## Thứ tự thực hiện
1. Sửa hàm `getCategoryDisplayName()` trong taomabanve.js
2. Sửa dropdown trong `renderTaomabanveContent()` 
3. Kiểm tra kết quả

## Code song ngữ cố định (hardcoded)
```javascript
const CATEGORIES_BILINGUAL = {
    'SJT': 'SJT散件图 - Bản vẽ tách chi tiết',
    'WLJ': 'WLJ物料架 - Giá đựng vật liệu',
    'ZZC': 'ZZC周转车 - Xe trung chuyển',
    'GZT': 'GZT工作台 - Bàn thao tác',
    'WCP': 'WCP无尘棚 - Phòng sạch',
    'LSX': 'LSX流水线 - Băng tải',
    'ZWJ': 'ZWJ转弯机 - Băng tải chuyển hướng 90,180',
    'GZL': 'GZL改造类 - Cải tạo',
    'BSX': 'BSX倍速线 - Băng chuyền xích',
    'WLL': 'WLL围栏类 - Hàng rào',
    'GTX': 'GTX滚筒线 - Băng chuyền con lăn',
    'ZHT': 'ZHT展会图 - Bản vẽ mặt bằng',
    'LHX': 'LHX老化线 - Băng chuyền lão hóa'
};
```
