// Base JavaScript for WinnieCho Chocolate Ordering System
// FIXED: Message auto-dismiss now works properly

document.addEventListener('DOMContentLoaded', function() {
    // Initialize
    initializeNavigation();
    initializeMessages(); // ✅ This will now work
    loadCartCount();
    
    // Mobile menu toggle
    const mobileToggle = document.getElementById('mobileMenuToggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleMobileMenu);
    }
});

// =====================
// NAVIGATION
// =====================

function initializeNavigation() {
    // Highlight active nav link based on current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || currentPath.startsWith(href + '/')) {
            link.classList.add('active');
        }
    });
}

function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    navMenu.classList.toggle('mobile-active');
}

// =====================
// MESSAGES - FIXED AUTO-DISMISS
// =====================

function initializeMessages() {
    // Get all Django messages
    const messages = document.querySelectorAll('.message-jp[data-auto-dismiss="true"]');
    
    console.log(`Found ${messages.length} messages to auto-dismiss`); // Debug
    
    messages.forEach((message, index) => {
        // Add fade-out animation after 3 seconds
        setTimeout(() => {
            console.log(`Dismissing message ${index + 1}`); // Debug
            message.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                message.remove();
                console.log(`Message ${index + 1} removed`); // Debug
            }, 300);
        }, 3000); // 3 seconds
    });
    
    // Close button handlers
    const closeButtons = document.querySelectorAll('.message-close-jp');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const message = this.closest('.message-jp');
            message.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => message.remove(), 300);
        });
    });
}

// ✅ UNIFIED showNotification() - Works on ALL pages
function showNotification(message, type = 'success') {
    // Create notification container if doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'toast-container-jp';
        document.body.appendChild(container);
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `toast toast-${type}`;
    
    // Icon based on type
    const icons = {
        success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7a9479" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
        </svg>`,
        error: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b85c5c" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>`,
        info: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4a4a4a" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>`
    };
    
    notification.innerHTML = `
        ${icons[type] || icons.success}
        <span>${message}</span>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Show with animation
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// =====================
// CART
// =====================

function loadCartCount() {
    // This would normally load from session/API
    // For now, just ensure badge is visible if there's a count
    const cartBadge = document.getElementById('cartCount');
    if (cartBadge && parseInt(cartBadge.textContent) > 0) {
        cartBadge.style.display = 'flex';
    }
}

function updateCartCount(count) {
    const cartBadge = document.getElementById('cartCount');
    if (cartBadge) {
        cartBadge.textContent = count;
        cartBadge.style.display = count > 0 ? 'flex' : 'none';
    }
}

// =====================
// UTILITY FUNCTIONS
// =====================

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

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[0-9\-\+\(\)\s]+$/;
    return re.test(phone);
}

// =====================
// SMOOTH SCROLL
// =====================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// =====================
// INTERSECTION OBSERVER (for animations)
// =====================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

// Observe elements with 'animate-on-scroll' class
document.querySelectorAll('.animate-on-scroll').forEach(el => {
    observer.observe(el);
});

// =====================
// LOADING STATES
// =====================

function showLoading(button) {
    button.disabled = true;
    button.dataset.originalText = button.textContent;
    button.textContent = 'Loading...';
}

function hideLoading(button) {
    button.disabled = false;
    if (button.dataset.originalText) {
        button.textContent = button.dataset.originalText;
        delete button.dataset.originalText;
    }
}

// =====================
// EXPORT FUNCTIONS
// =====================

window.WinnieCho = {
    getCookie,
    showNotification,
    updateCartCount,
    validateEmail,
    validatePhone,
    showLoading,
    hideLoading
};

// =====================
// GLOBAL CSS FOR NOTIFICATIONS
// =====================

const style = document.createElement('style');
style.textContent = `
    /* Toast Container (Fixed Position) */
    .toast-container-jp,
    #notification-container {
        position: fixed;
        top: 100px;
        right: 32px;
        z-index: 3000;
        display: flex;
        flex-direction: column;
        gap: 12px;
        pointer-events: none;
    }

    /* Toast Notification (Minimalist) */
    .toast {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: #fafaf8;
        border: 1px solid #e8e6e0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        font-size: 13px;
        min-width: 320px;
        opacity: 0;
        transform: translateX(400px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        pointer-events: auto;
    }

    .toast.show {
        opacity: 1;
        transform: translateX(0);
    }

    .toast-success {
        border-left: 2px solid #7a9479;
    }

    .toast-error {
        border-left: 2px solid #b85c5c;
    }

    .toast-info {
        border-left: 2px solid #4a4a4a;
    }

    .toast svg {
        flex-shrink: 0;
    }

    /* Slide Out Animation */
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .toast-container-jp,
        #notification-container {
            right: 16px;
            left: 16px;
            top: 80px;
        }

        .toast {
            min-width: auto;
            width: 100%;
        }
    }
`;
document.head.appendChild(style);