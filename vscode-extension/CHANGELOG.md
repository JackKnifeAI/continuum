# Changelog

All notable changes to the Continuum Memory VS Code extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-06

### Added

- Initial release of Continuum Memory extension
- Memory search command with keyboard shortcut (Ctrl+Shift+M)
- Store code selection command with keyboard shortcut (Ctrl+Shift+S)
- Recall context command with keyboard shortcut (Ctrl+Shift+R)
- Memory Explorer sidebar view with statistics and recent entities
- Status bar integration showing connection and sync status
- Auto-sync feature with configurable interval
- Configuration command for easy setup
- Hover provider for contextual memory display
- Experimental completion provider for memory-aware suggestions
- Support for Continuum API v0.2.0+
- Comprehensive settings for customization
- Security: API key storage in VS Code settings
- Full TypeScript implementation with type safety
- Error handling and user-friendly error messages
- Welcome message for first-time users
- Integration with VS Code command palette
- Context menu integration for editor actions
- Tree view with collapsible categories
- Real-time sync status updates
- Connection testing on activation and configuration changes

### Security

- API keys stored in VS Code workspace/user settings
- No cloud services or external dependencies
- All communication direct to configured Continuum server
- Optional telemetry (disabled by default)

### Documentation

- Comprehensive README with usage examples
- Troubleshooting guide
- Configuration reference
- Command reference with keybindings
- Security best practices

## [Unreleased]

### Planned Features

- Secure API key storage using VS Code Secret Storage
- Advanced search filters in Memory Explorer
- Export/import memory data
- Offline mode with local caching
- Graph visualization view
- Memory timeline view
- Relationship explorer
- Bulk operations (store multiple files)
- Integration with Git (associate memories with commits)
- Workspace-specific memory namespaces
- Collaboration features (shared memories)
- Advanced hover with relationship graphs
- Smarter completion provider with ranking
- Memory health monitoring and alerts
- Performance optimizations for large knowledge graphs
- Custom themes for Memory Explorer
- Keyboard shortcuts customization UI
- Quick access panel with recent searches
- Memory tagging and categorization
- Search history
- Favorites/bookmarks for important memories
