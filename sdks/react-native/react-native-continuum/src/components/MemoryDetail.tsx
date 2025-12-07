/**
 * Memory Detail Component - Full memory view
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { useMemory } from '../hooks';
import { ConceptTag } from './ConceptTag';

interface MemoryDetailProps {
  memoryId: string;
}

export function MemoryDetail({ memoryId }: MemoryDetailProps) {
  const { memory, isLoading, error } = useMemory(memoryId);

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
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

  if (!memory) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Memory not found</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.typeBadge}>
          <Text style={styles.typeBadgeText}>{memory.type}</Text>
        </View>
        <Text style={styles.timestamp}>
          {new Date(memory.createdAt).toLocaleString()}
        </Text>
      </View>

      <Text style={styles.content}>{memory.content}</Text>

      {memory.tags && memory.tags.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Tags</Text>
          <View style={styles.tags}>
            {memory.tags.map((tag, index) => (
              <View key={index} style={styles.tag}>
                <Text style={styles.tagText}>#{tag}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {memory.concepts && memory.concepts.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Related Concepts</Text>
          <View style={styles.concepts}>
            {memory.concepts.map((conceptName, index) => (
              <View key={index} style={styles.conceptChip}>
                <Text style={styles.conceptText}>{conceptName}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {memory.metadata && Object.keys(memory.metadata).length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Metadata</Text>
          {Object.entries(memory.metadata).map(([key, value]) => (
            <View key={key} style={styles.metadataRow}>
              <Text style={styles.metadataKey}>{key}:</Text>
              <Text style={styles.metadataValue}>{JSON.stringify(value)}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  typeBadge: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  typeBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  timestamp: {
    fontSize: 13,
    color: '#6B7280',
  },
  content: {
    fontSize: 16,
    color: '#1F2937',
    lineHeight: 24,
    padding: 16,
  },
  section: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tag: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    marginRight: 8,
    marginBottom: 8,
  },
  tagText: {
    fontSize: 13,
    color: '#4B5563',
  },
  concepts: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  conceptChip: {
    backgroundColor: '#DBEAFE',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    marginRight: 8,
    marginBottom: 8,
  },
  conceptText: {
    fontSize: 13,
    color: '#1E40AF',
    fontWeight: '500',
  },
  metadataRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  metadataKey: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
    marginRight: 8,
  },
  metadataValue: {
    fontSize: 13,
    color: '#1F2937',
    flex: 1,
  },
  errorText: {
    fontSize: 16,
    color: '#EF4444',
    textAlign: 'center',
  },
});
