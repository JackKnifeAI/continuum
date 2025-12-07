/**
 * Concept Tag Component
 */

import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import type { ConceptTagProps } from '../types';

export function ConceptTag({
  concept,
  onPress,
  size = 'medium',
}: ConceptTagProps) {
  const handlePress = () => {
    onPress?.(concept);
  };

  const sizeStyles = {
    small: styles.tagSmall,
    medium: styles.tagMedium,
    large: styles.tagLarge,
  };

  const textSizeStyles = {
    small: styles.textSmall,
    medium: styles.textMedium,
    large: styles.textLarge,
  };

  return (
    <TouchableOpacity
      style={[styles.tag, sizeStyles[size]]}
      onPress={handlePress}
      disabled={!onPress}
    >
      <Text style={[styles.text, textSizeStyles[size]]}>{concept.name}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  tag: {
    backgroundColor: '#DBEAFE',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
  },
  tagSmall: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  tagMedium: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  tagLarge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  text: {
    color: '#1E40AF',
    fontWeight: '500',
  },
  textSmall: {
    fontSize: 11,
  },
  textMedium: {
    fontSize: 13,
  },
  textLarge: {
    fontSize: 15,
  },
});
