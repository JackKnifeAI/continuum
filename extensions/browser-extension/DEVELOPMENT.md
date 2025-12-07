# Development Guide

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development:**
   ```bash
   npm run dev:chrome    # For Chrome
   npm run dev:firefox   # For Firefox
   ```

3. **Load extension:**
   - Chrome: `chrome://extensions` → Load unpacked → `dist/chrome`
   - Firefox: `about:debugging` → Load Temporary Add-on → `dist/firefox/manifest.json`

## Architecture

### Background Service Worker

Located in `src/background/service-worker.ts`, handles:
- API communication
- Context menu setup
- Keyboard shortcuts
- Background sync
- Message routing

### Content Scripts

Located in `src/content/`, injected into all pages:
- `content.ts` - Main coordinator
- `highlighter.ts` - Text highlighting
- `overlay.ts` - Inline UI
- `extractor.ts` - Page content extraction

### UI Components

React-based interfaces:
- **Popup** (`src/popup/`) - Quick actions
- **Sidebar** (`src/sidebar/`) - Full browser
- **Options** (`src/options/`) - Settings

### Shared Utilities

- `api-client.ts` - CONTINUUM API wrapper
- `storage.ts` - Chrome storage abstraction
- `messaging.ts` - Cross-component messaging
- `types.ts` - TypeScript definitions

## Message Flow

```
Content Script → Background → API
     ↓              ↓
  Overlay      Popup/Sidebar
```

All messages use typed `ExtensionMessage` format.

## Building

### Development Build
```bash
npm run build:chrome    # Chrome/Edge
npm run build:firefox   # Firefox
```

Output: `dist/{browser}/`

### Production Build
```bash
npm run build:all
```

Output: `packages/*.zip`

## Testing

### Unit Tests
```bash
npm test
npm run test:watch
```

### E2E Tests
```bash
npm run test:e2e
```

Uses Puppeteer to test in real browser.

### Manual Testing

1. Load extension in development mode
2. Open DevTools for each component:
   - Background: chrome://extensions → Inspect views → service worker
   - Popup: Right-click popup → Inspect
   - Content: Right-click page → Inspect

## Debugging

### Background Worker
```javascript
console.log('Background:', data);
```

View in: Extensions page → Inspect service worker

### Content Script
```javascript
console.log('Content:', data);
```

View in: Page DevTools console

### Storage
```javascript
chrome.storage.local.get(null, console.log);
```

### Messages
```javascript
chrome.runtime.onMessage.addListener((msg) => {
  console.log('Message:', msg);
  return true;
});
```

## Common Tasks

### Add New Content Extractor

1. Create `src/content/extractors/sitename.ts`:
   ```typescript
   export class SiteExtractor {
     extract() {
       return { content: '', metadata: {} };
     }
   }
   ```

2. Register in `extractor.ts`:
   ```typescript
   if (hostname.includes('site.com')) {
     return this.extractSite();
   }
   ```

### Add New Message Type

1. Add to `types.ts`:
   ```typescript
   type MessageType = ... | 'NEW_TYPE';
   ```

2. Handle in background:
   ```typescript
   case 'NEW_TYPE':
     return handleNewType(message.payload);
   ```

3. Send from content:
   ```typescript
   await sendToBackground({
     type: 'NEW_TYPE',
     payload: data,
   });
   ```

### Add New Permission

1. Add to `manifest.json`:
   ```json
   "permissions": [..., "newPermission"]
   ```

2. Document in README

3. Explain in privacy policy

## Best Practices

### Performance

- Debounce search queries
- Lazy load sidebar content
- Cache API responses
- Use background sync for captures

### Security

- Sanitize all user input
- Validate API responses
- Use CSP headers
- Never inject eval()

### UX

- Show loading states
- Handle errors gracefully
- Provide offline feedback
- Use optimistic updates

### Code Quality

- Use TypeScript strictly
- Write tests for new features
- Follow ESLint rules
- Document complex logic

## Deployment

### Chrome Web Store

1. Build production:
   ```bash
   npm run build:chrome
   ```

2. Create store listing
3. Upload `packages/continuum-chrome-v*.zip`
4. Submit for review

### Firefox Add-ons

1. Build production:
   ```bash
   npm run build:firefox
   ```

2. Create listing
3. Upload `packages/continuum-firefox-v*.zip`
4. Submit for review

### Edge Add-ons

Same as Chrome (uses same manifest).

## Troubleshooting

### Extension won't load
- Check manifest.json syntax
- Verify all referenced files exist
- Check browser console for errors

### Content script not injecting
- Check host permissions
- Verify matches pattern
- Check CSP on target page

### API calls failing
- Verify API endpoint in options
- Check CORS headers
- Confirm API key is valid

### Messages not received
- Ensure sender exists
- Return `true` from async listeners
- Check message format

## Resources

- [Chrome Extension Docs](https://developer.chrome.com/docs/extensions/)
- [Firefox Extension Docs](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)
- [WebExtension Polyfill](https://github.com/mozilla/webextension-polyfill)
