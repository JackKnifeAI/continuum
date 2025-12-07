/**
 * Options Component
 * Settings and configuration page
 */

import React, { useState, useEffect } from 'react';
import { Storage } from '../shared/storage';
import type { ContinuumConfig } from '../shared/types';

export const Options: React.FC = () => {
  const [config, setConfig] = useState<ContinuumConfig | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    const cfg = await Storage.getConfig();
    setConfig(cfg);
  };

  const handleSave = async () => {
    if (!config) return;

    try {
      setIsSaving(true);
      await Storage.setConfig(config);

      // Notify background script
      await browser.runtime.sendMessage({
        type: 'UPDATE_CONFIG',
        payload: config,
      });

      setSaveMessage('Settings saved successfully!');
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      setSaveMessage('Failed to save settings');
      console.error('Save error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  if (!config) {
    return <div className="options-loading">Loading...</div>;
  }

  return (
    <div className="options-container">
      <header className="options-header">
        <h1>
          <span className="options-logo">∞</span>
          CONTINUUM Settings
        </h1>
      </header>

      <main className="options-content">
        <section className="settings-section">
          <h2>API Configuration</h2>

          <div className="form-group">
            <label htmlFor="api-endpoint">API Endpoint</label>
            <input
              id="api-endpoint"
              type="url"
              value={config.apiEndpoint}
              onChange={(e) => setConfig({ ...config, apiEndpoint: e.target.value })}
              placeholder="http://localhost:8000"
            />
            <p className="form-help">
              URL of your CONTINUUM server
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="api-key">API Key</label>
            <input
              id="api-key"
              type="password"
              value={config.apiKey}
              onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
              placeholder="Your API key"
            />
            <p className="form-help">
              Get your API key from CONTINUUM settings
            </p>
          </div>
        </section>

        <section className="settings-section">
          <h2>Capture Preferences</h2>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={config.autoCapture}
                onChange={(e) => setConfig({ ...config, autoCapture: e.target.checked })}
              />
              <span>Enable auto-capture</span>
            </label>
            <p className="form-help">
              Automatically capture page content when you visit
            </p>
          </div>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={config.capturePreferences.saveMetadata}
                onChange={(e) => setConfig({
                  ...config,
                  capturePreferences: {
                    ...config.capturePreferences,
                    saveMetadata: e.target.checked,
                  },
                })}
              />
              <span>Save page metadata</span>
            </label>
          </div>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={config.capturePreferences.saveScreenshots}
                onChange={(e) => setConfig({
                  ...config,
                  capturePreferences: {
                    ...config.capturePreferences,
                    saveScreenshots: e.target.checked,
                  },
                })}
              />
              <span>Save page screenshots</span>
            </label>
          </div>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={config.capturePreferences.captureCode}
                onChange={(e) => setConfig({
                  ...config,
                  capturePreferences: {
                    ...config.capturePreferences,
                    captureCode: e.target.checked,
                  },
                })}
              />
              <span>Capture code snippets</span>
            </label>
          </div>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={config.capturePreferences.captureVideos}
                onChange={(e) => setConfig({
                  ...config,
                  capturePreferences: {
                    ...config.capturePreferences,
                    captureVideos: e.target.checked,
                  },
                })}
              />
              <span>Capture video transcripts</span>
            </label>
          </div>
        </section>

        <section className="settings-section">
          <h2>Appearance</h2>

          <div className="form-group">
            <label>Theme</label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  name="theme"
                  value="light"
                  checked={config.theme === 'light'}
                  onChange={(e) => setConfig({ ...config, theme: 'light' })}
                />
                <span>Light</span>
              </label>
              <label>
                <input
                  type="radio"
                  name="theme"
                  value="dark"
                  checked={config.theme === 'dark'}
                  onChange={(e) => setConfig({ ...config, theme: 'dark' })}
                />
                <span>Dark</span>
              </label>
              <label>
                <input
                  type="radio"
                  name="theme"
                  value="system"
                  checked={config.theme === 'system'}
                  onChange={(e) => setConfig({ ...config, theme: 'system' })}
                />
                <span>System</span>
              </label>
            </div>
          </div>
        </section>

        <section className="settings-section">
          <h2>Sync</h2>

          <div className="form-group">
            <label htmlFor="sync-interval">Sync Interval (minutes)</label>
            <input
              id="sync-interval"
              type="number"
              min="1"
              max="60"
              value={config.syncInterval / 60000}
              onChange={(e) => setConfig({
                ...config,
                syncInterval: parseInt(e.target.value) * 60000,
              })}
            />
            <p className="form-help">
              How often to sync pending captures
            </p>
          </div>
        </section>
      </main>

      <footer className="options-footer">
        {saveMessage && (
          <div className={`save-message ${saveMessage.includes('success') ? 'success' : 'error'}`}>
            {saveMessage}
          </div>
        )}

        <button
          className="save-button"
          onClick={handleSave}
          disabled={isSaving}
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </button>
      </footer>
    </div>
  );
};
