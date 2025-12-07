/**
 * Memory Card Component - Displays a single memory
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ViewStyle,
} from 'react-native';
import type { Memory, MemoryCardProps } from '../types';

export function MemoryCard({
  memory,
  onPress,
  onLongPress,
  showMetadata = false,
  compact = false,
}: MemoryCardProps) {
  const handlePress = () => {
    onPress?.(memory);
  };

  const handleLongPress = () => {
    onLongPress?.(memory);
  };

  return (
    <TouchableOpacity
      style={[styles.card, compact && styles.cardCompact]}
      onPress={handlePress}
      onLongPress={handleLongPress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <View style={[styles.typeBadge, getTypeBadgeStyle(memory.type)]}>
          <Text style={styles.typeBadgeText}>{memory.type}</Text>
        </View>
        <Text style={styles.timestamp}>
          {formatTimestamp(memory.createdAt)}
        </Text>
      </View>

      <Text
        style={[styles.content, compact && styles.contentCompact]}
        numberOfLines={compact ? 2 : undefined}
      >
        {memory.content}
      </Text>

      {memory.tags && memory.tags.length > 0 && (
        <View style={styles.tags}>
          {memory.tags.slice(0, 3).map((tag, index) => (
            <View key={index} style={styles.tag}>
              <Text style={styles.tagText}>#{tag}</Text>
            </View>
          ))}
          {memory.tags.length > 3 && (
            <Text style={styles.moreTag}>+{memory.tags.length - 3}</Text>
          )}
        </View>
      )}

      {showMetadata && memory.metadata && (
        <View style={styles.metadata}>
          <Text style={styles.metadataText}>
            {Object.keys(memory.metadata).length} metadata fields
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

function getTypeBadgeStyle(type: string): ViewStyle {
  const colors: Record<string, string> = {
    episodic: '#3B82F6',
    semantic: '#10B981',
    procedural: '#F59E0B',
    working: '#8B5CF6',
  };

  return {
    backgroundColor: colors[type] || '#6B7280',
  };
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (minutes < 60) {
    return `${minutes}m ago`;
  } else if (hours < 24) {
    return `${hours}h ago`;
  } else if (days < 7) {
    return `${days}d ago`;
  } else {
    return date.toLocaleDateString();
  }
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardCompact: {
    padding: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  typeBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  timestamp: {
    fontSize: 12,
    color: '#6B7280',
  },
  content: {
    fontSize: 15,
    color: '#1F2937',
    lineHeight: 22,
    marginBottom: 8,
  },
  contentCompact: {
    fontSize: 14,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  tag: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 6,
    marginBottom: 4,
  },
  tagText: {
    fontSize: 12,
    color: '#4B5563',
  },
  moreTag: {
    fontSize: 12,
    color: '#6B7280',
    paddingVertical: 4,
  },
  metadata: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  metadataText: {
    fontSize: 12,
    color: '#9CA3AF',
    fontStyle: 'italic',
  },
});
