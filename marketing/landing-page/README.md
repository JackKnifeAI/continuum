# JackKnife.io Landing Page

**Decentralized AI Infrastructure for the Sovereign Web**

## Overview

This is the official landing page for JackKnife.io - a revolutionary platform providing enterprise-grade AI coordination through federated MCP (Model Context Protocol) servers. Built with vanilla HTML, CSS, and JavaScript for maximum performance and zero dependencies.

## Features

### Design
- **Twilight Aesthetic**: Dark theme with aurora-inspired gradients (purples, blues, cyans)
- **Glass Morphism**: Frosted glass effects with subtle transparency
- **Responsive Design**: Mobile-first approach, works on all devices
- **Smooth Animations**: Intersection observer-based animations for performance
- **Accessibility**: WCAG AA compliant, keyboard navigation support

### Sections
1. **Hero**: Eye-catching header with animated stats and gradient text
2. **Problem/Solution**: Side-by-side comparison of centralized vs. JackKnife approach
3. **Features**: 6-card grid showcasing core capabilities
4. **Code Examples**: Interactive tabs with syntax highlighting and copy buttons
5. **Pricing**: 3-tier pricing table (Developer, Professional, Enterprise)
6. **Testimonials**: Customer quotes with avatar placeholders
7. **CTA**: Call-to-action with sign-up links
8. **Footer**: Links, social media, attribution

### Interactive Features
- Smooth scrolling navigation
- Animated counter statistics
- Syntax highlighting for code blocks
- Copy-to-clipboard functionality
- Tab switching for code examples
- Mobile menu toggle
- Scroll-based fade-in animations
- Floating particle field
- Easter egg: π×φ constant (click to reveal)

## File Structure

```
landing-page/
├── index.html          # Main HTML structure
├── styles.css          # Twilight-themed CSS with glass morphism
├── script.js           # Interactive features and animations
├── assets/
│   ├── DESIGN_SPECIFICATIONS.md  # Complete design guide
│   ├── images/         # Logo, illustrations, backgrounds (to be created)
│   └── icons/          # Feature icons, favicon set (to be created)
└── README.md           # This file
```

## Quick Start

### Local Development

1. **Clone or navigate to the directory**:
   ```bash
   cd ~/Projects/continuum/marketing/landing-page
   ```

2. **Serve locally** (choose one method):

   **Option A: Python Simple Server**
   ```bash
   python3 -m http.server 8000
   ```

   **Option B: Node.js http-server**
   ```bash
   npx http-server -p 8000
   ```

   **Option C: PHP Built-in Server**
   ```bash
   php -S localhost:8000
   ```

3. **Open in browser**:
   ```
   http://localhost:8000
   ```

### Deployment

#### GitHub Pages
```bash
# From continuum repo root
git add marketing/landing-page/
git commit -m "Add JackKnife.io landing page"
git push origin main

# Enable GitHub Pages in repo settings → Pages → Source: main branch
# Site will be available at: https://jackknife.github.io/continuum/marketing/landing-page/
```

#### Netlify
```bash
# Drag and drop the landing-page/ folder to Netlify
# Or connect GitHub repo and set build directory to marketing/landing-page/
```

#### Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd landing-page/
vercel
```

#### Custom Domain
Point your DNS to the deployed site:
```
A Record: jackknife.io → [deployment IP]
CNAME: www.jackknife.io → [deployment URL]
```

## Customization

### Colors

All colors are defined as CSS variables in `styles.css`:

```css
:root {
    --twilight-deep: #0a0a1f;
    --aurora-purple: #8b5cf6;
    --aurora-blue: #3b82f6;
    /* ... more colors */
}
```

To change the color scheme, modify these variables.

### Content

#### Update Tagline
Edit the `<h1>` in the hero section:
```html
<h1 class="hero-title">
    <span class="gradient-text">Your New Tagline</span>
</h1>
```

#### Add New Features
Add feature cards to the `.features-grid`:
```html
<div class="feature-card">
    <div class="feature-icon">🎯</div>
    <h3>Your Feature</h3>
    <p>Description here...</p>
</div>
```

#### Update Pricing
Modify the `.pricing-card` elements with your pricing tiers.

#### Add Testimonials
Add real testimonials by updating the `.testimonial-card` elements.

### Assets

See `assets/DESIGN_SPECIFICATIONS.md` for complete design requirements.

**Priority assets to create**:
1. Logo (SVG) - Replace ⚡ emoji with actual logo
2. Favicon set - Generate from logo icon
3. Feature icons - Replace emoji placeholders with custom SVG icons
4. OG/social images - For social media sharing

## Performance

### Optimization Checklist
- ✅ No external frameworks (vanilla JS)
- ✅ Minimal CSS (no preprocessor needed)
- ✅ Font subsetting (Google Fonts with display=swap)
- ✅ Lazy loading for images (implemented)
- ✅ Intersection observers for animations
- ⚠️ Image optimization (pending asset creation)
- ⚠️ SVG minification (pending asset creation)

### Lighthouse Scores (Target)
- **Performance**: 95+
- **Accessibility**: 100
- **Best Practices**: 100
- **SEO**: 100

## Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions
- Mobile browsers: iOS Safari 12+, Chrome Android 90+

**Progressive Enhancement**:
- Works without JavaScript (base content visible)
- Graceful degradation for older browsers
- Respects `prefers-reduced-motion`

## Easter Eggs

1. **π×φ Constant**: Click the "Edge constant: 5.083203692" in the pricing section
2. **Console Art**: Open browser console for ASCII art and messages
3. **Particle Field**: Subtle floating particles in hero background

## SEO & Meta Tags

Already included in `index.html`:
- Open Graph tags for social sharing
- Twitter Card tags
- Semantic HTML5 structure
- Descriptive meta description

**To add** (when domain is live):
```html
<meta property="og:image" content="https://jackknife.io/assets/og-image.png">
<link rel="canonical" href="https://jackknife.io">
```

## Analytics Integration

Placeholder analytics tracking is in `script.js`. To integrate:

### Google Analytics
```html
<!-- Add before </head> -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Plausible (Privacy-focused)
```html
<script defer data-domain="jackknife.io" src="https://plausible.io/js/script.js"></script>
```

Event tracking is already implemented - just uncomment the gtag calls in `script.js`.

## Contributing

This landing page is part of the JackKnife/Continuum project.

### Making Changes
1. Edit files locally
2. Test thoroughly across browsers
3. Validate HTML: https://validator.w3.org/
4. Check accessibility: https://wave.webaim.org/
5. Test performance: Lighthouse in Chrome DevTools

### Design Assets
If you're a designer, see `assets/DESIGN_SPECIFICATIONS.md` for asset requirements.

## Technology Stack

- **HTML5**: Semantic markup
- **CSS3**: Grid, Flexbox, Custom Properties, Animations
- **JavaScript (ES6+)**: Intersection Observer, Clipboard API, Fetch API
- **Fonts**: Inter (sans-serif), JetBrains Mono (monospace) from Google Fonts

**Zero dependencies. Zero build process. Pure web standards.**

## Roadmap

### Phase 1 (Current)
- ✅ Core HTML structure
- ✅ Twilight CSS theme
- ✅ Interactive JavaScript features
- ✅ Responsive design
- ⚠️ Design assets (in progress)

### Phase 2 (Next)
- [ ] Create all design assets (logo, icons, illustrations)
- [ ] Add real testimonials
- [ ] Integrate analytics
- [ ] Set up contact form with backend
- [ ] Add blog section integration

### Phase 3 (Future)
- [ ] Interactive product demo
- [ ] Video walkthrough
- [ ] Customer case studies
- [ ] Live chat integration
- [ ] A/B testing variants

## Support

- **Website**: https://jackknife.io (pending deployment)
- **Email**: hello@jackknife.io
- **GitHub**: https://github.com/JackKnifeAI/continuum
- **Twitter**: @JackKnifeAI (placeholder)

## License

Copyright © 2025 JackKnife.io

This landing page is part of the Continuum project. See main project repository for license details.

---

**Built at the twilight boundary** ⚡

*Operating where chaos meets order: π × φ = 5.083203692315260*
