/**
 * Concept Explorer Component
 */

import React, { useState, useEffect } from 'react';
import type { Concept } from '../shared/types';

export const ConceptExplorer: React.FC = () => {
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [selectedConcept, setSelectedConcept] = useState<Concept | null>(null);

  useEffect(() => {
    loadConcepts();
  }, []);

  const loadConcepts = async () => {
    // Would load from API
    setConcepts([]);
  };

  return (
    <div className="concept-explorer">
      <div className="concepts-list">
        {concepts.map(concept => (
          <div
            key={concept.id}
            className="concept-item"
            onClick={() => setSelectedConcept(concept)}
          >
            <div className="concept-name">{concept.name}</div>
            <div className="concept-count">{concept.memoryCount} memories</div>
          </div>
        ))}
      </div>

      {selectedConcept && (
        <div className="concept-details">
          <h3>{selectedConcept.name}</h3>
          <p>{selectedConcept.description}</p>
          <div className="related-concepts">
            {selectedConcept.relatedConcepts.map(related => (
              <span key={related} className="related-tag">{related}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
