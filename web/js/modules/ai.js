/**
 * AI Chat Module (Gemini AI)
 * Updated to use Google Gemini API
 */

// ============================================
// STATE
// ============================================

const AIState = {
    messages: [],
    isLoading: false,
    isConnected: false,
    currentModel: 'meta-llama/llama-3.1-8b-instruct',  // Default to working model
    chatHistory: [],
    STORAGE_KEY: 'gemini_ai_history',
    useStreaming: true,  // Enable streaming by default
    abortController: null,  // For stopping streaming
    // NEW: Session support for long-term memory
    currentSessionId: null,
    sessions: [],
    SESSION_STORAGE_KEY: 'ai_chat_sessions',
    // NEW: Sidebar state
    showSidebar: false,
    // NEW: Helper to get auth token consistently
    getAuthToken: function () {
        return window.getAuthToken ? window.getAuthToken() : localStorage.getItem('auth_token');
    }
};

// ============================================
// SYSTEM STATE (Long-term Memory)
// ============================================

/**
 * Update System State when user performs actions
 * This helps AI understand the current context
 * @param {string} currentProject - Current project name
 * @param {string} currentStep - Current step in workflow
 * @param {string} lastAction - Last action performed
 * @param {object} metadata - Additional metadata
 */
async function updateAISystemState(currentProject = null, currentStep = null, lastAction = null, metadata = null) {
    try {
        // FIX: Skip API call if no actual data to update
        // This prevents 500 error when user has no AI session yet
        if (!currentProject && !currentStep && !lastAction && !metadata) {
            console.log('[AI] No system state data to update, skipping API call...');
            return false;
        }
        
        const response = await fetch('/api/ai/chat/system-state', {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                current_project: currentProject,
                current_step: currentStep,
                last_action: lastAction,
                metadata: metadata
            })
        });

        if (response.ok) {
            console.log('[AI] System state updated:', { currentProject, currentStep, lastAction });
            return true;
        }
    } catch (e) {
        console.warn('[AI] Could not update system state:', e);
    }
    return false;
}

/**
 * Get current System State
 * @returns {Promise<object>} System state object
 */
async function getAISystemState() {
    try {
        const response = await fetch('/api/ai/chat/system-state', {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            return data.system_state || {};
        }
    } catch (e) {
        console.warn('[AI] Could not get system state:', e);
    }
    return {};
}

/**
 * Sync System State when starting AI chat
 * Load current context (project, step, last action) into AI
 */
async function syncAISystemStateOnStart() {
    try {
        const state = await getAISystemState();
        console.log('[AI] Synced system state on start:', state);
        return state;
    } catch (e) {
        console.warn('[AI] Could not sync system state:', e);
        return {};
    }
}

// Export to global
window.updateAISystemState = updateAISystemState;
window.getAISystemState = getAISystemState;
window.syncAISystemStateOnStart = syncAISystemStateOnStart;
window.getAISessionCount = getAISessionCount;

// ============================================
// SESSION MANAGEMENT (Long-term Memory)
// ============================================

/**
 * Load sessions from server
 */
async function loadAISessions() {
    try {
        // Sử dụng AIState.getAuthToken() để tận dụng fallback từ api.js
        const token = AIState.getAuthToken();
        if (!token) {
            console.warn('[AI] Not logged in, cannot load sessions');
            return [];
        }

        const response = await fetch('/api/ai/chat/sessions', {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            console.warn('[AI] Not authenticated (401), attempting to re-authenticate...');

            // Try to re-verify auth by calling /api/me
            try {
                const meResponse = await fetch('/api/me', {
                    method: 'GET',
                    headers: getAuthHeaders()
                });

                if (meResponse.status === 401) {
                    // Auth expired - clear tokens and notify user
                    console.warn('[AI] Auth expired, clearing tokens');
                    if (window.clearAuthToken) {
                        window.clearAuthToken();
                    }
                    localStorage.removeItem('auth_token');
                    sessionStorage.removeItem('auth_token');

                    // Dispatch event to notify app
                    window.dispatchEvent(new CustomEvent('authExpired', {
                        detail: { message: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.' }
                    }));

                    // Show notification
                    if (typeof showToast === 'function') {
                        showToast('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.', 'warning');
                    }
                }
            } catch (authError) {
                console.warn('[AI] Error re-verifying auth:', authError);
            }

            return [];
        }

        if (response.ok) {
            const data = await response.json();
            AIState.sessions = data.sessions || [];
            return AIState.sessions;
        }
    } catch (e) {
        console.warn('[AI] Could not load sessions from server:', e);
    }
    return [];
}

/**
 * Toggle sidebar visibility
 */
function toggleAISidebar() {
    AIState.showSidebar = !AIState.showSidebar;
    const sidebar = document.getElementById('ai-sidebar');
    const mainContainer = document.querySelector('.ai-main-container');

    if (sidebar && mainContainer) {
        if (AIState.showSidebar) {
            sidebar.style.display = 'flex';
            mainContainer.classList.add('with-sidebar');

            // Reload sessions when sidebar opens (in case auth wasn't ready initially)
            if (typeof window._aiLoadSessionsOnSidebarOpen === 'function') {
                console.log('[AI] Reloading sessions when sidebar opens');
                window._aiLoadSessionsOnSidebarOpen();
            }
        } else {
            sidebar.style.display = 'none';
            mainContainer.classList.remove('with-sidebar');
        }
    }
}

/**
 * Create new session and switch to it
 */
async function createNewAISession() {
    try {
        // Check if user is logged in first
        // Sử dụng AIState.getAuthToken() để tận dụng fallback từ api.js
        const token = AIState.getAuthToken();
        if (!token) {
            alert('Bạn cần đăng nhập để tạo cuộc trò chuyện mới. Vui lòng đăng nhập trước.');
            return;
        }

        const newSession = await createAISession('Cuộc trò chuyện mới');
        if (newSession) {
            // Switch to the new session
            await switchToSession(newSession.id);
            // Update the session list
            renderAISessionsList();
        }
    } catch (error) {
        console.error('[AI] Error creating new session:', error);
        alert('Không thể tạo cuộc trò chuyện mới. Vui lòng thử lại sau.\nLỗi: ' + (error.message || 'Lỗi không xác định'));
    }
}

/**
 * Delete a session
 */
async function deleteAISession(sessionId) {
    if (!confirm('Bạn có chắc muốn xóa cuộc trò chuyện này?')) {
        return false;
    }

    try {
        const response = await fetch(`/api/ai/chat/sessions/${sessionId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            // Remove from local list
            AIState.sessions = AIState.sessions.filter(s => s.id !== sessionId);

            // If was current session, clear
            if (AIState.currentSessionId === sessionId) {
                AIState.currentSessionId = null;
                localStorage.removeItem('ai_last_session_id');
                clearAIChat();
            }

            // Re-render sidebar
            renderAISessionsList();
            return true;
        }
    } catch (e) {
        console.error('[AI] Error deleting session:', e);
    }
    return false;
}

/**
 * Update session title
 */
async function updateAISessionTitle(sessionId, newTitle) {
    if (!newTitle || !newTitle.trim()) return false;

    try {
        const response = await fetch(`/api/ai/chat/sessions/${sessionId}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ title: newTitle.trim() })
        });

        if (response.ok) {
            // Update local list
            const session = AIState.sessions.find(s => s.id === sessionId);
            if (session) {
                session.title = newTitle.trim();
            }

            // Re-render sidebar
            renderAISessionsList();
            return true;
        }
    } catch (e) {
        console.error('[AI] Error updating session title:', e);
    }
    return false;
}

/**
 * Search chat history
 */
async function searchAIChat(query) {
    if (!query || !query.trim()) return [];

    try {
        const response = await fetch(`/api/ai/chat/search?q=${encodeURIComponent(query)}`, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            return data.results || [];
        }
    } catch (e) {
        console.error('[AI] Error searching chat:', e);
    }
    return [];
}

/**
 * Get total session count for current user
 * Used to answer questions like "Có bao nhiêu cuộc hội thoại rồi"
 * @returns {Promise<number>} Number of sessions
 */
async function getAISessionCount() {
    try {
        const response = await fetch('/api/ai/chat/sessions/count', {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            return data.count || 0;
        }
    } catch (e) {
        console.warn('[AI] Could not get session count:', e);
    }
    return 0;
}

/**
 * Render sessions list in sidebar
 */
function renderAISessionsList() {
    const sidebarList = document.getElementById('ai-sessions-list');
    if (!sidebarList) return;

    if (AIState.sessions.length === 0) {
        sidebarList.innerHTML = `
            <div class="ai-empty-sessions">
                <i class="bi bi-chat-dots"></i>
                <p>Chưa có cuộc trò chuyện nào</p>
            </div>
        `;
        return;
    }

    sidebarList.innerHTML = AIState.sessions.map(session => {
        const isActive = session.id === AIState.currentSessionId;
        const updatedAt = session.updated_at ? new Date(session.updated_at).toLocaleDateString('vi-VN') : '';

        return `
            <div class="ai-session-item ${isActive ? 'active' : ''}" data-session-id="${session.id}">
                <div class="ai-session-content">
                    <div class="ai-session-title">${escapeHtml(session.title || 'Cuộc trò chuyện mới')}</div>
                    <div class="ai-session-date">${updatedAt}</div>
                </div>
                <div class="ai-session-actions">
                    <button class="ai-session-btn" onclick="event.stopPropagation(); renameAISession('${session.id}', '${escapeHtml(session.title || 'Cuộc trò chuyện mới')}')" title="Đổi tên">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="ai-session-btn delete" onclick="event.stopPropagation(); deleteAISession('${session.id}')" title="Xóa">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    // Add click handlers
    sidebarList.querySelectorAll('.ai-session-item').forEach(item => {
        item.addEventListener('click', () => {
            const sessionId = item.dataset.sessionId;
            switchToSession(sessionId);
        });
    });
}

/**
 * Rename session (prompt user)
 */
async function renameAISession(sessionId, currentTitle) {
    const newTitle = prompt('Nhập tên mới cho cuộc trò chuyện:', currentTitle);
    if (newTitle && newTitle.trim()) {
        await updateAISessionTitle(sessionId, newTitle.trim());
    }
}

/**
 * Open search modal
 */
function openAISearchModal() {
    const query = prompt('Nhập từ khóa tìm kiếm:');
    if (query && query.trim()) {
        searchAIChat(query.trim()).then(results => {
            if (results.length > 0) {
                let message = `Tìm thấy ${results.length} kết quả:\n\n`;
                results.slice(0, 5).forEach(r => {
                    message += `• ${r.title}\n${r.content.substring(0, 100)}...\n\n`;
                });
                alert(message);
            } else {
                alert('Không tìm thấy kết quả nào');
            }
        });
    }
}

/**
 * Create new session on server
 */
async function createAISession(title = null) {
    try {
        const response = await fetch('/api/ai/chat/sessions', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                title: title || 'Cuộc trò chuyện mới'
            })
        });

        if (response.status === 401) {
            console.error('[AI] Not authenticated, please login first');
            return null;
        }

        if (response.ok) {
            const data = await response.json();
            if (data.session) {
                // Add to local sessions list
                AIState.sessions.unshift(data.session);
                return data.session;
            }
        } else {
            console.error('[AI] Failed to create session:', response.status, await response.text());
        }
    } catch (e) {
        console.error('[AI] Error creating session:', e);
    }
    return null;
}

/**
 * Load messages for a session
 */
async function loadSessionMessages(sessionId) {
    try {
        const response = await fetch(`/api/ai/chat/sessions/${sessionId}/messages`, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            console.warn('[AI] Not authenticated to load messages');
            return [];
        }

        if (response.ok) {
            const data = await response.json();
            return data.messages || [];
        }
    } catch (e) {
        console.error('[AI] Error loading session messages:', e);
    }
    return [];
}

/**
 * Save message to server (for long-term memory)
 */
async function saveMessageToSession(sessionId, role, content) {
    try {
        const response = await fetch(`/api/ai/chat/sessions/${sessionId}/messages`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                role: role,
                content: content
            })
        });

        return response.ok;
    } catch (e) {
        console.warn('[AI] Could not save message to server:', e);
        return false;
    }
}

/**
 * Get auth headers helper (with X-User-ID support for AI chat)
 */
function getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    // Sử dụng window.getAuthToken() để tận dụng fallback từ api.js
    // (localStorage → sessionStorage → memory)
    const token = AIState.getAuthToken();
    // Lấy user_id từ current user data
    const userId = window.getUserId ? window.getUserId() : null;

    // DEBUG: Log token availability
    console.log('[AI] getAuthHeaders - Token found:', !!token, token ? 'Bearer ' + token.substring(0, 20) + '...' : 'none');
    console.log('[AI] getAuthHeaders - User ID:', userId);

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Thêm X-User-ID header (giải pháp cho 401 auth)
    if (userId) {
        headers['X-User-ID'] = userId;
    }

    return headers;
}

/**
 * Switch to a different session
 */
async function switchToSession(sessionId) {
    try {
        // Save current messages to localStorage first
        if (AIState.currentSessionId && AIState.messages.length > 0) {
            saveChatHistory();
        }

        // Save session ID to localStorage for persistence
        localStorage.setItem('ai_last_session_id', sessionId);
        console.log('[AI] Saved session to localStorage:', sessionId);

        // Load new session
        AIState.currentSessionId = sessionId;

        // Load messages from server
        const messages = await loadSessionMessages(sessionId);

        if (messages.length > 0) {
            // Convert to frontend format
            AIState.messages = messages.map(msg => ({
                role: msg.role,
                content: msg.content
            }));

            // Render messages
            renderAIChatMessages();
        } else {
            // Start fresh
            AIState.messages = [];
            clearAIChat();
        }
    } catch (error) {
        console.error('[AI] Error switching to session:', error);
        alert('Không thể tải cuộc trò chuyện. Vui lòng thử lại sau.\nLỗi: ' + (error.message || 'Lỗi không xác định'));
    }
}

/**
 * Render chat messages (extracted for reuse)
 */
function renderAIChatMessages() {
    const chatMessages = document.getElementById('chat-messages-ai');
    const welcome = document.getElementById('welcome-ai');

    if (!chatMessages || !welcome) return;

    chatMessages.innerHTML = '';

    if (AIState.messages.length === 0) {
        chatMessages.style.display = 'none';
        welcome.style.display = 'flex';
        return;
    }

    chatMessages.style.display = 'flex';
    welcome.style.display = 'none';

    for (const msg of AIState.messages) {
        addAIMessage(msg.role, msg.content);
    }
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize AI module
 */
function initAIModule() {
    console.log('[AI] Initializing Gemini AI module...');

    // Render the module content
    renderAIContent();

    // Setup event listeners
    setupAIEvents();

    // Load chat history from localStorage
    loadChatHistory();

    // Check connection
    checkConnection();

    // Start periodic connection check
    startConnectionCheck();

    // Wait for auth token to be available before loading sessions
    // Sử dụng window.getAuthToken() để tận dụng fallback từ api.js
    // FIX: Increased maxAttempts and added exponential backoff for slow networks
    const waitForAuth = async (callback, maxAttempts = 20) => {
        let attempts = 0;
        const checkAuth = async () => {
            const token = AIState.getAuthToken();
            if (token) {
                // Verify token with server before proceeding
                try {
                    const meResponse = await fetch('/api/me', {
                        method: 'GET',
                        headers: getAuthHeaders()
                    });

                    if (meResponse.ok) {
                        // Token is valid, proceed
                        callback();
                    } else if (meResponse.status === 401) {
                        // Token invalid or expired - try to re-authenticate once
                        console.warn('[AI] Token invalid, attempting to refresh...');
                        if (attempts < maxAttempts) {
                            attempts++;
                            // Exponential backoff: 500ms, 750ms, 1125ms, etc.
                            const delay = Math.min(500 * Math.pow(1.5, attempts), 5000);
                            await new Promise(resolve => setTimeout(resolve, delay));
                            checkAuth();
                        } else {
                            console.warn('[AI] Auth token invalid after retries');
                            // Dispatch auth expired event
                            window.dispatchEvent(new CustomEvent('authExpired', {
                                detail: { message: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.' }
                            }));
                        }
                    } else {
                        // Other error, but token exists - proceed anyway
                        callback();
                    }
                } catch (e) {
                    // Network error, but token exists - proceed anyway
                    console.warn('[AI] Error verifying auth, proceeding anyway:', e);
                    callback();
                }
            } else if (attempts < maxAttempts) {
                attempts++;
                // Exponential backoff
                const delay = Math.min(500 * Math.pow(1.5, attempts), 5000);
                setTimeout(checkAuth, delay);
            } else {
                console.warn('[AI] Auth token not available after retries');
            }
        };
        checkAuth();
    };

    // Try to load sessions - wait for auth token first
    const loadSessionsWithRetry = () => {
        loadAISessions().then((sessions) => {
            console.log('[AI] Loaded sessions:', sessions.length);
            renderAISessionsList();

            // NEW: Tự động tạo session mới nếu chưa có session nào
            if (sessions.length === 0) {
                console.log('[AI] No sessions found, creating new session automatically...');
                createNewAISession().then(newSession => {
                    if (newSession) {
                        console.log('[AI] New session created:', newSession.id);
                        // Switch to new session
                        switchToSession(newSession.id);
                    }
                }).catch(err => {
                    console.warn('[AI] Error creating new session:', err);
                });
            } else {
                // NEW: Sync system state on start
                try {
                    syncAISystemStateOnStart();
                } catch (err) {
                    console.warn('[AI] Error syncing system state on start:', err);
                }

                // Try to restore last session from localStorage
                const lastSessionId = localStorage.getItem('ai_last_session_id');
                console.log('[AI] Last session from localStorage:', lastSessionId);

                if (lastSessionId) {
                    // Check if the session still exists
                    const sessionExists = sessions.some(s => s.id === lastSessionId);
                    if (sessionExists) {
                        console.log('[AI] Restoring last session:', lastSessionId);
                        switchToSession(lastSessionId);
                    } else {
                        console.log('[AI] Last session not found, clearing localStorage');
                        localStorage.removeItem('ai_last_session_id');
                    }
                }
            }
        }).catch(err => {
            console.warn('[AI] Load sessions failed:', err);
        });
    };

    // Wait for auth and then load
    waitForAuth(loadSessionsWithRetry);

    // Also load when sidebar is opened (in case auth token wasn't ready initially)
    window._aiLoadSessionsOnSidebarOpen = () => {
        const token = AIState.getAuthToken();
        if (token) {
            loadSessionsWithRetry();
        } else {
            waitForAuth(loadSessionsWithRetry);
        }
    };

    // NEW: Listen for userAuthenticated event to reload sessions after login
    window.addEventListener('userAuthenticated', function (event) {
        console.log('[AI] User authenticated event received, reloading sessions');
        loadSessionsWithRetry();
    });
}

/**
 * Render AI module content
 */
function renderAIContent() {
    const container = document.getElementById('ai-container');

    container.innerHTML = `
        <div class="ai-main-container">
            <!-- Sidebar -->
            <div class="ai-sidebar" id="ai-sidebar" style="display: none;">
                <div class="ai-sidebar-header">
                    <h5>Cuộc trò chuyện</h5>
                    <button class="ai-sidebar-close" onclick="toggleAISidebar()" title="Đóng">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
                <div class="ai-sidebar-actions">
                    <button class="btn btn-primary btn-sm w-100" onclick="createNewAISession()">
                        <i class="bi bi-plus-lg me-1"></i> Cuộc trò chuyện mới
                    </button>
                    <button class="btn btn-outline-secondary btn-sm w-100 mt-2" onclick="openAISearchModal()">
                        <i class="bi bi-search me-1"></i> Tìm kiếm
                    </button>
                </div>
                <div class="ai-sessions-list" id="ai-sessions-list">
                    <!-- Sessions will be rendered here -->
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="ai-content">
                <!-- Toolbar -->
                <div class="ai-toolbar">
                    <div class="toolbar-left">
                        <button class="btn btn-outline-secondary btn-sm" onclick="toggleAISidebar()" title="Danh sách cuộc trò chuyện">
                            <i class="bi bi-list-ul"></i>
                        </button>
                        ${AIState.currentSessionId ? `<span class="ai-current-session-title" id="ai-session-title-display">${escapeHtml(AIState.sessions.find(s => s.id === AIState.currentSessionId)?.title || 'Cuộc trò chuyện mới')}</span>` : ''}
                    </div>
                    <div class="toolbar-center">
                        <select class="model-select" id="model-select-ai">
                            <optgroup label="OpenRouter (Miễn phí)">
                                <option value="meta-llama/llama-3.1-8b-instruct" selected>Llama 3.1 8B (Miễn phí)</option>
                                <option value="qwen/qwen-2.5-7b-instruct">Qwen 2.5 7B (Miễn phí)</option>
                                <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
                                <option value="anthropic/claude-3-haiku">Claude 3 Haiku</option>
                                <option value="meta-llama/llama-3.1-8b-instruct">Llama 3.1 8B</option>
                            </optgroup>
                            <optgroup label="Google Gemini">
                                <option value="gemini-3-flash-preview">Gemini 3.0 Flash Preview</option>
                                <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                                <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                                <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                            </optgroup>
                            <optgroup label="Ollama (Local)">
                                <option value="llama3.2:latest">Llama 3.2 (Latest)</option>
                                <option value="llama3.1:latest">Llama 3.1</option>
                                <option value="qwen3:8b">Qwen 3 8B</option>
                                <option value="qwen2.5:14b">Qwen 2.5 14B</option>
                                <option value="phi4:latest">Phi-4</option>
                                <option value="mistral:latest">Mistral</option>
                                <option value="codellama:7b">CodeLlama 7B</option>
                            </optgroup>
                        </select>
                    </div>
                    <div class="toolbar-right">
                        <div class="status-item">
                            <div class="status-dot" id="status-dot-ai"></div>
                            <span id="status-text-ai">Đang kết nối...</span>
                            <button class="retry-btn" id="retry-btn-ai" title="Thử kết nối lại">
                                <i class="bi bi-arrow-clockwise"></i>
                            </button>
                        </div>
                        <button class="clear-btn" id="clear-btn-ai" title="Xóa chat">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                </div>

                <!-- Chat Container -->
                <div class="chat-container">
                    <!-- Welcome (shown when no messages) -->
                    <div class="welcome-container" id="welcome-ai">
                        <div class="welcome-icon">
                            <i class="bi bi-chat-dots"></i>
                        </div>
                        <h2 class="welcome-title">Chào bạn! 👋</h2>
                        <p class="welcome-subtitle">
                            Tôi là trợ lý AI Gemini của Propack VP. 
                            Hãy hỏi tôi về dự án, mã bản vẽ, hoặc bất kỳ điều gì bạn cần hỗ trợ nhé!
                        </p>
                    </div>

                    <!-- Chat Messages -->
                    <div class="chat-messages" id="chat-messages-ai" style="display: none;">
                        <!-- Messages will be added here -->
                    </div>

                    <!-- Input Area -->
                    <div class="chat-input-container">
                        <div class="chat-input-wrapper">
                            <textarea 
                                class="chat-input" 
                                id="chat-input-ai" 
                                placeholder="Nhập tin nhắn..." 
                                rows="1"
                                autocomplete="off"
                            ></textarea>
                            <button class="send-btn" id="send-btn-ai" disabled>
                                <i class="bi bi-send"></i>
                            </button>
                            <button class="stop-btn" id="stop-btn-ai" style="display: none;" title="Dừng">
                                <i class="bi bi-stop-fill"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
            .ai-main-container {
                display: flex;
                flex-direction: row;
                max-width: 100%;
                margin: 0 auto;
                gap: 0;
                height: calc(100vh - 250px);
                min-height: 400px;
            }
            
            /* Mobile: Adjust height for smaller screens */
            @media (max-width: 768px) {
                .ai-main-container {
                    height: calc(100vh - 200px);
                    min-height: 350px;
                }
            }
            
            .ai-main-container .ai-toolbar {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            
            .ai-main-container .status-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
                color: #64748b;
            }
            
            .ai-main-container .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #dc2626;
                animation: pulse 2s infinite;
            }
            
            .ai-main-container .status-dot.connected {
                background: #22c55e;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .ai-main-container .model-select {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 0.375rem 0.75rem;
                font-size: 0.875rem;
                background: white;
                cursor: pointer;
                outline: none;
            }
            
            .ai-main-container .chat-container {
                flex: 1;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .ai-main-container .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 1.5rem;
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            
            .ai-main-container .message {
                display: flex;
                gap: 0.75rem;
                max-width: 85%;
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .ai-main-container .message.user {
                align-self: flex-end;
                flex-direction: row-reverse;
            }
            
            .ai-main-container .message-avatar {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
                flex-shrink: 0;
            }
            
            .ai-main-container .message.user .message-avatar {
                background: #4f46e5;
                color: white;
            }
            
            .ai-main-container .message.ai .message-avatar {
                background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
                color: white;
            }
            
            .ai-main-container .message-content {
                padding: 0.875rem 1rem;
                border-radius: 16px;
                line-height: 1.6;
                font-size: 0.9375rem;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                word-wrap: break-word;
            }
            
            .ai-main-container .message.user .message-content {
                background: #4f46e5;
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .ai-main-container .message.ai .message-content {
                background: #f8fafc;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-bottom-left-radius: 4px;
            }
            
            .ai-main-container .message-time {
                font-size: 0.75rem;
                color: #64748b;
                margin-top: 0.25rem;
            }
            
            .ai-main-container .message.user .message-time {
                text-align: right;
            }
            
            .ai-main-container .typing-indicator {
                display: flex;
                gap: 0.25rem;
                padding: 0.75rem 1rem;
            }
            
            .ai-main-container .typing-indicator span {
                width: 8px;
                height: 8px;
                background: #64748b;
                border-radius: 50%;
                animation: bounce 1.4s infinite ease-in-out;
            }
            
            .ai-main-container .typing-indicator span:nth-child(1) { animation-delay: 0s; }
            .ai-main-container .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
            .ai-main-container .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes bounce {
                0%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-8px); }
            }
            
            .ai-main-container .chat-input-container {
                padding: 1rem 1.5rem;
                border-top: 1px solid #e2e8f0;
                background: white;
            }
            
            .ai-main-container .chat-input-wrapper {
                display: flex;
                gap: 0.75rem;
                align-items: flex-end;
            }
            
            .ai-main-container .chat-input {
                flex: 1;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 0.75rem 1rem;
                font-size: 0.9375rem;
                resize: none;
                outline: none;
                transition: border-color 0.2s;
                font-family: inherit;
                min-height: 48px;
                max-height: 150px;
            }
            
            .ai-main-container .chat-input:focus {
                border-color: #4285f4;
            }
            
            .ai-main-container .send-btn {
                width: 48px;
                height: 48px;
                border-radius: 12px;
                border: none;
                background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
                color: white;
                font-size: 1.25rem;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            }
            
            .ai-main-container .send-btn:hover:not(:disabled) {
                transform: scale(1.05);
            }
            
            .ai-main-container .send-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .ai-main-container .send-btn.loading {
                position: relative;
            }
            
            .ai-main-container .send-btn.loading::after {
                content: '';
                position: absolute;
                width: 20px;
                height: 20px;
                border: 2px solid transparent;
                border-top-color: white;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            
            .ai-main-container .stop-btn {
                width: 48px;
                height: 48px;
                border-radius: 12px;
                border: none;
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                color: white;
                font-size: 1.25rem;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            }
            
            .ai-main-container .stop-btn:hover {
                transform: scale(1.05);
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .ai-main-container .welcome-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 2rem;
            }
            
            .ai-main-container .welcome-icon {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
                border-radius: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2.5rem;
                color: white;
                margin-bottom: 1.5rem;
            }
            
            .ai-main-container .welcome-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 0.5rem;
            }
            
            .ai-main-container .welcome-subtitle {
                color: #64748b;
                max-width: 400px;
                line-height: 1.6;
            }
            
            .ai-main-container .error-message {
                background: #fef2f2;
                border: 1px solid #fecaca;
                color: #dc2626;
                padding: 0.75rem 1rem;
                border-radius: 12px;
                font-size: 0.875rem;
            }
            
            .ai-main-container .clear-btn {
                background: transparent;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 0.375rem 0.75rem;
                font-size: 0.875rem;
                color: #64748b;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 0.375rem;
            }
            
            .ai-main-container .clear-btn:hover {
                background: #fee2e2;
                border-color: #fecaca;
                color: #dc2626;
            }
            
            .ai-main-container .retry-btn {
                background: transparent;
                border: none;
                padding: 0.25rem 0.5rem;
                cursor: pointer;
                color: #64748b;
                transition: color 0.2s;
                font-size: 0.875rem;
            }
            
            .ai-main-container .retry-btn:hover {
                color: #4285f4;
            }
            
            @media (max-width: 768px) {
                .ai-main-container .message {
                    max-width: 90%;
                }
                
                /* Mobile: Ensure input is always visible */
                .ai-main-container .chat-input-container {
                    padding: 0.75rem;
                    flex-shrink: 0;
                }
                
                .ai-main-container .chat-input {
                    min-height: 44px;
                    font-size: 16px; /* Prevent zoom on iOS */
                }
                
                .ai-main-container .send-btn,
                .ai-main-container .stop-btn {
                    width: 44px;
                    height: 44px;
                }
                
                /* Mobile: Make toolbar more compact */
                .ai-main-container .ai-toolbar {
                    padding: 0.5rem;
                    gap: 0.5rem;
                }
                
                .ai-main-container .toolbar-left,
                .ai-main-container .toolbar-center,
                .ai-main-container .toolbar-right {
                    gap: 0.25rem;
                }
                
                .ai-main-container .model-select {
                    font-size: 0.75rem;
                    padding: 0.25rem 0.5rem;
                }
                
                .ai-main-container .ai-current-session-title {
                    max-width: 100px;
                }
                
                .ai-main-container .status-item {
                    font-size: 0.75rem;
                }
            }
            
            /* Sidebar Styles */
            .ai-sidebar {
                width: 280px;
                background: #f8fafc;
                border-right: 1px solid #e2e8f0;
                display: flex;
                flex-direction: column;
                flex-shrink: 0;
            }
            
            .ai-sidebar-header {
                padding: 1rem;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .ai-sidebar-header h5 {
                margin: 0;
                font-size: 1rem;
                font-weight: 600;
                color: #1e293b;
            }
            
            .ai-sidebar-close {
                background: none;
                border: none;
                padding: 0.25rem;
                cursor: pointer;
                color: #64748b;
            }
            
            .ai-sidebar-close:hover {
                color: #1e293b;
            }
            
            .ai-sidebar-actions {
                padding: 1rem;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .ai-sessions-list {
                flex: 1;
                overflow-y: auto;
                padding: 0.5rem;
            }
            
            .ai-session-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.75rem;
                margin-bottom: 0.5rem;
                border-radius: 8px;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .ai-session-item:hover {
                background: #e2e8f0;
            }
            
            .ai-session-item.active {
                background: #4f46e5;
                color: white;
            }
            
            .ai-session-item.active .ai-session-date {
                color: rgba(255, 255, 255, 0.7);
            }
            
            .ai-session-content {
                flex: 1;
                min-width: 0;
            }
            
            .ai-session-title {
                font-size: 0.875rem;
                font-weight: 500;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .ai-session-date {
                font-size: 0.75rem;
                color: #64748b;
                margin-top: 0.25rem;
            }
            
            .ai-session-actions {
                display: flex;
                gap: 0.25rem;
                opacity: 0;
                transition: opacity 0.2s;
            }
            
            .ai-session-item:hover .ai-session-actions {
                opacity: 1;
            }
            
            .ai-session-btn {
                background: none;
                border: none;
                padding: 0.25rem;
                cursor: pointer;
                color: #64748b;
                border-radius: 4px;
            }
            
            .ai-session-btn:hover {
                background: rgba(0, 0, 0, 0.1);
                color: #1e293b;
            }
            
            .ai-session-btn.delete:hover {
                background: rgba(220, 38, 38, 0.1);
                color: #dc2626;
            }
            
            .ai-empty-sessions {
                text-align: center;
                padding: 2rem 1rem;
                color: #64748b;
            }
            
            .ai-empty-sessions i {
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            
            /* Content Area */
            .ai-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                min-width: 0;
            }
            
            .ai-toolbar {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            
            .toolbar-left, .toolbar-center, .toolbar-right {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .ai-current-session-title {
                font-size: 0.875rem;
                color: #64748b;
                max-width: 200px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            /* Layout with sidebar */
            .ai-main-container.with-sidebar {
                flex-direction: row;
            }
            
            .ai-main-container.with-sidebar .ai-sidebar {
                display: flex;
            }
        </style>
    `;
}

/**
 * Setup AI event listeners
 */
function setupAIEvents() {
    // Chat input
    const chatInput = document.getElementById('chat-input-ai');
    chatInput.addEventListener('input', function () {
        updateAISendButton();

        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    chatInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendAIMessage();
        }
    });

    // Send button
    document.getElementById('send-btn-ai').addEventListener('click', sendAIMessage);

    // Stop button
    document.getElementById('stop-btn-ai').addEventListener('click', stopAIStreaming);

    // Clear button
    document.getElementById('clear-btn-ai').addEventListener('click', function () {
        if (confirm('Bạn có chắc muốn xóa toàn bộ cuộc trò chuyện?')) {
            clearAIChat();
        }
    });

    // Retry button
    document.getElementById('retry-btn-ai').addEventListener('click', function () {
        retryAIConnection();
    });

    // Model select
    document.getElementById('model-select-ai').addEventListener('change', function () {
        AIState.currentModel = this.value;
        checkConnection();  // Re-check connection for the new model
    });
}

// ============================================
// CONNECTION
// ============================================

/**
 * Check Gemini connection
 */
async function checkConnection() {
    const statusDot = document.getElementById('status-dot-ai');
    const statusText = document.getElementById('status-text-ai');
    const model = AIState.currentModel;

    try {
        // Check based on model type
        let endpoint = '/api/ollama-status';
        if (model.startsWith('gemini')) {
            endpoint = '/api/gemini/status';
        } else if (model.includes('/') || model.includes(':')) {
            // OpenRouter model format: provider/model-name or stepfun/step-3.5-flash:free
            endpoint = '/api/openrouter/status';
        }

        const response = await fetch(endpoint, {
            method: 'GET',
            signal: AbortSignal.timeout(10000)
        });

        if (response.ok) {
            const data = await response.json();

            // For Gemini
            if (model.startsWith('gemini')) {
                if (data.configured && data.connected) {
                    statusDot.classList.add('connected');
                    statusText.textContent = 'Đã kết nối ' + (data.model || 'Gemini');
                    AIState.isConnected = true;
                } else if (data.configured && !data.connected) {
                    statusDot.classList.remove('connected');
                    statusText.textContent = 'Gemini chưa kết nối';
                    AIState.isConnected = false;
                } else {
                    statusDot.classList.remove('connected');
                    statusText.textContent = 'Chưa cấu hình Gemini';
                    AIState.isConnected = false;
                }
            } else if (model.includes('/') || model.includes(':')) {
                // For OpenRouter
                if (data.configured && data.connected) {
                    statusDot.classList.add('connected');
                    statusText.textContent = 'Đã kết nối OpenRouter';
                    AIState.isConnected = true;
                } else if (data.configured && !data.connected) {
                    statusDot.classList.remove('connected');
                    statusText.textContent = 'OpenRouter chưa kết nối';
                    AIState.isConnected = false;
                } else {
                    statusDot.classList.remove('connected');
                    statusText.textContent = 'Chưa cấu hình OpenRouter';
                    AIState.isConnected = false;
                }
            } else {
                // For Ollama
                if (data.enabled && data.connected) {
                    statusDot.classList.add('connected');
                    statusText.textContent = 'Đã kết nối Ollama';
                    AIState.isConnected = true;
                } else if (data.enabled && !data.connected) {
                    statusDot.classList.remove('connected');
                    statusText.textContent = 'Ollama chưa kết nối';
                    AIState.isConnected = false;
                } else {
                    statusDot.classList.remove('connected');
                    statusText.textContent = 'Ollama đang tắt';
                    AIState.isConnected = false;
                }
            }
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Lỗi kết nối';
            AIState.isConnected = false;
        }
    } catch (error) {
        console.error('[AI] Connection check failed:', error);
        statusDot.classList.remove('connected');
        statusText.textContent = 'Chưa kết nối';
        AIState.isConnected = false;
    }
}

/**
 * Retry connection
 */
function retryAIConnection() {
    const statusText = document.getElementById('status-text-ai');
    statusText.textContent = 'Đang thử kết nối...';
    checkConnection();
}

/**
 * Start periodic connection check
 */
let connectionCheckInterval = null;

function startConnectionCheck() {
    if (connectionCheckInterval) {
        clearInterval(connectionCheckInterval);
    }

    connectionCheckInterval = setInterval(() => {
        checkConnection();
    }, 30000);
}

// ============================================
// MARKDOWN PARSING (for AI messages)
// ============================================

/**
 * Parse simple Markdown to HTML (only for AI responses)
 * Converts: **bold**, *italic*, `code`, and newlines
 * @param {string} text - Text with Markdown syntax
 * @returns {string} - HTML string
 */
/**
 * Parse simple Markdown to HTML (only for AI responses)
 * FIX #3: Improved XSS protection - always escape first, then parse markdown
 * @param {string} text - Text with Markdown syntax
 * @returns {string} - HTML string
 */
function parseSimpleMarkdown(text) {
    if (!text) return '';

    // DEBUG: Log input to check if content is already escaped
    console.log('[DEBUG parseSimpleMarkdown] Input:', text.substring(0, 200));
    console.log('[DEBUG parseSimpleMarkdown] Contains &lt;:', text.includes('&lt;'));
    console.log('[DEBUG parseSimpleMarkdown] Contains <br>:', text.includes('<br>'));

    // Check if content is already HTML (contains HTML tags)
    // This prevents double-escaping when loading messages from storage
    const hasHtmlTags = /<br|<b>|<i>|<code>|<\/|<span|<div/i.test(text);
    const isAlreadyEscaped = text.includes('&lt;') || text.includes('&gt;') || text.includes('&amp;');
    
    let html;
    if (hasHtmlTags || isAlreadyEscaped) {
        // Content already contains HTML - don't re-escape, just handle newlines
        console.log('[DEBUG parseSimpleMarkdown] Content already HTML, preserving tags');
        html = text;
        // Convert newlines to <br> for already-HTML content
        html = html.replace(/\n/g, '<br>');
    } else {
        // Plain text - escape HTML first as security baseline
        html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    // Then parse Markdown (order matters - parse in reverse for nested patterns)
    // Code inline: `code` → <code>code</code>
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold: **text** → <b>text</b>
    html = html.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');

    // Italic: *text* → <i>text</i>
    html = html.replace(/\*([^*]+)\*/g, '<i>$1</i>');

    // Handle newlines properly
    // 1. Normalize multiple consecutive newlines to single newline
    html = html.replace(/\n\n+/g, '\n');
    // 2. Trim leading/trailing newlines
    html = html.trim();
    // 3. Convert remaining single newlines to <br>
    html = html.replace(/\n/g, '<br>');

    return html;
}

// ============================================
// CHAT OPERATIONS
// ============================================

/**
 * Send message to AI
 */
async function sendAIMessage() {
    const chatInput = document.getElementById('chat-input-ai');
    const sendBtn = document.getElementById('send-btn-ai');
    const prompt = chatInput.value.trim();

    // Check if user is logged in
    const authToken = AIState.getAuthToken();
    if (!authToken) {
        alert('Bạn cần đăng nhập để sử dụng AI. Vui lòng đăng nhập trước.');
        return;
    }

    if (!prompt || AIState.isLoading) return;

    // Add user message
    addAIMessage('user', prompt);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    updateAISendButton();

    // Show typing
    showAITyping();

    AIState.isLoading = true;
    sendBtn.disabled = true;
    sendBtn.classList.add('loading');

    // Create abort controller for stopping
    AIState.abortController = new AbortController();

    // Show stop button, hide send button
    document.getElementById('send-btn-ai').style.display = 'none';
    document.getElementById('stop-btn-ai').style.display = 'flex';

    try {
        // NEW: Ensure we have a session for long-term memory
        if (!AIState.currentSessionId) {
            // Create new session if not exists
            const newSession = await createAISession();
            if (newSession) {
                AIState.currentSessionId = newSession.id;
                // Save to localStorage
                localStorage.setItem('ai_last_session_id', newSession.id);
                console.log('[AI] Created and saved new session:', newSession.id);
            }
        }

        // Build history for API call
        const history = AIState.messages.map(msg => ({
            role: msg.role === 'user' ? 'user' : 'model',
            content: msg.content
        }));

        // Create AI message placeholder
        const aiMessageDiv = createAIMessagePlaceholder();

        if (AIState.useStreaming) {
            // Use streaming API
            await sendToAIStream(prompt, history, aiMessageDiv);
        } else {
            // Use non-streaming API (fallback)
            const response = await sendToGemini(prompt, history);
            removeAITyping();
            updateAIMessageContent(aiMessageDiv, response);
        }

        // Get AI response content
        const aiContent = getAIMessageContent(aiMessageDiv);
        
        // DEBUG: Log AI content status
        console.log('[AI] DEBUG aiContent status:', {
            aiContent: aiContent,
            aiContentLength: aiContent ? aiContent.length : 0,
            aiContentTrimmed: aiContent ? aiContent.trim() : 'null',
            isEmpty: !aiContent || !aiContent.trim(),
            sessionId: AIState.currentSessionId
        });

        // Add to local state
        AIState.messages.push({ role: 'user', content: prompt });
        AIState.messages.push({ role: 'ai', content: aiContent });

        // Save to localStorage (fallback)
        saveChatHistory();

        // NEW: Save to server for long-term memory
        // FIX: Only save if content is not empty - wait for full AI response
        if (AIState.currentSessionId && aiContent && aiContent.trim()) {
            console.log('[AI] Saving messages to server for long-term memory...');
            try {
                await saveMessageToSession(AIState.currentSessionId, 'user', prompt);
                await saveMessageToSession(AIState.currentSessionId, 'ai', aiContent);
            } catch (saveError) {
                console.warn('[AI] Failed to save messages to server:', saveError);
            }

            // NEW: Tự động đặt tên session dựa trên tin nhắn đầu tiên (chỉ chạy 1 lần)
            const session = AIState.sessions.find(s => s.id === AIState.currentSessionId);
            if (session && session.title === 'Cuộc trò chuyện mới') {
                // Chỉ đặt tên nếu là tin nhắn user đầu tiên
                const messageCount = AIState.messages.filter(m => m.role === 'user').length;
                if (messageCount === 1 && aiContent) {
                    // Tạo title ngắn gọn từ tin nhắn đầu tiên (lấy 50 ký tự đầu tiên)
                    let autoTitle = prompt.substring(0, 50).trim();
                    if (prompt.length > 50) {
                        autoTitle += '...';
                    }
                    // Cập nhật title
                    await updateAISessionTitle(AIState.currentSessionId, autoTitle);
                    // Cập nhật UI
                    const titleDisplay = document.getElementById('ai-session-title-display');
                    if (titleDisplay) {
                        titleDisplay.textContent = autoTitle;
                    }
                }
            }
        } else if (!aiContent || !aiContent.trim()) {
            console.warn('[AI] Skipping save - AI content is empty:', aiContent);
        }
    } catch (error) {
        // DEBUG: Log what happened when error occurs
        console.log('[AI] DEBUG catch block:', {
            errorName: error.name,
            errorMessage: error.message,
            isAbort: error.name === 'AbortError',
            currentSessionId: AIState.currentSessionId
        });
        
        // Only show error if it's not an abort (user stopped)
        removeAITyping();
        if (error.name !== 'AbortError') {
            addAIError(error.message);
        }
    } finally {
        AIState.isLoading = false;
        sendBtn.disabled = false;
        sendBtn.classList.remove('loading');
        chatInput.focus();

        // Reset abort controller
        AIState.abortController = null;

        // Show send button, hide stop button
        document.getElementById('send-btn-ai').style.display = 'flex';
        document.getElementById('stop-btn-ai').style.display = 'none';
    }
}

/**
 * Create AI message placeholder
 */
function createAIMessagePlaceholder() {
    const chatMessages = document.getElementById('chat-messages-ai');
    const welcome = document.getElementById('welcome-ai');

    const now = new Date();
    const timeStr = now.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
    });

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="bi bi-robot"></i>
        </div>
        <div class="message-content-wrapper">
            <div class="message-content" id="ai-response-content"></div>
            <div class="message-time">${timeStr}</div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.style.display = 'flex';
    welcome.style.display = 'none';

    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

/**
 * Get AI message content
 */
function getAIMessageContent(messageDiv) {
    const contentDiv = messageDiv.querySelector('#ai-response-content');
    return contentDiv ? contentDiv.innerHTML : '';
}

/**
 * Update AI message content
 */
function updateAIMessageContent(messageDiv, content) {
    const contentDiv = messageDiv.querySelector('#ai-response-content');
    if (contentDiv) {
        contentDiv.innerHTML = parseSimpleMarkdown(content);
    }

    const chatMessages = document.getElementById('chat-messages-ai');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Append to AI message content (for streaming)
 */
function appendToAIMessageContent(messageDiv, newContent) {
    const contentDiv = messageDiv.querySelector('#ai-response-content');
    if (contentDiv) {
        // Don't escape - it's already streamed HTML
        contentDiv.innerHTML = newContent;
    }

    const chatMessages = document.getElementById('chat-messages-ai');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Send to AI with streaming (SSE)
 * @param {string} prompt - User prompt
 * @param {Array} history - Chat history
 * @param {HTMLElement} messageDiv - Message placeholder element
 */
async function sendToAIStream(prompt, history, messageDiv) {
    // Determine which API to use based on current model
    let endpoint = '/api/ollama/chat/stream';
    const model = AIState.currentModel;

    // Check if it's a Gemini model
    if (model.startsWith('gemini')) {
        endpoint = '/api/gemini/chat/stream';
    } else if (model.includes('/') || model.includes(':')) {
        // OpenRouter model format: provider/model-name or stepfun/step-3.5-flash:free
        endpoint = '/api/openrouter/chat/stream';
    }

    // Get auth token for user identification
    const authToken = AIState.getAuthToken();

    const headers = {
        'Content-Type': 'application/json'
    };

    // Add authorization header if token exists
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    // Validate session_id if exists
    let sessionId = AIState.currentSessionId || '';
    if (sessionId && typeof sessionId !== 'string') {
        console.warn('[AI] Invalid session_id format, resetting');
        sessionId = '';
    }

    // Build request body with session_id for long-term memory context
    const requestBody = {
        message: prompt,
        model: model,
        history: history,
        session_id: sessionId  // Include session ID if available
    };

    const response = await fetch(endpoint, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestBody),
        signal: AIState.abortController ? AIState.abortController.signal : null
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        // Check for rate limit specific errors
        if (response.status === 429 || (data.error && (data.error.includes('rate') || data.error.includes('tạm thời')))) {
            throw new Error('⚠️ Quá tải API! Hệ thống sẽ tự động thử lại với model khác. Nếu vẫn lỗi, vui lòng chọn model khác trong danh sách bên trên.');
        }
        throw new Error(data.error || `Lỗi ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';

    // Remove typing indicator and show streaming
    removeAITyping();

    // Tạo status display element cho message
    const contentDiv = messageDiv.querySelector('.ai-message-content');
    let statusDiv = messageDiv.querySelector('.ai-message-status');
    if (!statusDiv && contentDiv) {
        statusDiv = document.createElement('div');
        statusDiv.className = 'ai-message-status';
        contentDiv.parentNode.insertBefore(statusDiv, contentDiv);
    }

    while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                try {
                    const parsed = JSON.parse(data);

                    // Xử lý status events
                    if (parsed.type === 'status' && parsed.value) {
                        // Cập nhật status trong message
                        if (statusDiv) {
                            const statusText = window.getStatusDisplay ? window.getStatusDisplay(parsed.value) : parsed.value;
                            statusDiv.innerHTML = `<span class="spinner"></span>${statusText}`;
                            // Thêm class theo status
                            statusDiv.className = 'ai-message-status ' + parsed.value;
                        }
                        // Cập nhật global status bar
                        window.updateGlobalStatusBar && window.updateGlobalStatusBar(parsed.value);
                    }

                    // Xử lý tool events
                    else if (parsed.type === 'tool' && parsed.name) {
                        if (statusDiv) {
                            statusDiv.innerHTML = `🔧 Đang gọi: ${parsed.name}...`;
                            statusDiv.className = 'ai-message-status calling_tool';
                        }
                    }

                    // Xử lý content chunks
                    else if (parsed.type === 'chunk' && parsed.full) {
                        // Ẩn status khi có content
                        if (statusDiv) {
                            statusDiv.style.display = 'none';
                        }
                        // Update content with streaming text
                        appendToAIMessageContent(messageDiv, parseSimpleMarkdown(parsed.full));
                    }

                    // Xử lý done
                    else if (parsed.type === 'done' && parsed.full) {
                        // DEBUG: Log done event content
                        console.log('[AI] DEBUG done event:', {
                            parsedFull: parsed.full,
                            parsedFullLength: parsed.full ? parsed.full.length : 0,
                            parsedFullExists: !!parsed.full,
                            hasError: !!parsed.error
                        });
                        
                        if (statusDiv) {
                            statusDiv.innerHTML = '✅ Hoàn thành';
                            statusDiv.className = 'ai-message-status success';
                            setTimeout(() => {
                                if (statusDiv) statusDiv.style.display = 'none';
                            }, 2000);
                        }
                        appendToAIMessageContent(messageDiv, parseSimpleMarkdown(parsed.full));
                        // Reset global status bar
                        window.updateGlobalStatusBar && window.updateGlobalStatusBar('idle');
                        // If model was switched, show notification
                        if (parsed.model_used) {
                            const notification = document.createElement('div');
                            notification.className = 'text-muted';
                            notification.style.fontSize = '0.75rem';
                            notification.style.marginTop = '0.5rem';
                            notification.innerHTML = `<i class="bi bi-arrow-left-right"></i> Đã tự động chuyển sang model: ${parsed.model_used}`;
                            contentDiv.parentElement.appendChild(notification);
                        }
                    } else if (parsed.error) {
                        // Check for rate limit error
                        if (parsed.code === 'ALL_MODELS_FAILED') {
                            throw new Error('⚠️ Tất cả model AI đều bị quá tải. Vui lòng thử lại sau hoặc chọn Ollama (local).');
                        }
                        // Hiển thị lỗi
                        if (statusDiv) {
                            statusDiv.innerHTML = '❌ ' + parsed.error;
                            statusDiv.className = 'ai-message-status error';
                        }
                        // Update global status bar
                        window.updateGlobalStatusBar && window.updateGlobalStatusBar('error');
                        throw new Error(parsed.error);
                    }
                } catch (e) {
                    // Not valid JSON or aborted
                    if (e.name === 'AbortError') {
                        console.log('[AI] Stream aborted');
                        window.updateGlobalStatusBar && window.updateGlobalStatusBar('idle');
                        return;
                    }
                }
            }
        }
    }
}

/**
 * Send to Gemini API (non-streaming fallback)
 * @param {string} prompt - User prompt
 * @param {Array} history - Chat history
 * @returns {Promise<string>} AI response
 */
async function sendToGemini(prompt, history) {
    const model = AIState.currentModel;

    // Get auth token for user identification
    // Sử dụng AIState.getAuthToken() để tận dụng fallback từ api.js
    const authToken = AIState.getAuthToken();

    const headers = {
        'Content-Type': 'application/json'
    };

    // Add authorization header if token exists
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch('/api/gemini/chat', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            message: prompt,
            model: model,
            history: history,
            session_id: AIState.currentSessionId || ''  // NEW: Include session ID
        }),
        signal: AbortSignal.timeout(120000)
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `Lỗi ${response.status}`);
    }

    const data = await response.json();

    if (!data.success) {
        throw new Error(data.error || 'Không có phản hồi từ AI');
    }

    return data.response || 'Không có phản hồi từ AI';
}

/**
 * Add message to chat
 * @param {string} role - 'user' or 'ai'
 * @param {string} content - Message content
 */
function addAIMessage(role, content) {
    const chatMessages = document.getElementById('chat-messages-ai');
    const welcome = document.getElementById('welcome-ai');

    const now = new Date();
    const timeStr = now.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
    });

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    const contentHtml = role === 'ai' ? parseSimpleMarkdown(content) : escapeHtml(content);
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="bi ${role === 'user' ? 'bi-person' : 'bi-robot'}"></i>
        </div>
        <div class="message-content-wrapper">
            <div class="message-content">${contentHtml}</div>
            <div class="message-time">${timeStr}</div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.style.display = 'flex';
    welcome.style.display = 'none';

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Show typing indicator
 */
function showAITyping() {
    const chatMessages = document.getElementById('chat-messages-ai');

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai';
    typingDiv.id = 'typing-indicator-ai';
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <i class="bi bi-robot"></i>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Remove typing indicator
 */
function removeAITyping() {
    const typing = document.getElementById('typing-indicator-ai');
    if (typing) {
        typing.remove();
    }
}

/**
 * Add error message
 * @param {string} message - Error message
 */
function addAIError(message) {
    const chatMessages = document.getElementById('chat-messages-ai');
    const welcome = document.getElementById('welcome-ai');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'message ai';
    errorDiv.innerHTML = `
        <div class="message-avatar">
            <i class="bi bi-exclamation-triangle"></i>
        </div>
        <div class="message-content">
            <div class="error-message">
                <i class="bi bi-exclamation-circle me-2"></i>
                ${escapeHtml(message)}
            </div>
        </div>
    `;

    chatMessages.appendChild(errorDiv);
    chatMessages.style.display = 'flex';
    welcome.style.display = 'none';
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Update send button state
 */
function updateAISendButton() {
    const chatInput = document.getElementById('chat-input-ai');
    const sendBtn = document.getElementById('send-btn-ai');
    sendBtn.disabled = chatInput.value.trim().length === 0;
}

/**
 * Clear chat
 */
function clearAIChat() {
    const chatMessages = document.getElementById('chat-messages-ai');
    const welcome = document.getElementById('welcome-ai');

    chatMessages.innerHTML = '';
    chatMessages.style.display = 'none';
    welcome.style.display = 'flex';

    AIState.messages = [];
    AIState.chatHistory = [];

    try {
        localStorage.removeItem(AIState.STORAGE_KEY);
    } catch (e) {
        console.warn('[AI] Could not clear localStorage:', e);
    }
}

// ============================================
// HISTORY
// ============================================

/**
 * Load chat history from localStorage
 */
function loadChatHistory() {
    try {
        const saved = localStorage.getItem(AIState.STORAGE_KEY);
        if (saved) {
            AIState.chatHistory = JSON.parse(saved);
        }
    } catch (e) {
        console.warn('[AI] Could not load from localStorage:', e);
        AIState.chatHistory = [];
    }
}

/**
 * Save chat history to localStorage
 */
function saveChatHistory() {
    try {
        // Only keep last 50 messages to avoid localStorage limit
        const messagesToSave = AIState.messages.slice(-50);
        localStorage.setItem(AIState.STORAGE_KEY, JSON.stringify(messagesToSave));
    } catch (e) {
        console.warn('[AI] Could not save to localStorage:', e);
    }
}

// ============================================
// STOP STREAMING
// ============================================

/**
 * Stop the current AI streaming
 */
function stopAIStreaming() {
    if (AIState.abortController) {
        AIState.abortController.abort();
        console.log('[AI] Streaming aborted by user');
    }

    // Remove typing indicator
    removeAITyping();

    // Reset state
    AIState.isLoading = false;
    AIState.abortController = null;

    // Reset UI
    const sendBtn = document.getElementById('send-btn-ai');
    sendBtn.disabled = false;
    sendBtn.classList.remove('loading');
    sendBtn.style.display = 'flex';

    document.getElementById('stop-btn-ai').style.display = 'none';
    document.getElementById('chat-input-ai').focus();

    // Add a message indicating stopped
    const chatMessages = document.getElementById('chat-messages-ai');
    if (chatMessages && chatMessages.style.display !== 'none') {
        // Find the last AI message and add note
        const lastMessage = chatMessages.querySelector('.message.ai:last-child');
        if (lastMessage) {
            const contentDiv = lastMessage.querySelector('.message-content');
            if (contentDiv) {
                contentDiv.innerHTML += '<br><span class="text-muted" style="font-size: 0.8rem;"><i class="bi bi-stop-circle"></i> Đã dừng</span>';
            }
        }
    }
}

// ============================================
// TAB INIT CALLBACK
// ============================================

window.initAIModule = initAIModule;
window.onAITabInit = function () {
    // Called when AI tab is shown
    checkConnection();

    // Also reload sessions when tab is shown (in case auth wasn't ready initially)
    if (typeof window._aiLoadSessionsOnSidebarOpen === 'function') {
        console.log('[AI] Reloading sessions when AI tab is shown');
        window._aiLoadSessionsOnSidebarOpen();
    }
};

// ============================================
// AGENT HELPER FUNCTIONS (NEW)
// ============================================

/**
 * Get extended tools for AI Agent
 * @returns {Promise<Array>} List of available tools
 */
async function getAgentTools() {
    try {
        const response = await fetch('/api/ai/chat/agent/tools', {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            return data.tools || [];
        }
    } catch (e) {
        console.error('[AI] Error getting agent tools:', e);
    }
    return [];
}

/**
 * Get agent system prompt
 * @returns {Promise<string>} System prompt for AI
 */
async function getAgentPrompt() {
    try {
        const response = await fetch('/api/ai/chat/agent/prompt', {
            method: 'GET'
        });

        if (response.ok) {
            const data = await response.json();
            return data.prompt || '';
        }
    } catch (e) {
        console.error('[AI] Error getting agent prompt:', e);
    }
    return '';
}

/**
 * Execute agent to process message (uses Agent capabilities)
 * @param {string} message - User message
 * @returns {Promise<Object>} Agent response
 */
async function executeAgentMessage(message) {
    try {
        const response = await fetch('/api/ai/chat/agent/execute', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                message: message,
                session_id: AIState.currentSessionId
            })
        });

        if (response.ok) {
            const data = await response.json();
            return {
                success: true,
                message: data.message,
                intent: data.intent,
                confidence: data.confidence,
                tools_used: data.tools_used,
                suggestions: data.suggestions
            };
        }
    } catch (e) {
        console.error('[AI] Error executing agent:', e);
    }
    return { success: false, message: '' };
}

/**
 * Get active triggers/suggestions for current user
 * @returns {Promise<Array>} List of active triggers
 */
async function getAgentTriggers() {
    try {
        const response = await fetch('/api/ai/chat/agent/trigger', {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            return data.triggers || [];
        }
    } catch (e) {
        console.error('[AI] Error getting triggers:', e);
    }
    return [];
}

/**
 * Get agent context (from memory layers)
 * @param {string} query - Optional search query
 * @returns {Promise<string>} Assembled context
 */
async function getAgentContext(query = '') {
    try {
        const url = query
            ? `/api/ai/chat/agent/context?q=${encodeURIComponent(query)}`
            : '/api/ai/chat/agent/context';

        const response = await fetch(url, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            return data.context || '';
        }
    } catch (e) {
        console.error('[AI] Error getting context:', e);
    }
    return '';
}

// Export to global
window.getAgentTools = getAgentTools;
window.getAgentPrompt = getAgentPrompt;
window.executeAgentMessage = executeAgentMessage;
window.getAgentTriggers = getAgentTriggers;
window.getAgentContext = getAgentContext;
