// AI Chat Widget
document.addEventListener('DOMContentLoaded', function() {
    const chatToggle = document.getElementById('chat-toggle');
    const chatPanel = document.getElementById('chat-panel');
    const chatClose = document.getElementById('chat-close');
    const chatSend = document.getElementById('chat-send');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    let conversationHistory = [];
    
    // Toggle chat panel
    chatToggle.addEventListener('click', function() {
        chatPanel.classList.add('open');
        chatToggle.classList.add('hidden');
        chatInput.focus();
    });
    
    // Close chat panel
    chatClose.addEventListener('click', function() {
        chatPanel.classList.remove('open');
        chatToggle.classList.remove('hidden');
    });
    
    // Send message on button click
    chatSend.addEventListener('click', sendMessage);
    
    // Send message on Enter key
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    async function sendMessage() {
        const message = chatInput.value.trim();
        
        if (!message) return;
        
        // Disable input
        chatInput.disabled = true;
        chatSend.disabled = true;
        
        // Add user message to chat
        addMessage(message, 'user');
        conversationHistory.push({role: 'user', content: message});
        
        // Clear input
        chatInput.value = '';
        
        // Show typing indicator
        const typingId = addTypingIndicator();
        
        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message,
                    history: conversationHistory.slice(-10)  // Send last 10 messages for context
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator(typingId);
            
            if (data.success) {
                // Add assistant response
                addMessage(data.response, 'assistant', data.redirect_url, data.redirect_text);
                conversationHistory.push({role: 'assistant', content: data.response});
            } else {
                addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            removeTypingIndicator(typingId);
            addMessage('Sorry, I could not connect. Please check your internet connection.', 'assistant');
        } finally {
            // Re-enable input
            chatInput.disabled = false;
            chatSend.disabled = false;
            chatInput.focus();
        }
    }
    
    function addMessage(text, sender, redirectUrl = null, redirectText = null) {
        // Remove welcome message if it exists
        const welcome = chatMessages.querySelector('.chat-welcome');
        if (welcome) {
            welcome.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = text;
        
        // Add redirect button if provided
        if (redirectUrl && redirectText) {
            const redirectBtn = document.createElement('a');
            redirectBtn.href = redirectUrl;
            redirectBtn.className = 'message-redirect';
            redirectBtn.textContent = redirectText;
            redirectBtn.target = '_blank';
            messageDiv.appendChild(document.createElement('br'));
            messageDiv.appendChild(redirectBtn);
        }
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-' + Date.now();
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingDiv.appendChild(dot);
        }
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return typingDiv.id;
    }
    
    function removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});