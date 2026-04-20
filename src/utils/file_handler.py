# -*- coding: utf-8 -*-
"""
File Handler Utilities - Xử lý upload files cho log/feedback
"""
import os
import uuid
from werkzeug.utils import secure_filename


# Cấu hình upload
UPLOAD_FOLDER = 'uploads/logs'

# Các định dạng file được phép
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', 'mkv', 'flv', 'wmv'}

# Tất cả extensions được phép
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS


def allowed_file(filename):
    """
    Kiểm tra xem file có được phép upload không
    
    Args:
        filename: Tên file cần kiểm tra
        
    Returns:
        bool: True nếu file được phép, False nếu không
    """
    if not filename:
        return False
    
    # Lấy extension (không phân biệt hoa thường)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    return ext in ALLOWED_EXTENSIONS


def get_file_type(filename):
    """
    Xác định loại file (image hay video)
    
    Args:
        filename: Tên file cần kiểm tra
        
    Returns:
        str: 'image', 'video', hoặc 'unknown'
    """
    if not filename:
        return 'unknown'
    
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    else:
        return 'unknown'


def generate_unique_filename(original_filename):
    """
    Tạo tên file unique để tránh trùng lặp
    
    Args:
        original_filename: Tên file gốc
        
    Returns:
        str: Tên file unique mới
    """
    if not original_filename:
        return f"file_{uuid.uuid4().hex[:8]}"
    
    # Secure filename để tránh path traversal
    safe_name = secure_filename(original_filename)
    
    # Nếu secure_filename trả về rỗng (ví dụ: file bắt đầu bằng dấu .)
    if not safe_name:
        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else ''
        return f"file_{uuid.uuid4().hex[:8]}.{ext}" if ext else f"file_{uuid.uuid4().hex[:8]}"
    
    return safe_name


def ensure_upload_folder(subfolder=''):
    """
    Đảm bảo thư mục upload tồn tại
    
    Args:
        subfolder: Thư mục con (ví dụ: timestamp của log)
        
    Returns:
        str: Đường dẫn tuyệt đối của thư mục
    """
    if subfolder:
        folder_path = os.path.join(UPLOAD_FOLDER, subfolder)
    else:
        folder_path = UPLOAD_FOLDER
    
    # Tạo thư mục nếu chưa tồn tại (recursive để tạo cả parent directories)
    os.makedirs(folder_path, exist_ok=True)
    
    return os.path.abspath(folder_path)


def save_uploaded_file(file, subfolder=''):
    """
    Lưu một file upload vào thư mục
    
    Args:
        file: File object từ Flask request
        subfolder: Thư mục con để lưu file
        
    Returns:
        dict: Thông tin file đã lưu {
            'success': bool,
            'path': str (đường dẫn tuyệt đối),
            'relative_path': str (đường dẫn tương đối),
            'filename': str (tên file),
            'size': int (kích thước bytes),
            'type': str ('image' hoặc 'video')
        }
    """
    if not file:
        return {'success': False, 'error': 'No file provided'}
    
    if file.filename == '':
        return {'success': False, 'error': 'No file selected'}
    
    if not allowed_file(file.filename):
        return {'success': False, 'error': f'File type not allowed: {file.filename}'}
    
    try:
        # Tạo tên file unique
        unique_filename = generate_unique_filename(file.filename)
        
        # Đảm bảo thư mục tồn tại
        folder_path = ensure_upload_folder(subfolder)
        
        # Đường dẫn đầy đủ của file
        file_path = os.path.join(folder_path, unique_filename)
        
        # Lưu file (dùng chunks cho large files)
        file.save(file_path)
        
        # Lấy kích thước file
        file_size = os.path.getsize(file_path)
        
        return {
            'success': True,
            'path': file_path,
            'relative_path': os.path.join(subfolder, unique_filename) if subfolder else unique_filename,
            'filename': unique_filename,
            'size': file_size,
            'type': get_file_type(file.filename)
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def save_multiple_files(files, subfolder=''):
    """
    Lưu nhiều files cùng lúc
    
    Args:
        files: List của file objects từ Flask request (thường là request.files.getlist('attachments'))
        subfolder: Thư mục con để lưu files
        
    Returns:
        dict: Kết quả {
            'success': bool,
            'saved': list of dict (thông tin các file đã lưu thành công),
            'failed': list of dict (thông tin các file thất bại),
            'total_count': int,
            'saved_count': int,
            'failed_count': int
        }
    """
    saved_files = []
    failed_files = []
    
    for file in files:
        result = save_uploaded_file(file, subfolder)
        if result.get('success'):
            saved_files.append(result)
        else:
            failed_files.append({
                'original_filename': file.filename if file else 'unknown',
                'error': result.get('error', 'Unknown error')
            })
    
    return {
        'success': len(failed_files) == 0,
        'saved': saved_files,
        'failed': failed_files,
        'total_count': len(files),
        'saved_count': len(saved_files),
        'failed_count': len(failed_files)
    }


def get_upload_folder_path(subfolder=''):
    """
    Lấy đường dẫn thư mục upload
    
    Args:
        subfolder: Thư mục con (ví dụ: 'web_log_20260330_083329')
        
    Returns:
        str: Đường dẫn tuyệt đối
    """
    if subfolder:
        return os.path.join(os.path.abspath(UPLOAD_FOLDER), subfolder)
    return os.path.abspath(UPLOAD_FOLDER)


def get_all_upload_subfolders():
    """
    Lấy danh sách tất cả các thư mục con trong uploads/logs
    
    Returns:
        list: Danh sách tên thư mục con
    """
    folder_path = os.path.abspath(UPLOAD_FOLDER)
    if not os.path.exists(folder_path):
        return []
    
    subfolders = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            subfolders.append(item)
    
    return sorted(subfolders, reverse=True)  # Mới nhất trước


def get_files_in_subfolder(subfolder):
    """
    Lấy danh sách files trong một thư mục con
    
    Args:
        subfolder: Tên thư mục con
        
    Returns:
        list: Danh sách thông tin files {
            'filename': str,
            'path': str,
            'size': int,
            'type': str,
            'extension': str
        }
    """
    folder_path = get_upload_folder_path(subfolder)
    if not os.path.exists(folder_path):
        return []
    
    files_info = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            files_info.append({
                'filename': filename,
                'path': file_path,
                'size': os.path.getsize(file_path),
                'type': get_file_type(filename),
                'extension': ext
            })
    
    return files_info


def delete_upload_subfolder(subfolder):
    """
    Xóa toàn bộ thư mục con và các files bên trong
    
    Args:
        subfolder: Tên thư mục con cần xóa
        
    Returns:
        dict: Kết quả {
            'success': bool,
            'deleted_count': int,
            'error': str (nếu có lỗi)
        }
    """
    import shutil
    
    folder_path = get_upload_folder_path(subfolder)
    if not os.path.exists(folder_path):
        return {'success': False, 'error': 'Folder not found'}
    
    try:
        # Đếm số files trước khi xóa
        file_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
        
        # Xóa thư mục và tất cả nội dung
        shutil.rmtree(folder_path)
        
        return {
            'success': True,
            'deleted_count': file_count
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def format_file_size(size_bytes):
    """
    Format kích thước file thành string dễ đọc
    
    Args:
        size_bytes: Kích thước file tính bằng bytes
        
    Returns:
        str: Kích thước đã format (ví dụ: '1.5 MB')
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"