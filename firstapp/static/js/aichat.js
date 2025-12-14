// Modern Japanese Minimalist AI Chat
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const promptButtons = document.querySelectorAll('.prompt-btn');
    const clearHistoryBtn = document.getElementById('clearHistory');
    const charCount = document.getElementById('charCount');
    const historyList = document.getElementById('historyList');
    const usageFill = document.getElementById('usageFill');
    
    // State
    let conversationHistory = [];
    let isGenerating = false;
    
    // Initialize
    loadChatHistory();
    updateUsageBar();
    
    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Update character count
        charCount.textContent = this.value.length;
        
        // Enable/disable send button
        sendBtn.disabled = this.value.trim().length === 0 || isGenerating;
    });
    
    // Form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await sendMessage();
    });
    
    // Enter key handling
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isGenerating && messageInput.value.trim()) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });
    
    // Prompt buttons
    promptButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt');
            messageInput.value = prompt;
            messageInput.dispatchEvent(new Event('input'));
            messageInput.focus();
        });
    });
    
    // Clear history
    clearHistoryBtn.addEventListener('click', function() {
        if (confirm('Clear all chat history?')) {
            conversationHistory = [];
            saveChatHistory();
            loadChatHistory();
            chatMessages.innerHTML = '';
            addWelcomeMessage();
        }
    });
    
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || isGenerating) return;
        
        // Disable input
        isGenerating = true;
        messageInput.disabled = true;
        sendBtn.disabled = true;
        
        // Add user message
        addMessage(message, 'user');
        conversationHistory.push({
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        });
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        charCount.textContent = '0';
        
        // Save history
        saveChatHistory();
        updateChatHistory();
        
        // Show typing indicator
        const typingId = showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    message: message,
                    history: conversationHistory.slice(-5).map(h => ({
                        role: h.role,
                        content: h.content
                    }))
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            hideTypingIndicator(typingId);
            
            if (data.success) {
                // Add AI response
                addMessage(data.response, 'ai');
                conversationHistory.push({
                    role: 'assistant',
                    content: data.response,
                    timestamp: new Date().toISOString()
                });
                
                // Update usage
                if (data.tokens_used) {
                    updateUsageBar(data.tokens_used);
                }
            } else {
                addMessage('Apologies, I encountered an error. Please try again.', 'ai');
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            hideTypingIndicator(typingId);
            addMessage('Unable to connect. Please check your connection.', 'ai');
        } finally {
            // Re-enable input
            isGenerating = false;
            messageInput.disabled = false;
            messageInput.focus();
            sendBtn.disabled = messageInput.value.trim().length === 0;
            
            // Save updated history
            saveChatHistory();
            updateChatHistory();
        }
    }
    
    function addMessage(text, sender) {
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message-wrapper ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const senderName = document.createElement('span');
        senderName.className = 'sender-name';
        senderName.textContent = sender === 'user' ? 'You' : 'Choco AI';
        
        const time = document.createElement('span');
        time.className = 'message-time';
        time.textContent = formatTime(new Date());
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        // Convert URLs to links and preserve line breaks
        const processedText = text.replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        
        messageText.innerHTML = processedText;
        
        // Assemble message
        header.appendChild(senderName);
        header.appendChild(time);
        content.appendChild(header);
        content.appendChild(messageText);
        messageWrapper.appendChild(avatar);
        messageWrapper.appendChild(content);
        
        // Add to chat
        chatMessages.appendChild(messageWrapper);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function showTypingIndicator() {
        const typingTemplate = document.getElementById('typingIndicator');
        const clone = typingTemplate.content.cloneNode(true);
        chatMessages.appendChild(clone);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return Date.now();
    }
    
    function hideTypingIndicator() {
        const typing = chatMessages.querySelector('.typing-message');
        if (typing) {
            typing.remove();
        }
    }
    
    function addWelcomeMessage() {
        // This will be added by Django template
    }
    
    function formatTime(date) {
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || CSRF_TOKEN;
    }
    
    function saveChatHistory() {
        try {
            localStorage.setItem('winniecho_chat_history', JSON.stringify(conversationHistory));
        } catch (e) {
            console.error('Failed to save chat history:', e);
        }
    }
    
    function loadChatHistory() {
        try {
            const saved = localStorage.getItem('winniecho_chat_history');
            if (saved) {
                conversationHistory = JSON.parse(saved);
            }
        } catch (e) {
            console.error('Failed to load chat history:', e);
        }
    }
    
    function updateChatHistory() {
        historyList.innerHTML = '';
        
        // Show last 10 conversations
        const recent = conversationHistory
            .filter(msg => msg.role === 'user')
            .slice(-10)
            .reverse();
        
        recent.forEach(msg => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.textContent = msg.content.substring(0, 60) + (msg.content.length > 60 ? '...' : '');
            item.addEventListener('click', () => {
                messageInput.value = msg.content;
                messageInput.dispatchEvent(new Event('input'));
                messageInput.focus();
            });
            historyList.appendChild(item);
        });
    }
    
    function updateUsageBar(tokensUsed = 0) {
        // Simple usage simulation
        const usage = Math.min(30 + (tokensUsed / 100), 100);
        usageFill.style.width = `${usage}%`;
    }
    
    // Initialize chat history display
    updateChatHistory();
});