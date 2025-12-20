// Japanese-Modern Products Page JavaScript
// Interactive Drag & Drop Shopping Cart
// FIXED: Clear localStorage after payment success

// Global state
let cart = [];
let productData = {};
let currentModalProduct = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadProductData();
    initializeCategories();
    initializeDragAndDrop();
    initializeSearch();
    initializeSort();
    loadCartFromStorage();
    updateCartDisplay();
});

// =====================
// AJAX CATEGORY FILTERING
// =====================
function initializeCategories() {
    const categoryLinks = document.querySelectorAll('[data-category]');
    
    categoryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const category = this.dataset.category;
            const searchQuery = document.getElementById('searchInput')?.value || '';
            const sortBy = document.getElementById('sortSelect')?.value || '';
            
            console.log('📁 Category clicked:', category);
            
            // Update active state
            categoryLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Load products via AJAX
            loadProducts(searchQuery, category, sortBy);
        });
    });
}

// =====================
// LOAD PRODUCTS VIA AJAX
// =====================
async function loadProducts(search = '', category = '', sort = '') {
    const productsGrid = document.getElementById('productsGrid');
    const productCount = document.getElementById('productCount');
    
    if (!productsGrid) return;
    
    // Show loading state
    productsGrid.style.opacity = '0.5';
    
    try {
        // Build query string
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (category) params.append('category', category);
        if (sort) params.append('sort', sort);
        
        // Make AJAX request
        const response = await fetch(`/products/?${params.toString()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load products');
        }
        
        const data = await response.json();
        
        // Update product count
        if (productCount) {
            productCount.textContent = data.count;
        }
        
        // Clear grid
        productsGrid.innerHTML = '';
        
        // Render products
        if (data.products.length === 0) {
            productsGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; color: var(--ash);">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="margin-bottom: 20px; opacity: 0.3;">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.35-4.35"/>
                    </svg>
                    <p style="font-size: 15px;">No products found</p>
                </div>
            `;
        } else {
            data.products.forEach(product => {
                const productCard = createProductCard(product);
                productsGrid.appendChild(productCard);
            });
            
            // Reinitialize drag and drop for new products
            initializeDragAndDrop();
        }
        
        // Update product data for modal
        data.products.forEach(product => {
            productData[product.id] = product;
        });
        
        // Restore opacity
        productsGrid.style.opacity = '1';
        
        // Update URL without page refresh
        const newUrl = `/products/?${params.toString()}`;
        window.history.pushState({}, '', newUrl);
        
    } catch (error) {
        console.error('Error loading products:', error);
        showToast('Failed to load products', 'error');
        productsGrid.style.opacity = '1';
    }
}

// =====================
// CREATE PRODUCT CARD
// =====================
function createProductCard(product) {
    const card = document.createElement('article');
    card.className = 'product-card-jp';
    card.draggable = true;
    card.dataset.productId = product.id;
    card.dataset.productName = product.name;
    card.dataset.productPrice = product.price;
    card.dataset.productStock = product.stock;
    card.dataset.productCategory = product.category;
    
    // Get primary image
    const primaryImage = product.images && product.images.length > 0 
        ? product.images[0] 
        : '/static/img/product/placeholder.jpg';
    
    // Stock badge
    let stockBadge = '';
    if (product.stock <= 5 && product.stock > 0) {
        stockBadge = `<span class="stock-badge-jp low">${product.stock} left</span>`;
    } else if (product.stock === 0) {
        stockBadge = `<span class="stock-badge-jp out">Out</span>`;
    }
    
    card.innerHTML = `
        <!-- Drag Indicator -->
        <div class="drag-indicator-jp">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="9" cy="21" r="1"/>
                <circle cx="20" cy="21" r="1"/>
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
            </svg>
            <span>Add</span>
        </div>
        
        <!-- Product Image -->
        <div class="product-image-container-jp">
            <img src="${primaryImage}" alt="${product.name}" class="product-image-jp">
            ${stockBadge}
        </div>
        
        <!-- Product Info -->
        <div class="product-info-jp">
            <span class="category-badge-jp">${product.category}</span>
            <h3 class="product-name-jp">${product.name}</h3>
            
            <div class="product-footer-jp">
                <span class="product-price-jp">${product.price}<small>RM</small></span>
                <button class="btn-view-jp" onclick="showProductDetails('${product.id}')">
                    Details
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M5 12h14"/>
                        <path d="m12 5 7 7-7 7"/>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    return card;
}

// =====================
// UPDATE SEARCH WITH DEBOUNCE
// =====================
let searchTimeout;
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        
        searchTimeout = setTimeout(() => {
            const query = this.value.trim();
            
            // ✅ FIXED: Correct CSS class selector
            const activeCategoryLink = document.querySelector('.nav-link-jpp.active');
            const category = activeCategoryLink ? activeCategoryLink.dataset.category : '';
            
            const sort = document.getElementById('sortSelect')?.value || '';
            
            console.log('🔍 Searching - Active category:', category, 'Query:', query);
            
            loadProducts(query, category, sort);
        }, 300);
    });
}

// =====================
// UPDATE SORT
// =====================
function initializeSort() {
    const sortSelect = document.getElementById('sortSelect');
    
    if (!sortSelect) {
        console.error('Sort select element not found!');
        return;
    }
    
    sortSelect.addEventListener('change', async function() {
        const sortValue = this.value;
        const searchQuery = document.getElementById('searchInput')?.value || '';
        
        // ✅ FIXED: Correct CSS class selector (nav-link-jpp, not nav-link-jp)
        const activeCategoryLink = document.querySelector('.nav-link-jpp.active');
        const category = activeCategoryLink ? activeCategoryLink.dataset.category : '';
        
        console.log('🔀 Sorting - Active category:', category, 'Sort value:', sortValue);
        
        // Map frontend values to backend values
        const sortMapping = {
            'price_asc': 'price_low',
            'price_desc': 'price_high',
            'name_asc': 'name',
            'created_desc': 'newest',
            '': ''
        };
        
        const backendSortValue = sortMapping[sortValue] || '';
        
        // Debug log to see what's being sent
        console.log('📤 Sending to server:', {
            search: searchQuery,
            category: category,
            sort: backendSortValue
        });
        
        await loadProducts(searchQuery, category, backendSortValue);
    });
}

// =====================
// LOAD PRODUCT DATA
// =====================
function loadProductData() {
    const dataScript = document.getElementById('productData');
    if (dataScript) {
        try {
            productData = JSON.parse(dataScript.textContent);
        } catch (e) {
            console.error('Error loading product data:', e);
        }
    }
}

// =====================
// DRAG AND DROP (FIXED)
// =====================
function initializeDragAndDrop() {
    const products = document.querySelectorAll('.product-card-jp');
    const dropzone = document.getElementById('cartDropzone');
    const cartBox = document.getElementById('floatingCart');
    
    // Remove old event listeners to prevent duplicates
    const oldCartBox = cartBox.cloneNode(true);
    cartBox.parentNode.replaceChild(oldCartBox, cartBox);
    
    // Get fresh reference
    const freshCartBox = document.getElementById('floatingCart');
    
    products.forEach(product => {
        // Remove old listeners by cloning
        const newProduct = product.cloneNode(true);
        product.parentNode.replaceChild(newProduct, product);
    });
    
    // Re-select all products after cloning
    const freshProducts = document.querySelectorAll('.product-card-jp');
    
    freshProducts.forEach(product => {
        // Drag start
        product.addEventListener('dragstart', function(e) {
            this.classList.add('dragging');
            const productId = this.dataset.productId;
            const productName = this.dataset.productName;
            const productPrice = this.dataset.productPrice;
            const productStock = this.dataset.productStock;
            
            e.dataTransfer.setData('productId', productId);
            e.dataTransfer.setData('productName', productName);
            e.dataTransfer.setData('productPrice', productPrice);
            e.dataTransfer.setData('productStock', productStock);
            e.dataTransfer.effectAllowed = 'copy';
        });
        
        // Drag end
        product.addEventListener('dragend', function() {
            this.classList.remove('dragging');
        });
    });
    
    const freshDropzone = document.getElementById('cartDropzone');
    
    // Cart box drag over
    freshCartBox.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        freshDropzone?.classList.add('drag-over');
    });
    
    freshCartBox.addEventListener('dragleave', function(e) {
        if (e.target === this || !this.contains(e.relatedTarget)) {
            freshDropzone?.classList.remove('drag-over');
        }
    });
    
    // Drop on cart - SINGLE EVENT ONLY
    freshCartBox.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation(); // IMPORTANT: Prevent event bubbling
        freshDropzone?.classList.remove('drag-over');
        
        const productId = e.dataTransfer.getData('productId');
        const productName = e.dataTransfer.getData('productName');
        const productPrice = parseFloat(e.dataTransfer.getData('productPrice'));
        const productStock = parseInt(e.dataTransfer.getData('productStock'));
        
        if (productId && productStock > 0) {
            console.log(`🎯 Adding to cart: ${productName} x1`); // Debug log
            addToCart(productId, productName, productPrice, productStock);
        } else if (productStock === 0) {
            showToast('This item is out of stock', 'error');
        }
    });
    
    // Drag out of cart to remove
    document.addEventListener('dragover', function(e) {
        const isOverCart = freshCartBox.contains(e.target);
        if (!isOverCart && e.dataTransfer.types.includes('cartitemid')) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }
    });
    
    document.addEventListener('drop', function(e) {
        const isOverCart = freshCartBox.contains(e.target);
        if (!isOverCart && e.dataTransfer.types.includes('cartitemid')) {
            e.preventDefault();
            const productId = e.dataTransfer.getData('cartitemid');
            if (productId) {
                removeFromCart(productId, true);
                showToast('Removed from cart', 'success');
            }
        }
    });
}

// =====================
// CART MANAGEMENT
// =====================
function addToCart(productId, productName, productPrice, productStock) {
    const existingItem = cart.find(item => item.id === productId);
    
    // ✅ ALWAYS get current stock from productData (may have been updated)
    const currentProduct = productData[productId];
    const currentStock = currentProduct ? currentProduct.stock : productStock;
    
    if (existingItem) {
        // ✅ Check against CURRENT stock, not stored stock
        if (existingItem.quantity < currentStock) {
            existingItem.quantity++;
            // ✅ Update stored stock to current stock
            existingItem.stock = currentStock;
            showToast('Quantity updated!', 'success');
        } else {
            showToast('Maximum stock reached', 'error');
            return;
        }
    } else {
        const productInfo = productData[productId];
        const imageUrl = productInfo?.images?.[0] || '/static/img/product/placeholder.jpg';
        
        cart.push({
            id: productId,
            name: productName,
            price: productPrice,
            quantity: 1,
            stock: currentStock, // ✅ Use current stock
            image: imageUrl
        });
        showToast('Added to cart!', 'success');
    }
    
    updateCartDisplay();
    saveCartToStorage();
    pulseCart();
    
    // Expand cart if minimized
    const cartBox = document.getElementById('floatingCart');
    cartBox.classList.remove('cart-minimized');
}

function removeFromCart(productId, fullRemove = false) {
    const itemIndex = cart.findIndex(item => item.id === productId);
    
    if (itemIndex !== -1) {
        if (fullRemove) {
            cart.splice(itemIndex, 1);
        } else {
            if (cart[itemIndex].quantity > 1) {
                cart[itemIndex].quantity--;
            } else {
                cart.splice(itemIndex, 1);
            }
        }
        
        updateCartDisplay();
        saveCartToStorage();
        
        // ✅ IMMEDIATELY SYNC TO DJANGO
        syncCurrentCartToDjango();
    }
}

// ✅ NEW: Sync cart removal to Django
async function syncCurrentCartToDjango() {
    console.log('🔄 Syncing current cart state to Django');
    
    try {
        const csrfToken = getCookie('csrftoken');
        
        if (!csrfToken) {
            console.log('❌ No CSRF token');
            return;
        }
        
        // Clear Django cart first
        await fetch('/cart/clear/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken }
        }).catch(() => console.log('Clear endpoint not found'));
        
        // Add all current items
        for (const item of cart) {
            const formData = new FormData();
            formData.append('quantity', item.quantity);
            formData.append('sync', 'true');
            
            await fetch(`/cart/add/${item.id}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            });
        }
        
        console.log(`✅ Django cart synced with ${cart.length} items`);
        
    } catch (error) {
        console.error('Error syncing to Django:', error);
    }
}

function updateQuantity(productId, change) {
    const item = cart.find(item => item.id === productId);
    
    if (item) {
        const newQuantity = item.quantity + change;
        
        if (newQuantity <= 0) {
            removeFromCart(productId, true);
            showToast('Removed from cart', 'success');
        } else if (newQuantity <= item.stock) {
            item.quantity = newQuantity;
            updateCartDisplay();
            saveCartToStorage();
        } else {
            showToast('Maximum stock reached', 'error');
        }
    }
}

function updateCartDisplay() {
    const cartItems = document.getElementById('cartItems');
    const cartDropzone = document.getElementById('cartDropzone');
    const cartCountBadge = document.getElementById('cartCountBadge');
    const cartTotal = document.getElementById('cartTotal');
    
    // Update count badge
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    if (cartCountBadge) {
        cartCountBadge.textContent = totalItems;
    }
    
    
    // Calculate total
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    if (cartTotal) {
        cartTotal.innerHTML = `${total.toFixed(2)}<small>RM</small>`;
    }
    
    // Show/hide dropzone
    if (cart.length === 0) {
        if (cartDropzone) cartDropzone.style.display = 'block';
        if (cartItems) cartItems.style.display = 'none';
    } else {
        if (cartDropzone) cartDropzone.style.display = 'none';
        if (cartItems) cartItems.style.display = 'flex';
    }
    
    // Render cart items
    if (cartItems) {
        cartItems.innerHTML = '';
        cart.forEach(item => {
            const cartItem = document.createElement('div');
            cartItem.className = 'cart-item';
            cartItem.draggable = true;
            cartItem.dataset.productId = item.id;
            
            // Make cart item draggable for removal
            cartItem.addEventListener('dragstart', function(e) {
                e.dataTransfer.setData('cartitemid', item.id);
                e.dataTransfer.effectAllowed = 'move';
            });
            
            cartItem.innerHTML = `
                <img src="${item.image}" alt="${item.name}" class="cart-item-img">
                <div class="cart-item-info">
                    <p class="cart-item-name">${item.name}</p>
                    <p class="cart-item-price">RM ${item.price.toFixed(2)}</p>
                    <div class="cart-item-controls">
                        <button class="qty-btn-mini" onclick="updateQuantity('${item.id}', -1)">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="5" y1="12" x2="19" y2="12"/>
                            </svg>
                        </button>
                        <span class="qty-display-mini">${item.quantity}</span>
                        <button class="qty-btn-mini" onclick="updateQuantity('${item.id}', 1)">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="12" y1="5" x2="12" y2="19"/>
                                <line x1="5" y1="12" x2="19" y2="12"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <button class="cart-item-remove" onclick="removeFromCart('${item.id}', true)">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            `;
            
            cartItems.appendChild(cartItem);
        });
    }
}

// =====================
// CART STORAGE (FIXED - Clear after payment)
// =====================
function saveCartToStorage() {
    localStorage.setItem('chocolateCart', JSON.stringify(cart));
}

function loadCartFromStorage() {
    const savedCart = localStorage.getItem('chocolateCart');
    if (savedCart) {
        try {
            cart = JSON.parse(savedCart);
            
            // ✅ CRITICAL FIX: Check if payment just completed
            const paymentCompleted = sessionStorage.getItem('payment_completed');
            
            if (paymentCompleted === 'true') {
                console.log('🧹 Payment completed - clearing localStorage cart');
                cart = [];
                localStorage.removeItem('chocolateCart');
                sessionStorage.removeItem('payment_completed');
                sessionStorage.removeItem('cart_cleared_at');
                saveCartToStorage();
                console.log('✅ Cart cleared after payment success');
            } else {
                // ✅ REFRESH STOCK VALUES from productData for each item
                cart = cart.map(item => {
                    const currentProduct = productData[item.id];
                    if (currentProduct) {
                        console.log(`🔄 Updating stock for ${item.name}: ${item.stock} → ${currentProduct.stock}`);
                        return {
                            ...item,
                            stock: currentProduct.stock // Update to current stock
                        };
                    }
                    return item;
                });
                
                // Save updated cart back to localStorage
                saveCartToStorage();
                console.log('✅ Cart stock values refreshed from productData');
            }
        } catch (e) {
            console.error('Error loading cart from storage:', e);
            cart = [];
        }
    }
}

async function clearCart() {
    console.log('🗑️ Clearing cart from products.js');
    
    try {
        // Clear Django cart first
        const csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            await fetch('/cart/clear/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            console.log('✅ Django cart cleared');
        }
    } catch (error) {
        console.log('Note: Django clear endpoint may not exist');
    }
    
    // Then clear localStorage
    cart = [];
    localStorage.removeItem('chocolateCart');
    updateCartDisplay();
    showToast('Cart cleared', 'success');
}

// =====================
// CART TOGGLE
// =====================
function toggleCart() {
    const cartBox = document.getElementById('floatingCart');
    cartBox.classList.toggle('cart-minimized');
}

// =====================
// CART SYNC TO DJANGO
// =====================
async function syncCartToDjango() {
    console.log('🔄 Starting cart sync...', cart);
    
    if (cart.length === 0) {
        console.log('✅ Cart is empty, no sync needed');
        return true;
    }
    
    try {
        let csrfToken = getCookie('csrftoken');
        
        if (!csrfToken) {
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfInput) {
                csrfToken = csrfInput.value;
            }
        }
        
        if (!csrfToken) {
            console.error('❌ CSRF token not found!');
            showToast('Security token missing. Please refresh the page.', 'error');
            return false;
        }
        
        console.log('✅ CSRF token found');
        
        let successCount = 0;
        let failCount = 0;
        
        for (const item of cart) {
            console.log(`📦 Syncing: ${item.name} (ID: ${item.id}, Qty: ${item.quantity})`);
            
            const formData = new FormData();
            formData.append('quantity', item.quantity);
            formData.append('sync', 'true');
            
            try {
                const response = await fetch(`/cart/add/${item.id}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log(`✅ Synced ${item.name}:`, data);
                    successCount++;
                } else {
                    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                    console.error(`❌ Failed to sync ${item.name}:`, errorData);
                    showToast(errorData.error || `Failed to add ${item.name}`, 'error');
                    failCount++;
                }
            } catch (error) {
                console.error(`❌ Network error syncing ${item.name}:`, error);
                failCount++;
            }
        }
        
        console.log(`📊 Sync complete: ${successCount} success, ${failCount} failed`);
        
        if (failCount > 0) {
            showToast(`Some items failed to sync (${failCount}/${cart.length})`, 'error');
            return false;
        }
        
        console.log('✅ All items synced successfully!');
        return true;
        
    } catch (error) {
        console.error('❌ Cart sync error:', error);
        showToast('Failed to sync cart. Please try again.', 'error');
        return false;
    }
}

// =====================
// CHECKOUT
// =====================
async function proceedToCheckout() {
    console.log('🛒 Checkout initiated');
    
    if (cart.length === 0) {
        showToast('Your cart is empty', 'error');
        return;
    }
    
    const isLoggedIn = document.body.dataset.userLoggedIn === 'true';
    
    if (!isLoggedIn) {
        showToast('Please log in to checkout', 'error');
        setTimeout(() => {
            window.location.href = '/login/?next=/checkout/';
        }, 1500);
        return;
    }
    
    showToast('Syncing your cart...', 'success');
    
    try {
        const csrfToken = getCookie('csrftoken');
        await fetch('/cart/clear/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
    } catch (e) {
        console.log('Note: cart clear endpoint not found, continuing...');
    }
    
    const synced = await syncCartToDjango();
    
    if (synced) {
        console.log('✅ Cart synced successfully!');
        showToast('Redirecting to checkout...', 'success');
        
        setTimeout(() => {
            // DON'T clear localStorage - keep cart synced
            // clearCart();
            window.location.href = '/checkout/';
        }, 500);
    } else {
        console.error('❌ Cart sync failed!');
        showToast('Failed to prepare checkout. Please try again.', 'error');
    }
}

// =====================
// PRODUCT MODAL
// =====================
function showProductDetails(productId) {
    const modal = document.getElementById('productModal');
    const product = productData[productId];
    
    if (!product) {
        showToast('Product not found', 'error');
        return;
    }
    
    currentModalProduct = productId;
    
    document.getElementById('modalCategory').textContent = product.category;
    document.getElementById('modalTitle').textContent = product.name;
    document.getElementById('modalPrice').textContent = `RM ${product.price}`;
    document.getElementById('modalDescription').textContent = product.description;
    
    const stockEl = document.getElementById('modalStock');
    if (product.stock > 0) {
        stockEl.textContent = `${product.stock} in stock`;
        stockEl.className = 'modal-stock-jp in-stock';
    } else {
        stockEl.textContent = 'Out of stock';
        stockEl.className = 'modal-stock-jp out-stock';
    }
    
    if (product.images && product.images.length > 0) {
        const mainImage = document.getElementById('modalMainImage');
        mainImage.src = product.images[0];
        
        const thumbnails = document.getElementById('modalThumbnails');
        thumbnails.innerHTML = '';
        
        product.images.forEach((imageUrl, index) => {
            const thumb = document.createElement('div');
            thumb.className = `modal-thumb ${index === 0 ? 'active' : ''}`;
            thumb.innerHTML = `<img src="${imageUrl}" alt="${product.name}">`;
            thumb.onclick = () => switchModalImage(imageUrl, thumb);
            thumbnails.appendChild(thumb);
        });
    }
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function switchModalImage(imageUrl, thumbElement) {
    document.getElementById('modalMainImage').src = imageUrl;
    document.querySelectorAll('.modal-thumb').forEach(t => t.classList.remove('active'));
    thumbElement.classList.add('active');
}

function closeProductModal() {
    const modal = document.getElementById('productModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
    currentModalProduct = null;
}

document.getElementById('modalAddToCart')?.addEventListener('click', function() {
    if (currentModalProduct) {
        const product = productData[currentModalProduct];
        if (product && product.stock > 0) {
            addToCart(currentModalProduct, product.name, parseFloat(product.price), product.stock);
            closeProductModal();
        } else {
            showToast('This item is out of stock', 'error');
        }
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeProductModal();
    }
});

// =====================
// UTILITIES
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

function pulseCart() {
    const cartBox = document.getElementById('floatingCart');
    if (cartBox) {
        cartBox.style.animation = 'pulse 0.5s ease';
        setTimeout(() => {
            cartBox.style.animation = '';
        }, 500);
    }
}

// =====================
// AUTO-SAVE CART
// =====================
setInterval(() => {
    if (cart.length > 0) {
        saveCartToStorage();
    }
}, 30000);

window.addEventListener('beforeunload', function() {
    saveCartToStorage();
});

// =====================
// ANIMATIONS
// =====================
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.03); }
    }
`;
document.head.appendChild(style);