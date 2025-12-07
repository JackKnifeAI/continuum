/**
 * Recent Memories Component
 */

import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import type { Memory } from '../shared/types';

interface RecentMemoriesProps {
  memories: Memory[];
}

export const RecentMemories: React.FC<RecentMemoriesProps> = ({ memories }) => {
  if (memories.length === 0) {
    return (
      <div className="recent-memories empty">
        <div className="empty-state">
          <div className="empty-icon">∞</div>
          <h3>No memories yet</h3>
          <p>Start capturing content to build your knowledge graph</p>
        </div>
      </div>
    );
  }

  return (
    <div className="recent-memories">
      {memories.map((memory) => (
        <div
          key={memory.id}
          className="memory-card"
          onClick={() => window.open(memory.source.url, '_blank')}
        >
          <div className="memory-header">
            <div className="memory-type">{memory.source.type}</div>
            <div className="memory-date">
              {formatDistanceToNow(new Date(memory.createdAt), { addSuffix: true })}
            </div>
          </div>

          <div className="memory-title">{memory.source.title}</div>

          <div className="memory-content">
            {memory.content.slice(0, 100)}...
          </div>

          {memory.concepts.length > 0 && (
            <div className="memory-concepts">
              {memory.concepts.slice(0, 3).map((concept) => (
                <span key={concept} className="concept-tag">
                  {concept}
                </span>
              ))}
              {memory.concepts.length > 3 && (
                <span className="concept-tag more">
                  +{memory.concepts.length - 3}
                </span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
