/**
 * Sync Status Badge - Shows sync status indicator
 */

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useSyncStatus } from '../hooks';

export function SyncStatusBadge() {
  const { isSyncing, lastSyncTime, pendingOperations } = useSyncStatus();

  if (!isSyncing && pendingOperations === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      {isSyncing ? (
        <>
          <ActivityIndicator size="small" color="#3B82F6" />
          <Text style={styles.text}>Syncing...</Text>
        </>
      ) : pendingOperations > 0 ? (
        <>
          <View style={styles.pendingDot} />
          <Text style={styles.text}>{pendingOperations} pending</Text>
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  text: {
    fontSize: 12,
    color: '#3B82F6',
    marginLeft: 6,
    fontWeight: '500',
  },
  pendingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#F59E0B',
  },
});
