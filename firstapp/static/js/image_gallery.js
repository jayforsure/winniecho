// Product Image Gallery

document.addEventListener('DOMContentLoaded', function() {
    initializeImageGallery();
});

function initializeImageGallery() {
    const mainImage = document.getElementById('main-product-image');
    const thumbnails = document.querySelectorAll('.thumbnail-image');
    
    if (!mainImage || thumbnails.length === 0) return;
    
    // Thumbnail click handlers
    thumbnails.forEach((thumbnail, index) => {
        thumbnail.addEventListener('click', function() {
            // Remove active class from all thumbnails
            thumbnails.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked thumbnail
            this.classList.add('active');
            
            // Update main image
            const newSrc = this.dataset.fullImage;
            mainImage.src = newSrc;
            
            // Add fade effect
            mainImage.style.opacity = '0';
            setTimeout(() => {
                mainImage.style.opacity = '1';
            }, 100);
        });
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        const activeThumbnail = document.querySelector('.thumbnail-image.active');
        const currentIndex = Array.from(thumbnails).indexOf(activeThumbnail);
        
        if (e.key === 'ArrowLeft' && currentIndex > 0) {
            thumbnails[currentIndex - 1].click();
        } else if (e.key === 'ArrowRight' && currentIndex < thumbnails.length - 1) {
            thumbnails[currentIndex + 1].click();
        }
    });
    
    // Touch swipe for mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    mainImage.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    mainImage.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
    
    function handleSwipe() {
        const activeThumbnail = document.querySelector('.thumbnail-image.active');
        const currentIndex = Array.from(thumbnails).indexOf(activeThumbnail);
        
        if (touchEndX < touchStartX - 50 && currentIndex < thumbnails.length - 1) {
            // Swipe left - next image
            thumbnails[currentIndex + 1].click();
        }
        
        if (touchEndX > touchStartX + 50 && currentIndex > 0) {
            // Swipe right - previous image
            thumbnails[currentIndex - 1].click();
        }
    }
}

// Zoom functionality
function initializeImageZoom() {
    const mainImage = document.getElementById('main-product-image');
    if (!mainImage) return;
    
    mainImage.addEventListener('click', function() {
        this.classList.toggle('zoomed');
    });
}

initializeImageZoom();