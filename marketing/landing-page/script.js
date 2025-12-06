// ============================================
// JackKnife Landing Page - Interactive Features
// ============================================

// ============================================
// Smooth Scrolling
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offset = 80; // Account for fixed nav
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ============================================
    // Animated Counters
    // ============================================
    const animateCounter = (element, target, suffix = '') => {
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;

        const updateCounter = () => {
            current += increment;
            if (current < target) {
                element.textContent = Math.floor(current).toLocaleString() + suffix;
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target.toLocaleString() + suffix;
            }
        };

        updateCounter();
    };

    // Intersection Observer for counter animation
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.dataset.animated) {
                const target = parseFloat(entry.target.dataset.target);
                const suffix = entry.target.textContent.includes('%') ? '%' : '';
                animateCounter(entry.target, target, suffix);
                entry.target.dataset.animated = 'true';
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.stat-value').forEach(stat => {
        counterObserver.observe(stat);
    });

    // ============================================
    // Code Syntax Highlighting (Simple)
    // ============================================
    const highlightCode = () => {
        document.querySelectorAll('pre code').forEach(block => {
            let html = block.innerHTML;

            // Comments
            html = html.replace(/(#.*$)/gm, '<span style="color: #6b7280;">$1</span>');

            // Strings
            html = html.replace(/(".*?"|'.*?')/g, '<span style="color: #10b981;">$1</span>');

            // Keywords (bash, yaml, python, json)
            const keywords = [
                'npm', 'install', 'cd', 'from', 'import', 'async', 'def', 'await', 'return',
                'if', 'else', 'for', 'while', 'class', 'function', 'const', 'let', 'var'
            ];
            keywords.forEach(keyword => {
                const regex = new RegExp(`\\b(${keyword})\\b`, 'g');
                html = html.replace(regex, '<span style="color: #8b5cf6;">$1</span>');
            });

            // Numbers
            html = html.replace(/\b(\d+)\b/g, '<span style="color: #f59e0b;">$1</span>');

            // URLs
            html = html.replace(/(https?:\/\/[^\s<]+)/g, '<span style="color: #06b6d4;">$1</span>');

            // YAML keys
            html = html.replace(/^(\s*)([a-zA-Z_]+):/gm, '$1<span style="color: #ec4899;">$2</span>:');

            block.innerHTML = html;
        });
    };

    highlightCode();

    // ============================================
    // Code Copy Buttons
    // ============================================
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const targetId = button.dataset.target;
            const codeBlock = document.getElementById(targetId);

            if (codeBlock) {
                const code = codeBlock.textContent;

                try {
                    await navigator.clipboard.writeText(code);

                    // Visual feedback
                    const originalText = button.querySelector('.copy-text').textContent;
                    button.classList.add('copied');
                    button.querySelector('.copy-text').textContent = 'Copied!';
                    button.querySelector('.copy-icon').textContent = '✓';

                    setTimeout(() => {
                        button.classList.remove('copied');
                        button.querySelector('.copy-text').textContent = originalText;
                        button.querySelector('.copy-icon').textContent = '📋';
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy:', err);
                    button.querySelector('.copy-text').textContent = 'Failed';
                    setTimeout(() => {
                        button.querySelector('.copy-text').textContent = 'Copy';
                    }, 2000);
                }
            }
        });
    });

    // ============================================
    // Tab Switching
    // ============================================
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            // Remove active class from all buttons and content
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const content = document.getElementById(tabName);
            if (content) {
                content.classList.add('active');
            }
        });
    });

    // ============================================
    // Mobile Menu Toggle
    // ============================================
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            mobileMenuToggle.classList.toggle('active');

            // Animate hamburger to X
            const spans = mobileMenuToggle.querySelectorAll('span');
            if (mobileMenuToggle.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translateY(8px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translateY(-8px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }

    // ============================================
    // Scroll-based Animations
    // ============================================
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                fadeObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    // Observe elements for fade-in animation
    document.querySelectorAll('.feature-card, .pricing-card, .testimonial-card, .comparison-card').forEach(el => {
        fadeObserver.observe(el);
    });

    // ============================================
    // Particle Field Animation
    // ============================================
    const createParticles = () => {
        const particleField = document.querySelector('.particle-field');
        if (!particleField) return;

        // Create floating particles
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'absolute';
            particle.style.width = `${Math.random() * 4 + 1}px`;
            particle.style.height = particle.style.width;
            particle.style.background = 'rgba(139, 92, 246, 0.5)';
            particle.style.borderRadius = '50%';
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.animation = `float ${Math.random() * 10 + 10}s linear infinite`;
            particle.style.animationDelay = `${Math.random() * 5}s`;

            particleField.appendChild(particle);
        }
    };

    // Add float animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0%, 100% {
                transform: translate(0, 0);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translate(${Math.random() * 200 - 100}px, ${Math.random() * 200 - 100}px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    createParticles();

    // ============================================
    // Nav Background on Scroll
    // ============================================
    let lastScroll = 0;
    const nav = document.querySelector('.nav');

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            nav.style.background = 'rgba(10, 10, 31, 0.95)';
            nav.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
        } else {
            nav.style.background = 'rgba(10, 10, 31, 0.8)';
            nav.style.boxShadow = 'none';
        }

        lastScroll = currentScroll;
    });

    // ============================================
    // Easter Egg: π×φ Constant
    // ============================================
    const easterEgg = document.querySelector('.constant-value');
    if (easterEgg) {
        let clickCount = 0;
        easterEgg.addEventListener('click', () => {
            clickCount++;

            if (clickCount === 1) {
                easterEgg.textContent = '5.083203692315260';
                easterEgg.style.color = '#8b5cf6';
            }

            if (clickCount === 2) {
                easterEgg.textContent = 'π × φ = Edge of Chaos';
                easterEgg.style.background = 'linear-gradient(135deg, #8b5cf6, #3b82f6)';
                easterEgg.style.webkitBackgroundClip = 'text';
                easterEgg.style.webkitTextFillColor = 'transparent';
            }

            if (clickCount === 3) {
                easterEgg.innerHTML = '⚡ Operating in the twilight ⚡';
                easterEgg.style.webkitTextFillColor = '#8b5cf6';
                easterEgg.style.animation = 'pulse 2s ease-in-out infinite';
            }

            if (clickCount >= 4) {
                // Reset
                clickCount = 0;
                easterEgg.textContent = '5.083203692';
                easterEgg.style.background = 'none';
                easterEgg.style.webkitTextFillColor = '#8b5cf6';
                easterEgg.style.animation = 'none';
            }
        });

        // Subtle hint on hover
        easterEgg.addEventListener('mouseenter', () => {
            easterEgg.style.cursor = 'pointer';
            easterEgg.title = 'The edge constant... click to explore';
        });
    }

    // ============================================
    // Performance Optimization: Lazy Load
    // ============================================
    if ('IntersectionObserver' in window) {
        const lazyObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        lazyObserver.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            lazyObserver.observe(img);
        });
    }

    // ============================================
    // Form Validation (if contact form added later)
    // ============================================
    const validateEmail = (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    };

    // ============================================
    // Analytics Event Tracking (placeholder)
    // ============================================
    const trackEvent = (category, action, label) => {
        // Placeholder for analytics integration
        console.log('Event tracked:', { category, action, label });

        // Example: Google Analytics integration
        // if (typeof gtag !== 'undefined') {
        //     gtag('event', action, {
        //         event_category: category,
        //         event_label: label
        //     });
        // }
    };

    // Track CTA clicks
    document.querySelectorAll('.btn-primary, .btn-primary-large').forEach(btn => {
        btn.addEventListener('click', () => {
            trackEvent('CTA', 'click', btn.textContent.trim());
        });
    });

    // Track code copies
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            trackEvent('Code', 'copy', btn.dataset.target);
        });
    });

    // ============================================
    // Accessibility Enhancements
    // ============================================

    // Skip to main content link (add to HTML if needed)
    const skipLink = document.createElement('a');
    skipLink.href = '#features';
    skipLink.textContent = 'Skip to main content';
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 0;
        background: #8b5cf6;
        color: white;
        padding: 8px;
        text-decoration: none;
        z-index: 10000;
    `;
    skipLink.addEventListener('focus', () => {
        skipLink.style.top = '0';
    });
    skipLink.addEventListener('blur', () => {
        skipLink.style.top = '-40px';
    });
    document.body.insertBefore(skipLink, document.body.firstChild);

    // Keyboard navigation for tabs
    document.querySelectorAll('.tab-button').forEach((button, index, buttons) => {
        button.addEventListener('keydown', (e) => {
            let newIndex;

            switch (e.key) {
                case 'ArrowLeft':
                    newIndex = index > 0 ? index - 1 : buttons.length - 1;
                    buttons[newIndex].click();
                    buttons[newIndex].focus();
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                    newIndex = index < buttons.length - 1 ? index + 1 : 0;
                    buttons[newIndex].click();
                    buttons[newIndex].focus();
                    e.preventDefault();
                    break;
            }
        });
    });

    // ============================================
    // Console Easter Egg
    // ============================================
    const consoleStyle = [
        'color: #8b5cf6',
        'font-size: 16px',
        'font-weight: bold',
        'text-shadow: 0 0 10px rgba(139, 92, 246, 0.5)'
    ].join(';');

    console.log('%cJackKnife.io', consoleStyle);
    console.log('%c⚡ Operating at the twilight boundary', 'color: #3b82f6; font-size: 12px;');
    console.log('%cπ × φ = 5.083203692315260', 'color: #10b981; font-size: 10px; font-family: monospace;');
    console.log('%cDecentralized AI infrastructure for the sovereign web', 'color: #94a3b8; font-size: 10px;');
    console.log('\n%cInterested in joining the revolution? hello@jackknife.io', 'color: #ec4899;');

    // ============================================
    // Performance Monitoring
    // ============================================
    if ('PerformanceObserver' in window) {
        try {
            // Monitor largest contentful paint
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                console.log('LCP:', lastEntry.renderTime || lastEntry.loadTime);
            });
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

            // Monitor first input delay
            const fidObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry) => {
                    console.log('FID:', entry.processingStart - entry.startTime);
                });
            });
            fidObserver.observe({ entryTypes: ['first-input'] });
        } catch (e) {
            // Performance monitoring not supported
        }
    }

    // ============================================
    // Stripe Checkout Integration
    // ============================================

    // Get config from config.js
    const config = window.STRIPE_CONFIG;

    // Initialize Stripe with publishable key
    let stripe = null;
    if (typeof Stripe !== 'undefined') {
        try {
            stripe = Stripe(config.publishableKey);
            console.log('%c✓ Stripe initialized', 'color: #635bff; font-weight: bold;');
        } catch (e) {
            console.error('Failed to initialize Stripe:', e);
            console.warn('Make sure to configure STRIPE_PUBLISHABLE_KEY in config.js');
        }
    }

    // Handle pricing button clicks
    document.querySelectorAll('[data-tier]').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const tier = button.dataset.tier;

            // Track the click
            trackEvent('Pricing', 'click', tier);

            if (tier === 'free') {
                // For free tier, redirect to GitHub
                window.location.href = 'https://github.com/JackKnifeAI/continuum';
                return;
            }

            if (tier === 'pro') {
                // Initialize Stripe checkout for Pro tier
                await initiateStripeCheckout(tier);
            }

            // Enterprise handled by mailto link in HTML
        });
    });

    async function initiateStripeCheckout(tier) {
        // Check if Stripe is initialized
        if (!stripe) {
            alert('Payment system not configured. Please contact support or check back later.');
            console.error('Stripe not initialized. Configure publishable key in config.js');
            return;
        }

        // Show loading state
        const button = document.querySelector(`[data-tier="${tier}"]`);
        const originalText = button.textContent;
        button.textContent = 'Loading...';
        button.disabled = true;

        try {
            console.log(`Initiating Stripe checkout for tier: ${tier}`);

            // Call backend to create checkout session
            const response = await fetch(config.checkoutEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // In production, include API key if required
                    // 'X-API-Key': 'your-api-key'
                },
                body: JSON.stringify({
                    tier: tier,
                    success_url: config.successUrl,
                    cancel_url: config.cancelUrl,
                    // customer_email: 'user@example.com'  // Optional: pre-fill email
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create checkout session');
            }

            const session = await response.json();

            // Redirect to Stripe Checkout
            const result = await stripe.redirectToCheckout({
                sessionId: session.session_id
            });

            if (result.error) {
                throw new Error(result.error.message);
            }

        } catch (error) {
            console.error('Checkout error:', error);

            // User-friendly error message
            let errorMessage = 'Unable to start checkout. ';
            if (error.message.includes('not configured') || error.message.includes('not yet implemented')) {
                errorMessage += 'Payment system is being configured. Please contact sales@jackknife.io for early access.';
            } else {
                errorMessage += 'Please try again or contact support@jackknife.io';
            }

            alert(errorMessage);
        } finally {
            // Restore button state
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    // ============================================
    // Ready State
    // ============================================
    console.log('%c✓ JackKnife landing page initialized', 'color: #10b981; font-weight: bold;');
});
