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
    currentModel: 'stepfun/step-3.5-flash:free',  // Step Fun model as default
    chatHistory: [],
    STORAGE_KEY: 'gemini_ai_history',
    useStreaming: true,  // Enable streaming by default
    abortController: null  // For stopping streaming
};

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
}

/**
 * Render AI module content
 */
function renderAIContent() {
    const container = document.getElementById('ai-container');
    
    container.innerHTML = `
        <div class="ai-main-container">
            <!-- Status Bar -->
            <div class="status-bar">
                <div class="status-item">
                    <div class="status-dot" id="status-dot-ai"></div>
                    <span id="status-text-ai">Đang kết nối...</span>
                    <button class="retry-btn" id="retry-btn-ai" title="Thử kết nối lại">
                        <i class="bi bi-arrow-clockwise"></i>
                    </button>
                </div>
                <div class="d-flex align-items-center gap-3">
                    <select class="model-select" id="model-select-ai">
                        <optgroup label="OpenRouter (Miễn phí)">
                            <option value="stepfun/step-3.5-flash:free" selected>StepFun Step 3.5 Flash (Miễn phí)</option>
                            <option value="google/gemini-2.0-flash-exp:free">Gemini 2.0 Flash (Miễn phí)</option>
                            <option value="google/gemini-1.5-flash-8b:free">Gemini 1.5 Flash 8B (Miễn phí)</option>
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
                    <button class="clear-btn" id="clear-btn-ai">
                        <i class="bi bi-trash3"></i>
                        <span class="d-none d-sm-inline">Xóa chat</span>
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
        
        <style>
            .ai-main-container {
                max-width: 900px;
                margin: 0 auto;
                display: flex;
                flex-direction: column;
                height: calc(100vh - 250px);
                min-height: 400px;
            }
            
            .ai-main-container .status-bar {
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
    chatInput.addEventListener('input', function() {
        updateAISendButton();
        
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });
    
    chatInput.addEventListener('keydown', function(e) {
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
    document.getElementById('clear-btn-ai').addEventListener('click', function() {
        if (confirm('Bạn có chắc muốn xóa toàn bộ cuộc trò chuyện?')) {
            clearAIChat();
        }
    });
    
    // Retry button
    document.getElementById('retry-btn-ai').addEventListener('click', function() {
        retryAIConnection();
    });
    
    // Model select
    document.getElementById('model-select-ai').addEventListener('change', function() {
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
function parseSimpleMarkdown(text) {
    if (!text) return '';
    
    // First escape HTML (for security)
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Then parse Markdown (order matters - parse in reverse for nested patterns)
    // Code inline: `code` → <code>code</code>
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Bold: **text** → <b>text</b>
    html = html.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
    
    // Italic: *text* → <i>text</i>
    html = html.replace(/\*([^*]+)\*/g, '<i>$1</i>');
    
    // Newlines to <br>
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
        
        // Save to history
        AIState.messages.push({ role: 'user', content: prompt });
        AIState.messages.push({ role: 'ai', content: getAIMessageContent(aiMessageDiv) });
        saveChatHistory();
    } catch (error) {
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
    const authToken = localStorage.getItem('auth_token') || '';
    
    const headers = {
        'Content-Type': 'application/json'
    };
    
    // Add authorization header if token exists
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            message: prompt,
            model: model,
            history: history
        }),
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
                    
                    if (parsed.type === 'chunk' && parsed.full) {
                        // Update content with streaming text
                        appendToAIMessageContent(messageDiv, parseSimpleMarkdown(parsed.full));
                    } else if (parsed.type === 'done' && parsed.full) {
                        appendToAIMessageContent(messageDiv, parseSimpleMarkdown(parsed.full));
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
                        throw new Error(parsed.error);
                    }
                } catch (e) {
                    // Not valid JSON or aborted
                    if (e.name === 'AbortError') {
                        console.log('[AI] Stream aborted');
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
    const authToken = localStorage.getItem('auth_token') || '';
    
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
            history: history
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
window.onAITabInit = function() {
    // Called when AI tab is shown
    checkConnection();
};
