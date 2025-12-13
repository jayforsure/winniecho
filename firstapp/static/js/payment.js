// Payment Processing JavaScript - FIXED VERSION
// Works with your existing process_payment view

document.addEventListener('DOMContentLoaded', function() {
    initializePaymentForm();
});

function initializePaymentForm() {
    const paymentForm = document.getElementById('paymentForm');
    if (!paymentForm) return;
    
    // Payment method selection
    const paymentMethods = document.querySelectorAll('input[name="payment_method"]');
    paymentMethods.forEach(method => {
        method.addEventListener('change', handlePaymentMethodChange);
    });
    
    // Trigger initial display
    const checkedMethod = document.querySelector('input[name="payment_method"]:checked');
    if (checkedMethod) {
        handlePaymentMethodChange({ target: checkedMethod });
    }
}

function handlePaymentMethodChange(e) {
    const method = e.target.value;
    
    // Show/hide relevant payment fields
    document.querySelectorAll('.payment-fields').forEach(field => {
        field.style.display = 'none';
    });
    
    const selectedField = document.querySelector(`.payment-fields[data-method="${method}"]`);
    if (selectedField) {
        selectedField.style.display = 'block';
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