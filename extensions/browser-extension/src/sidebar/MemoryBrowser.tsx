/**
 * Memory Browser Component
 */

import React, { useState, useEffect } from 'react';
import type { Memory } from '../shared/types';

interface MemoryBrowserProps {
  onSelectMemory: (memory: Memory) => void;
}

export const MemoryBrowser: React.FC<MemoryBrowserProps> = ({ onSelectMemory }) => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    // Would load from API
    setMemories([]);
  };

  const filteredMemories = memories.filter(m =>
    m.content.toLowerCase().includes(filter.toLowerCase()) ||
    m.source.title.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="memory-browser">
      <input
        type="text"
        className="filter-input"
        placeholder="Filter memories..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />

      <div className="memories-list">
        {filteredMemories.map(memory => (
          <div
            key={memory.id}
            className="memory-item"
            onClick={() => onSelectMemory(memory)}
          >
            <div className="memory-item-title">{memory.source.title}</div>
            <div className="memory-item-preview">
              {memory.content.slice(0, 100)}...
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
