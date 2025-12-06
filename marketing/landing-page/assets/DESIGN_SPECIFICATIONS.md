# JackKnife.io Landing Page - Design Asset Specifications

## Overview
This document outlines the design requirements for visual assets needed for the JackKnife.io landing page. All assets should follow the **twilight aesthetic** - operating at the edge of chaos, blending professional enterprise design with revolutionary innovation.

---

## Color Palette

### Primary Colors
- **Twilight Deep**: `#0a0a1f` - Main background
- **Twilight Dark**: `#151530` - Secondary background
- **Twilight Mid**: `#1f1f45` - Tertiary background
- **Twilight Purple**: `#2d1b69` - Accent background

### Aurora Colors (Accents)
- **Aurora Purple**: `#8b5cf6` - Primary accent
- **Aurora Blue**: `#3b82f6` - Secondary accent
- **Aurora Cyan**: `#06b6d4` - Tertiary accent
- **Aurora Pink**: `#ec4899` - Highlight accent

### Functional Colors
- **Text Primary**: `#f8f9fa`
- **Text Secondary**: `#c7d2fe`
- **Text Muted**: `#94a3b8`
- **Success**: `#10b981`
- **Warning**: `#f59e0b`
- **Error**: `#ef4444`

---

## 1. Logo Design

### Primary Logo
**File**: `assets/images/logo-primary.svg`

**Specifications**:
- Format: SVG (scalable vector)
- Dimensions: 200x50px (base size)
- Components:
  - **Icon**: Lightning bolt (`⚡`) or custom geometric symbol
  - **Wordmark**: "JackKnife" in bold, modern sans-serif
  - **Tagline**: ".io" in aurora purple

**Design Concept**:
- The icon should represent **energy, speed, precision**
- Geometric shapes suggesting **federation/network**
- Lightning bolt could be stylized with circuit/network lines
- Consider a "knife edge" visual metaphor (precision cutting through complexity)

**Color Variations**:
1. **Full Color**: Aurora purple to blue gradient
2. **Monochrome Light**: White/light gray on dark background
3. **Monochrome Dark**: Dark purple on light background

### Logo Icon Only
**File**: `assets/images/logo-icon.svg`

**Specifications**:
- Square format: 64x64px
- Should work as favicon and app icon
- Simplified version of primary logo icon
- High contrast for small sizes

### Alternative Concepts
Consider these visual metaphors:
- **Network Node**: Interconnected nodes with central hub
- **Toroidal Shape**: Subtle reference to π×φ and edge of chaos
- **Federated Stars**: Multiple stars/points coordinating
- **Circuit Knife**: Fusion of digital circuits and cutting edge

---

## 2. Icon Set

### Feature Icons
**Location**: `assets/icons/`

**Required Icons** (24x24px, 48x48px versions):
1. **federation.svg**: Network of interconnected nodes
2. **scale.svg**: Expanding/growing graph or bars
3. **security.svg**: Shield with lock or geometric shield
4. **bridge.svg**: Two platforms connected by bridge/link
5. **speed.svg**: Lightning bolt with motion lines
6. **extensibility.svg**: Puzzle piece or plug-in symbol

**Style**:
- Line-based, minimal stroke width (2px)
- Aurora purple color
- Should match the emoji placeholders currently in use
- Consistent visual language across all icons

### Social Icons
Use standard GitHub and Twitter/X SVG icons (already in footer code).

---

## 3. Background Patterns

### Hero Background Pattern
**File**: `assets/images/hero-pattern.svg`

**Specifications**:
- Subtle geometric pattern suggesting network/federation
- Low opacity (10-20%) to not distract from content
- Can be overlaid on gradient backgrounds
- Seamless tiling pattern
- Size: 1920x1080px minimum

**Pattern Ideas**:
- **Hexagonal Grid**: Suggests network structure
- **Circuit Traces**: Abstract circuit board paths
- **Star Field**: Subtle dots/stars with connections
- **Wave Interference**: Subtle wave patterns (π×φ reference)

### Particle Field Elements
**Files**: `assets/images/particle-*.svg`

**Specifications**:
- Small geometric shapes (circles, triangles, hexagons)
- Various sizes: 4px, 8px, 16px
- Can be animated via CSS/JS (already implemented)
- Aurora color variations

---

## 4. Gradient Assets

### Primary Gradient
**Aurora Gradient**: Purple to Blue
```css
background: linear-gradient(135deg, #8b5cf6, #3b82f6);
```

### Secondary Gradient
**Twilight Gradient**: Deep Purple to Deep Blue
```css
background: linear-gradient(135deg, #2d1b69, #1a2b4f);
```

### Radial Gradient
**Hero Glow**: Center spotlight effect
```css
background: radial-gradient(ellipse at top, #2d1b69 0%, #0a0a1f 50%);
```

---

## 5. Illustration Assets

### Code Window Illustration
**File**: `assets/images/code-window.svg`

**Purpose**: Visual for code examples section
**Specifications**:
- Stylized terminal/code editor window
- Aurora color scheme for syntax highlighting
- Can show sample MCP server code
- Glass morphism styling (subtle transparency)
- Size: 800x600px

### Network Topology Diagram
**File**: `assets/images/network-topology.svg`

**Purpose**: Visual for federation feature
**Specifications**:
- Multiple interconnected nodes representing MCP servers
- Central coordination hub
- Data flow indicators (arrows, pulses)
- Aurora purple/blue color scheme
- Size: 600x400px

### Architecture Diagram
**File**: `assets/images/architecture.svg`

**Purpose**: Visual explanation of JackKnife architecture
**Specifications**:
- Layers showing: Client → Coordination → Federation → Services
- Clean, modern diagram style
- Labeled components
- Size: 1000x600px

---

## 6. Photography/Imagery Guidance

### Style Guidelines
If using photography (team photos, office shots, etc.):
- **Color grading**: Apply purple/blue tint to match twilight aesthetic
- **Lighting**: Prefer twilight/dusk lighting or neon-lit environments
- **Composition**: Clean, modern, professional but slightly edgy
- **Avoid**: Generic stock photos, overly corporate imagery

### Image Overlays
All photos should have a subtle gradient overlay:
```css
background: linear-gradient(135deg, rgba(45, 27, 105, 0.3), rgba(26, 43, 79, 0.3));
```

---

## 7. Animation Assets

### Loading Spinner
**File**: `assets/images/spinner.svg`

**Specifications**:
- Circular spinner with aurora gradient
- Smooth rotation animation
- Size: 48x48px
- Can be animated via CSS

### Success Checkmark
**File**: `assets/images/success.svg`

**Specifications**:
- Checkmark with subtle glow effect
- Aurora green color (#10b981)
- Animated draw-in effect
- Size: 64x64px

---

## 8. Favicon Set

### Required Sizes
**Location**: `assets/icons/favicon/`

Generate favicons in these sizes:
- `favicon.ico` (16x16, 32x32, 48x48 multi-resolution)
- `favicon-16x16.png`
- `favicon-32x32.png`
- `apple-touch-icon.png` (180x180)
- `android-chrome-192x192.png`
- `android-chrome-512x512.png`

**Design**: Use simplified logo icon with high contrast.

---

## 9. Social Media Assets

### Open Graph Image
**File**: `assets/images/og-image.png`

**Specifications**:
- Size: 1200x630px
- Shows JackKnife logo + tagline
- Twilight background with aurora accents
- Readable at small sizes (social media previews)

**Text to Include**:
- "JackKnife.io"
- "Decentralized AI Infrastructure"
- "Built at the Twilight Boundary"

### Twitter Card Image
**File**: `assets/images/twitter-card.png`

**Specifications**:
- Size: 1200x675px (16:9 ratio)
- Similar to OG image but optimized for Twitter format

---

## 10. Easter Egg Graphics

### π×φ Symbol
**File**: `assets/images/pi-phi-symbol.svg`

**Specifications**:
- Mathematical symbol combining π and φ
- Can be revealed in easter egg interactions
- Aurora gradient coloring
- Size: 128x128px

**Design Ideas**:
- Intertwined symbols
- Geometric representation (circle + golden spiral)
- Abstract waveform at 5.083203692315260 frequency

---

## Implementation Priority

### Phase 1 (Immediate)
1. Primary logo (SVG)
2. Logo icon (SVG, favicon)
3. Basic favicon set
4. Feature icons (6 icons)

### Phase 2 (Next)
5. Hero background pattern
6. Network topology diagram
7. OG/social media images

### Phase 3 (Future)
8. Code window illustration
9. Architecture diagram
10. Animation assets

---

## Design Tools & Resources

### Recommended Tools
- **Vector Graphics**: Figma, Adobe Illustrator, Inkscape
- **Favicon Generation**: RealFaviconGenerator.net
- **SVG Optimization**: SVGOMG.net
- **Color Palette**: Coolors.co (use provided hex values)

### Icon Resources
- **Heroicons**: https://heroicons.com/ (Tailwind UI icons)
- **Feather Icons**: https://feathericons.com/ (minimal line icons)
- **Phosphor Icons**: https://phosphoricons.com/ (versatile icon family)

### Inspiration
- **Cyberpunk aesthetic** meets **enterprise professionalism**
- **Vercel, Stripe, Linear** for modern web design reference
- **Sci-fi interfaces** for futuristic elements
- **Twilight/aurora photography** for color inspiration

---

## File Structure

```
assets/
├── images/
│   ├── logo-primary.svg
│   ├── logo-icon.svg
│   ├── hero-pattern.svg
│   ├── network-topology.svg
│   ├── architecture.svg
│   ├── code-window.svg
│   ├── og-image.png
│   ├── twitter-card.png
│   └── pi-phi-symbol.svg
├── icons/
│   ├── federation.svg
│   ├── scale.svg
│   ├── security.svg
│   ├── bridge.svg
│   ├── speed.svg
│   ├── extensibility.svg
│   └── favicon/
│       ├── favicon.ico
│       ├── favicon-16x16.png
│       ├── favicon-32x32.png
│       ├── apple-touch-icon.png
│       ├── android-chrome-192x192.png
│       └── android-chrome-512x512.png
└── particles/
    ├── particle-circle.svg
    ├── particle-triangle.svg
    └── particle-hexagon.svg
```

---

## Notes for Designers

1. **Consistency**: All assets should feel cohesive and part of the same visual system
2. **Scalability**: Vector formats (SVG) preferred for crisp rendering at all sizes
3. **Performance**: Optimize all assets for web (compress PNGs, minimize SVG code)
4. **Accessibility**: Ensure sufficient contrast ratios (WCAG AA minimum)
5. **Brand Voice**: Professional yet revolutionary, cutting-edge but trustworthy

---

## Easter Egg: Edge Constant

Incorporate **5.083203692** subtly into designs:
- Wave frequencies in background patterns
- Rotation angles (5.08 degrees)
- Spacing ratios (1:5.08)
- Hidden in circuit traces or network connections

This creates a cohesive "twilight boundary" aesthetic across all visual elements.

---

**Version**: 1.0
**Last Updated**: 2025-12-06
**Contact**: Design team via hello@jackknife.io
