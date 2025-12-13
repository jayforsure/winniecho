// Smooth scroll animations
document.addEventListener('DOMContentLoaded', function() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.15,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    // Observe section headers
    const sectionHeaders = document.querySelectorAll('.section-header');
    sectionHeaders.forEach(header => {
        observer.observe(header);
    });

    // Observe about content
    const aboutContent = document.querySelector('.about-content');
    if (aboutContent) {
        observer.observe(aboutContent);
    }

    // Observe each room card
    const roomCards = document.querySelectorAll('.room-card');
    roomCards.forEach(card => {
        observer.observe(card);
    });

    // Observe services grid
    const servicesGrid = document.querySelector('.services-grid');
    if (servicesGrid) {
        observer.observe(servicesGrid);
    }

    // Observe quick link cards
    const quickLinkCards = document.querySelectorAll('.quick-link-card');
    quickLinkCards.forEach((card, index) => {
        const cardObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('visible');
                    }, index * 200);
                }
            });
        }, observerOptions);
        cardObserver.observe(card);
    });

    // Observe FAQ items with stagger
    const faqItems = document.querySelectorAll('.faq-preview-item');
    faqItems.forEach((item, index) => {
        const faqObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('visible');
                    }, index * 150); // Stagger animation
                }
            });
        }, observerOptions);
        faqObserver.observe(item);
    });

    // Smooth parallax effect for videos and images
    let ticking = false;
    
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const scrolled = window.pageYOffset;
                
                // Parallax for hero video
                const heroVideo = document.querySelector('.elevator-video-container');
                if (heroVideo) {
                    heroVideo.style.transform = `translateY(${scrolled * 0.5}px)`;
                }

                // Parallax for about video
                const aboutVideo = document.querySelector('.about-content video');
                if (aboutVideo) {
                    const aboutSection = aboutVideo.closest('.about-section');
                    const aboutRect = aboutSection.getBoundingClientRect();
                    if (aboutRect.top < window.innerHeight && aboutRect.bottom > 0) {
                        const progress = (window.innerHeight - aboutRect.top) / (window.innerHeight + aboutRect.height);
                        aboutVideo.style.transform = `translateY(${progress * 100}px)`;
                    }
                }

                ticking = false;
            });
            ticking = true;
        }
    });

    // Add smooth hover effects for room cards
    roomCards.forEach(card => {
        const image = card.querySelector('.room-image img');
        
        card.addEventListener('mouseenter', () => {
            image.style.transform = 'scale(1.08)';
        });
        
        card.addEventListener('mouseleave', () => {
            image.style.transform = 'scale(1)';
        });
    });
});

// Navbar scroll effect
window.addEventListener("scroll", function(){
    const navbar = document.getElementById("navbar");
    const scrollPosition = window.scrollY;

    if (scrollPosition > 100) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});