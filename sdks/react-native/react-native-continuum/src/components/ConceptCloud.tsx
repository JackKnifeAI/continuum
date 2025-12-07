/**
 * Concept Cloud Component - Tag cloud of concepts
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { ConceptTag } from './ConceptTag';
import type { Concept } from '../types';

interface ConceptCloudProps {
  concepts: Concept[];
  onConceptPress?: (concept: Concept) => void;
}

export function ConceptCloud({ concepts, onConceptPress }: ConceptCloudProps) {
  return (
    <View style={styles.container}>
      {concepts.map((concept) => (
        <ConceptTag
          key={concept.id}
          concept={concept}
          onPress={onConceptPress}
          size="medium"
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
  },
});
