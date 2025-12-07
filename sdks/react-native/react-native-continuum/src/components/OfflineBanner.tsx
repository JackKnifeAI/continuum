/**
 * Offline Banner - Shows when device is offline
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useOfflineStatus } from '../hooks';

export function OfflineBanner() {
  const isOffline = useOfflineStatus();

  if (!isOffline) {
    return null;
  }

  return (
    <View style={styles.banner}>
      <Text style={styles.text}>Offline Mode - Changes will sync when online</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: '#FEF3C7',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#FCD34D',
  },
  text: {
    fontSize: 14,
    color: '#92400E',
    textAlign: 'center',
    fontWeight: '500',
  },
});
