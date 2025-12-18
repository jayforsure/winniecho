// Dashboard JavaScript - Modern Medium Style

document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initForms();
});

// ===================================
// Navigation (updated for MEDIUM)
// ===================================
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-item-medium');
    const panels = document.querySelectorAll('.content-panel-medium');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get panel ID from href
            const panelId = this.getAttribute('href').substring(1);
            
            // Remove active from all
            navLinks.forEach(l => l.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            const targetPanel = document.getElementById(panelId);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
}

// ===================================
// Forms
// ===================================
function initForms() {
    // Profile Form
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }
    
    // Password Form
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', handlePasswordChange);
    }
}

// Profile Update
async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const button = this.querySelector('button[type="submit"]');
    
    button.disabled = true;
    button.textContent = 'Updating...';
    
    try {
        const response = await fetch('/profile/update/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Profile updated successfully!', 'success');
        } else {
            showToast(data.error || 'Update failed', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
    }
    
    button.disabled = false;
    button.textContent = 'Update Profile';
}

// Password Change
async function handlePasswordChange(e) {
    e.preventDefault();
    
    const newPass = document.querySelector('input[name="new_password"]').value;
    const confirmPass = document.querySelector('input[name="confirm_password"]').value;
    
    if (newPass !== confirmPass) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    if (newPass.length < 8) {
        showToast('Password must be at least 8 characters', 'error');
        return;
    }
    
    const formData = new FormData(this);
    const button = this.querySelector('button[type="submit"]');
    
    button.disabled = true;
    button.textContent = 'Changing...';
    
    try {
        const response = await fetch('/password/change/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Password changed successfully!', 'success');
            this.reset();
        } else {
            showToast(data.error || 'Change failed', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
    }
    
    button.disabled = false;
    button.textContent = 'Change Password';
}

// ===================================
// Address Functions
// ===================================
async function setDefaultAddress(addressId) {
    try {
        const response = await fetch(`/addresses/${addressId}/set-default/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Default address updated!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Update failed', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
    }
}

// ===================================
// Utilities
// ===================================
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

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7a9479" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
        </svg>`,
        error: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b85c5c" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>`
    };
    
    toast.innerHTML = `
        ${icons[type] || icons.success}
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}