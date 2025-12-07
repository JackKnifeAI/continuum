/**
 * Memory List Component - Scrollable list of memories
 */

import React from 'react';
import { FlatList, View, Text, StyleSheet, RefreshControl } from 'react-native';
import { useMemories } from '../hooks';
import { MemoryCard } from './MemoryCard';
import type { MemoryListProps } from '../types';

export function MemoryList({
  filter,
  onMemoryPress,
  emptyComponent,
  headerComponent,
  footerComponent,
}: MemoryListProps) {
  const { memories, isLoading, error, refetch, loadMore, hasMore } =
    useMemories(filter);

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Error: {error.message}</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={memories}
      renderItem={({ item }) => (
        <MemoryCard memory={item} onPress={onMemoryPress} />
      )}
      keyExtractor={(item) => item.id}
      refreshControl={
        <RefreshControl refreshing={isLoading} onRefresh={refetch} />
      }
      onEndReached={loadMore}
      onEndReachedThreshold={0.5}
      ListEmptyComponent={
        emptyComponent || (
          <View style={styles.centerContainer}>
            <Text style={styles.emptyText}>No memories found</Text>
          </View>
        )
      }
      ListHeaderComponent={headerComponent}
      ListFooterComponent={
        hasMore ? (
          footerComponent || (
            <View style={styles.footerContainer}>
              <Text style={styles.footerText}>Loading more...</Text>
            </View>
          )
        ) : null
      }
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
  footerContainer: {
    padding: 16,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
