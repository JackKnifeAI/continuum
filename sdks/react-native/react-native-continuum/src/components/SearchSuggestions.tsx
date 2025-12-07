/**
 * Search Suggestions Component
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface SearchSuggestionsProps {
  onSelect: (suggestion: string) => void;
}

const SUGGESTIONS = [
  'Recent memories',
  'Important notes',
  'Today',
  'This week',
  'Work',
  'Personal',
];

export function SearchSuggestions({ onSelect }: SearchSuggestionsProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Suggestions</Text>
      <View style={styles.suggestions}>
        {SUGGESTIONS.map((suggestion, index) => (
          <TouchableOpacity
            key={index}
            style={styles.suggestion}
            onPress={() => onSelect(suggestion)}
          >
            <Text style={styles.suggestionText}>{suggestion}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  suggestions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  suggestion: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginRight: 8,
    marginBottom: 8,
  },
  suggestionText: {
    fontSize: 14,
    color: '#4B5563',
  },
});
