# Privacy Policy

## CONTINUUM Browser Extension

**Last Updated:** December 6, 2025

## Overview

CONTINUUM respects your privacy. This extension is designed to work with your self-hosted or privately-managed CONTINUUM instance. We do not collect, store, or transmit your data to any third parties.

## Data Collection

### What We Collect

The extension captures and stores:
- Text content you explicitly select or save
- URLs and page titles of captured content
- Page metadata (author, date, tags)
- Your configuration (API endpoint, preferences)

### Where It Goes

All data is sent **only** to:
- Your configured CONTINUUM API endpoint
- Your browser's local storage (for offline queue and cache)

**We do not:**
- Send data to CONTINUUM servers
- Send data to third-party analytics
- Track your browsing history
- Collect personal information
- Share data with advertisers

## Data Storage

### Browser Storage

Stored locally in your browser:
- API configuration (endpoint, key)
- User preferences (theme, sync interval)
- Offline capture queue
- Recent memories cache

This data:
- Never leaves your device except to sync with your CONTINUUM instance
- Can be cleared via extension options
- Is removed when you uninstall

### Your CONTINUUM Instance

Captured content is sent to your configured CONTINUUM server. You control:
- Where this server is hosted
- Who has access to it
- How data is stored
- Retention policies

## Permissions

### Why We Need Them

- `storage` - Store configuration and offline queue locally
- `contextMenus` - Add "Save to CONTINUUM" menu items
- `activeTab` - Access current page to capture content
- `sidePanel` - Display sidebar panel (Chrome only)
- `notifications` - Show capture confirmations
- `<all_urls>` - Inject content script to enable highlighting and capture

### What We Don't Do

We **never**:
- Access pages you don't interact with
- Read passwords or form data
- Track your browsing
- Modify page content (except highlights)
- Access other extensions

## Third-Party Services

**None.** This extension communicates exclusively with:
1. Your configured CONTINUUM API endpoint
2. Your browser's local storage

No analytics, tracking, or third-party services.

## Security

- All API communication uses HTTPS (recommended)
- API keys stored securely in browser storage
- Content Security Policy prevents code injection
- No eval() or inline scripts

## Your Rights

You have the right to:
- Access all data stored by the extension
- Export your data from CONTINUUM
- Delete all extension data (uninstall or clear storage)
- Configure or disable the extension anytime

## Changes

We may update this privacy policy. Changes will be:
- Posted in this document
- Included in extension updates
- Reflected in the version number

## Contact

Questions about privacy?
- Email: privacy@continuum.ai
- GitHub: https://github.com/continuum/browser-extension/issues
- Discord: https://discord.gg/continuum

## Open Source

This extension is open source. You can:
- Review the code: https://github.com/continuum/browser-extension
- Verify data handling
- Build from source
- Audit security

## Compliance

This extension is designed for:
- GDPR compliance (data stays with you)
- CCPA compliance (no data sale)
- Self-hosted deployment (full control)

---

Your data is yours. We're just helping you remember it.
