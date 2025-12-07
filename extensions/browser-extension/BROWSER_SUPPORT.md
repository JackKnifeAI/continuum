# Browser Support Matrix

## Chrome / Edge (Manifest V3)

### ✅ Fully Supported

- Chrome 109+
- Edge 109+
- Brave 1.48+ (Chromium-based)
- Opera 95+ (Chromium-based)
- Vivaldi 5.7+ (Chromium-based)

### Features

| Feature | Chrome | Edge | Status |
|---------|--------|------|--------|
| Service Worker | ✅ | ✅ | Full support |
| Side Panel | ✅ | ✅ | Chrome 114+, Edge 114+ |
| Context Menus | ✅ | ✅ | Full support |
| Storage API | ✅ | ✅ | Full support |
| Notifications | ✅ | ✅ | Full support |
| Keyboard Shortcuts | ✅ | ✅ | Full support |
| Content Scripts | ✅ | ✅ | Full support |
| Declarative Net Request | ✅ | ✅ | Not used |

### Known Issues

- **Side Panel**: Only available in Chrome/Edge 114+. Falls back to popup in older versions.
- **Service Worker**: Must handle suspension/wake properly. Implemented with persistent message ports.

## Firefox (Manifest V2)

### ✅ Fully Supported

- Firefox 109+
- Firefox ESR 115+

### Features

| Feature | Firefox | Status |
|---------|---------|--------|
| Background Scripts | ✅ | Persistent background page |
| Sidebar Action | ✅ | Native sidebar support |
| Context Menus | ✅ | Full support |
| Storage API | ✅ | Full support |
| Notifications | ✅ | Full support |
| Keyboard Shortcuts | ✅ | Full support |
| Content Scripts | ✅ | Full support |

### Manifest V3 Migration

Firefox is migrating to Manifest V3. When stable:
- Update `manifest.firefox.json` to v3
- Replace background scripts with service worker
- Test thoroughly

### Known Issues

- **Service Worker**: Not yet stable in Firefox. Using persistent background page.
- **Side Panel**: Uses sidebar action instead. Different API but same functionality.

## Safari

### ⚠️ Experimental Support

Safari support requires:
1. Converting extension to Safari Web Extension format
2. Building with Xcode
3. App Store submission

### Status

- Not currently supported
- Planned for future release
- Community contributions welcome

### Requirements

- Safari 14+
- macOS 11+ / iOS 14+
- Xcode 12+

## Mobile Browsers

### Status

**Not currently supported**

Mobile extension support varies:
- **Chrome Android**: Limited API support
- **Firefox Android**: Better support but UX challenges
- **Safari iOS**: Requires native app wrapper

### Future Plans

- Investigate Firefox Android support
- Consider companion mobile app
- Progressive Web App for mobile

## API Compatibility

### WebExtension APIs Used

| API | Chrome | Firefox | Safari | Polyfill |
|-----|--------|---------|--------|----------|
| runtime | ✅ | ✅ | ✅ | - |
| storage | ✅ | ✅ | ✅ | - |
| tabs | ✅ | ✅ | ✅ | - |
| contextMenus | ✅ | ✅ | ⚠️ | - |
| notifications | ✅ | ✅ | ⚠️ | - |
| commands | ✅ | ✅ | ⚠️ | - |
| sidePanel | ✅ | N/A | N/A | Fallback |
| scripting | ✅ | ⚠️ | ⚠️ | tabs.executeScript |

### Polyfills

Using `webextension-polyfill` for cross-browser compatibility:
- Promises instead of callbacks
- Consistent API across browsers
- Automatic namespace detection (chrome vs browser)

## Testing

### Browsers Tested

- ✅ Chrome 120 (latest)
- ✅ Edge 120 (latest)
- ✅ Firefox 121 (latest)
- ⚠️ Safari 17 (experimental)

### Test Matrix

| Test | Chrome | Firefox | Safari |
|------|--------|---------|--------|
| Installation | ✅ | ✅ | ⚠️ |
| Content Capture | ✅ | ✅ | ⚠️ |
| Search | ✅ | ✅ | ⚠️ |
| Highlighting | ✅ | ✅ | ⚠️ |
| Offline Queue | ✅ | ✅ | ⚠️ |
| Settings | ✅ | ✅ | ⚠️ |

## Minimum Versions

### Chrome/Edge
- **Minimum**: 109 (service worker stability)
- **Recommended**: 114+ (side panel support)

### Firefox
- **Minimum**: 109 (API compatibility)
- **Recommended**: 115 ESR (long-term support)

### Safari
- **Minimum**: 14 (when supported)
- **Recommended**: 17+ (modern APIs)

## Feature Detection

Extension gracefully degrades:

```typescript
// Side panel fallback
if (browser.sidePanel) {
  await browser.sidePanel.open();
} else {
  await browser.browserAction.openPopup();
}

// Storage API fallback
const storage = browser.storage.local || browser.storage.sync;
```

## Reporting Issues

Browser-specific issues:
1. Check known issues above
2. Test in other browsers
3. Report with browser version
4. Include console errors

Template:
```
Browser: Chrome 120
OS: macOS 14
Issue: [description]
Steps: [reproduction]
Expected: [expected behavior]
Actual: [actual behavior]
```

## Future Support

### Planned
- Safari (2024)
- Firefox Manifest V3 (when stable)

### Considering
- Mobile browsers
- Alternative browsers (Tor, Brave-specific features)

### Not Planned
- IE11 (deprecated)
- Legacy Edge (deprecated)
- Chrome <109 (incompatible APIs)
