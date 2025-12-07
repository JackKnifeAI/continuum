/**
 * Concept Graph Component - Visual representation of concept relationships
 * Note: This is a placeholder. For production, consider using react-native-svg or similar
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { Concept } from '../types';

interface ConceptGraphProps {
  rootConcept: Concept;
  depth?: number;
}

export function ConceptGraph({ rootConcept, depth = 2 }: ConceptGraphProps) {
  return (
    <View style={styles.container}>
      <View style={styles.node}>
        <Text style={styles.nodeText}>{rootConcept.name}</Text>
      </View>
      <Text style={styles.placeholder}>
        Concept graph visualization (depth: {depth})
      </Text>
      <Text style={styles.note}>
        Full graph rendering requires react-native-svg
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    alignItems: 'center',
  },
  node: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  nodeText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  placeholder: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 8,
  },
  note: {
    fontSize: 12,
    color: '#9CA3AF',
    fontStyle: 'italic',
    textAlign: 'center',
  },
});
