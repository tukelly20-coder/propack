"""
Auto-Updater Module for Mở mã liệu UI
Module xử lý việc kiểm tra và cập nhật ứng dụng tự động.
Chỉ dành cho cập nhật ứng dụng đã đóng gói thành thư mục (.exe onedir) qua file .zip.
"""

import os
import sys
import json
import zipfile
import shutil
import subprocess
import ctypes
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

# Fix Unicode for Windows console
if sys.platform == 'win32':
    import io
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr is not None and hasattr(sys.stderr, 'buffer') and sys.stderr.buffer is not None:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ========================================================================
# CẤU HÌNH
# ========================================================================
APP_NAME = "Mở mã liệu UI"
CURRENT_VERSION = "1.0.0"
NETWORK_UPDATE_PATH = r"\\192.168.2.165\越南vp共享文件夹\13-IT_data\Software\Tool_Open\updates"


# ========================================================================
# HÀM TIỆN ÍCH
# ========================================================================
def get_app_path():
    """Lấy đường dẫn thư mục chính của ứng dụng"""
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
        internal_dir = os.path.join(app_dir, '_internal')
        if os.path.exists(internal_dir):
            return internal_dir
        return app_dir
    else:
        return os.path.dirname(os.path.abspath(__file__))


def get_onedir_path():
    """Lấy đường dẫn thư mục chứa exe (onedir)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_version_file_path():
    """Lấy đường dẫn file version"""
    return os.path.join(get_app_path(), "version.json")


def get_short_path_name(long_path):
    """
    Chuyển đổi đường dẫn dài sang định dạng 8.3 ngắn
    Trả về đường dẫn gốc nếu short path không tồn tại hoặc lỗi
    
    Ưu tiên dùng đường dẫn gốc vì PowerShell xử lý Unicode tốt hơn
    
    Args:
        long_path: Đường dẫn gốc (có thể chứa Unicode và dấu cách)
    
    Returns:
        Đường dẫn gốc (ưu tiên) hoặc short path 8.3 nếu tồn tại
    """
    if not long_path:
        return long_path
    
    # ƯU TIÊN: Nếu đường dẫn gốc tồn tại, dùng đường dẫn gốc
    # PowerShell xử lý Unicode tốt hơn cmd/robocopy
    if os.path.exists(long_path):
        print(f"[UPDATER] Đường dẫn gốc tồn tại, dùng đường dẫn gốc: {long_path}")
        return long_path
    
    try:
        # Gọi Windows API GetShortPathNameW
        GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        GetShortPathNameW.restype = wintypes.DWORD
        
        # Lấy độ dài cần thiết
        buffer_size = GetShortPathNameW(long_path, None, 0)
        if buffer_size == 0:
            print(f"[UPDATER] Không chuyển được short path, dùng đường dẫn gốc")
            return long_path
        
        # Lấy đường dẫn ngắn
        buffer = ctypes.create_unicode_buffer(buffer_size)
        GetShortPathNameW(long_path, buffer, buffer_size)
        short_path = buffer.value
        
        # KIỂM TRA: Short path có tồn tại không bằng Windows API GetFileAttributesW
        # os.path.exists() không nhận diện đúng short path 8.3
        if short_path and short_path != long_path:
            GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
            GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
            GetFileAttributesW.restype = wintypes.DWORD
            
            attrs = GetFileAttributesW(short_path)
            if attrs != -1:  # -1 means file/directory doesn't exist
                print(f"[UPDATER] Short path hợp lệ: {long_path} -> {short_path}")
                return short_path
        
        print(f"[UPDATER] Short path không tồn tại, dùng đường dẫn gốc: {long_path}")
        return long_path
            
    except Exception as e:
        print(f"[UPDATER] Lỗi chuyển đổi short path: {e}")
        return long_path


def load_local_version():
    """Đọc version hiện tại từ file"""
    version_file = get_version_file_path()
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('version', CURRENT_VERSION)
    except (FileNotFoundError, json.JSONDecodeError):
        return CURRENT_VERSION


def save_local_version(version):
    """Lưu version hiện hành"""
    version_file = get_version_file_path()
    data = {
        "app_name": APP_NAME,
        "version": version,
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def compare_versions(local_ver, remote_ver):
    """So sánh 2 version string. Trả về True nếu remote_ver > local_ver"""
    try:
        local_ver = local_ver.lstrip('v').strip()
        remote_ver = remote_ver.lstrip('v').strip()
        
        local_is_beta = 'beta' in local_ver.lower()
        remote_is_beta = 'beta' in remote_ver.lower()
        
        local_ver_clean = local_ver.replace('Beta', '').strip()
        local_ver_clean = local_ver_clean.replace('beta', '').strip()
        remote_ver_clean = remote_ver.replace('Beta', '').strip()
        remote_ver_clean = remote_ver_clean.replace('beta', '').strip()
        
        local_parts = []
        remote_parts = []
        
        for part in local_ver_clean.split('.'):
            num = ''.join(c for c in part if c.isdigit())
            if num:
                local_parts.append(int(num))
        
        for part in remote_ver_clean.split('.'):
            num = ''.join(c for c in part if c.isdigit())
            if num:
                remote_parts.append(int(num))
        
        if not local_parts or not remote_parts:
            return False
            
        for l, r in zip(local_parts, remote_parts):
            if r > l:
                return True
            elif r < l:
                return False
                
        if local_is_beta and not remote_is_beta:
            return True
        elif not local_is_beta and remote_is_beta:
            return False
            
        if len(remote_parts) > len(local_parts):
            return True
            
        return False
    except Exception as e:
        print(f"[UPDATER] Lỗi so sánh version: {e}")
        return False


# ========================================================================
# KIỂM TRA CẬP NHẬT
# ========================================================================
def check_update_from_network():
    """
    Kiểm tra cập nhật từ network share - tìm file thông báo và file .zip
    Trả về dict với thông tin chi tiết: {
        'found_update': bool,
        'update_info': dict or None,
        'error': str or None
    }
    """
    result = {
        'found_update': False,
        'update_info': None,
        'error': None
    }
    
    if not NETWORK_UPDATE_PATH:
        result['error'] = "Đường dẫn cập nhật mạng chưa được cấu hình"
        print(f"[UPDATER] Lỗi: {result['error']}")
        return result
    
    if not os.path.exists(NETWORK_UPDATE_PATH):
        result['error'] = f"Không thể truy cập đường dẫn mạng: {NETWORK_UPDATE_PATH}"
        print(f"[UPDATER] Lỗi: {result['error']}")
        print(f"[UPDATER] Vui lòng kiểm tra đường dẫn network share")
        return result
    
    update_info_file = os.path.join(NETWORK_UPDATE_PATH, "update_info.json")
    if not os.path.exists(update_info_file):
        result['error'] = f"Không tìm thấy file update_info.json trên network"
        print(f"[UPDATER] Lỗi: {result['error']}")
        print(f"[UPDATER] Đường dẫn: {NETWORK_UPDATE_PATH}")
        return result
    
    try:
        with open(update_info_file, 'r', encoding='utf-8') as f:
            update_info = json.load(f)
        
        local_version = load_local_version()
        remote_version = update_info.get('version', '0.0.0')
        
        if compare_versions(local_version, remote_version):
            # Kiểm tra file update zip
            zip_filename = update_info.get('onedir_filename') or update_info.get('filename', '')
            if zip_filename and zip_filename.endswith('.zip'):
                zip_path = os.path.join(NETWORK_UPDATE_PATH, zip_filename)
                if os.path.exists(zip_path):
                    update_info['download_path'] = zip_path
                    result['found_update'] = True
                    result['update_info'] = update_info
                    return result
                else:
                    result['error'] = f"Không tìm thấy file cập nhật: {zip_filename}"
                    print(f"[UPDATER] Lỗi: {result['error']}")
                    return result
            else:
                result['error'] = "Thông tin cập nhật không hợp lệ (thiếu tên file .zip)"
                print(f"[UPDATER] Lỗi: {result['error']}")
                return result
        else:
            # Không có bản cập nhật mới
            result['found_update'] = False
            result['error'] = None
            return result
    except Exception as e:
        result['error'] = f"Lỗi đọc file cập nhật: {str(e)}"
        print(f"[UPDATER] {result['error']}")
        return result


def check_for_updates():
    """
    Điểm vào gốc để kiểm tra mạng cho file .zip cập nhật
    Trả về dict: {
        'has_update': bool,
        'update_info': dict or None,
        'error': str or None
    }
    """
    result = {
        'has_update': False,
        'update_info': None,
        'error': None
    }
    
    print(f"\n{'='*50}")
    print(f"[UPDATER] ĐANG KIỂM TRA CẬP NHẬT...")
    print(f"{'='*50}")
    print(f"[UPDATER] Version hiện tại: {load_local_version()}")
    print(f"[UPDATER] Đường dẫn network: {NETWORK_UPDATE_PATH}")
    
    check_result = check_update_from_network()
    
    if check_result is None:
        # Lỗi không xác định
        result['error'] = "Lỗi kiểm tra cập nhật, vui lòng thử lại sau"
        print(f"[UPDATER] Lỗi: {result['error']}")
        print(f"{'='*50}\n")
        return result
    
    if check_result.get('error'):
        # Có lỗi cụ thể
        result['error'] = check_result['error']
        print(f"[UPDATER] Lỗi: {result['error']}")
        print(f"{'='*50}\n")
        return result
    
    if check_result.get('found_update'):
        update_info = check_result.get('update_info')
        print(f"[UPDATER] >>> TÌM THẤY BẢN CẬP NHẬT: v{update_info['version']}")
        result['has_update'] = True
        result['update_info'] = update_info
        return result
    
    # Không có cập nhật mới
    print(f"[UPDATER] Không có cập nhật mới")
    print(f"{'='*50}\n")
    return result


# ========================================================================
# TRẠNG THÁI CẬP NHẬT (STATE TRACKING)
# ========================================================================
def get_state_file_path():
    """Đường dẫn file lưu trạng thái cập nhật để app check khi khởi động"""
    return os.path.join(get_app_path(), "upd_state.json")

def set_update_state(status, message="", backup_dir=""):
    """Ghi trạng thái cập nhật"""
    try:
        data = {
            "status": status,
            "message": message,
            "backup_dir": backup_dir,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(get_state_file_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[UPDATER] Lỗi ghi trạng thái: {e}")

def get_update_state():
    """Đọc trạng thái cập nhật khi khởi động"""
    try:
        state_file = get_state_file_path()
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def clear_update_state():
    """Xóa file trạng thái sau khi đã thông báo cho user"""
    try:
        state_file = get_state_file_path()
        if os.path.exists(state_file):
            os.remove(state_file)
    except Exception:
        pass


# ========================================================================
# CÀI ĐẶT CẬP NHẬT ONEDIR
# ========================================================================
BAT_PAYLOAD_PATH = None

def apply_onedir_update(zip_path, progress_callback=None):
    """
    Tiến hành cập nhật bằng cách sao chép file .zip từ mạng về máy,
    giải nén, và tạo file batch để thay thế thư mục sau khi tắt ứng dụng.
    """
    global BAT_PAYLOAD_PATH
    import tempfile
    
    onedir_path = get_onedir_path()
    app_name = os.path.basename(onedir_path)
    
    # === LẤY SHORT PATH TRƯỚC KHI TẠO BACKUP PATH ===
    # GetShortPathNameW chỉ hoạt động với đường dẫn TỒN TẠI
    # Lấy short path của thư mục nguồn trước
    onedir_path_short = get_short_path_name(onedir_path)
    
    # Sử dụng basename của SHORT PATH cho tên backup
    # Điều này đảm bảo backup_path cũng chỉ chứa ASCII
    app_name_short = os.path.basename(onedir_path_short)
    print(f"[UPDATER] app_name (gốc): {app_name}")
    print(f"[UPDATER] app_name (short): {app_name_short}")
    
    print(f"[UPDATER] === BẮT ĐẦU APPLY ONEDIR UPDATE ===")
    print(f"[UPDATER] onedir_path (long): {onedir_path}")
    print(f"[UPDATER] onedir_path (short): {onedir_path_short}")
    print(f"[UPDATER] zip_path: {zip_path}")
    print(f"[UPDATER] app_name: {app_name}")
    print(f"[UPDATER] app_name (short): {app_name_short}")
    
    # BƯỚC 1: Tải (copy) file .zip từ network về temp local
    if progress_callback:
        progress_callback(10, "Đang tải bản cập nhật...")
    
    # Kiểm tra file zip nguồn tồn tại và kích thước
    if not os.path.exists(zip_path):
        print(f"[UPDATER] LỖI: File zip nguồn không tồn tại: {zip_path}")
        return False
    
    source_size = os.path.getsize(zip_path)
    print(f"[UPDATER] Kích thước file zip nguồn: {source_size} bytes")
    if source_size == 0:
        print(f"[UPDATER] LỖI: File zip có kích thước 0 bytes!")
        return False
    
    # Sử dụng tên thư mục an toàn (không dấu tiếng Việt)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_app_name = "app_update"  # Tên an toàn không dấu
    temp_folder = os.path.join(tempfile.gettempdir(), f"{safe_app_name}_{timestamp}")
    print(f"[UPDATER] Thư mục temp: {temp_folder}")
    
    if os.path.exists(temp_folder):
        try:
            shutil.rmtree(temp_folder)
            print(f"[UPDATER] Đã xóa thư mục temp cũ")
        except Exception as e:
            print(f"[UPDATER] Cảnh báo: Không xóa được thư mục temp cũ: {e}")
    
    try:
        os.makedirs(temp_folder, exist_ok=True)
        print(f"[UPDATER] Đã tạo thư mục temp")
    except Exception as e:
        print(f"[UPDATER] Lỗi tạo thư mục tạm: {e}")
        return False
    
    local_zip_path = os.path.join(temp_folder, "update.zip")
    print(f"[UPDATER] Đường dẫn file zip local: {local_zip_path}")
    
    try:
        shutil.copy2(zip_path, local_zip_path)
        print(f"[UPDATER] Đã copy file zip từ network về local")
        # Kiểm tra kích thước sau khi copy
        local_size = os.path.getsize(local_zip_path)
        print(f"[UPDATER] Kích thước file zip local: {local_size} bytes")
        if local_size != source_size:
            print(f"[UPDATER] LỖI: Kích thước file không khớp! Source: {source_size}, Local: {local_size}")
            return False
    except Exception as e:
        print(f"[UPDATER] Lỗi copy bản cập nhật từ mạng: {e}")
        return False

    # BƯỚC 2: Giải nén
    if progress_callback:
        progress_callback(30, "Đang giải nén tập tin...")
        
    extract_folder = os.path.join(temp_folder, "extracted")
    os.makedirs(extract_folder, exist_ok=True)
    print(f"[UPDATER] Thư mục giải nén: {extract_folder}")
    
    try:
        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
        print(f"[UPDATER] Đã giải nén file zip")
    except Exception as e:
        print(f"[UPDATER] Lỗi giải nén .zip: {e}")
        return False
        
    # Xác định đúng đường dẫn thư mục gốc bị nén
    temp_contents = os.listdir(extract_folder)
    print(f"[UPDATER] Nội dung thư mục giải nén: {temp_contents}")
    
    if len(temp_contents) == 1 and os.path.isdir(os.path.join(extract_folder, temp_contents[0])):
        final_extracted_folder = os.path.join(extract_folder, temp_contents[0])
        print(f"[UPDATER] Phát hiện thư mục cha, sử dụng: {final_extracted_folder}")
    else:
        final_extracted_folder = extract_folder
        print(f"[UPDATER] Sử dụng thư mục giải nén trực tiếp: {final_extracted_folder}")
    
    # === CHUYỂN ĐỔI SANG SHORT PATH ĐỂ TRÁNH LỖI UNICODE TRONG BATCH ===
    final_extracted_folder_short = get_short_path_name(final_extracted_folder)
    print(f"[UPDATER] Short path extracted: {final_extracted_folder_short}")
    
    # Kiểm tra nội dung thư mục giải nén
    extracted_contents = os.listdir(final_extracted_folder)
    print(f"[UPDATER] Nội dung thư mục cuối cùng: {extracted_contents}")
        
    # BƯỚC 3: Tạo lệnh thay thế thư mục
    if progress_callback:
        progress_callback(60, "Đang chuẩn bị cập nhật...")
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # PowerShell xử lý Unicode tốt, không cần short path
    # Dùng short path để đảm bảo robocopy hoạt động đúng
    backup_path = os.path.join(os.path.dirname(onedir_path_short), f"{app_name_short}_backup_{timestamp}")
    
    # === SHORT PATH CHO CÁC ĐƯỜNG DẪN ===
    # onedir_path_short đã có từ trên
    # backup_path đã tạo từ short path, nên cũng là short path rồi
    # Nhưng vẫn gọi lại để đảm bảo an toàn
    backup_path_short = get_short_path_name(backup_path)
    
    print(f"[UPDATER] Đường dẫn backup (long): {backup_path}")
    print(f"[UPDATER] Đường dẫn backup (short): {backup_path_short}")
    
    # Lấy thư mục cha (để ghi state file)
    # Sử dụng short path để đảm bảo tương thích
    parent_dir = os.path.dirname(onedir_path_short)
    parent_dir_short = get_short_path_name(parent_dir)  # Chuyển đổi sang short path
    parent_dir_original = parent_dir  # Giữ nguyên cho các thao tác liên quan đến Explorer
    
    print(f"[UPDATER] Short path onedir: {onedir_path_short}")
    print(f"[UPDATER] Short path backup: {backup_path_short}")
    print(f"[UPDATER] Short path parent: {parent_dir_short}")
    print(f"[UPDATER] Short path extracted: {final_extracted_folder_short}")
    
    # Escape đường dẫn backup - sử dụng cách an toàn hơn cho batch
    backup_path_escaped = f"\"{backup_path_short}\""
    
    # Escape đường dẫn onedir - sử dụng short path
    onedir_path_escaped = f"\"{onedir_path_short}\""
    
    print(f"[UPDATER] Đường dẫn app (short): {onedir_path_escaped}")
    print(f"[UPDATER] Đường dẫn backup (short): {backup_path_escaped}")
    
    # NOTE: We don't use sys.executable here because after folder swap,
    # the path will be wrong. Instead, the batch script will find .exe dynamically.
    start_cmd = "REM Will be determined dynamically in batch script"
    
    print(f"[UPDATER] Lệnh khởi động: Batch script sẽ tự tìm .exe trong thư mục mới")
    
    # Trạng thái bắt đầu chuẩn bị cài
    set_update_state("Applying", "Preparing to apply update via batch script")

    # === TẠO POWERSHELL SCRIPT (XỬ LÝ Unicode TỐT HƠN - KHÔNG CẦN SHORT PATH) ===
    # PowerShell hỗ trợ Unicode natively, không cần chuyển đổi short path
    # Script bao gồm tính năng tự động đóng ứng dụng
    # Cập nhật: Sử dụng robocopy thay vì Move-Item để xử lý tốt hơn với file locks
    # Bao gồm: Refresh Explorer Shell và Close Explorer Windows
    ps_content = '''# Auto-Updater PowerShell Script
# Supports Unicode paths natively - No short path conversion needed!
# Uses robocopy instead of Move-Item to handle file locks better
# Includes Explorer shell refresh to release locks

param(
    [string]$OnedirPath,
    [string]$BackupPath,
    [string]$ExtractedPath,
    [string]$ParentDir
)

# Force output to be UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================"
Write-Host "POWERSHELL UPDATE SCRIPT - Unicode Support"
Write-Host "========================================"
Write-Host "OnedirPath (raw param): '$OnedirPath'"
Write-Host "OnedirPath (short): $OnedirPath"
Write-Host "BackupPath (raw param): '$BackupPath'"
Write-Host "BackupPath (short): $BackupPath"
Write-Host "ExtractedPath (raw param): '$ExtractedPath'"
Write-Host "ExtractedPath (short): $ExtractedPath"
Write-Host "ParentDir (raw param): '$ParentDir'"
Write-Host "ParentDir (short): $ParentDir"

# Resolve short paths to long paths for operations that need the actual folder names
# (like finding the executable)
function Resolve-ShortPath {
    param([string]$Path)
    if (-not $Path) { return $Path }
    try {
        # Use the Scripting.FileSystemObject to get the long path
        $fso = New-Object -ComObject Scripting.FileSystemObject
        if ($fso.FolderExists($Path)) {
            return $fso.GetFolder($Path).Path
        } elseif ($fso.FileExists($Path)) {
            return $fso.GetFile($Path).Path
        } else {
            # If we can't resolve, return the original path
            return $Path
        }
    } catch {
        Write-Host "[DEBUG] Could not resolve short path '$Path': $_"
        return $Path
    }
}

# Get long paths for operations that need actual folder names
$OnedirPathLong = Resolve-ShortPath $OnedirPath
$BackupPathLong = Resolve-ShortPath $BackupPath
$ExtractedPathLong = Resolve-ShortPath $ExtractedPath
$ParentDirLong = Resolve-ShortPath $ParentDir

Write-Host "OnedirPath (long): $OnedirPathLong"
Write-Host "BackupPath (long): $BackupPathLong"
Write-Host "ExtractedPath (long): $ExtractedPathLong"
Write-Host "ParentDir (long): $ParentDirLong"

# ===== REFRESH EXPLORER SHELL FUNCTION =====
function Refresh-ExplorerShell {
    Write-Host "[INFO] Dang refresh Windows Explorer shell..."
    
    try {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class ExplorerRefresh {
    [DllImport(\"shell32.dll\")]
    public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
}
"@ -ErrorAction SilentlyContinue
        
        # SHCNE_UPDIR = 0x00000002, SHCNF_IDLIST = 0x0000
        [ExplorerRefresh]::SHChangeNotify(0x00000002, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero) 2>$null
        
        Write-Host "[INFO] Da refresh Explorer shell"
    } catch {
        Write-Host "[DEBUG] Khong refresh duoc Explorer: $_"
    }
}

# ===== CLOSE EXPLORER WINDOWS FUNCTION =====
function Close-ExplorerWindowsWithPath {
    param([string]$FolderPath)
    
    # Use long path for Explorer operations
    $LongFolderPath = Resolve-ShortPath $FolderPath
    Write-Host "[INFO] Dang tim cua so Explorer mo folder: $LongFolderPath"
    
    try {
        $shell = New-Object -ComObject Shell.Application
        $windows = $shell.Windows()
        
        $closedCount = 0
        foreach ($window in $windows) {
            try {
                if ($window.Document) {
                    $folderPath2 = $window.Document.Folder.Self.Path
                    if ($folderPath2 -like "*$LongFolderPath*" -or $LongFolderPath -like "*$folderPath2*") {
                        Write-Host "[INFO] Dong cua so Explorer: $($window.LocationName)"
                        $window.Quit()
                        $closedCount++
                    }
                }
            } catch {}
        }
        
        if ($windows) {
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($windows) | Out-Null
        }
        
        Write-Host "[INFO] Da dong $closedCount cua so Explorer"
    } catch {
        Write-Host "[DEBUG] Khong dong duoc Explorer: $_"
    }
}

# ===== TIM VA DONG UNG DUNG (GIAI PHAP 2: TU DONG DONG) =====
# Find exe name from path (use long path for file operations)
$folderName = [System.IO.Path]::GetFileName($OnedirPathLong)
$exeName = $folderName

# Try to find .exe in folder
$exeFiles = Get-ChildItem -Path $OnedirPathLong -Filter "*.exe" -File -ErrorAction SilentlyContinue
if ($exeFiles) {
    $exeName = $exeFiles[0].Name
    $exeName = $exeName -replace '\\.exe$', ''
} else {
    $exeName = $null
}

if ($exeName) {
    Write-Host "[INFO] Ten process can tim: $exeName"
    
    # Kiem tra va dong ung dung
    $processRunning = $true
    $attemptCount = 0
    $maxAttempts = 5
    
    while ($processRunning -and $attemptCount -lt $maxAttempts) {
        $processes = Get-Process -Name $exeName -ErrorAction SilentlyContinue
        
        if ($processes) {
            Write-Host "[INFO] Phat hien ung dung dang chay (lan $($attemptCount + 1)/$maxAttempts)"
            
            # Thu gui yeu cau dong (graceful shutdown)
            foreach ($proc in $processes) {
                try {
                    $result = $proc.CloseMainWindow()
                    if ($result) {
                        Write-Host "[INFO] Da gui yeu cau dong cho process $($proc.Name)"
                    }
                } catch {
                    Write-Host "[DEBUG] Khong gui duoc CloseMainWindow: $_"
                }
            }
            
            # Doi 3 giay
            Write-Host "[INFO] Doi 3 giay cho ung dung dong..."
            Start-Sleep -Seconds 3
            
            # Kiem tra lai
            $processes = Get-Process -Name $exeName -ErrorAction SilentlyContinue
            if (-not $processes) {
                $processRunning = $false
                Write-Host "[INFO] Ung dung da dong thanh cong!"
            } else {
                $attemptCount++
                if ($attemptCount -lt $maxAttempts) {
                    Write-Host "[WARN] Ung dung van con chay, thu lai..."
                }
            }
        } else {
            $processRunning = $false
            Write-Host "[INFO] Ung dung khong con chay!"
        }
    }
    
    # Neu van con chay sau khi thu nhieu lan, force kill
    if ($processRunning) {
        Write-Host "[WARN] Ung dung khong dong sau $maxAttempts lan thu, force kill..."
        $processes = Get-Process -Name $exeName -ErrorAction SilentlyContinue
        if ($processes) {
            Stop-Process -Name $exeName -Force -ErrorAction SilentlyContinue
            Write-Host "[INFO] Da force kill ung dung!"
            Start-Sleep -Seconds 3
        }
    }
} else {
    Write-Host "[WARN] Khong tim thay ten .exe, bo qua buoc dong ung dung"
}

# Doi them de dam bao file duoc giai phong
Write-Host "[INFO] Doi them 5 giay de dam bao file duoc giai phong..."
Start-Sleep -Seconds 5

# ===== REFRESH EXPLORER AND CLOSE WINDOWS =====
# Refresh Explorer shell to release locks
Refresh-ExplorerShell

# Close Explorer windows that might be viewing the folder
Close-ExplorerWindowsWithPath -FolderPath $OnedirPath

# Additional wait after refresh
Start-Sleep -Seconds 2

# Ham kiem tra xem folder co the di chuyen duoc khong
function Test-FolderMovable {
    param([string]$FolderPath)
    
    try {
        # Thu rename thu muc (chi doi ten, khong di chuyen)
        $testName = $FolderPath + ".test_move"
        Rename-Item -Path $FolderPath -NewName "test_move" -Force -ErrorAction Stop
        # Doi lai ten ban dau
        Rename-Item -Path "$FolderPath.test_move" -NewName $folderName -Force -ErrorAction Stop
        return $true
    } catch {
        Write-Host "[DEBUG] Folder bi khoa: $_"
        return $false
    }
}

# ===== BUOC 1: Sao luu he thong cu (SU DUNG ROBOCOPY COPY) =====
  Write-Host "[1/5] Dang sao luu he thong cu..."
  Write-Host "Robocopy: '$sourcePath' -> '$destPath' (copy)"
 
  # KIEM TRA: Duong dan nguon co ton tai khong?
  # Su dung OnedirPathLong cho tat ca cac thao tac robocopy
  # PowerShell xu li Unicode tot hon cmd/robocopy
  $sourcePath = $OnedirPathLong
  $destPath = $BackupPathLong
  
  Write-Host "[DEBUG] Kiem tra duong dan nguon..."
  if (-not (Test-Path $sourcePath)) {
      Write-Host "[WARN] Long path khong ton tai: $sourcePath"
      # Thu voi OnedirPath goc
      if ($OnedirPath -ne $OnedirPathLong) {
          Write-Host "[DEBUG] Thu voi duong dan goc..."
          $sourcePath = $OnedirPath
          $destPath = $BackupPath
      }
  }
  
  # Neu van khong ton tai, thoat
  if (-not (Test-Path $sourcePath)) {
      Write-Host "[LOI] Thu muc nguon khong ton tai: $sourcePath"
      Write-Host "[LOI] Vui long kiem tra lai duong dan ung dung!"
      $state = @{status="Failed"; message="Source folder does not exist: $sourcePath"} | ConvertTo-Json
      Set-Content -Path "$ParentDir\\upd_state.json" -Value $state -Encoding UTF8
      exit 1
  }
 
  # Liet ke noi dung thu muc nguon de debug
  Write-Host "[DEBUG] Noi dung thu muc nguon (5 items dau):"
  Get-ChildItem -Path $sourcePath -ErrorAction SilentlyContinue | Select-Object -First 5 | ForEach-Object {
      Write-Host "[DEBUG]   - $($_.Name)"
  }
 
  $robocopySuccess = $false
  $robocopyRetries = 0
  $maxRobocopyRetries = 3
  $usedLongPath = $false
 
  # Sao luu su dung robocopy copy (khong xoa nguon)
  while (-not $robocopySuccess -and $robocopyRetries -lt $maxRobocopyRetries) {
      # Xoa backup folder neu da ton tai
      if (Test-Path $destPath) {
          try {
              Remove-Item -Path $destPath -Recurse -Force -ErrorAction SilentlyContinue
              Start-Sleep -Seconds 2
          } catch {}
      }
      
      # Su dung robocopy de copy (khong xoa nguon)
      # /E = subdirectories including empty
      # /COPYALL = copy all file info
      # /R:3 = retry 3 times
      # /W:5 = wait 5 seconds between retries
      # /MT:8 = 8 threads for faster copy (co the gay loi voi Unicode)
      # /V = verbose output for debugging
      Write-Host "[INFO] Thu robocopy copy lan $($robocopyRetries + 1)/$maxRobocopyRetries..."
      Write-Host "[DEBUG] Source: $sourcePath -> Dest: $destPath"
      
      # Su dung bien de theo doi neu can thu lai khong co MT
      $tryWithoutMT = $false
      
      $robocopyResult = robocopy "$sourcePath" "$destPath" /E /COPYALL /R:3 /W:5 /MT:8 /V /NFL /NDL /NC /NS /NP 2>&1
      $robocopyExitCode = $LASTEXITCODE
      
      Write-Host "[DEBUG] Robocopy exit code: $robocopyExitCode"
      
      # Hien thi mot so dong ket qua de debug
      if ($robocopyResult) {
          $robocopyResult | Select-Object -First 5 | ForEach-Object {
              Write-Host "[DEBUG]   $_"
          }
      }
      
      # Xu ly exit code 16 - Serious error
      if ($robocopyExitCode -eq 16) {
          Write-Host "[LOI] Robocopy exit code 16: Serious error!"
          Write-Host "[LOI] Cac nguyen nhan co the:"
          Write-Host "[LOI]   1. Duong dan nguon khong ton tai hoac khong the truy cap"
          Write-Host "[LOI]   2. Thu muc bi khoa boi process khac"
          Write-Host "[LOI]   3. Khong du quyen truy cap"
          Write-Host "[LOI]   4. Van de voi /MT:8 va Unicode"
          
          # Thu lai khong co /MT:8 (co the gay xung dot voi Unicode)
          if (-not $tryWithoutMT) {
              Write-Host "[DEBUG] Thu lai khong co /MT:8..."
              $robocopyResult = robocopy "$sourcePath" "$destPath" /E /COPYALL /R:3 /W:5 /V /NFL /NDL /NC /NS /NP 2>&1
              $robocopyExitCode = $LASTEXITCODE
              $tryWithoutMT = $true
              Write-Host "[DEBUG] Robocopy exit code (khong /MT): $robocopyExitCode"
          }
          
          # Neu van loi, thu PowerShell Copy-Item
          if ($robocopyExitCode -ge 8) {
              Write-Host "[DEBUG] Thu dung PowerShell Copy-Item..."
              try {
                  # Xoa neu da ton tai
                  if (Test-Path $destPath) {
                      Remove-Item -Path $destPath -Recurse -Force -ErrorAction SilentlyContinue
                      Start-Sleep -Seconds 2
                  }
                  
                  # Tao thu muc dich
                  New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                  
                  # Copy su dung PowerShell
                  Copy-Item -Path "$sourcePath\*" -Destination "$destPath" -Recurse -Force -ErrorAction Stop
                  $robocopyExitCode = 1
                  Write-Host "[INFO] Copy-Item thanh cong!"
              } catch {
                  Write-Host "[LOI] Copy-Item that bai: $_"
                  $robocopyExitCode = 16
              }
          }
      }
      
      if ($robocopyExitCode -lt 8) {
          $robocopySuccess = $true
          Write-Host "[DEBUG] Sao luu thanh cong!"
      } else {
          Write-Host "[WARN] Robocopy that bai voi ma: $robocopyExitCode"
          $robocopyRetries++
          
          if ($robocopyRetries -lt $maxRobocopyRetries) {
              # Refresh Explorer before retry
              Refresh-ExplorerShell
              Close-ExplorerWindowsWithPath -FolderPath $OnedirPath
              Write-Host "[DEBUG] Thu lai sau 5 giay..."
              Start-Sleep -Seconds 5
          }
      }
  }

$backupSuccess = $robocopySuccess

if (-not $backupSuccess) {
    Write-Host "[LOI] Khong the sao luu he thong cu!"
    Write-Host "[LOI] Vui long thu lai."
    
    $state = @{status="Failed"; message="Cannot backup current system"} | ConvertTo-Json
    Set-Content -Path "$ParentDir\\upd_state.json" -Value $state -Encoding UTF8
    exit 1
}

# ===== BUOC 2: Copy ban moi tu thu muc giai nen vao vi tri (SU DUNG ROBOCOPY) =====
  Write-Host "[2/5] Dang cai dat ban moi..."
  
  # Su dung long path cho install
  $installSourceBase = $ExtractedPathLong
  $installDest = $OnedirPathLong
  
  Write-Host "Robocopy: '$installSourceBase' -> '$installDest' (copy)"
 
  # Xoa noi dung cu trong onedir_path truoc khi copy moi
  Write-Host "[INFO] Xoa noi dung cu trong onedir_path..."
  try {
      # Xoa tat ca file va thu muc con trong onedir_path
      Get-ChildItem -Path $installDest -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
      Write-Host "[DEBUG] Da xoa noi dung cu"
  } catch {
      Write-Host "[DEBUG] Khong xoa duoc noi dung cu: $_"
  }
 
  Start-Sleep -Seconds 2
 
  # Su dung robocopy de copy ban moi vao onedir_path
  $robocopyInstallSuccess = $false
  $robocopyInstallRetries = 0
  $maxRobocopyInstallRetries = 3
  $usedInstallLongPath = $false
 
  while (-not $robocopyInstallSuccess -and $robocopyInstallRetries -lt $maxRobocopyInstallRetries) {
      Write-Host "[INFO] Thu robocopy install lan $($robocopyInstallRetries + 1)/$maxRobocopyInstallRetries..."
      
      # Kiem tra xem ExtractedPath co ton tai khong
      if (-not (Test-Path $installSourceBase)) {
          Write-Host "[LOI] Thu muc giai nen khong ton tai: $installSourceBase"
          # Thu voi duong dan goc
          if (-not $usedInstallLongPath) {
              $installSourceBase = $ExtractedPath
              $installDest = $OnedirPath
              $usedInstallLongPath = $true
              Write-Host "[DEBUG] Thu voi duong dan goc..."
          }
      }
      
      # Neu ExtractedPath la thu muc con (nhu Mo ma lieu UI), lay noi dung ben trong
      $sourcePath = $installSourceBase
      $extractedItems = Get-ChildItem -Path $installSourceBase -ErrorAction SilentlyContinue
      if ($extractedItems -and $extractedItems.Count -eq 1 -and $extractedItems[0].PSIsContainer) {
          # Co mot thu muc con, su dung thu muc con lam nguon
          $sourcePath = $extractedItems[0].FullName
          Write-Host "[DEBUG] Su dung thu muc con lam nguon: $sourcePath"
      }
      
      Write-Host "[DEBUG] Install: $sourcePath -> $installDest"
      
      # Bien de theo doi neu can thu lai khong co MT
      $tryInstallWithoutMT = $false
      
      $robocopyInstallResult = robocopy "$sourcePath" "$installDest" /E /COPYALL /R:3 /W:5 /MT:8 /V /NFL /NDL /NC /NS /NP 2>&1
      $robocopyInstallExitCode = $LASTEXITCODE
      
      Write-Host "[DEBUG] Robocopy install exit code: $robocopyInstallExitCode"
      
      # Hien thi mot so dong ket qua de debug
      if ($robocopyInstallResult) {
          $robocopyInstallResult | Select-Object -First 5 | ForEach-Object {
              Write-Host "[DEBUG]   $_"
          }
      }
      
      # Xu ly exit code 16 - Serious error
      if ($robocopyInstallExitCode -eq 16) {
          Write-Host "[LOI] Robocopy install exit code 16: Serious error!"
          
          # Thu lai khong co /MT:8
          if (-not $tryInstallWithoutMT) {
              Write-Host "[DEBUG] Thu lai khong co /MT:8..."
              $robocopyInstallResult = robocopy "$sourcePath" "$installDest" /E /COPYALL /R:3 /W:5 /V /NFL /NDL /NC /NS /NP 2>&1
              $robocopyInstallExitCode = $LASTEXITCODE
              $tryInstallWithoutMT = $true
              Write-Host "[DEBUG] Robocopy install exit code (khong /MT): $robocopyInstallExitCode"
          }
          
          # Neu van loi, thu PowerShell Copy-Item
          if ($robocopyInstallExitCode -ge 8) {
              Write-Host "[DEBUG] Thu dung PowerShell Copy-Item cho install..."
              try {
                  # Xoa noi dung cu
                  Get-ChildItem -Path $installDest -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                  Start-Sleep -Seconds 1
                  
                  # Tao thu muc dich
                  New-Item -ItemType Directory -Path $installDest -Force | Out-Null
                  
                  # Copy su dung PowerShell
                  Copy-Item -Path "$sourcePath\*" -Destination "$installDest" -Recurse -Force -ErrorAction Stop
                  $robocopyInstallExitCode = 1
                  Write-Host "[INFO] Install Copy-Item thanh cong!"
              } catch {
                  Write-Host "[LOI] Install Copy-Item that bai: $_"
                  $robocopyInstallExitCode = 16
              }
          }
      }
      
      # Exit codes: 0-7 = success, 8+ = error
      if ($robocopyInstallExitCode -lt 8) {
          $robocopyInstallSuccess = $true
          Write-Host "[DEBUG] Copy ban moi thanh cong!"
      } else {
          Write-Host "[WARN] Robocopy install that bai voi ma: $robocopyInstallExitCode"
          $robocopyInstallRetries++
          
          if ($robocopyInstallRetries -lt $maxRobocopyInstallRetries) {
              Refresh-ExplorerShell
              Close-ExplorerWindowsWithPath -FolderPath $installDest
              Write-Host "[DEBUG] Thu lai sau 5 giay..."
              Start-Sleep -Seconds 5
          }
      }
  }

if (-not $robocopyInstallSuccess) {
    Write-Host "[LOI] Khong the cai dat ban moi!"
    # Khoi phuc tu backup
    Write-Host "[INFO] Dang khoi phuc tu backup..."
    try {
        # Su dung long path cho restore
        $restoreSource = $BackupPathLong
        $restoreDest = $OnedirPathLong
        
        # Xoa noi dung hien tai
        Get-ChildItem -Path $restoreDest -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        # Copy tu backup ve
        robocopy "$restoreSource" "$restoreDest" /E /COPYALL /R:3 /W:5 /MT:8 /NFL /NDL /NC /NS /NP | Out-Null
        Write-Host "[DEBUG] Da khoi phuc tu backup"
    } catch {}
    
    $state = @{status="Failed"; message="Failed to install new version, rolled back"} | ConvertTo-Json
    Set-Content -Path "$ParentDir\\upd_state.json" -Value $state -Encoding UTF8
    exit 1
}

# ===== BUOC 3: Xoa backup folder (neu update thanh cong) =====
Write-Host "[3/5] Xoa thu muc backup..."
try {
    if (Test-Path $BackupPathLong) {
        Remove-Item -Path $BackupPathLong -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "[DEBUG] Da xoa thu muc backup"
    }
} catch {
    Write-Host "[DEBUG] Khong xoa duoc backup: $_"
}

# ===== BUOC 4: Kiem tra va khoi dong exe =====
Write-Host "[4/5] Hoan tat! Kiem tra va khoi dong..."

$exeFiles = Get-ChildItem -Path $OnedirPathLong -Filter "*.exe" -File | Select-Object -First 1

if ($exeFiles) {
    Write-Host "[DEBUG] Tim thay .exe: $($exeFiles.FullName)"
    $state = @{status="Success"; message="Update completed successfully"} | ConvertTo-Json
    Set-Content -Path "$ParentDir\\upd_state.json" -Value $state -Encoding UTF8
    
    Write-Host "[5/5] Dang khoi dong lai ung dung..."
    Start-Process -FilePath $exeFiles.FullName
} else {
    Write-Host "[LOI] Khong tim thay file .exe!"
    if (Test-Path $BackupPathLong) {
        Write-Host "Dang khoi phuc tu backup..."
        try {
            # Su dung long path cho restore
            $restoreSource = $BackupPathLong
            $restoreDest = $OnedirPathLong
            
            # Xoa noi dung hien tai
            Get-ChildItem -Path $restoreDest -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            # Copy tu backup ve
            robocopy "$restoreSource" "$restoreDest" /E /COPYALL /R:3 /W:5 /MT:8 /NFL /NDL /NC /NS /NP | Out-Null
        } catch {}
    }
    $state = @{status="Failed"; message="No .exe found in new folder"} | ConvertTo-Json
    Set-Content -Path "$ParentDir\\upd_state.json" -Value $state -Encoding UTF8
    exit 1
}

Write-Host "Hoan tat!"
exit 0
'''
    
    # Lưu PowerShell script (dùng UTF-8 with BOM để PowerShell hiểu Unicode)
    ps_path = os.path.join(temp_folder, "apply_update.ps1")
    try:
        # Write with UTF-8 BOM for PowerShell compatibility
        import codecs
        with codecs.open(ps_path, 'w', encoding='utf-8-sig') as f:
            f.write(ps_content)
        print(f"[UPDATER] Đã tạo PowerShell script: {ps_path}")
    except Exception as e:
        print(f"[UPDATER] Lỗi tạo PowerShell script: {e}")
        return False
    
    # Tạo batch script wrapper để gọi PowerShell
    # Dùng short path để tránh lỗi Unicode và dấu cách
    bat_content = rf'''@echo off
    chcp 65001 > NUL
    
    echo ========================================
    echo POWERSHELL UPDATE - Unicode Support
    echo ========================================
    echo onedir_path: {onedir_path_short}
    echo backup_path: {backup_path_short}
    echo extracted_path: {final_extracted_folder_short}
    echo parent_dir: {parent_dir_short}
    echo ========================================
    
    powershell.exe -ExecutionPolicy Bypass -File "{ps_path}" -OnedirPath "{onedir_path_short}" -BackupPath "{backup_path_short}" -ExtractedPath "{final_extracted_folder_short}" -ParentDir "{parent_dir_short}"
    
    if %ERRORLEVEL% NEQ 0 (
        echo [LOI] PowerShell script that bai!
        pause
    )
    
    del "%~f0"
    '''
    
    bat_path = os.path.join(temp_folder, "apply_update.bat")
    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
        BAT_PAYLOAD_PATH = bat_path
        print(f"[UPDATER] Đã tạo batch script: {bat_path}")
    except Exception as e:
        print(f"[UPDATER] Lỗi chuẩn bị script cập nhật: {e}")
        return False
        
    if progress_callback:
        progress_callback(100, "Sẵn sàng cập nhật!")
    
    print(f"[UPDATER] === KẾT THÚC APPLY ONEDIR UPDATE ===")
    print(f"[UPDATER] Batch script path: {BAT_PAYLOAD_PATH}")
    
    return True


def perform_update(update_info, progress_callback=None):
    """
    Thực hiện logic cập nhật
    update_info: dict chứa 'download_path' và 'version'
    """
    print(f"[UPDATER] ===== BẮT ĐẦU QUÁ TRÌNH CẬP NHẬT =====")
    
    if isinstance(update_info, dict):
        download_path = update_info.get('download_path', '')
        version = update_info.get('version', '?')
    else:
        download_path = update_info.get('download_path', '') if update_info else ''
        version = '?'
    
    print(f"[UPDATER] Version mới: {version}")
    print(f"[UPDATER] Đường dẫn file: {download_path}")
    
    if not download_path:
        print(f"[UPDATER] Lỗi: Không có đường dẫn tải xuống")
        return False
        
    if not os.path.exists(download_path):
        print(f"[UPDATER] Lỗi: Không tìm thấy tệp {download_path}")
        return False
    
    print(f"[UPDATER] Tệp tồn tại, bắt đầu apply_onedir_update()...")
    success = apply_onedir_update(download_path, progress_callback)
    
    if success:
        print(f"[UPDATER] apply_onedir_update() thành công!")
        if version and version != '?':
            save_local_version(version)
        print(f"[UPDATER] Đã cập nhật thành công lên phiên bản {version}")
    else:
        print(f"[UPDATER] Lỗi: apply_onedir_update() thất bại!")
        
    return success


# ========================================================================
# KHỞI ĐỘNG LẠI ỨNG DỤNG
# ========================================================================
def restart_application():
    """Khởi động lại exe mới nhất thay vì scripts"""
    global BAT_PAYLOAD_PATH
    
    print(f"[UPDATER] ===== KHỞI ĐỘNG LẠI ỨNG DỤNG =====")
    print(f"[UPDATER] BAT_PAYLOAD_PATH: {BAT_PAYLOAD_PATH}")
    
    app_path = get_app_path()
    onedir_path = get_onedir_path()
    
    print(f"[UPDATER] app_path: {app_path}")
    print(f"[UPDATER] onedir_path: {onedir_path}")
    
    # Xóa .pyc files
    try:
        pyc_count = 0
        for pyc_file in Path(app_path).glob("**/*.pyc"):
            try:
                os.remove(pyc_file)
                pyc_count += 1
            except Exception as e:
                print(f"[UPDATER] Không xóa được {pyc_file}: {e}")
        print(f"[UPDATER] Đã xóa {pyc_count} file .pyc")
    except Exception as e:
        print(f"[UPDATER] Lỗi khi xóa .pyc: {e}")
    
    # Kiểm tra batch script
    if BAT_PAYLOAD_PATH and os.path.exists(BAT_PAYLOAD_PATH):
        print(f"[UPDATER] Tìm thấy batch script, đang thực thi: {BAT_PAYLOAD_PATH}")
        
        # Đọc nội dung batch để debug
        try:
            with open(BAT_PAYLOAD_PATH, 'r', encoding='utf-8') as f:
                bat_content = f.read()
            print(f"[UPDATER] Nội dung batch (500 ký tự đầu):")
            print(bat_content[:500])
        except Exception as e:
            print(f"[UPDATER] Không đọc được nội dung batch: {e}")
        
        # Chạy file bat để swap folder và khởi động lại
        # DETACHED_PROCESS = 0x00000008
        try:
            print(f"[UPDATER] Đang chạy batch script với DETACHED_PROCESS...")
            # Sử dụng CREATE_NO_WINDOW = 0x08000000 kết hợp với DETACHED_PROCESS
            subprocess.Popen(
                ["cmd.exe", "/c", "start", "", BAT_PAYLOAD_PATH],
                creationflags=0x00000008 | 0x08000000,
                stdout=open(os.devnull, 'w'),
                stderr=open(os.devnull, 'w')
            )
            print(f"[UPDATER] Đã khởi động batch script, thoát ứng dụng...")
            print(f"[UPDATER] === CHÚ Ý: Ứng dụng sẽ khởi động lại sau khi batch chạy xong ===")
            sys.exit(0)
        except Exception as e:
            print(f"[UPDATER] Lỗi khi chạy batch script: {e}")
            # Thử cách khác
            try:
                print(f"[UPDATER] Thử cách khác để chạy batch...")
                os.startfile(BAT_PAYLOAD_PATH)
                print(f"[UPDATER] Đã chạy batch với os.startfile")
                sys.exit(0)
            except Exception as e2:
                print(f"[UPDATER] Lỗi cách 2: {e2}")
    else:
        print(f"[UPDATER] Không tìm thấy batch script, khởi động lại thông thường")
        if getattr(sys, 'frozen', False):
            print("[UPDATER] Đang khởi động lại ứng dụng (.exe)...")
            exe_path = sys.executable
            print(f"[UPDATER] exe_path: {exe_path}")
            subprocess.Popen([exe_path])
            sys.exit(0)
        else:
            # Nếu đang debug ở chế độ .py, vẫn hỗ trợ chạy lại kịch bản
            main_file = os.path.join(app_path, "Mở mã liệu UI.py")
            if os.path.exists(main_file):
                print("[UPDATER] Đang khởi động lại ứng dụng script (.py)...")
                print(f"[UPDATER] main_file: {main_file}")
                subprocess.Popen([sys.executable, main_file])
                sys.exit(0)
            else:
                print(f"[UPDATER] LỖI: Không tìm thấy file chính: {main_file}")
