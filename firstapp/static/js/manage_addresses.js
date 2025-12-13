// Manage Addresses JavaScript - Modern Version

// Load address data
let addressesData = {};
try {
    const dataElement = document.getElementById('addressData');
    if (dataElement) {
        addressesData = JSON.parse(dataElement.textContent);
    }
} catch (error) {
    console.error('Error loading address data:', error);
}

// ===================================
// Modal Functions
// ===================================

function openAddressModal() {
    const modal = document.getElementById('addressModal');
    const form = document.getElementById('addressForm');
    const title = document.getElementById('modalTitle');
    
    // Reset form
    form.reset();
    document.getElementById('addressId').value = '';
    title.textContent = 'Add New Address';
    
    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeAddressModal() {
    const modal = document.getElementById('addressModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

function editAddress(addressId) {
    const address = addressesData[addressId];
    if (!address) {
        showToast('Address not found', 'error');
        return;
    }
    
    // Fill form
    document.getElementById('addressId').value = address.id;
    document.getElementById('label').value = address.label;
    document.getElementById('address').value = address.address;
    document.getElementById('city').value = address.city;
    document.getElementById('state').value = address.state;
    document.getElementById('postal_code').value = address.postal_code;
    document.getElementById('is_default').checked = address.is_default;
    
    // Update title
    document.getElementById('modalTitle').textContent = 'Edit Address';
    
    // Show modal
    openAddressModal();
}

// ===================================
// Form Submission
// ===================================

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('addressForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // Close modal on Esc key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAddressModal();
        }
    });
});

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const addressId = document.getElementById('addressId').value;
    
    // Fix: Change 'true' to 'on' for checkbox
    const isDefaultCheckbox = document.getElementById('is_default');
    if (isDefaultCheckbox && isDefaultCheckbox.checked) {
        formData.set('is_default', 'on');
    }
    
    const url = addressId ? `/addresses/${addressId}/update/` : '/addresses/add/';
    
    const submitBtn = this.querySelector('.btn-submit-modern');
    if (!submitBtn) return;
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(addressId ? 'Address updated!' : 'Address added!', 'success');
            closeAddressModal();
            
            // Check if should redirect to checkout
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            } else {
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            showToast(data.error || 'Operation failed', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Address';
        }
    } catch (error) {
        showToast('An error occurred', 'error');
        console.error('Error:', error);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Address';
    }
}

// ===================================
// Address Actions
// ===================================

async function setDefaultAddress(addressId) {
    try {
        const response = await fetch(`/addresses/${addressId}/set-default/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Default address updated!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Operation failed', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
        console.error('Error:', error);
    }
}

async function deleteAddress(addressId) {
    if (!confirm('Are you sure you want to delete this address?')) {
        return;
    }
    
    try {
        const response = await fetch(`/addresses/${addressId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Address deleted!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Cannot delete default address', 'error');
        }
    } catch (error) {
        showToast('An error occurred', 'error');
        console.error('Error:', error);
    }
}

// ===================================
// Utility Functions
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
    const container = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' 
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>'
        : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    
    toast.innerHTML = `${icon}<span>${message}</span>`;
    container.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto-remove after 3 seconds
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