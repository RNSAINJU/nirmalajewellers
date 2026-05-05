/**
 * Ornament Details Chatbot
 * Provides ornament information through a conversational interface
 */

class OrnamentChatbot {
    constructor(options = {}) {
        this.apiEndpoint = options.apiEndpoint || '/ornament/api/chat/';
        this.containerId = options.containerId || 'chatbot-container';
        this.position = options.position || 'bottom-right';
        this.title = options.title || 'Ornament Details';
        this.subtitle = options.subtitle || 'Ask me about ornaments...';
        this.isOpen = false;
        this.messages = [];
        this.init();
    }

    init() {
        this.createChatWidget();
        this.attachEventListeners();
    }

    createChatWidget() {
        // Create container if doesn't exist
        let container = document.getElementById(this.containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.containerId;
            document.body.appendChild(container);
        }

        // Chat widget HTML
        const chatHTML = `
            <div class="chatbot-widget ${this.position}">
                <!-- Toggle Button -->
                <button class="chatbot-toggle" title="Chat with us">
                    <i class="bi bi-chat-dots"></i>
                    <span class="chat-badge">💬</span>
                </button>

                <!-- Chat Window -->
                <div class="chatbot-window">
                    <!-- Header -->
                    <div class="chatbot-header">
                        <div>
                            <h5 class="chat-title">${this.title}</h5>
                            <p class="chat-subtitle">${this.subtitle}</p>
                        </div>
                        <button class="chat-close" title="Close">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>

                    <!-- Messages Container -->
                    <div class="chatbot-messages">
                        <div class="chat-message bot">
                            <div class="message-content">
                                👋 Hello! I can help you find ornament details. Try asking:
                                <div class="example-queries">
                                    <button class="query-button" data-query="Show me gold necklaces">Gold necklaces</button>
                                    <button class="query-button" data-query="What ornaments are under 50000?">Under 50000</button>
                                    <button class="query-button" data-query="Find lightweight ornaments">Lightweight</button>
                                </div>
                            </div>
                            <span class="message-time">Just now</span>
                        </div>
                    </div>

                    <!-- Input Area -->
                    <div class="chatbot-input-area">
                        <input 
                            type="text" 
                            class="chat-input" 
                            placeholder="Ask about ornaments..."
                            autocomplete="off"
                        >
                        <button class="send-button" title="Send">
                            <i class="bi bi-send"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = chatHTML;
    }

    attachEventListeners() {
        const toggle = document.querySelector('.chatbot-toggle');
        const closeBtn = document.querySelector('.chat-close');
        const input = document.querySelector('.chat-input');
        const sendBtn = document.querySelector('.send-button');
        const queryButtons = document.querySelectorAll('.query-button');

        toggle.addEventListener('click', () => this.toggleChat());
        closeBtn.addEventListener('click', () => this.closeChat());
        sendBtn.addEventListener('click', () => this.sendMessage());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        queryButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = e.target.dataset.query;
                input.value = query;
                this.sendMessage();
            });
        });
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        const widget = document.querySelector('.chatbot-widget');
        widget.classList.add('open');
        this.isOpen = true;
        document.querySelector('.chat-input').focus();
    }

    closeChat() {
        const widget = document.querySelector('.chatbot-widget');
        widget.classList.remove('open');
        this.isOpen = false;
    }

    sendMessage() {
        const input = document.querySelector('.chat-input');
        const message = input.value.trim();

        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        input.value = '';

        // Show loading
        this.showTyping();

        // Send to API
        this.fetchOrnamentDetails(message);
    }

    addMessage(text, sender, details = null) {
        const messagesContainer = document.querySelector('.chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;

        const time = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        if (sender === 'bot' && details) {
            // Format ornament details
            let content = text;
            if (Array.isArray(details) && details.length > 0) {
                content += '<div class="ornament-results">';
                details.forEach(ornament => {
                    content += `
                        <div class="ornament-card">
                            <div class="ornament-header">
                                <strong>${ornament.ornament_name}</strong>
                                <span class="ornament-code">${ornament.code}</span>
                            </div>
                            <div class="ornament-details">
                                <div class="detail-item">
                                    <span class="label">Type:</span>
                                    <span class="value">${ornament.type || 'N/A'}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="label">Weight:</span>
                                    <span class="value">${ornament.weight}g</span>
                                </div>
                                <div class="detail-item">
                                    <span class="label">Metal:</span>
                                    <span class="value">${ornament.metal_type}</span>
                                </div>
                                ${ornament.diamond_weight ? `
                                <div class="detail-item">
                                    <span class="label">Diamond:</span>
                                    <span class="value">${ornament.diamond_weight}g</span>
                                </div>
                                ` : ''}
                                ${ornament.stone_weight ? `
                                <div class="detail-item">
                                    <span class="label">Stone:</span>
                                    <span class="value">${ornament.stone_weight}g</span>
                                </div>
                                ` : ''}
                                ${ornament.kaligar ? `
                                <div class="detail-item">
                                    <span class="label">Kaligar:</span>
                                    <span class="value">${ornament.kaligar}</span>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                });
                content += '</div>';
            }
            messageDiv.innerHTML = `
                <div class="message-content">${content}</div>
                <span class="message-time">${time}</span>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">${this.escapeHtml(text)}</div>
                <span class="message-time">${time}</span>
            `;
        }

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTyping() {
        const messagesContainer = document.querySelector('.chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot typing';
        typingDiv.innerHTML = `
            <div class="message-content">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        typingDiv.id = 'typing-indicator';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeTyping() {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    }

    fetchOrnamentDetails(query) {
        fetch(this.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({ query: query })
        })
        .then(res => res.json())
        .then(data => {
            this.removeTyping();
            if (data.success) {
                this.addMessage(data.response, 'bot', data.ornaments);
            } else {
                this.addMessage(data.response || 'Sorry, I couldn\'t find any results.', 'bot');
            }
        })
        .catch(error => {
            this.removeTyping();
            console.error('Chat error:', error);
            this.addMessage('Sorry, there was an error. Please try again.', 'bot');
        });
    }

    getCookie(name) {
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

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if chatbot should be enabled
    if (document.body.dataset.enableChatbot !== 'false') {
        window.ornamentChatbot = new OrnamentChatbot({
            apiEndpoint: '/ornament/api/chat/',
            title: 'Ornament Assistant',
            subtitle: 'Ask about our ornaments...'
        });
    }
});
