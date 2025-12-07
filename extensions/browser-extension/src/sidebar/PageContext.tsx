/**
 * Page Context Component
 */

import React from 'react';
import type { PageContext as PageContextType, Memory } from '../shared/types';

interface PageContextProps {
  context: PageContextType | null;
  onSelectMemory: (memory: Memory) => void;
}

export const PageContext: React.FC<PageContextProps> = ({ context, onSelectMemory }) => {
  if (!context) {
    return (
      <div className="page-context empty">
        <p>No related memories for this page</p>
      </div>
    );
  }

  return (
    <div className="page-context">
      <section className="related-memories">
        <h3>Related Memories ({context.relatedMemories.length})</h3>
        {context.relatedMemories.map(memory => (
          <div
            key={memory.id}
            className="memory-card"
            onClick={() => onSelectMemory(memory)}
          >
            <div className="memory-title">{memory.source.title}</div>
            <div className="memory-preview">
              {memory.content.slice(0, 100)}...
            </div>
          </div>
        ))}
      </section>

      <section className="suggested-concepts">
        <h3>Suggested Concepts</h3>
        {context.suggestedConcepts.map(concept => (
          <div key={concept.id} className="concept-tag">
            {concept.name}
          </div>
        ))}
      </section>
    </div>
  );
};
