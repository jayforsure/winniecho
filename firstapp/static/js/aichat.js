// AI Chat JavaScript for DeepSeek API Integration

class AIChat {
    constructor() {
        this.apiKey = 'sk-b4833eb8508444c1a0f127c596ae56ed';
        this.apiUrl = 'https://api.deepseek.com/v1/chat/completions';
        this.conversationHistory = [];
        this.maxHistory = 10;
        this.isLoading = false;
        
        // DOM Elements
        this.messageInput = document.getElementById('messageInput');
        this.chatForm = document.getElementById('chatForm');
        this.sendBtn = document.getElementById('sendBtn');
        this.chatMessages = document.getElementById('chatMessages');
        this.historyList = document.getElementById('historyList');
        this.clearHistoryBtn = document.getElementById('clearHistory');
        this.charCount = document.getElementById('charCount');
        this.usageFill = document.getElementById('usageFill');
        
        // Prompt buttons
        this.promptButtons = document.querySelectorAll('.prompt-btn');
        
        this.initialize();
    }

    initialize() {
        // Load chat history from localStorage
        this.loadHistory();
        
        // Event listeners
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.messageInput.addEventListener('input', () => this.handleInput());
        this.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        
        // Prompt buttons
        this.promptButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handlePromptClick(e));
        });
        
        // Enter key handling (send on Enter, new line on Shift+Enter)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.sendBtn.disabled) return;
                this.handleSubmit(e);
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.resizeTextarea();
        });
        
        // Initialize textarea height
        this.resizeTextarea();
        
        // Initialize usage indicator
        this.updateUsageIndicator();
    }

    resizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
    }

    handleInput() {
        const text = this.messageInput.value.trim();
        this.sendBtn.disabled = !text;
        this.charCount.textContent = text.length;
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;
        
        // Add user message
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.sendBtn.disabled = true;
        this.charCount.textContent = '0';
        this.resizeTextarea();
        
        // Show typing indicator
        const typingIndicator = this.showTypingIndicator();
        
        try {
            this.isLoading = true;
            
            // Get AI response
            const response = await this.getAIResponse(message);
            
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add AI response
            this.addMessage(response, 'ai');
            
            // Save to history
            this.saveToHistory(message);
            
            // Update usage
            this.updateUsageIndicator();
            
        } catch (error) {
            console.error('Error:', error);
            typingIndicator.remove();
            this.addMessage(
                'Sorry, I encountered an error. Please try again or check your API configuration.',
                'ai'
            );
        } finally {
            this.isLoading = false;
        }
    }

    handlePromptClick(e) {
        const prompt = e.currentTarget.dataset.prompt;
        this.messageInput.value = prompt;
        this.messageInput.focus();
        this.handleInput();
        this.resizeTextarea();
    }

    async getAIResponse(userMessage) {
        const messages = [
            {
                role: 'system',
                content: `You are a helpful chocolate expert assistant for WinnieCho Chocolate Shop. You provide accurate, helpful information about chocolate types, recipes, storage, health benefits, gift ideas, and chocolate making. Keep responses informative but concise.

                STORE INFORMATION:
                - Store Name: WinnieCho Chocolate Shop
                - Products: Premium chocolates, truffles, chocolate bars, gift boxes, seasonal collections
                - Price Range: RM 20 - RM 200+
                - Specialties: Handcrafted chocolates, custom gift boxes, corporate gifts
                - Shipping: Free shipping for orders above RM 100, 2-3 business days delivery
                - Loyalty Program: 1 point per RM 1 spent, redeemable for discounts
                - Contact: support@WinnieCho.com, +60 3-1234 5678
                
                POLICIES:
                - Returns: 7-day return policy for unopened items
                - Refunds: Processed within 3-5 business days
                - Delivery Issues: Contact support within 24 hours of delivery
                
                Your role: Provide accurate, helpful information about chocolate types, recipes, storage, health benefits, gift ideas, and chocolate making. Also help with order inquiries, shipping info, and store policies.
                
                IMPORTANT GUIDELINES:
                1. ALWAYS be polite and professional
                2. When asked about products, suggest relevant items from our store
                3. For pricing and stock inquiries, direct users to the product pages
                4. For order issues, ask for order number and suggest contacting support
                5. Keep responses informative but concise (2-3 paragraphs maximum)
                6. If you don't know something, admit it and suggest contacting support`
            },
            ...this.conversationHistory,
            {
                role: 'user',
                content: userMessage
            }
        ];

        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                model: 'deepseek-chat',
                messages: messages,
                max_tokens: 1000,
                temperature: 0.7,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        
        // Update conversation history (keep last 10 messages)
        this.conversationHistory.push(
            { role: 'user', content: userMessage },
            { role: 'assistant', content: data.choices[0].message.content }
        );
        
        if (this.conversationHistory.length > this.maxHistory * 2) {
            this.conversationHistory = this.conversationHistory.slice(-this.maxHistory * 2);
        }

        return data.choices[0].message.content;
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-wrapper ${sender}-message`;
        
        const timestamp = this.getCurrentTime();
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${sender === 'ai' ? this.getAIIcon() : this.getUserIcon()}
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="sender-name">${sender === 'ai' ? 'Choco AI' : 'You'}</span>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-text">${this.formatMessage(content)}</div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const template = document.getElementById('typingIndicator');
        const typingIndicator = template.content.cloneNode(true);
        this.chatMessages.appendChild(typingIndicator);
        this.scrollToBottom();
        return this.chatMessages.lastElementChild;
    }

    formatMessage(text) {
        // Convert markdown-like formatting to HTML
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(.+)/, '<p>$1</p>')
            .replace(/## (.*?)(?=\n|$)/g, '<h4>$1</h4>')
            .replace(/- (.*?)(?=\n|$)/g, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>');
    }

    getAIIcon() {
        return `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <path d="M8.56 2.75c4.37 6.03 6.02 9.42 8.03 17.72m2.54-15.38c-3.72 4.35-8.94 5.66-16.88 5.85m19.5 1.9c-3.5-.93-6.63-.82-8.94 0-2.58.92-5.01 2.86-7.44 6.32"/>
            </svg>
        `;
    }

    getUserIcon() {
        return `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
            </svg>
        `;
    }

    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    saveToHistory(message) {
        const history = JSON.parse(localStorage.getItem('aiChatHistory') || '[]');
        const timestamp = new Date().toISOString();
        
        history.unshift({
            message: message,
            timestamp: timestamp,
            time: this.getCurrentTime()
        });
        
        if (history.length > 20) {
            history.pop();
        }
        
        localStorage.setItem('aiChatHistory', JSON.stringify(history));
        this.loadHistory();
    }

    loadHistory() {
        const history = JSON.parse(localStorage.getItem('aiChatHistory') || '[]');
        this.historyList.innerHTML = '';
        
        history.forEach((item, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.title = item.message;
            historyItem.innerHTML = `
                <div class="history-preview">${item.message.substring(0, 50)}${item.message.length > 50 ? '...' : ''}</div>
                <div class="history-time">${item.time}</div>
            `;
            
            historyItem.addEventListener('click', () => {
                this.messageInput.value = item.message;
                this.messageInput.focus();
                this.handleInput();
                this.resizeTextarea();
            });
            
            this.historyList.appendChild(historyItem);
        });
    }

    clearHistory() {
        if (confirm('Are you sure you want to clear all chat history?')) {
            localStorage.removeItem('aiChatHistory');
            this.loadHistory();
        }
    }

    updateUsageIndicator() {
        // Simulate usage (in real app, track actual API usage)
        const usage = Math.random() * 30 + 10; // Random between 10-40%
        this.usageFill.style.width = `${usage}%`;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.aiChat = new AIChat();
    
    // Add CSS for history items
    const style = document.createElement('style');
    style.textContent = `
        .history-preview {
            font-size: 12px;
            color: var(--text-dark);
            margin-bottom: 2px;
        }
        
        .history-time {
            font-size: 10px;
            color: var(--text-light);
        }
    `;
    document.head.appendChild(style);
});