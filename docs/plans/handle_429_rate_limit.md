# Kế hoạch xử lý lỗi 429 Rate Limit cho AI API

## Vấn đề
Khi sử dụng OpenRouter API (đặc biệt model miễn phí như StepFun Step 3.5 Flash), server trả về lỗi 429:
```
Provider returned error - stepfun/step-3.5-flash:free is temporarily rate-limited upstream
```

## Nguyên nhân
- Model miễn phí có giới hạn request mỗi phút
- Không có retry logic trong server
- Không có fallback model khi bị rate limit
- Client hiển thị lỗi thô từ API thay vì thông báo thân thiện

## Giải pháp

### 1. Server-side: Thêm retry logic với exponential backoff
- Thêm hàm `call_openrouter_with_retry()` trong `server.py`
- Retry tối đa 3 lần với delay tăng dần (1s, 2s, 4s)
- Timeout cho mỗi attempt: 60 giây

### 2. Server-side: Thêm fallback model
- Khi retry fail, tự động chuyển sang model thay thế
- Fallback models:
  - `google/gemini-2.0-flash-exp:free` (miễn phí, nhanh)
  - `google/gemini-1.5-flash-8b:free` (miễn phí)
  - `meta-llama/llama-3.1-8b-instruct` (miễn phí)

### 3. Client-side: Cải thiện hiển thị lỗi
- Trong `ai.js`, thêm xử lý cho error 429
- Hiển thị thông báo: "Model đang bận, đang thử lại..." hoặc "Đã chuyển sang model dự phòng"
- Cho phép người dùng chọn model khác thủ công

### 4. Config: Lưu cấu hình retry/fallback
- Thêm vào `credentials.json`:
  ```json
  {
    "ai_retry": {
      "max_retries": 3,
      "initial_delay_ms": 1000,
      "max_delay_ms": 10000
    },
    "fallback_models": [
      "google/gemini-2.0-flash-exp:free",
      "google/gemini-1.5-flash-8b:free"
    ]
  }
  ```

## Triển khai

### Bước 1: Sửa server.py (OpenRouter endpoint)
- Thêm hàm retry wrapper cho API calls
- Thêm logic fallback model
- Cập nhật endpoint `/api/openrouter/chat/stream`

### Bước 2: Sửa ai.js (Client)
- Thêm xử lý lỗi 429 đặc biệt
- Hiển thị thông báo retry/fallback
- Auto-switch model khi rate limit

### Bước 3: Cập nhật credentials.json
- Thêm cấu hình retry/fallback

## Flow xử lý mới
```
User gửi message
    ↓
Gọi OpenRouter API
    ↓
Bị lỗi 429?
    ↓ Yes
Retry (lần 1) → Thành công → Trả kết quả
    ↓ No
Retry (lần 2) → Thành công → Trả kết quả
    ↓ Fail
Retry (lần 3) → Thành công → Trả kết quả
    ↓ Fail
Fallback sang model khác → Trả kết quả
    ↓
Client hiển thị kết quả
```

## Files cần sửa
1. `server.py` - Thêm retry/fallback logic
2. `web/js/modules/ai.js` - Cải thiện hiển thị lỗi
3. `credentials.json` - Thêm config