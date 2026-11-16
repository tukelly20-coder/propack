# Kế hoạch sửa lỗi AI hiển thị dấu ** (Markdown)

## Vấn đề
AI (StepFun Step 3.5 Flash) trả lời có dấu `**` (Markdown syntax) hiển thị dạng thô thay vì được render thành bold text.

## Nguyên nhân
- Hàm `escapeHtml()` trong `web/js/components.js` convert `**` thành `**` (entity HTML)
- Khi AI trả về text có Markdown như `**text**`, nó bị escape thành `**text**`
- Thay vì `<b>text</b>` như người dùng mong đợi

## Giải pháp đề xuất

### Phương án 1: Xử lý Markdown phía Client (Khuyến nghị)
- Thêm hàm xử lý Markdown cơ bản trong `ai.js`
- Chỉ áp dụng cho message từ AI (không áp dụng cho user message)

### Phương án 2: Tắt Markdown phía Server
- Thêm option để AI không trả về Markdown
- Cần thay đổi prompt hoặc cấu hình API

## Tiến hành
1. Thêm hàm `parseSimpleMarkdown()` trong `ai.js`
2. Thay thế `escapeHtml()` bằng `parseSimpleMarkdown()` cho message từ AI
3. Giữ nguyên `escapeHtml()` cho user message (bảo mật)

## Markdown cần hỗ trợ
- `**text**` → `<b>text</b>` (bold)
- `*text*` → `<i>text</i>` (italic)
- `\n` → `<br>` (xuống dòng)
- `` `code` `` → `<code>code</code>` (inline code)