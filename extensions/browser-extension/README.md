# CONTINUUM Browser Extension

Your AI never forgets. Capture, recall, and connect knowledge across the web.

## Overview

The CONTINUUM browser extension integrates AI-powered memory capture and recall directly into your browsing experience. Highlight text, capture pages, and access your knowledge graph without leaving your browser.

## Features

### Core Capabilities

- **Text Selection Capture** - Highlight and save any text with one click
- **Smart Page Capture** - Automatically extract article content, code snippets, videos
- **Inline Search** - Search your memories without leaving the page
- **Memory Highlighting** - See your captured content highlighted on pages
- **Context Menu Integration** - Right-click to save or search
- **Keyboard Shortcuts** - Quick access via customizable shortcuts
- **Offline Queue** - Captures sync when you're back online

### UI Components

1. **Popup** - Quick capture, search, and recent memories
2. **Sidebar** (Chrome) - Full memory browser and concept explorer
3. **Content Overlay** - Inline capture and search on any page
4. **Options Page** - Configure API, preferences, and sync

### Content Extraction

Intelligent extraction for:
- Articles (Medium, blogs, news)
- Code snippets (GitHub, StackOverflow)
- GitHub (repos, issues, PRs)
- Twitter/X posts
- YouTube videos (title, description)
- PDFs
- Generic web pages

## Browser Support

| Browser | Manifest | Status |
|---------|----------|--------|
| Chrome  | V3       | ✅ Full support |
| Edge    | V3       | ✅ Full support |
| Firefox | V2       | ✅ Full support |

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/continuum/browser-extension.git
   cd browser-extension
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build for your browser:
   ```bash
   # Chrome/Edge
   npm run build:chrome

   # Firefox
   npm run build:firefox
   ```

4. Load the extension:
   - **Chrome/Edge**: Navigate to `chrome://extensions`, enable Developer Mode, click "Load unpacked", select `dist/chrome`
   - **Firefox**: Navigate to `about:debugging`, click "Load Temporary Add-on", select `dist/firefox/manifest.json`

### From Store (Coming Soon)

- Chrome Web Store
- Firefox Add-ons
- Edge Add-ons

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
npm install
npm run dev:chrome    # Chrome development mode
npm run dev:firefox   # Firefox development mode
```

### Project Structure

```
browser-extension/
├── src/
│   ├── background/      # Service worker
│   │   ├── service-worker.ts
│   │   └── api.ts
│   ├── content/         # Content scripts
│   │   ├── content.ts
│   │   ├── highlighter.ts
│   │   ├── overlay.ts
│   │   ├── extractor.ts
│   │   └── extractors/  # Site-specific extractors
│   ├── popup/           # Popup UI (React)
│   │   ├── Popup.tsx
│   │   ├── QuickCapture.tsx
│   │   ├── QuickSearch.tsx
│   │   └── RecentMemories.tsx
│   ├── sidebar/         # Sidebar (React)
│   │   ├── Sidebar.tsx
│   │   ├── MemoryBrowser.tsx
│   │   └── ConceptExplorer.tsx
│   ├── options/         # Options page (React)
│   │   └── Options.tsx
│   └── shared/          # Shared utilities
│       ├── api-client.ts
│       ├── storage.ts
│       ├── messaging.ts
│       └── types.ts
├── styles/              # CSS
├── assets/              # Icons, images
├── manifest.json        # Chrome manifest
├── manifest.firefox.json # Firefox manifest
└── webpack.config.js    # Build config
```

### Building

```bash
# Development builds (with source maps)
npm run build:chrome
npm run build:firefox
npm run build:edge

# Production builds (minified, packaged as .zip)
npm run build:all

# Packages will be in packages/
```

### Testing

```bash
npm test              # Unit tests
npm run test:watch    # Watch mode
npm run test:e2e      # End-to-end tests
```

## Configuration

### API Setup

1. Open extension options (right-click extension icon → Options)
2. Enter your CONTINUUM API endpoint (e.g., `http://localhost:8000`)
3. Enter your API key
4. Configure capture preferences

### Keyboard Shortcuts

Default shortcuts (customizable in browser settings):

- `Ctrl+Shift+C` - Capture selected text
- `Ctrl+Shift+F` - Quick search
- `Ctrl+Shift+M` - Toggle sidebar

### Permissions

The extension requires:

- `storage` - Store configuration and offline queue
- `contextMenus` - Right-click menu integration
- `activeTab` - Access current page for capture
- `sidePanel` - Sidebar panel (Chrome only)
- `notifications` - Capture confirmations
- `<all_urls>` - Content script injection

## Usage

### Capturing Content

**Method 1: Selection**
1. Highlight text on any page
2. Click the capture button that appears
3. Or use `Ctrl+Shift+C`

**Method 2: Right-Click Menu**
1. Right-click selected text
2. Choose "Save to CONTINUUM"

**Method 3: Popup**
1. Click extension icon
2. Type or paste content
3. Click "Capture"

**Method 4: Full Page**
1. Right-click on page
2. Choose "Capture entire page"

### Searching

**Quick Search:**
1. Press `Ctrl+Shift+F`
2. Type your query
3. Results appear inline

**Popup Search:**
1. Click extension icon
2. Switch to "Search" tab
3. Enter query

**Sidebar Search:**
1. Open sidebar (`Ctrl+Shift+M`)
2. Browse all memories
3. Filter and explore concepts

### Highlighting

Captured content is automatically highlighted on pages you visit. Click highlights to:
- View full memory
- Find related content
- Navigate to source

## Architecture

### Manifest V3 (Chrome/Edge)

- **Service Worker** - Background processing, API calls, context menus
- **Content Scripts** - Page interaction, highlighting, overlay
- **Action Popup** - Quick UI for capture/search
- **Side Panel** - Full memory browser
- **Options Page** - Settings and configuration

### Manifest V2 (Firefox)

- **Background Scripts** - Persistent background page
- **Content Scripts** - Same as V3
- **Browser Action** - Popup
- **Sidebar Action** - Sidebar equivalent
- **Options Page** - Same as V3

### Message Passing

All components communicate via typed messages:

```typescript
interface ExtensionMessage<T> {
  type: MessageType;
  payload: T;
  requestId?: string;
}
```

Types: `CAPTURE_SELECTION`, `QUICK_SEARCH`, `GET_PAGE_CONTEXT`, etc.

### Storage

- Chrome Storage API for config and cache
- Offline queue for pending captures
- Automatic sync on reconnect

## API Integration

The extension connects to CONTINUUM backend API:

```typescript
// Endpoints used
POST   /api/memories          // Capture
GET    /api/search            // Search
GET    /api/context           // Page context
GET    /api/concepts          // Concepts
GET    /api/memories/recent   // Recent
```

See `src/shared/api-client.ts` for full API client.

## Privacy

- All data stays in your CONTINUUM instance
- No tracking or analytics
- No third-party services
- Offline-first design

See [PRIVACY.md](PRIVACY.md) for full privacy policy.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE)

## Support

- Documentation: https://docs.continuum.ai
- Issues: https://github.com/continuum/browser-extension/issues
- Discord: https://discord.gg/continuum

## Roadmap

- [ ] Chrome Web Store listing
- [ ] Firefox Add-ons listing
- [ ] Safari support
- [ ] PDF text extraction
- [ ] Video transcript capture
- [ ] Collaborative highlighting
- [ ] Mobile support
- [ ] Offline full-text search

---

Built with ∞ by the CONTINUUM team
