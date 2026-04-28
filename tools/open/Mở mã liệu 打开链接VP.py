import requests
import subprocess
import os
import re
import pandas as pd
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import time
import pyperclip

# Lấy thư mục của ứng dụng (hỗ trợ cả PyInstaller và Python thường)
if getattr(sys, 'frozen', False):
    # Đang chạy như file .exe (PyInstaller)
    app_dir = os.path.dirname(sys.executable)
else:
    # Đang chạy như script Python
    app_dir = os.path.dirname(os.path.abspath(__file__))

log_path = os.path.join(app_dir, 'material_query.log')

# Cấu hình logging với RotatingFileHandler (max 5MB, giữ 3 bản)
file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))

console_stream_handler = logging.StreamHandler()
console_stream_handler.setLevel(logging.WARNING)
console_stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_stream_handler]
)
logger = logging.getLogger(__name__)

# Tạo logger riêng cho console với level cao hơn để tránh quá nhiều thông tin
console_logger = logging.getLogger('console')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Đường dẫn UNC dự phòng khi server không trả về kết quả
FALLBACK_BASE_PATH = r"\\192.168.2.165\越南vp共享文件夹\09-工程图纸 Bản vẽ Kỹ Thuật Công Trình\存货档案图片"

# Đường dẫn file Excel chứa mapping cEngineerFigNo -> cInvCode
EXCEL_PATH = r"\\192.168.2.165\越南vp共享文件夹\09-工程图纸 Bản vẽ Kỹ Thuật Công Trình\存货档案库.xlsx"


def shorten_path_display(path: str, max_len: int = 500) -> str:
    """Hiển thị đường dẫn đầy đủ."""
    return path  # Hiển thị đầy đủ không rút gọn


def safe_print(message: str):
    """In message an toàn, xử lý UnicodeEncodeError trên Windows."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Nếu terminal không hỗ trợ Unicode, thử encode với cp437 hoặc bỏ qua
        try:
            print(message.encode('utf-8').decode('utf-8', errors='ignore'))
        except:
            print(message.encode('ascii', errors='ignore').decode('ascii'))


def open_folder_from_unc(path: str, select_files: list = None, open_file_directly: bool = False) -> bool:
    """Mở File Explorer hoặc mở trực tiếp file.
    
    Args:
        path: Đường dẫn UNC đến file hoặc folder
        select_files: Danh sách các files cần select (nếu có)
        open_file_directly: Nếu True, mở trực tiếp file thay vì chỉ mở folder
    
    Returns:
        bool: True nếu mở thành công, False nếu thất bại
    """
    windows_path = path.replace('/', '\\')
    logger.debug(f"[File] Processing path: {windows_path}")
    logger.debug(f"[File] open_file_directly: {open_file_directly}")
    
    # Nếu yêu cầu mở trực tiếp file
    if open_file_directly:
        if os.path.exists(windows_path):
            try:
                os.startfile(windows_path)
                safe_print(f"[OK] Opened file directly: {shorten_path_display(windows_path)}")
                logger.info(f"Opened file directly: {windows_path}")
                logger.debug(f"[File] File exists and was opened successfully")
                return True
            except Exception as e:
                safe_print(f"[ERROR] Cannot open file directly: {e}")
                logger.error(f"Error opening file directly: {e}")
                logger.exception("[File] Exception details:")
                return False
        else:
            # File không tồn tại
            safe_print(f"[ERROR] File not found: {shorten_path_display(windows_path)}")
            logger.warning(f"[File] File does not exist: {windows_path}")
            return False
    
    try:
        if select_files and len(select_files) > 1:
            # Windows Explorer /select không hỗ trợ multi-select
            # Giải pháp: Mở folder và select file đầu tiên
            folder = os.path.dirname(windows_path)
            first_file = select_files[0]
            first_full_path = os.path.join(folder, first_file)
            logger.debug(f"[File] Opening folder with first file selected: {first_full_path}")
            subprocess.run(f'explorer /select,"{first_full_path}"', shell=True)
            safe_print(f"[OK] Opened folder with {len(select_files)} files (first selected)")
            logger.info(f"Opened folder with {len(select_files)} files: {folder}")
            return True
        else:
            # Mở và select 1 file (hoặc folder)
            logger.debug(f"[File] Opening File Explorer with selection: {windows_path}")
            subprocess.run(f'explorer /select,"{windows_path}"', shell=True)
            safe_print(f"[OK] Opened File Explorer: {os.path.dirname(windows_path)}")
            logger.info(f"Opened File Explorer: {windows_path}")
            return True
    except Exception as e:
        safe_print(f"[ERROR] Cannot open File Explorer: {e}")
        logger.error(f"Error opening File Explorer: {e}")
        logger.exception("[File] Exception details:")
        return False


def get_folder_and_files(url: str) -> tuple[str, str]:
    """Trích xuất folder path và filename từ URL.
    
    Args:
        url: Đường dẫn đầy đủ đến file (VD: \\server\folder\file.jpg)
    
    Returns:
        Tuple (folder_path, filename)
    """
    # Chuyển đổi về dạng Windows path
    windows_path = url.replace('/', '\\')
    
    # Lấy phần folder và filename
    folder = os.path.dirname(windows_path)
    filename = os.path.basename(windows_path)
    
    return folder, filename


def group_urls_by_folder(urls: list) -> dict[str, list]:
    """Nhóm các URLs theo folder cha.
    
    Args:
        urls: Danh sách các URLs
    
    Returns:
        Dictionary {folder_path: [filename1, filename2, ...]}
    """
    grouped = {}
    
    for url in urls:
        folder, filename = get_folder_and_files(url)
        
        if folder not in grouped:
            grouped[folder] = []
        
        if filename:
            grouped[folder].append(filename)
    
    return grouped


def open_all_folders(urls: list):
    """Mở tất cả các thư mục từ danh sách URLs.
    
    Nếu các URLs cùng folder, sẽ mở 1 folder và select tất cả các files.
    """
    if not urls:
        return
    
    # Nhóm URLs theo folder
    grouped = group_urls_by_folder(urls)
    
    safe_print(f"\n[INFO] Opening {len(grouped)} folder(s)...")
    logger.info(f"[File] Opening {len(grouped)} folder(s) with {len(urls)} total file(s)")
    
    # Mở từng folder
    for folder_path, filenames in grouped.items():
        if filenames and len(filenames) > 0:
            logger.debug(f"[File] Opening folder: {folder_path} with {len(filenames)} file(s): {filenames}")
            # Mở folder với file được select đầu tiên
            first_file = filenames[0]
            full_path = os.path.join(folder_path, first_file)
            open_folder_from_unc(full_path, select_files=filenames if len(filenames) > 1 else None)
    
    return len(grouped)


def copy_to_clipboard(text: str):
    """Copy text vào clipboard."""
    try:
        pyperclip.copy(text)
        # Hiển thị đầy đủ
        display_text = text
        safe_print(f"[OK] Copied: {display_text}")
        logger.info(f"Copied to clipboard: {text}")
    except Exception as e:
        safe_print(f"[WARN] Cannot copy to clipboard: {e}")
        logger.error(f"Clipboard error: {e}")


def is_engineer_fig_no(code: str) -> bool:
    r"""
    Kiểm tra nếu code là dạng cEngineerFigNo.
    - Full pattern: P[A-Z]{3,}\d{3}-\d{4}-\d{2}-A\d (VD: PGZT076-0000-00-A0, PLSX048-0000-00-A0)
    - Partial patterns:
      - P[A-Z]{3,}\d{1,3} (VD: PGZT076, PGZT, PLSX048)
      - P[A-Z]{3,}\d{3}-\d{4} (VD: PGZT092-0000)
      - P[A-Z]{3,}\d{3}-\d{4}-\d{2} (VD: PGZT092-0000-02)
      - P[A-Z]{3,}\d{3}-\d{4}-\d{2}-A (VD: PGZT092-0000-02-A)
    """
    # Full pattern đầy đủ - cho phép 3+ ký tự chữ cái sau P
    full_pattern = r'^P[A-Z]{3,}\d{3}-\d{4}-\d{2}-A\d$'
    if re.match(full_pattern, code, re.IGNORECASE):
        return True
    
    # Partial pattern - bắt đầu bằng P và có ít nhất 4 ký tự (P + 3 ký tự + 1-3 số)
    partial_pattern = r'^P[A-Z]{3,}\d{1,3}$'
    if re.match(partial_pattern, code, re.IGNORECASE):
        return True
    
    # Extended patterns for more flexible matching
    # P[A-Z]{3,}\d{3}-\d{4} (e.g., PGZT092-0000)
    extended_pattern1 = r'^P[A-Z]{3,}\d{3}-\d{4}$'
    if re.match(extended_pattern1, code, re.IGNORECASE):
        return True
    
    # P[A-Z]{3,}\d{3}-\d{4}-\d{2} (e.g., PGZT092-0000-02)
    extended_pattern2 = r'^P[A-Z]{3,}\d{3}-\d{4}-\d{2}$'
    if re.match(extended_pattern2, code, re.IGNORECASE):
        return True
    
    # P[A-Z]{3,}\d{3}-\d{4}-\d{2}-A (e.g., PGZT092-0000-02-A)
    extended_pattern3 = r'^P[A-Z]{3,}\d{3}-\d{4}-\d{2}-A$'
    if re.match(extended_pattern3, code, re.IGNORECASE):
        return True
    
    return False


def normalize_unc_path(path: str) -> str:
    """Normalize UNC path để đảm bảo tương thích với Windows."""
    path = path.replace('/', '\\')
    if not path.startswith('\\\\'):
        path = '\\\\' + path.lstrip('\\')
    return path


CACHED_EXCEL_DATA = None

def get_excel_data(excel_path: str):
    """Đọc dữ liệu Excel vào memory (chỉ tải 1 lần)."""
    global CACHED_EXCEL_DATA
    logger.debug(f"[Excel] get_excel_data called with path: {excel_path}, CACHED_EXCEL_DATA is {'None' if CACHED_EXCEL_DATA is None else f'{len(CACHED_EXCEL_DATA)} sheets'}")
    if CACHED_EXCEL_DATA is not None:
        logger.debug(f"[Excel] Returning cached data with {len(CACHED_EXCEL_DATA)} sheets")
        return CACHED_EXCEL_DATA
        
    safe_print(f"   [INFO] Đang tải dữ liệu Excel vào bộ nhớ 1 lần duy nhất, vui lòng đợi...")
    logger.info(f"Loading Excel into memory: {excel_path}")
    
    try:
        xls = pd.ExcelFile(excel_path)
        data = []
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            if 'cEngineerFigNo' in df.columns and 'cInvCode' in df.columns:
                data.append((sheet_name, df))
        safe_print(f"   [OK] Đã tải xong dữ liệu Excel!")
        CACHED_EXCEL_DATA = data
        logger.info(f"[Excel] Cached {len(data)} sheets")
        return CACHED_EXCEL_DATA
    except Exception as e:
        safe_print(f"   [ERROR] Lỗi khi tải dữ liệu Excel: {e}")
        logger.error(f"Failed to load Excel data: {e}")
        return None

def find_cinvcode_from_excel(engineer_fig_no: str, return_all: bool = False) -> str | list | None:
    """Tìm cInvCode tương ứng với cEngineerFigNo trong file Excel.
    
    Args:
        engineer_fig_no: Mã cEngineerFigNo cần tìm
        return_all: Nếu True, trả về tất cả các kết quả; nếu False, trả về kết quả đầu tiên
    
    Returns:
        - str: Một cInvCode đơn (khi return_all=False hoặc chỉ có 1 kết quả)
        - list: Danh sách các dict chứa cEngineerFigNo và cInvCode (khi return_all=True và có nhiều kết quả)
        - None: Không tìm thấy kết quả
    """
    excel_path = normalize_unc_path(EXCEL_PATH)
    
    try:
        logger.debug(f"[Excel] Looking for cEngineerFigNo: {engineer_fig_no}")
        
        if not os.path.exists(excel_path):
            safe_print(f"   [ERROR] File not found or not accessible")
            safe_print(f"   [TIP] Please check network connection and access rights")
            logger.warning(f"Excel file not found: {excel_path}")
            return None
            
        excel_data = get_excel_data(excel_path)
        if not excel_data:
            return None
        
        # Duyệt qua từng sheet đã lưu trong cache để tìm
        for sheet_name, df in excel_data:
            try:
                logger.debug(f"[Excel] Searching in sheet: {sheet_name}")
                
                # Thử exact match trước
                mask = df['cEngineerFigNo'].astype(str).str.upper() == engineer_fig_no.upper()
                logger.debug(f"[Excel] Exact match result: {mask.sum()} rows")
                
                # Nếu không tìm thấy exact match, thử partial match (startswith)
                if not mask.any():
                    safe_print(f"   [INFO] Exact match not found, trying partial match...")
                    logger.debug(f"[Excel] Trying partial match for: {engineer_fig_no}")
                    mask = df['cEngineerFigNo'].astype(str).str.upper().str.startswith(engineer_fig_no.upper())
                    logger.debug(f"[Excel] Partial match result: {mask.sum()} rows")
                
                if mask.any():
                    # Lấy tất cả các kết quả khớp
                    matches = df.loc[mask, ['cEngineerFigNo', 'cInvCode']]
                    match_count = len(matches)
                    safe_print(f"   [INFO] {match_count} match(es)")
                    logger.info(f"[Excel] Found {match_count} match(es) for '{engineer_fig_no}': {matches.to_dict('records')}")
                    
                    # Chuyển đổi DataFrame thành list of dicts
                    matches_list = matches.to_dict('records')
                    
                    # Lọc bỏ các giá trị NaN
                    matches_list = [{'cEngineerFigNo': str(m['cEngineerFigNo']), 'cInvCode': str(int(m['cInvCode']))} 
                                    for m in matches_list if pd.notna(m['cInvCode'])]
                    
                    if return_all:
                        # Trả về tất cả các kết quả
                        return matches_list
                    
                    # Lấy kết quả đầu tiên (behavior cũ)
                    if matches_list:
                        cinv_code = matches_list[0]['cInvCode']
                        logger.debug(f"[Excel] Returning cInvCode: {cinv_code}")
                        return cinv_code
                    return None
                    
            except Exception as e:
                logger.warning(f"Error reading sheet '{sheet_name}': {e}")
                continue
        
        safe_print(f"   [ERROR] '{engineer_fig_no}' not found in Excel")
        logger.warning(f"[Excel] cEngineerFigNo '{engineer_fig_no}' not found in any sheet")
        return None
        
    except FileNotFoundError:
        safe_print(f"[ERROR] Excel file not found: {EXCEL_PATH}")
        logger.error(f"FileNotFoundError: {EXCEL_PATH}")
        return None
    except Exception as e:
        safe_print(f"[ERROR] Error reading Excel: {e}")
        logger.error(f"Excel read error: {e}")
        logger.exception("Excel exception details:")
        return None


def query_material(code: str):
    """Gọi API để tìm URLs cho mã liệu."""
    API_URL = "http://192.168.2.164:8080/chafujianurl"

    try:
        logger.debug(f"[API] Requesting material for code: {code}")
        logger.debug(f"[API] URL: {API_URL}?code={code}")
        
        _t_start = time.time()
        resp = requests.get(API_URL, params={"code": code}, timeout=5)
        _elapsed = time.time() - _t_start
        logger.debug(f"[API] Response status: {resp.status_code}")
        logger.debug(f"[API] Response headers: {resp.headers}")
        safe_print(f"[API] Phản hồi trong {_elapsed:.2f}s (HTTP {resp.status_code})")
        resp.raise_for_status()

        data = resp.json()
        logger.debug(f"[API] Raw response data: {data}")
        logger.debug(f"[API] Data type: {type(data)}")

        if not isinstance(data, list) or len(data) == 0:
            safe_print(f"[ERROR] No data found for code: {code}")
            logger.warning(f"[API] No data found for code: {code}")
            return []

        # Thu thập tất cả URLs từ response, xử lý trường hợp nhiều URL trong một field
        all_urls = []
        for item in data:
            url_field = item.get("url", "")
            if url_field:
                # Tách các URL nếu có nhiều đường dẫn trong một field (ngăn cách bằng \n hoặc \r\n)
                split_urls = [u.strip() for u in url_field.replace('\r\n', '\n').replace('\r', '\n').split('\n') if u.strip()]
                logger.debug(f"[API] Found {len(split_urls)} URL(s) in item: {split_urls}")
                all_urls.extend(split_urls)

        urls = [u for u in all_urls if u]  # Lọc bỏ các URL rỗng
        logger.debug(f"[API] Total URLs found: {len(urls)}")

        if not urls:
            safe_print("[ERROR] No URLs in response data")
            logger.warning("[API] No URLs in response data")
            return []

        safe_print(f"[OK] URLs found: {len(urls)}")
        for i, url in enumerate(urls, 1):
            safe_print(f"  {i}. {shorten_path_display(url)}")
            logger.debug(f"[URL {i}] {url}")
        
        return urls

    except requests.exceptions.RequestException as e:
        safe_print(f"[WARN] Server connection error: {e}")
        logger.error(f"[API] Request failed: {e}")
        logger.exception("[API] Exception details:")
    except ValueError as e:
        safe_print("[WARN] Invalid JSON response from server")
        logger.error(f"[API] JSON decode error: {e}")
        logger.exception("[API] Exception details:")

    return []



def query_all_materials(cinv_codes: list) -> list:
    """Query API for multiple cInvCodes and collect all URLs.
    
    Args:
        cinv_codes: Danh sách các cInvCode cần query
    
    Returns:
        Danh sách tất cả URLs tìm được
    """
    all_urls = []
    
    for cinv_code in cinv_codes:
        logger.info(f"[API] Querying material with code: {cinv_code}")
        urls = query_material(cinv_code)
        
        if urls:
            all_urls.extend(urls)
        else:
            # Sử dụng fallback path nếu API không trả về kết quả
            fallback_path = f"{FALLBACK_BASE_PATH}\\{cinv_code}.jpg"
            logger.warning(f"[API] No URLs found for {cinv_code}, using fallback: {fallback_path}")
            if os.path.exists(fallback_path):
                all_urls.append(fallback_path)
            else:
                safe_print(f"[WARN] Fallback file not found: {cinv_code}.jpg")
    
    return all_urls

def test_excel_connection():
    """Kiểm tra kết nối đến file Excel."""
    excel_path = normalize_unc_path(EXCEL_PATH)
    safe_print(f"[INFO] Checking Excel connection...")
    safe_print(f"   Path: {shorten_path_display(excel_path)}")
    safe_print(f"   Exists: {os.path.exists(excel_path)}")
    
    parent_dir = os.path.dirname(excel_path)
    safe_print(f"   Parent exists: {os.path.exists(parent_dir)}")
    
    if os.path.exists(parent_dir):
        try:
            files = os.listdir(parent_dir)
            excel_files = [f for f in files if f.endswith('.xlsx')]
            if excel_files:
                safe_print(f"   Excel files: {len(excel_files)} file(s)")
        except Exception as e:
            safe_print(f"   [ERROR] Cannot list directory: {e}")
            
    if os.path.exists(excel_path):
        get_excel_data(excel_path)
    
    return os.path.exists(excel_path)


def main():
    """Hàm chính của chương trình."""
    safe_print("=== MATERIAL QUERY ===")
    logger.info("=== MATERIAL QUERY PROGRAM STARTED ===")
    
    # Kiểm tra kết nối Excel khi khởi động
    test_excel_connection()
    safe_print("")
    
    while True:
        try:
            # Dùng prompt ASCII-only để tránh lỗi codec trên Windows
            code = input("\n[Ma lieu / Code] (q=quit): ").strip().strip('"\'')
            logger.debug(f"[Input] User entered code: {code}")
        except (KeyboardInterrupt, EOFError):
            safe_print("\n[BYE] Program terminated by user")
            logger.info("Program terminated by user (Ctrl+C)")
            break
        
        if not code:
            safe_print("[ERROR] Code cannot be empty")
            logger.warning("[Input] Empty code entered")
            continue
        
        if code.lower() == 'q':
            safe_print("[BYE] Exiting program")
            logger.info("Program terminated by user (q)")
            break
        
        # Kiểm tra nếu là dạng cEngineerFigNo
        original_code = code
        logger.debug(f"[Process] Checking if code is Engineer Fig No: {code}")
        
        if is_engineer_fig_no(code):
            safe_print(f"[INFO] Detected Engineer Fig No: {code}")
            logger.info(f"[Detect] Code '{code}' is recognized as cEngineerFigNo pattern")
            
            # Tìm tất cả các kết quả
            all_matches = find_cinvcode_from_excel(code, return_all=True)
            
            if not all_matches:
                safe_print(f"[ERROR] cInvCode not found for: {code}")
                logger.warning(f"[Excel] cInvCode not found for cEngineerFigNo '{code}'")
                continue
            
            logger.debug(f"[Excel] Search result for '{code}': {all_matches}")
            
            # Nếu chỉ có 1 kết quả, giữ nguyên behavior cũ
            if len(all_matches) == 1:
                cinv_code = all_matches[0]['cInvCode']
                safe_print(f"[OK] Found cInvCode: {cinv_code}")
                logger.info(f"[Excel] Found cInvCode '{cinv_code}' for cEngineerFigNo '{code}'")
                copy_to_clipboard(cinv_code)
                code = cinv_code
            else:
                # Nhiều hơn 1 kết quả - hiển thị menu cho user chọn
                safe_print(f"\n[INFO] Found {len(all_matches)} matches:")
                for i, match in enumerate(all_matches, 1):
                    safe_print(f"  {i}. {match['cEngineerFigNo']} -> {match['cInvCode']}")
                
                # Menu lựa chọn
                safe_print(f"\n  [a] - Open ALL {len(all_matches)} files")
                safe_print(f"  [s] - Select specific file(s)")
                safe_print(f"  [q] - Quit to next search")
                
                choice = input("\n[Choice a/s/q]: ").strip().lower()
                
                if choice == 'q':
                    continue
                elif choice == 'a':
                    # Mở tất cả các file nhưng giới hạn tối đa 10 file
                    MAX_OPEN_LIMIT = 10
                    cinv_codes = [m['cInvCode'] for m in all_matches]
                    total_count = len(cinv_codes)
                    
                    # Giới hạn số lượng file tối đa
                    if total_count > MAX_OPEN_LIMIT:
                        safe_print(f"[INFO] Limiting to {MAX_OPEN_LIMIT} files (out of {total_count} total)")
                        cinv_codes = cinv_codes[:MAX_OPEN_LIMIT]
                    
                    safe_print(f"\n[INFO] Processing {len(cinv_codes)} code(s)...")
                    all_urls = query_all_materials(cinv_codes)
                    
                    if all_urls:
                        # Copy tất cả URLs vào clipboard
                        urls_text = "\n".join(all_urls)
                        copy_to_clipboard(urls_text)
                        logger.info(f"[Clipboard] Copied {len(all_urls)} URLs to clipboard")
                        
                        # Mở tất cả các thư mục
                        folder_count = open_all_folders(all_urls)
                        safe_print(f"\n[OK] Opened {folder_count} folder(s) with {len(all_urls)} file(s)")
                        logger.info(f"[Process] Completed query for '{code}' - opened {folder_count} folder(s) with {len(all_urls)} file(s)")
                    else:
                        safe_print("[ERROR] No files found for any of the codes")
                    continue
                elif choice == 's':
                    # Cho phép user chọn một hoặc nhiều kết quả
                    while True:
                        selected = input("\n[Enter number(s) separated by comma, e.g., 1,3,5 or * for all]: ").strip()
                        
                        if selected.lower() == 'q':
                            break
                        elif selected == '*':
                            # Chọn tất cả nhưng áp dụng giới hạn
                            MAX_OPEN_LIMIT = 10
                            if len(all_matches) > MAX_OPEN_LIMIT:
                                safe_print(f"[INFO] Giới hạn mở {MAX_OPEN_LIMIT} file (trên tổng {len(all_matches)}) tương tự như Open ALL.")
                                selected_indices = list(range(len(all_matches)))[:MAX_OPEN_LIMIT]
                            else:
                                selected_indices = list(range(len(all_matches)))
                        else:
                            # Parse danh sách số
                            try:
                                selected_indices = [int(x.strip()) - 1 for x in selected.split(',')]
                                # Validate
                                if any(i < 0 or i >= len(all_matches) for i in selected_indices):
                                    safe_print(f"[ERROR] Invalid selection. Please enter numbers 1-{len(all_matches)}")
                                    continue
                            except ValueError:
                                safe_print("[ERROR] Invalid input. Please enter numbers like 1,2,3")
                                continue
                        
                        # Xử lý các kết quả được chọn
                        cinv_codes = [all_matches[i]['cInvCode'] for i in selected_indices]
                        safe_print(f"\n[INFO] Processing {len(cinv_codes)} selected code(s)...")
                        all_urls = query_all_materials(cinv_codes)
                        
                        if all_urls:
                            urls_text = "\n".join(all_urls)
                            copy_to_clipboard(urls_text)
                            logger.info(f"[Clipboard] Copied {len(all_urls)} URLs to clipboard")
                            
                            folder_count = open_all_folders(all_urls)
                            safe_print(f"\n[OK] Opened {folder_count} folder(s) with {len(all_urls)} file(s)")
                            logger.info(f"[Process] Completed query for '{code}' - opened {folder_count} folder(s) with {len(all_urls)} file(s)")
                        else:
                            safe_print("[ERROR] No files found for selected codes")
                        break
                    continue
                else:
                    safe_print("[ERROR] Invalid choice, skipping...")
                    continue
        
        # Gọi API với code
        logger.info(f"[API] Querying material with code: {code}")
        urls = query_material(code)
        logger.debug(f"[API] URLs returned: {urls}")
        
        if urls:
            # Copy tất cả URLs vào clipboard (phân cách bằng xuống dòng)
            urls_text = "\n".join(urls)
            copy_to_clipboard(urls_text)
            logger.info(f"[Clipboard] Copied {len(urls)} URLs to clipboard")
            
            # Mở tất cả các thư mục
            folder_count = open_all_folders(urls)
            
            safe_print(f"\n[OK] Opened {folder_count} folder(s) with {len(urls)} file(s)")
            logger.info(f"[Process] Completed query for '{original_code}' - opened {folder_count} folder(s) with {len(urls)} file(s)")
        else:
            # Server không trả về path nào → kiểm tra đường dẫn dự phòng
            fallback_path = f"{FALLBACK_BASE_PATH}\\{code}.jpg"
            logger.warning(f"[API] No URLs found, checking fallback path: {fallback_path}")
            
            # Kiểm tra file fallback có tồn tại không
            if os.path.exists(fallback_path):
                safe_print(f"[INFO] Using fallback path: {shorten_path_display(fallback_path)}")
                copy_to_clipboard(fallback_path)
                open_folder_from_unc(fallback_path, open_file_directly=True)
            else:
                # File không tồn tại - hiển thị thông báo lỗi rõ ràng
                safe_print(f"[ERROR] Không tìm thấy dữ liệu cho mã: {code}")
                safe_print(f"[INFO] Vui lòng kiểm tra lại mã hoặc thử mã khác")
                logger.warning(f"[API] No data found for code: {code} (fallback file also not found)")
    
    safe_print("\n=== END ===")
    logger.info("=== MATERIAL QUERY PROGRAM ENDED ===")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        safe_print("\n[BYE] Program terminated")
        logger.info("Program terminated by KeyboardInterrupt")
        sys.exit(0)
    except Exception as e:
        safe_print(f"\n[ERROR] Unexpected error: {e}")
        logger.exception("Unexpected error")
        sys.exit(1)
