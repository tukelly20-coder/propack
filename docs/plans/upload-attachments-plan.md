# Kế hoạch: Thêm tính năng Up Ảnh và Video vào Log/Feedback

## 1. Tổng quan

**Yêu cầu từ user**: Thêm tính năng Up ảnh và video vào form feedback/log hiện tại, với khả năng gửi không giới hạn dung lượng (công cụ cá nhân).

**Lưu ý của user**: Không cần tự động xóa sau 30 ngày - files sẽ được lưu vĩnh viễn.

## 2. Phân tích hiện trạng

### Frontend (index.html - dòng 369-409)
- Modal log hiện tại chỉ có:
  - Dropdown chọn loại log (general, error, debug, login)
  - Textarea nhập nội dung
  - Nút gửi

### Backend (routes/log_routes.py)
- Endpoint `/api/logs` POST nhận JSON
- Lưu log vào file `.txt`
- Chưa xử lý multipart/form-data cho upload file

## 3. Thiết kế giải pháp

### 3.1 Backend Changes

#### A. Cập nhật `routes/log_routes.py`

**Thay đổi API endpoint**: Từ `application/json` sang `multipart/form-data`

```python
# Endpoint mới hỗ trợ upload files
@app.route('/api/logs', methods=['POST'])
def api_logs():
    # - Nhận text fields: content, type
    # - Nhận files: attachments[] (multiple)
    # - Validate content không trống
    # - Lưu files vào thư mục uploads/
    # - Tạo log entry với link đến files
    # - Trả về JSON response
```

**Thêm cấu hình**:
- `UPLOAD_FOLDER = 'uploads/logs/'`
- `MAX_CONTENT_LENGTH = None` (không giới hạn)
- Các định dạng được phép: jpg, jpeg, png, gif, webp, mp4, mov, avi, webm

#### B. Thêm `utils/file_handler.py`

```python
# Xử lý upload files
def save_uploaded_files(files, subfolder=''):
    # - Tạo thư mục nếu chưa có
    # - Generate unique filenames
    # - Lưu files với chunk reading (cho large files)
    # - Trả về danh sách saved paths
```

### 3.2 Frontend Changes

#### A. Cập nhật `index.html` (modal log)

```html
<!-- Thêm vào sau textarea -->
<div class="mb-3">
    <label class="form-label">
        <i class="bi bi-paperclip"></i> Đính kèm files
    </label>
    <div class="upload-area" id="upload-area">
        <div class="upload-placeholder">
            <i class="bi bi-cloud-arrow-up fs-1"></i>
            <p>Kéo thả files vào đây hoặc click để chọn</p>
            <small class="text-muted">Hỗ trợ: Ảnh, Video</small>
        </div>
        <input type="file" id="log-attachments" 
               multiple accept="image/*,video/*" hidden>
    </div>
    <div id="upload-preview" class="upload-preview"></div>
</div>
```

#### B. Thêm CSS vào `web/css/style.css`

```css
/* Upload Area */
.upload-area {
    border: 2px dashed #dee2e6;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
}

.upload-area:hover, .upload-area.dragover {
    border-color: var(--primary-color);
    background: rgba(0,0,0,0.02);
}

.upload-area.dragover {
    transform: scale(1.02);
}

.upload-preview {
    margin-top: 1rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.upload-preview-item {
    position: relative;
    width: 80px;
    height: 80px;
    border-radius: 4px;
    overflow: hidden;
}

.upload-preview-item img,
.upload-preview-item video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.upload-preview-item .remove-btn {
    position: absolute;
    top: 2px;
    right: 2px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: rgba(0,0,0,0.6);
    color: white;
    border: none;
    cursor: pointer;
}
```

#### C. Thêm JavaScript xử lý upload

```javascript
// Trong app.js, thêm upload handling

class FileUploadHandler {
    constructor(options) {
        this.container = options.container;
        this.preview = options.preview;
        this.maxSize = options.maxSize || Infinity;
        this.acceptedTypes = ['image/', 'video/'];
    }
    
    init() {
        // Drag and drop handlers
        // Click to select handler
        // Preview generation
        // File validation
    }
    
    getFiles() { return this.files; }
    clearFiles() { this.files = []; }
}
```

### 3.3 Cập nhật API client (`web/js/api.js`)

```javascript
// Thêm method mới cho upload với progress
async submitLogWithFiles(content, logType, files, deviceInfo) {
    const formData = new FormData();
    formData.append('content', content);
    formData.append('type', logType);
    
    // Append files
    for (let i = 0; i < files.length; i++) {
        formData.append('attachments', files[i]);
    }
    
    // Append device info as JSON
    formData.append('device_info_json', JSON.stringify(deviceInfo));
    
    // Fetch with progress tracking
    return this.uploadWithProgress('/api/logs', formData);
}
```

## 4. Cấu trúc thư mục sau khi implement

```
project/
├── uploads/
│   └── logs/
│       ├── web_log_20260330_083329/
│       │   ├── log.txt
│       │   ├── image_001.jpg
│       │   └── video_001.mp4
│       └── ...
├── routes/
│   └── log_routes.py (updated)
├── web/
│   ├── index.html (updated)
│   ├── css/
│   │   └── style.css (updated)
│   └── js/
│       ├── api.js (updated)
│       └── app.js (updated)
└── utils/
    └── file_handler.py (new)
```

## 5. Chi tiết các bước thực hiện

### Bước 1: Backend - Cập nhật log_routes.py
- [ ] Thêm imports: `werkzeug.utils`, `os`, `uuid`
- [ ] Định nghĩa `UPLOAD_FOLDER` và cấu hình
- [ ] Thay đổi endpoint để nhận multipart/form-data
- [ ] Xử lý save files với chunk reading
- [ ] Cập nhật log entry với file references

### Bước 2: Backend - Tạo file_handler.py
- [ ] Tạo utility functions cho upload
- [ ] Implement safe file saving (tránh overwrite)

### Bước 3: Frontend - Cập nhật index.html
- [ ] Thêm upload area HTML vào modal
- [ ] Thêm preview container
- [ ] Thêm upload CSS classes

### Bước 4: Frontend - Cập nhật style.css
- [ ] Thêm upload-area styles
- [ ] Thêm preview-item styles
- [ ] Thêm drag-over animation

### Bước 5: Frontend - Cập nhật api.js
- [ ] Thêm `submitLogWithFiles()` method
- [ ] Thêm progress tracking support

### Bước 6: Frontend - Cập nhật app.js
- [ ] Thêm FileUploadHandler class
- [ ] Kết nối upload với submit button
- [ ] Xử lý preview thumbnails
- [ ] Xử lý remove file

### Bước 7: Testing
- [ ] Test upload ảnh nhỏ
- [ ] Test upload ảnh lớn (>10MB)
- [ ] Test upload video
- [ ] Test upload nhiều files
- [ ] Test drag and drop
- [ ] Test mobile upload
- [ ] Test log entry có file links

## 6. Không cần làm (vì user nói là công cụ cá nhân)
- Giới hạn dung lượng
- Xóa files thủ công
- Auto cleanup sau 30 ngày
- Compression images
- Video thumbnails generation (dùng browser native)

## 7. Các quyết định đã xác nhận
1. **Thư mục lưu**: `uploads/logs/` - Mỗi log có thư mục riêng với log.txt + files
2. **Files cũ**: Không tự động xóa - lưu vĩnh viễn
3. **Link trong log**: Chỉ ghi đường dẫn, không embed base64
4. **Preview video**: Dùng video element với controls