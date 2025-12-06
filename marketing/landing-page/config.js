// ============================================
// Stripe Configuration
// ============================================

/**
 * STRIPE INTEGRATION CONFIGURATION
 *
 * This file contains Stripe configuration for checkout integration.
 *
 * SETUP INSTRUCTIONS:
 *
 * 1. Get your Stripe keys from https://dashboard.stripe.com/apikeys
 *    - Use test keys (pk_test_...) for development
 *    - Use live keys (pk_live_...) for production
 *
 * 2. Create pricing products in Stripe dashboard:
 *    - Free tier: $0/month
 *    - Pro tier: $29/month (recurring subscription)
 *    - Enterprise: Custom pricing (contact sales)
 *
 * 3. Copy price IDs from Stripe dashboard and paste below
 *
 * 4. Configure your backend API endpoint (default: /v1/billing/create-checkout-session)
 *
 * 5. Set up webhook endpoint in Stripe dashboard:
 *    URL: https://your-domain.com/v1/billing/webhook
 *    Events: customer.subscription.*, invoice.payment_*
 *
 * SECURITY:
 * - NEVER commit live keys to version control
 * - Use environment variables or secure config management in production
 * - Publishable keys (pk_*) are safe to expose in frontend
 * - Secret keys (sk_*) must ONLY be used server-side
 */

const STRIPE_CONFIG = {
    // Stripe Publishable Key (safe to expose in frontend)
    // Replace with your actual key or load from environment
    publishableKey: window.STRIPE_PUBLISHABLE_KEY || 'pk_test_YOUR_PUBLISHABLE_KEY_HERE',

    // Stripe Price IDs (from Stripe dashboard)
    priceIds: {
        free: 'price_free',
        pro: 'price_pro_monthly',
        enterprise: 'price_enterprise_custom'
    },

    // Backend API endpoint for creating checkout sessions
    checkoutEndpoint: '/v1/billing/create-checkout-session',

    // Success and cancel URLs (will be appended with session_id)
    successUrl: window.location.origin + '/success',
    cancelUrl: window.location.origin + '/#pricing',

    // Test mode indicator
    isTestMode: function() {
        return this.publishableKey.startsWith('pk_test_');
    }
};

// Export for use in script.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = STRIPE_CONFIG;
}

// Make available globally
window.STRIPE_CONFIG = STRIPE_CONFIG;

// Log configuration status (helps with debugging)
console.log('%c[Stripe Config]', 'color: #635bff; font-weight: bold;');
console.log('Test Mode:', STRIPE_CONFIG.isTestMode());
console.log('Endpoint:', STRIPE_CONFIG.checkoutEndpoint);
if (STRIPE_CONFIG.isTestMode()) {
    console.log('%cUsing Stripe TEST mode - no real charges will be made', 'color: #ffa726; background: #fff3e0; padding: 4px 8px;');
}
