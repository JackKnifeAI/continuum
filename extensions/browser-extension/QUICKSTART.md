# CONTINUUM Browser Extension - Quick Start

Get up and running with the CONTINUUM browser extension in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- Chrome, Firefox, or Edge browser
- CONTINUUM backend running (or configured endpoint)

## Installation

### Step 1: Install Dependencies

```bash
cd /var/home/alexandergcasavant/Projects/continuum/extensions/browser-extension
npm install
```

### Step 2: Build the Extension

**For Chrome/Edge:**
```bash
npm run build:chrome
```

**For Firefox:**
```bash
npm run build:firefox
```

### Step 3: Load in Browser

**Chrome/Edge:**
1. Open `chrome://extensions` (or `edge://extensions`)
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select `/var/home/alexandergcasavant/Projects/continuum/extensions/browser-extension/dist/chrome`

**Firefox:**
1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select `/var/home/alexandergcasavant/Projects/continuum/extensions/browser-extension/dist/firefox/manifest.json`

### Step 4: Configure API

1. Click the extension icon in your browser toolbar
2. Click "Settings" at the bottom
3. Enter your CONTINUUM API endpoint (e.g., `http://localhost:8000`)
4. Enter your API key
5. Click "Save Settings"

## First Capture

### Method 1: Text Selection
1. Visit any webpage
2. Highlight some text
3. Click the purple "Save" button that appears
4. Done! Content is captured to CONTINUUM

### Method 2: Popup
1. Click the extension icon
2. Type or paste content in the text area
3. Click "Capture"
4. Success!

### Method 3: Right-Click
1. Highlight text on any page
2. Right-click and select "Save to CONTINUUM"
3. Captured!

## First Search

1. Press `Ctrl+Shift+F` (or `Cmd+Shift+F` on Mac)
2. Type your search query
3. See results appear inline
4. Click a result to open

## Using the Sidebar (Chrome/Edge)

1. Press `Ctrl+Shift+M` (or `Cmd+Shift+M`)
2. Browse "This Page" to see related memories
3. Switch to "All Memories" to browse everything
4. Explore "Concepts" to see your knowledge graph

## Development Mode

Want to make changes? Use watch mode:

```bash
# Chrome
npm run dev:chrome

# Firefox
npm run dev:firefox
```

This rebuilds automatically when you edit files.

## Troubleshooting

### Extension won't load
- Check that you built for the correct browser
- Look for errors in browser console
- Verify manifest.json is valid

### API not connecting
- Confirm CONTINUUM backend is running
- Check API endpoint URL (include http://)
- Verify API key is correct
- Check browser console for errors

### Captures not working
- Ensure you're connected (check sync indicator)
- Try right-click capture instead
- Check offline queue (may be pending sync)

### Keyboard shortcuts not working
- Check for conflicts with other extensions
- Customize shortcuts in browser settings:
  - Chrome: `chrome://extensions/shortcuts`
  - Firefox: `about:addons` → Extensions → Gear icon → Manage shortcuts

## Next Steps

- Read the full [README.md](/var/home/alexandergcasavant/Projects/continuum/extensions/browser-extension/README.md)
- Check out [DEVELOPMENT.md](/var/home/alexandergcasavant/Projects/continuum/extensions/browser-extension/DEVELOPMENT.md) for development guide
- Review [BROWSER_SUPPORT.md](/var/home/alexandergcasavant/Projects/continuum/extensions/browser-extension/BROWSER_SUPPORT.md) for compatibility details

## Support

Need help?
- Check documentation in this directory
- File an issue on GitHub
- Join Discord community

---

Happy capturing! Your AI never forgets.
