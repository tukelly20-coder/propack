# Ollama API Proxy (for WAN access)
# ========================================================================

# Gemini API Configuration
GEMINI_API_KEY = None
GEMINI_MODEL = 'gemini-3-flash-preview'

# OpenRouter Retry Configuration
OPENROUTER_RETRY_CONFIG = {
    'max_retries': 3,
    'initial_delay_ms': 1000,
    'max_delay_ms': 10000,
    'timeout_seconds': 60
}

# System Prompt - AI để hiểu hệ thống
SYSTEM_PROMPT = """Bạn là trợ lý AI của Propack VP - hệ thống quản lý dự án và mã bản vẽ.

## HỆ THỐNG PROPACK VP

### 1. WORKFLOW SALES → ENGINEER
- Sales tạo Project mới → Lưu vào DB với is_pending='yes'
- Job mới hiển thị trong tab Notice (thông báo chờ)
- Engineer nhấn nút "Nhận Job" → Cập nhật is_pending='no', accepted_by=tên Engineer, accepted_at=thời gian
- Job biến khỏi danh sách chờ, được chuyển cho Engineer

### 2. DANH MỤC SẢN PHẨM (Loại sản phẩm)
- SJT:散件图 - Bản vẽ tách chi tiết
- WLJ:物料架 - Giá đựng vật liệu
- ZZC:周转车 - Xe trung chuyển
- GZT:工作台 - Bàn thao tác
- WCP:无尘棚 - Phòng sạch
- LSX:流水线 - Băng tải
- ZWJ:转弯机 - Băng tải chuyển hướng 90/180 độ
- GZL:改造类 - Cải tạo
- BSX:倍速线 - Băng chuyền xích
- WLL:围栏类 - Hàng rào
- GTX:滚筒线 - Băng chuyền con lăn
- ZHT:展会图 - Bản vẽ mặt bằng
- LHX:老化线 - Băng chuyền lão hóa

### 3. QUY TẮC MÃ BẢN VẼ
- SJT (散件图): PSJT{employee}-{serial}-00-A0 (vd: PSJT001-0001-00-A0)
  - employee: 3 chữ số (001, 002, ...)
  - serial: 0001-9999
- Các loại khác: P{prefix}{number}-0000-00-A0
  - WLJ → PWLJ001-0000-00-A0
  - ZZC → PZZC001-0000-00-A0
  - LSX → PLSX001-0000-00-A0
  - ...

### 4. DATABASE SCHEMA (bảng projects)
- tracking_id: INTEGER PRIMARY KEY
- Created_Date: DATE
- khach_hang: VARCHAR(200) - Tên khách hàng
- nhan_vien_kinh_doanh: VARCHAR(100) - Nhân viên kinh doanh
- ten_san_pham: VARCHAR(200) - Tên sản phẩm
- quy_cach: TEXT - Quy cách
- nguoi_lien_he_kh: VARCHAR(100) - Người liên hệ khách hàng
- so_luong: INTEGER - Số lượng
- ma_po: VARCHAR(50) - Mã PO
- ma_ban_ve: VARCHAR(50) - Mã bản vẽ phương án
- ma_me: VARCHAR(50) - Mã mẹ (parent code)
- loai_san_pham: VARCHAR(100) - Loại sản phẩm (SJT, WLJ, LSX...)
- user_id: INTEGER - ID người tạo
- is_pending: VARCHAR(10) - 'yes' = chờ nhận, 'no' = đã nhận
- accepted_by: VARCHAR(100) - Người nhận job
- accepted_at: TEXT - Thời gian nhận (ISO format)
- urgency_level: VARCHAR(20) - Mức độ khẩn cấp (normal/urgent/very_urgent)

### 5. API ENDPOINTS
- POST /api/socket - Socket API (ADD_SALES_RECORD, ACCEPT_JOB, ...)
- GET /api/notices/pending - Lấy danh sách job chờ (is_pending='yes')
- POST /api/notices/accept - Engineer nhận job
- POST /api/projects - Thêm project mới
- GET /api/projects - Lấy danh sách projects (phân trang)
- POST /api/codes/create - Tạo mã bản vẽ mới
- GET /api/codes/search-parent?code=xxx - Tìm mã mẹ

### 6. USER ROLES
- Sales: Tạo project, xem lịch sử
- Engineer: Nhận job, xem job đã nhận
- Admin: Tất cả quyền

Khi trả lời, hãy:
1. Hiểu context của hệ thống này
2. Trả lời bằng tiếng Việt
3. Nếu user hỏi về workflow, mã bản vẽ, hoặc dự án, hãy dựa vào kiến thức trên
4. Nếu cần thông tin về database, có thể truy vấn qua API

CURRENT_USER_INFO: Chưa đăng nhập (guest)"""
DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPT
SYSTEM_PROMPT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system_prompt.json')
SYSTEM_PROMPT_LOCK = threading.Lock()

def load_system_prompt_config():
    """Load custom system prompt from file if available."""
    global SYSTEM_PROMPT
    try:
        if os.path.exists(SYSTEM_PROMPT_CONFIG_PATH):
            with open(SYSTEM_PROMPT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            custom_prompt = data.get('system_prompt', '')
            if isinstance(custom_prompt, str) and custom_prompt.strip():
                SYSTEM_PROMPT = custom_prompt.strip()
                safe_print("[AI] Loaded custom system prompt")
    except Exception as e:
        safe_print(f"[AI] Error loading system prompt config: {e}")

def save_system_prompt_config(prompt_text):
    """Persist system prompt to file."""
    try:
        with open(SYSTEM_PROMPT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({'system_prompt': prompt_text}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        safe_print(f"[AI] Error saving system prompt config: {e}")
        return False

def get_user_session_info():
    """Lấy thông tin user từ session để bổ sung vào system prompt"""
    try:
        user_info = session.get('user', {})
        if user_info:
            username = user_info.get('username', 'unknown')
            role = user_info.get('role', 'unknown')
            full_name = user_info.get('full_name', '')
            user_id = user_info.get('user_id', '')
            employee_id = user_info.get('employee_id', '')
            
            return f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {username}
- Role: {role}
- Full Name: {full_name}
- User ID: {user_id}
- Employee ID: {employee_id}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user_id}
- Nếu là Engineer: Xem projects với accepted_by = '{username}'
"""
        return ""
    except:
        return ""

def get_full_system_prompt():
    """Lấy full system prompt bao gồm thông tin user"""
    return SYSTEM_PROMPT + get_user_session_info()

# Fallback models for rate limiting
OPENROUTER_FALLBACK_MODELS = [
    'openai/gpt-oss-20b:free',
    'google/gemma-3-12b-it:free',
    'meta-llama/llama-3.3-70b-instruct:free'
]

def load_gemini_config():
    """Load Gemini API key from credentials.json"""
    global GEMINI_API_KEY
    try:
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        if os.path.exists(cred_path):
            with open(cred_path, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                GEMINI_API_KEY = creds.get('gemini_api_key', '')
                if GEMINI_API_KEY:
                    safe_print(f"[Gemini] API Key loaded successfully")
                else:
                    safe_print("[Gemini] No API key found in credentials.json")
        else:
            safe_print("[Gemini] credentials.json not found")
    except Exception as e:
        safe_print(f"[Gemini] Error loading config: {e}")

def load_credentials():
    """Load all credentials from credentials.json"""
    try:
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        if os.path.exists(cred_path):
            with open(cred_path, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                # Check for OpenRouter API key from environment variable first
                env_api_key = os.environ.get('OPENROUTER_API_KEY')
                if env_api_key:
                    creds['openrouter_api_key'] = env_api_key
                return creds
    except Exception as e:
        safe_print(f"[Credentials] Error loading: {e}")
    return {}

def load_ai_retry_config():
    """Load AI retry configuration from credentials.json"""
    global OPENROUTER_RETRY_CONFIG, OPENROUTER_FALLBACK_MODELS
    try:
        creds = load_credentials()
        retry_config = creds.get('ai_retry', {})
        if retry_config:
            OPENROUTER_RETRY_CONFIG.update(retry_config)
            safe_print(f"[AI Retry] Config loaded: {OPENROUTER_RETRY_CONFIG}")
        
        fallback = creds.get('fallback_models', [])
        if fallback:
            OPENROUTER_FALLBACK_MODELS = fallback
            safe_print(f"[AI Retry] Fallback models: {OPENROUTER_FALLBACK_MODELS}")
    except Exception as e:
        safe_print(f"[AI Retry] Error loading config: {e}")

def is_rate_limit_error(response):
    """Check if response indicates rate limiting (429)"""
    try:
        data = response.json() if hasattr(response, 'json') else json.loads(response)
        if isinstance(data, dict):
            error = data.get('error', {})
            if isinstance(error, dict):
                code = error.get('code', 0)
                if code == 429:
                    return True
                # Also check for rate limit in message
                msg = str(error.get('message', '')).lower()
                if 'rate' in msg and 'limit' in msg:
                    return True
    except:
        pass
    return False


def extract_openrouter_error_message(response):
    """Extract a short error message from OpenRouter response body."""
    try:
        data = response.json()
        if isinstance(data, dict):
            error = data.get('error')
            if isinstance(error, dict):
                message = error.get('message')
                if message:
                    return str(message)
            message = data.get('message')
            if message:
                return str(message)
    except Exception:
        pass
    return (response.text or '').strip()[:300]


def get_non_retriable_openrouter_error(response):
    """
    Return user-friendly non-retriable error for auth/quota/access issues.
    Returns None if error can still be retried/fallbacked.
    """
    status = getattr(response, 'status_code', 0)
    detail = extract_openrouter_error_message(response)
    detail_suffix = f": {detail}" if detail else ""

    if status == 401:
        return f"OpenRouter API key không hợp lệ hoặc đã bị thu hồi{detail_suffix}"
    if status == 402:
        return f"Tài khoản OpenRouter không đủ credit để gọi model{detail_suffix}"
    if status == 403:
        return f"OpenRouter từ chối quyền truy cập model{detail_suffix}"
    if status == 404:
        return f"Model OpenRouter không tồn tại hoặc đã bị ngừng hỗ trợ{detail_suffix}"

    return None

def exponential_backoff(attempt, initial_delay_ms, max_delay_ms):
    """Calculate delay with exponential backoff"""
    delay = min(initial_delay_ms * (2 ** attempt), max_delay_ms)
    # Add some jitter
    import random
    jitter = random.randint(0, 1000)
    return (delay + jitter) / 1000  # Convert to seconds

def call_openrouter_with_retry(api_key, model, messages, timeout=60):
    """
    Call OpenRouter API with retry logic and fallback models.
    Returns: (response_text, model_used, error_message)
    """
    import time
    
    # Get config
    max_retries = OPENROUTER_RETRY_CONFIG.get('max_retries', 3)
    initial_delay = OPENROUTER_RETRY_CONFIG.get('initial_delay_ms', 1000)
    max_delay = OPENROUTER_RETRY_CONFIG.get('max_delay_ms', 10000)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        'model': model,
        'messages': messages,
        'stream': False
    }
    
    # Track which models we tried
    models_tried = [model]
    current_model = model
    
    # Try original model first with retries
    for attempt in range(max_retries):
        try:
            safe_print(f"[OpenRouter Retry] Attempt {attempt + 1}/{max_retries} with model: {current_model}")
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            # Check for rate limit
            if response.status_code == 429:
                safe_print(f"[OpenRouter Retry] Rate limited (429) on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, initial_delay, max_delay)
                    safe_print(f"[OpenRouter Retry] Waiting {delay:.2f}s before retry...")
                    time.sleep(delay)
                    continue
                else:
                    # All retries exhausted, try fallback
                    break
            
            if response.status_code >= 400:
                safe_print(f"[OpenRouter Retry] Error {response.status_code}: {response.text[:200]}")
                non_retriable_error = get_non_retriable_openrouter_error(response)
                if non_retriable_error:
                    return None, current_model, non_retriable_error
                # Check if it's a rate limit error in the response body
                try:
                    error_data = response.json()
                    if is_rate_limit_error(response):
                        if attempt < max_retries - 1:
                            delay = exponential_backoff(attempt, initial_delay, max_delay)
                            safe_print(f"[OpenRouter Retry] Rate limit detected, waiting {delay:.2f}s...")
                            time.sleep(delay)
                            continue
                except:
                    pass
                
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, initial_delay, max_delay)
                    time.sleep(delay)
                    continue
                else:
                    break
            
            # Success
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')
                return content, current_model, None
            
            return '', current_model, 'No content in response'
            
        except requests.exceptions.Timeout:
            safe_print(f"[OpenRouter Retry] Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                delay = exponential_backoff(attempt, initial_delay, max_delay)
                time.sleep(delay)
                continue
        except Exception as e:
            safe_print(f"[OpenRouter Retry] Exception: {e}")
            if attempt < max_retries - 1:
                delay = exponential_backoff(attempt, initial_delay, max_delay)
                time.sleep(delay)
                continue
            break
    
    # All retries failed, try fallback models
    safe_print("[OpenRouter Retry] All retries exhausted, trying fallback models...")
    
    # Filter out already tried models
    available_fallbacks = [m for m in OPENROUTER_FALLBACK_MODELS if m not in models_tried]
    
    for fallback_model in available_fallbacks:
        try:
            safe_print(f"[OpenRouter Retry] Trying fallback model: {fallback_model}")
            models_tried.append(fallback_model)
            
            # Update payload with new model
            fallback_payload = payload.copy()
            fallback_payload['model'] = fallback_model
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=fallback_payload,
                timeout=timeout
            )
            
            if response.status_code == 429:
                safe_print(f"[OpenRouter Retry] Fallback model also rate limited")
                continue
            
            if response.status_code >= 400:
                safe_print(f"[OpenRouter Retry] Fallback error: {response.status_code}")
                non_retriable_error = get_non_retriable_openrouter_error(response)
                if non_retriable_error:
                    return None, fallback_model, non_retriable_error
                continue
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')
                safe_print(f"[OpenRouter Retry] Fallback model {fallback_model} succeeded!")
                return content, fallback_model, None
            
        except Exception as e:
            safe_print(f"[OpenRouter Retry] Fallback exception: {e}")
            continue
    
    return None, model, "All retry attempts and fallback models failed"

# Load AI config on startup
load_ai_retry_config()
load_gemini_config()
load_system_prompt_config()

# Default Ollama URLs (always include port)
DEFAULT_OLLAMA_URLS = [
    'http://localhost:11434',
    'http://127.0.0.1:11434',
    'http://0.0.0.0:11434',
]

# Store the actual resolved URL for debugging
OLLAMA_RESOLVED_URL = None

# Get OLLAMA_URL from environment or try to discover
def get_ollama_url():
    """Try to get working Ollama URL with improved auto-discovery"""
    # First check OLLAMA_HOST environment variable (higher priority)
    ollama_host = os.environ.get('OLLAMA_HOST')
    if ollama_host:
        # Ensure it has http:// prefix and port
        if not ollama_host.startswith('http'):
            ollama_host = f'http://{ollama_host}'
        # Ensure port is included (default to 11434 if missing)
        if ':' not in ollama_host.split('//')[-1]:
            ollama_host = f"{ollama_host}:11434"
        safe_print(f"[Ollama] Using OLLAMA_HOST: {ollama_host}")
        return ollama_host
    
    # Also check OLLAMA_URL for backwards compatibility
    env_url = os.environ.get('OLLAMA_URL')
    if env_url:
        # Ensure port is included
        if not env_url.startswith('http'):
            env_url = f'http://{env_url}'
        if ':' not in env_url.split('//')[-1]:
            env_url = f"{env_url}:11434"
        return env_url
    
    # Try each URL in order (with port)
    for url in DEFAULT_OLLAMA_URLS:
        try:
            resp = requests.get(f"{url}/api/tags", timeout=3)
            if resp.ok:
                safe_print(f"[Ollama] Auto-discovered working URL: {url}")
                return url
        except:
            continue
    
    # Default to localhost with port
    return 'http://localhost:11434'

OLLAMA_URL = get_ollama_url()
OLLAMA_ENABLED = True

@app.route('/api/debug-ip', methods=['GET'])
def debug_ip():
    """Debug endpoint to see request details"""
    return jsonify({
        "remote_addr": request.remote_addr,
        "host": request.host,
        "url": request.url,
        "headers": dict(request.headers)
    })


@app.route('/api/ollama-test', methods=['POST', 'OPTIONS'])
def ollama_test():
    """Test endpoint to diagnose Ollama issues"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    data = request.get_json() or {}
    prompt = data.get('prompt', 'Hello')
    model = data.get('model', 'qwen3:8b')
    
    safe_print(f"[Ollama Test] Received request - model: {model}, prompt: {prompt}")
    safe_print(f"[Ollama Test] OLLAMA_URL: {OLLAMA_URL}")
    safe_print(f"[Ollama Test] Request from IP: {request.remote_addr}")
    
    # Try to call Ollama directly
    try:
        target_url = f"{OLLAMA_URL}/api/generate"
        safe_print(f"[Ollama Test] Calling: {target_url}")
        
        resp = requests.post(
            target_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        safe_print(f"[Ollama Test] Response status: {resp.status_code}")
        safe_print(f"[Ollama Test] Response body: {resp.text[:200]}")
        
        if resp.ok:
            return jsonify({
                "success": True,
                "status_code": resp.status_code,
                "response": resp.json()
            })
        else:
            return jsonify({
                "success": False,
                "status_code": resp.status_code,
                "error": resp.text,
                "ollama_url": OLLAMA_URL
            }), resp.status_code
            
    except Exception as e:
        safe_print(f"[Ollama Test] Exception: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "ollama_url": OLLAMA_URL
        }), 500


@app.route('/api/ollama/<path:ollama_path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def ollama_proxy(ollama_path):
    """Proxy requests to Ollama server with improved error handling"""
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not OLLAMA_ENABLED:
        return jsonify({
            "error": "Ollama đang tắt. Vui lòng bật Ollama server.",
            "hint": "Chạy 'ollama serve' để khởi động Ollama"
        }), 503
    
    # Log ALL requests for debugging
    safe_print(f"="*50)
    safe_print(f"[Ollama Proxy] NEW REQUEST:")
    safe_print(f"  Path: {ollama_path}")
    safe_print(f"  Method: {request.method}")
    safe_print(f"  Remote IP: {request.remote_addr}")
    safe_print(f"  Host: {request.host}")
    safe_print(f"  Origin: {request.headers.get('Origin', 'N/A')}")
    safe_print(f"  User-Agent: {request.headers.get('User-Agent', 'N/A')[:50]}")
    
    try:
        # Build the target URL
        target_url = f"{OLLAMA_URL}/{ollama_path}"
        safe_print(f"[Ollama Proxy] Forwarding to: {target_url}")
        
        # Get headers from original request (except host)
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}
        safe_print(f"[Ollama Proxy] Headers: {headers}")
        
        # Get request body for logging
        request_body = request.get_data()
        safe_print(f"[Ollama Proxy] Body length: {len(request_body)} bytes")
        
        # Handle different methods
        if request.method == 'GET':
            resp = requests.get(target_url, headers=headers, timeout=30)
        elif request.method == 'POST':
            resp = requests.post(
                target_url, 
                headers=headers, 
                json=request.get_json(), 
                timeout=120
            )
        elif request.method == 'PUT':
            resp = requests.put(
                target_url, 
                headers=headers, 
                json=request.get_json(), 
                timeout=120
            )
        elif request.method == 'DELETE':
            resp = requests.delete(target_url, headers=headers, timeout=30)
        else:
            return jsonify({"error": "Method not allowed"}), 405
        
        # Log the response status
        safe_print(f"[Ollama Proxy] Response status: {resp.status_code}")
        safe_print(f"[Ollama Proxy] Response headers: {dict(resp.headers)}")
        
        # Debug: Log full request and response for troubleshooting
        if resp.status_code >= 400:
            safe_print(f"[Ollama Proxy] FULL REQUEST DEBUG:")
            safe_print(f"  Target URL: {target_url}")
            safe_print(f"  Request method: {request.method}")
            safe_print(f"  Request headers: {dict(request.headers)}")
            safe_print(f"  Request body: {request.get_json()}")
            safe_print(f"  Response status: {resp.status_code}")
            safe_print(f"  Response body: {resp.text[:500]}")
        
        # Debug: Log response content for 403 errors
        if resp.status_code == 403:
            try:
                error_data = resp.json()
                safe_print(f"[Ollama Proxy] 403 Error response JSON: {error_data}")
            except:
                safe_print(f"[Ollama Proxy] 403 Error response text: {resp.text[:500]}")
        
        # If Ollama returns error status, provide helpful message
        if resp.status_code >= 400:
            error_msg = f"Ollama server trả về lỗi {resp.status_code}"
            error_details = {}
            
            try:
                error_data = resp.json()
                if 'error' in error_data:
                    error_msg = f"Ollama: {error_data['error']}"
                    error_details['ollama_error'] = error_data['error']
            except:
                pass
            
            # Provide specific guidance for 403 Forbidden
            if resp.status_code == 403:
                safe_print(f"[Ollama Proxy] 403 Forbidden - Access denied to Ollama at {OLLAMA_URL}")
                
                # Try to get more details from response
                try:
                    error_data = resp.json()
                    ollama_error = error_data.get('error', '')
                except:
                    ollama_error = ''
                
                return jsonify({
                    "error": "Ollama server từ chối truy cập (403 Forbidden)",
                    "ollama_url": OLLAMA_URL,
                    "ollama_error": ollama_error,
                    "hint": "Có thể do: (1) Ollama chưa được cấu hình cho phép remote access, (2) IP bị chặn, (3) Cần thiết lập OLLAMA_HOST=0.0.0.0:11434 khi chạy Ollama",
                    "fix_instructions": "Để cho phép remote access, hãy chạy:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n\nHoặc thêm vào config: { \"host\": \"0.0.0.0:11434\" }",
                    "debug_info": {
                        "target_url": target_url,
                        "response_status": resp.status_code,
                        "ollama_host_env": os.environ.get('OLLAMA_HOST', 'not set'),
                        "ollama_url_env": os.environ.get('OLLAMA_URL', 'not set')
                    },
                    "details": error_details
                }), 403
            
            # Provide specific guidance for connection issues
            if resp.status_code == 503:
                safe_print(f"[Ollama Proxy] 503 Service Unavailable - Ollama may not be running")
                return jsonify({
                    "error": "Ollama server không khả dụng (503)",
                    "ollama_url": OLLAMA_URL,
                    "hint": "Vui lòng khởi động Ollama bằng lệnh 'ollama serve' trong terminal",
                    "details": error_details
                }), 503
            
            return jsonify({
                "error": error_msg,
                "ollama_url": OLLAMA_URL,
                "hint": "Vui lòng kiểm tra Ollama server có đang chạy không",
                "details": error_details
            }), resp.status_code
        
        # Return the response from Ollama
        response = make_response(resp.content, resp.status_code)
        response.headers['Content-Type'] = resp.headers.get('Content-Type', 'application/json')
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except requests.exceptions.ConnectionError as e:
        safe_print(f"[Ollama Proxy] Connection error: {e}")
        
        # Get environment info for debugging
        ollama_host_env = os.environ.get('OLLAMA_HOST', 'not set')
        ollama_url_env = os.environ.get('OLLAMA_URL', 'not set')
        
        return jsonify({
            "error": "Không thể kết nối đến Ollama server",
            "ollama_url": OLLAMA_URL,
            "details": str(e),
            "hint": "Vui lòng đảm bảo Ollama đang chạy (thường là localhost:11434). \n\nĐể khởi động Ollama, hãy chạy lệnh 'ollama serve' trong terminal.\n\nĐể cho phép remote access, hãy thiết lập:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434",
            "debug_info": {
                "target_url": target_url,
                "ollama_host_env": ollama_host_env,
                "ollama_url_env": ollama_url_env,
                "troubleshooting": "Kiểm tra: (1) Ollama đang chạy, (2) Firewall không chặn, (3) Đúng port 11434"
            }
        }), 503
    except requests.exceptions.Timeout:
        safe_print(f"[Ollama Proxy] Timeout")
        return jsonify({
            "error": "Yêu cầu Ollama hết thời gian chờ",
            "hint": "Model có thể đang tải, vui lòng thử lại sau. Nếu vẫn lỗi, hãy thử model nhẹ hơn."
        }), 504
    except Exception as e:
        safe_print(f"[Ollama Proxy] Error: {e}")
        return jsonify({
            "error": f"Lỗi proxy Ollama: {str(e)}",
            "hint": "Liên hệ admin nếu lỗi tiếp tục"
        }), 500


@app.route('/api/ollama-models', methods=['GET', 'OPTIONS'])
def ollama_models():
    """Get available Ollama models"""
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not OLLAMA_ENABLED:
        return jsonify({
            "error": "Ollama đang tắt",
            "models": [],
            "hint": "Bật Ollama server để sử dụng tính năng AI"
        }), 200
    
    try:
        safe_print(f"[Ollama] Checking models at {OLLAMA_URL}")
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        
        if resp.status_code >= 400:
            safe_print(f"[Ollama] Error getting models: {resp.status_code}")
            return jsonify({
                "error": f"Ollama server lỗi: {resp.status_code}",
                "models": [],
                "hint": "Kiểm tra Ollama đang chạy"
            }), 200
        
        response = make_response(resp.content, resp.status_code)
        response.headers['Content-Type'] = resp.headers.get('Content-Type', 'application/json')
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except requests.exceptions.ConnectionError as e:
        safe_print(f"[Ollama] Connection failed: {e}")
        return jsonify({
            "error": "Không thể kết nối Ollama server",
            "models": [],
            "ollama_url": OLLAMA_URL,
            "hint": "Vui lòng chạy 'ollama serve' để khởi động Ollama"
        }), 200
    except Exception as e:
        safe_print(f"[Ollama] Error: {e}")
        return jsonify({
            "error": str(e),
            "models": []
        }), 200


@app.route('/api/ollama-status', methods=['GET', 'POST', 'OPTIONS'])
def ollama_status():
    """Get or set Ollama configuration with detailed status"""
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    global OLLAMA_URL, OLLAMA_ENABLED
    
    if request.method == 'POST':
        data = request.get_json()
        if data:
            if 'url' in data:
                # Validate URL format
                url = data['url']
                if not url.startswith('http'):
                    url = f'http://{url}'
                OLLAMA_URL = url
                safe_print(f"[Ollama] URL updated to: {OLLAMA_URL}")
            if 'enabled' in data:
                OLLAMA_ENABLED = data['enabled']
                safe_print(f"[Ollama] Enabled: {OLLAMA_ENABLED}")
        
        return jsonify({
            "success": True,
            "url": OLLAMA_URL,
            "enabled": OLLAMA_ENABLED
        })
    
    # GET - check status with detailed information
    # Try to connect to Ollama and collect info
    can_connect = False
    error_msg = None
    tried_urls = []
    
    # Try current URL first
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        can_connect = resp.ok
        tried_urls.append({
            "url": OLLAMA_URL,
            "status": "success" if resp.ok else f"error_{resp.status_code}",
            "status_code": resp.status_code
        })
    except Exception as e:
        error_msg = str(e)
        tried_urls.append({
            "url": OLLAMA_URL,
            "status": "connection_failed",
            "error": str(e)
        })
    
    # If current URL fails, try others for discovery
    if not can_connect:
        for url in DEFAULT_OLLAMA_URLS:
            if url == OLLAMA_URL:
                continue
            try:
                resp = requests.get(f"{url}/api/tags", timeout=3)
                tried_urls.append({
                    "url": url,
                    "status": "success" if resp.ok else f"error_{resp.status_code}",
                    "status_code": resp.status_code
                })
                if resp.ok and not can_connect:
                    # Optionally suggest this URL works
                    safe_print(f"[Ollama] Found working URL: {url}")
            except Exception as e:
                tried_urls.append({
                    "url": url,
                    "status": "connection_failed",
                    "error": str(e)
                })
    
    return jsonify({
        "url": OLLAMA_URL,
        "enabled": OLLAMA_ENABLED,
        "connected": can_connect,
        "error": error_msg,
        "tried_urls": tried_urls,
        "environment": {
            "OLLAMA_HOST": os.environ.get('OLLAMA_HOST', 'not set'),
            "OLLAMA_URL": os.environ.get('OLLAMA_URL', 'not set')
        },
        "fix_instructions": "Để cho phép remote access, hãy chạy:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434 && ollama serve"
    })


# ========================================================================
# Gemini AI API Endpoints (Streaming Support)
# ========================================================================

@app.route('/api/gemini/chat', methods=['POST', 'OPTIONS'])
def gemini_chat():
    """Chat với Gemini AI"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not GEMINI_API_KEY:
        return jsonify({
            "success": False,
            "error": "Chưa cấu hình Gemini API Key"
        }), 500
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', GEMINI_MODEL)
    history = data.get('history', [])
    
    # Get user info from token (Authorization header)
    auth_header = request.headers.get('Authorization', '')
    user_info_str = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        session_data, _ = get_web_session(token)
        if session_data:
            user = session_data.get('user', {})
            user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
    
    if not message:
        return jsonify({
            "success": False,
            "error": "Tin nhắn không được để trống"
        }), 400
    
    try:
        # Build messages for Gemini API
        # Add system prompt as first message
        system_instruction = {
            "role": "user",
            "parts": [{"text": SYSTEM_PROMPT + user_info_str}]
        }
        contents = [system_instruction]
        
        # Add history messages
        for msg in history:
            role = msg.get('role', 'user')
            if role == 'user':
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.get('content', '')}]
                })
            else:  # model
                contents.append({
                    "role": "model",
                    "parts": [{"text": msg.get('content', '')}]
                })
        
        # Add current message
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })
        
        # Call Gemini API
        import urllib.parse
        safe_print(f"[Gemini] Calling model: {model}")
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 2048,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        resp = requests.post(gemini_url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code >= 400:
            safe_print(f"[Gemini] Error: {resp.status_code} - {resp.text}")
            return jsonify({
                "success": False,
                "error": f"Lỗi API: {resp.status_code}",
                "details": resp.text
            }), resp.status_code
        
        result = resp.json()
        
        # Extract response text
        response_text = ""
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                response_text = "\n".join([p.get('text', '') for p in parts])
        
        if not response_text:
            response_text = "Không có phản hồi từ AI"
        
        return jsonify({
            "success": True,
            "response": response_text,
            "model": model
        })
        
    except Exception as e:
        safe_print(f"[Gemini] Exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Lỗi: {str(e)}"
        }), 500


@app.route('/api/gemini/chat/stream', methods=['POST', 'OPTIONS'])
def gemini_chat_stream():
    """Chat với Gemini AI với Streaming (SSE)"""
    from flask import Response
    
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not GEMINI_API_KEY:
        return Response(
            f"data: {json.dumps({'error': 'Chưa cấu hình Gemini API Key'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', GEMINI_MODEL)
    history = data.get('history', [])
    
    # Get user info from token (Authorization header)
    auth_header = request.headers.get('Authorization', '')
    user_info_str = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        session_data, _ = get_web_session(token)
        if session_data:
            user = session_data.get('user', {})
            user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
    
    if not message:
        return Response(
            f"data: {json.dumps({'error': 'Tin nhắn không được để trống'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def generate_stream():
        try:
            # Build messages for Gemini API
            # Add system prompt as first message
            system_instruction = {
                "role": "user",
                "parts": [{"text": SYSTEM_PROMPT + user_info_str}]
            }
            contents = [system_instruction]
            
            # Add history messages
            for msg in history:
                role = msg.get('role', 'user')
                if role == 'user':
                    contents.append({
                        "role": "user",
                        "parts": [{"text": msg.get('content', '')}]
                    })
                else:  # model
                    contents.append({
                        "role": "model",
                        "parts": [{"text": msg.get('content', '')}]
                    })
            
            # Add current message
            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })
            
            safe_print(f"[Gemini Stream] Calling model: {model}")
            
            # For streaming, we use the same API but accumulate the response
            # Note: Google Gemini API v1beta doesn't support true streaming in all cases
            # We'll simulate streaming by sending chunks of the response
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.9,
                    "maxOutputTokens": 2048,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            # Send initial ping
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            
            resp = requests.post(gemini_url, headers=headers, json=payload, timeout=120)
            
            if resp.status_code >= 400:
                safe_print(f"[Gemini Stream] Error: {resp.status_code} - {resp.text}")
                yield f"data: {json.dumps({'error': f'Lỗi API: {resp.status_code}', 'details': resp.text[:500]})}\n\n"
                return
            
            result = resp.json()
            
            # Extract response text
            response_text = ""
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    response_text = "\n".join([p.get('text', '') for p in parts])
            
            if not response_text:
                response_text = "Không có phản hồi từ AI"
            
            # Simulate streaming by sending in chunks
            # Chunk size: 20 characters for visible streaming effect
            chunk_size = 20
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full': response_text})}\n\n"
                
            # Send completion
            yield f"data: {json.dumps({'type': 'done', 'full': response_text})}\n\n"
            
        except Exception as e:
            safe_print(f"[Gemini Stream] Exception: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )


# ========================================================================
# Ollama AI API Endpoints (Streaming Support)
# ========================================================================

@app.route('/api/ollama/chat/stream', methods=['POST', 'OPTIONS'])
def ollama_chat_stream():
    """Chat với Ollama với Streaming (SSE)"""
    from flask import Response
    
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not OLLAMA_ENABLED:
        return Response(
            f"data: {json.dumps({'error': 'Ollama đang tắt. Vui lòng bật Ollama server.'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', 'llama3.2:latest')
    history = data.get('history', [])
    stream_option = data.get('stream', True)
    
    # Get user info from token (Authorization header)
    auth_header = request.headers.get('Authorization', '')
    user_info_str = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        session_data, _ = get_web_session(token)
        if session_data:
            user = session_data.get('user', {})
            user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
    
    if not message:
        return Response(
            f"data: {json.dumps({'error': 'Tin nhắn không được để trống'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def generate_stream():
        try:
            # Build prompt from history + current message
            # Add system prompt first
            prompt_parts = [f"System: {SYSTEM_PROMPT + user_info_str}"]
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    prompt_parts.append(f"User: {content}")
                else:
                    prompt_parts.append(f"Assistant: {content}")
            
            prompt_parts.append(f"User: {message}")
            full_prompt = "\n".join(prompt_parts)
            
            safe_print(f"[Ollama Stream] Model: {model}")
            
            # Use the streaming API endpoint of Ollama
            target_url = f"{OLLAMA_URL}/api/generate"
            
            # Send initial ping
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            
            # Call Ollama with streaming
            resp = requests.post(
                target_url,
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": True
                },
                stream=True,
                timeout=120
            )
            
            if resp.status_code >= 400:
                safe_print(f"[Ollama Stream] Error: {resp.status_code} - {resp.text}")
                yield f"data: {json.dumps({'error': f'Lỗi API: {resp.status_code}', 'details': resp.text[:500]})}\n\n"
                return
            
            # Process streaming response from Ollama
            full_response = ""
            
            for line in resp.iter_lines():
                if line:
                    try:
                        data_json = json.loads(line.decode('utf-8'))
                        
                        if 'response' in data_json:
                            chunk = data_json['response']
                            full_response += chunk
                            
                            # Send chunk to client
                            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full': full_response})}\n\n"
                        
                        # Check if done
                        if data_json.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            # Send completion
            yield f"data: {json.dumps({'type': 'done', 'full': full_response})}\n\n"
            
        except requests.exceptions.ConnectionError as e:
            safe_print(f"[Ollama Stream] Connection error: {e}")
            yield f"data: {json.dumps({'error': f'Không thể kết nối đến Ollama: {str(e)}'})}\n\n"
        except Exception as e:
            safe_print(f"[Ollama Stream] Exception: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )


@app.route('/api/gemini/models', methods=['GET', 'OPTIONS'])
def gemini_models():
    """Lấy danh sách models Gemini"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not GEMINI_API_KEY:
        return jsonify({
            "success": False,
            "error": "Chưa cấu hình Gemini API Key",
            "models": []
        }), 200
    
    # Return available Gemini models
    models = [
        {"name": "gemini-3-flash-preview", "display": "Gemini 3.0 Flash Preview (Nhanh nhất)"},
        {"name": "gemini-2.0-flash", "display": "Gemini 2.0 Flash"},
        {"name": "gemini-1.5-flash", "display": "Gemini 1.5 Flash"},
        {"name": "gemini-1.5-pro", "display": "Gemini 1.5 Pro"}
    ]
    
    return jsonify({
        "success": True,
        "models": models,
        "current_model": GEMINI_MODEL
    })


@app.route('/api/openrouter/chat/stream', methods=['POST', 'OPTIONS'])
def openrouter_chat_stream():
    """Chat với OpenRouter AI với Streaming (SSE) với retry và fallback logic"""
    from flask import Response
    
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Load OpenRouter API key từ credentials
    credentials = load_credentials()
    api_key = credentials.get('openrouter_api_key', '')
    
    if not api_key:
        return Response(
            f"data: {json.dumps({'error': 'OpenRouter API key chưa được cấu hình'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', 'openai/gpt-oss-20b:free')
    history = data.get('history', [])
    
    # Get user info from token (Authorization header)
    auth_header = request.headers.get('Authorization', '')
    user_info_str = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        session_data, _ = get_web_session(token)
        if session_data:
            user = session_data.get('user', {})
            user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
    
    if not message:
        return Response(
            f"data: {json.dumps({'error': 'Tin nhắn không được để trống'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def generate_stream():
        import time
        
        # Get retry config
        max_retries = OPENROUTER_RETRY_CONFIG.get('max_retries', 3)
        initial_delay = OPENROUTER_RETRY_CONFIG.get('initial_delay_ms', 1000)
        max_delay = OPENROUTER_RETRY_CONFIG.get('max_delay_ms', 10000)
        
        # Track models tried
        models_tried = [model]
        current_model = model
        
        # Build messages for OpenRouter API
        # Add system prompt as first message
        messages = [{"role": "system", "content": SYSTEM_PROMPT + user_info_str}]
        for msg in history:
            role = msg.get('role', 'user')
            if role == 'user':
                messages.append({"role": "user", "content": msg.get('content', '')})
            else:
                messages.append({"role": "assistant", "content": msg.get('content', '')})
        messages.append({"role": "user", "content": message})
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }
        
        payload = {
            'model': current_model,
            'messages': messages,
            'stream': True
        }
        
        # Try original model with retries first
        for attempt in range(max_retries):
            try:
                safe_print(f"[OpenRouter Stream] Attempt {attempt + 1}/{max_retries} with model: {current_model}")
                
                # Send start signal
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                
                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=120
                )
                
                # Check for rate limit
                if response.status_code == 429:
                    safe_print(f"[OpenRouter Stream] Rate limited (429) on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        delay = exponential_backoff(attempt, initial_delay, max_delay)
                        yield f"data: {json.dumps({'type': 'model_error', 'model': current_model, 'status': 429, 'attempt': attempt + 1, 'max_retries': max_retries, 'message': f'Model đang bị rate limit, sẽ thử lại sau {delay:.2f}s.'})}\n\n"
                        safe_print(f"[OpenRouter Stream] Waiting {delay:.2f}s before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        yield f"data: {json.dumps({'type': 'model_error', 'model': current_model, 'status': 429, 'attempt': attempt + 1, 'max_retries': max_retries, 'message': 'Model bị rate limit liên tục, chuyển sang fallback model.'})}\n\n"
                        # All retries exhausted, try fallback
                        break
                
                if response.status_code >= 400:
                    safe_print(f"[OpenRouter Stream] Error: {response.status_code} - {response.text[:500]}")
                    detail = extract_openrouter_error_message(response)
                    yield f"data: {json.dumps({'type': 'model_error', 'model': current_model, 'status': response.status_code, 'attempt': attempt + 1, 'max_retries': max_retries, 'message': detail or f'Lỗi HTTP {response.status_code}'})}\n\n"
                    non_retriable_error = get_non_retriable_openrouter_error(response)
                    if non_retriable_error:
                        yield f"data: {json.dumps({'error': non_retriable_error, 'code': 'OPENROUTER_AUTH_OR_BILLING_ERROR'})}\n\n"
                        return
                    # Check if it's a rate limit in response body
                    try:
                        error_data = response.json()
                        if is_rate_limit_error(response):
                            if attempt < max_retries - 1:
                                delay = exponential_backoff(attempt, initial_delay, max_delay)
                                safe_print(f"[OpenRouter Stream] Rate limit detected, waiting {delay:.2f}s...")
                                time.sleep(delay)
                                continue
                    except:
                        pass
                    
                    if attempt < max_retries - 1:
                        delay = exponential_backoff(attempt, initial_delay, max_delay)
                        time.sleep(delay)
                        continue
                    else:
                        break
                
                # Process streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                chunk_data = json.loads(line[6:])
                                
                                if chunk_data == '[DONE]':
                                    break
                                
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        content = delta['content']
                                        full_response += content
                                        yield f"data: {json.dumps({'type': 'chunk', 'content': content, 'full': full_response})}\n\n"
                            except json.JSONDecodeError:
                                continue
                
                # Send completion
                yield f"data: {json.dumps({'type': 'done', 'full': full_response})}\n\n"
                return
                
            except requests.exceptions.Timeout:
                safe_print(f"[OpenRouter Stream] Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, initial_delay, max_delay)
                    time.sleep(delay)
                    continue
            except Exception as e:
                safe_print(f"[OpenRouter Stream] Exception: {e}")
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, initial_delay, max_delay)
                    time.sleep(delay)
                    continue
                break
        
        # All retries failed, try fallback models
        safe_print("[OpenRouter Stream] All retries exhausted, trying fallback models...")
        
        available_fallbacks = [m for m in OPENROUTER_FALLBACK_MODELS if m not in models_tried]
        
        for fallback_model in available_fallbacks:
            try:
                safe_print(f"[OpenRouter Stream] Trying fallback model: {fallback_model}")
                models_tried.append(fallback_model)
                
                # Update payload with new model
                fallback_payload = payload.copy()
                fallback_payload['model'] = fallback_model
                
                # Send start signal
                yield f"data: {json.dumps({'type': 'start', 'model_switched': fallback_model})}\n\n"
                
                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=fallback_payload,
                    stream=True,
                    timeout=120
                )
                
                if response.status_code == 429:
                    safe_print(f"[OpenRouter Stream] Fallback model also rate limited")
                    yield f"data: {json.dumps({'type': 'model_error', 'model': fallback_model, 'status': 429, 'message': 'Fallback model đang bị rate limit, thử model fallback tiếp theo.'})}\n\n"
                    continue
                
                if response.status_code >= 400:
                    safe_print(f"[OpenRouter Stream] Fallback error: {response.status_code}")
                    detail = extract_openrouter_error_message(response)
                    yield f"data: {json.dumps({'type': 'model_error', 'model': fallback_model, 'status': response.status_code, 'message': detail or f'Lỗi HTTP {response.status_code}'})}\n\n"
                    non_retriable_error = get_non_retriable_openrouter_error(response)
                    if non_retriable_error:
                        yield f"data: {json.dumps({'error': non_retriable_error, 'code': 'OPENROUTER_AUTH_OR_BILLING_ERROR'})}\n\n"
                        return
                    continue
                
                # Process streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                chunk_data = json.loads(line[6:])
                                
                                if chunk_data == '[DONE]':
                                    break
                                
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        content = delta['content']
                                        full_response += content
                                        yield f"data: {json.dumps({'type': 'chunk', 'content': content, 'full': full_response})}\n\n"
                            except json.JSONDecodeError:
                                continue
                
                # Send completion
                yield f"data: {json.dumps({'type': 'done', 'full': full_response, 'model_used': fallback_model})}\n\n"
                safe_print(f"[OpenRouter Stream] Fallback model {fallback_model} succeeded!")
                return
                
            except Exception as e:
                safe_print(f"[OpenRouter Stream] Fallback exception: {e}")
                continue
        
        # All failed
        yield f"data: {json.dumps({'error': 'Tất cả model đều thất bại. Vui lòng thử lại sau hoặc chọn model khác.', 'code': 'ALL_MODELS_FAILED'})}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )


@app.route('/api/openrouter/models', methods=['GET', 'OPTIONS'])
def openrouter_models():
    """Lấy danh sách models OpenRouter"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    credentials = load_credentials()
    api_key = credentials.get('openrouter_api_key', '')
    
    if not api_key:
        return jsonify({
            "success": False,
            "error": "Chưa cấu hình OpenRouter API Key",
            "models": []
        }), 200
    
    # Return available OpenRouter models
    models = [
        {"name": "openai/gpt-oss-20b:free", "display": "GPT OSS 20B (Miễn phí)"},
        {"name": "google/gemma-3-12b-it:free", "display": "Gemma 3 12B IT (Miễn phí)"},
        {"name": "meta-llama/llama-3.3-70b-instruct:free", "display": "Llama 3.3 70B (Miễn phí)"},
        {"name": "openai/gpt-4o-mini", "display": "GPT-4o Mini"},
        {"name": "anthropic/claude-3-haiku", "display": "Claude 3 Haiku"},
        {"name": "meta-llama/llama-3.1-8b-instruct", "display": "Llama 3.1 8B"}
    ]
    
    return jsonify({
        "success": True,
        "models": models
    })


@app.route('/api/openrouter/status', methods=['GET', 'OPTIONS'])
def openrouter_status():
    """Kiểm tra trạng thái OpenRouter API"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    credentials = load_credentials()
    api_key = credentials.get('openrouter_api_key', '')
    
    has_key = bool(api_key)
    
    # Test key validity if API key exists
    connected = False
    error_msg = None
    
    if has_key:
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            resp = requests.get(
                'https://openrouter.ai/api/v1/key',
                headers=headers,
                timeout=10
            )
            connected = resp.status_code < 400
            if not connected:
                detail = extract_openrouter_error_message(resp)
                error_msg = f"HTTP {resp.status_code}" + (f": {detail}" if detail else "")
        except Exception as e:
            error_msg = str(e)
    
    return jsonify({
        "success": True,
        "configured": has_key,
        "connected": connected,
        "error": error_msg
    })


@app.route('/api/ai/system-prompt', methods=['GET', 'PUT', 'OPTIONS'])
def ai_system_prompt():
    """Lấy/cập nhật system prompt (admin only for update)."""
    global SYSTEM_PROMPT
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    user, auth_error = get_user_from_bearer_token()
    if auth_error:
        return jsonify({
            "success": False,
            "error": "Chưa đăng nhập hoặc phiên đã hết hạn",
            "reason": auth_error
        }), 401

    can_edit = is_admin_user(user)

    if request.method == 'GET':
        return jsonify({
            "success": True,
            "system_prompt": SYSTEM_PROMPT,
            "can_edit": can_edit
        })

    if not can_edit:
        return jsonify({
            "success": False,
            "error": "Bạn không có quyền chỉnh system prompt"
        }), 403

    data = request.get_json() or {}
    new_prompt = data.get('system_prompt', '')
    if not isinstance(new_prompt, str):
        return jsonify({
            "success": False,
            "error": "system_prompt phải là chuỗi"
        }), 400

    new_prompt = new_prompt.strip()
    if len(new_prompt) < 20:
        return jsonify({
            "success": False,
            "error": "System prompt quá ngắn (tối thiểu 20 ký tự)"
        }), 400

    if len(new_prompt) > 50000:
        return jsonify({
            "success": False,
            "error": "System prompt quá dài (tối đa 50,000 ký tự)"
        }), 400

    with SYSTEM_PROMPT_LOCK:
        SYSTEM_PROMPT = new_prompt
        saved = save_system_prompt_config(SYSTEM_PROMPT)

    if not saved:
        return jsonify({
            "success": False,
            "error": "Không thể lưu system prompt vào file cấu hình"
        }), 500

    safe_print(f"[AI] System prompt updated by user: {user.get('username', 'unknown')}")
    return jsonify({
        "success": True,
        "message": "Đã cập nhật system prompt",
        "system_prompt": SYSTEM_PROMPT,
        "can_edit": True
    })


@app.route('/api/gemini/status', methods=['GET', 'OPTIONS'])
def gemini_status():
    """Kiểm tra trạng thái Gemini API"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    has_key = bool(GEMINI_API_KEY)
    
    # Test connection if API key exists
    connected = False
    error_msg = None
    
    if has_key:
        try:
            # Quick test with a minimal request
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            resp = requests.post(
                gemini_url,
                headers={'Content-Type': 'application/json'},
                json={"contents": [{"role": "user", "parts": [{"text": "test"}]}]},
                timeout=10
            )
            connected = resp.status_code < 400
            if not connected:
                error_msg = f"HTTP {resp.status_code}"
        except Exception as e:
            error_msg = str(e)
    
    return jsonify({
        "success": True,
        "configured": has_key,
        "connected": connected,
        "model": GEMINI_MODEL,
        "error": error_msg
    })


@app.route('/api/gemini/config', methods=['POST', 'OPTIONS'])
def gemini_config():
    """Cấu hình Gemini API (update API key or model)"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    global GEMINI_API_KEY, GEMINI_MODEL
    
    data = request.get_json() or {}
    
    if 'api_key' in data:
        GEMINI_API_KEY = data['api_key']
        # Save to credentials.json
        try:
            cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
            if os.path.exists(cred_path):
                with open(cred_path, 'r', encoding='utf-8') as f:
                    creds = json.load(f)
                creds['gemini_api_key'] = GEMINI_API_KEY
                with open(cred_path, 'w', encoding='utf-8') as f:
                    json.dump(creds, f, ensure_ascii=False, indent=4)
                safe_print("[Gemini] API Key saved to credentials.json")
        except Exception as e:
            safe_print(f"[Gemini] Error saving config: {e}")
    
    if 'model' in data:
        GEMINI_MODEL = data['model']
    
    return jsonify({
        "success": True,
        "api_key_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL
    })


# ========================================================================
