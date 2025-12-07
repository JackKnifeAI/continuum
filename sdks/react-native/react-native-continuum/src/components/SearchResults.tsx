/**
 * Search Results Component
 */

import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { useSearch } from '../hooks';
import { MemoryCard } from './MemoryCard';
import type { Memory } from '../types';

interface SearchResultsProps {
  query: string;
  onMemoryPress?: (memory: Memory) => void;
}

export function SearchResults({ query, onMemoryPress }: SearchResultsProps) {
  const { results, isLoading, error } = useSearch(query);

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.loadingText}>Searching...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Error: {error.message}</Text>
      </View>
    );
  }

  if (results.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.emptyText}>No results found</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={results}
      renderItem={({ item }) => (
        <View style={styles.resultItem}>
          <MemoryCard memory={item.memory} onPress={onMemoryPress} />
          <Text style={styles.similarity}>
            {Math.round(item.similarity * 100)}% match
          </Text>
        </View>
      )}
      keyExtractor={(item) => item.memory.id}
      contentContainerStyle={styles.container}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  resultItem: {
    position: 'relative',
  },
  similarity: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: '#10B981',
    color: '#FFFFFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    fontSize: 11,
    fontWeight: '600',
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
  },
  errorText: {
    fontSize: 16,
    color: '#EF4444',
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#9CA3AF',
    textAlign: 'center',
  },
});
