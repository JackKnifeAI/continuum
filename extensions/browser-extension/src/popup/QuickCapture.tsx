/**
 * Quick Capture Component
 */

import React, { useState } from 'react';

interface QuickCaptureProps {
  onCapture: (content: string) => Promise<void>;
}

export const QuickCapture: React.FC<QuickCaptureProps> = ({ onCapture }) => {
  const [content, setContent] = useState('');
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCapture = async () => {
    if (!content.trim()) {
      setError('Please enter some content');
      return;
    }

    try {
      setIsCapturing(true);
      setError(null);

      await onCapture(content);

      // Success - clear form
      setContent('');
      showSuccess();
    } catch (err) {
      setError('Failed to capture. Try again.');
      console.error('Capture error:', err);
    } finally {
      setIsCapturing(false);
    }
  };

  const showSuccess = () => {
    const message = document.createElement('div');
    message.className = 'success-message';
    message.textContent = 'Captured to CONTINUUM!';
    document.body.appendChild(message);

    setTimeout(() => message.remove(), 2000);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleCapture();
    }
  };

  return (
    <div className="quick-capture">
      <textarea
        className="capture-input"
        placeholder="What do you want to remember?"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={5}
        autoFocus
      />

      {error && <div className="error-message">{error}</div>}

      <div className="capture-actions">
        <div className="hint">
          Press {navigator.platform.includes('Mac') ? 'Cmd' : 'Ctrl'}+Enter to capture
        </div>

        <button
          className="capture-button"
          onClick={handleCapture}
          disabled={isCapturing || !content.trim()}
        >
          {isCapturing ? 'Capturing...' : 'Capture'}
        </button>
      </div>

      <div className="quick-actions">
        <button
          className="quick-action-button"
          onClick={async () => {
            const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
            setContent(`${tab?.title}\n${tab?.url}`);
          }}
        >
          Capture Current Page
        </button>

        <button
          className="quick-action-button"
          onClick={async () => {
            const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
            if (tab?.id) {
              const response = await browser.tabs.sendMessage(tab.id, {
                type: 'GET_SELECTION',
              });
              if (response?.selection) {
                setContent(response.selection);
              }
            }
          }}
        >
          Capture Selection
        </button>
      </div>
    </div>
  );
};
