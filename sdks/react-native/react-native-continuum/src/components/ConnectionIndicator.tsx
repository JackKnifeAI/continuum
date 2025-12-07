/**
 * Connection Indicator - Shows network connection status
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useConnectionStatus } from '../hooks';

export function ConnectionIndicator() {
  const { isConnected, type } = useConnectionStatus();

  return (
    <View style={styles.container}>
      <View
        style={[
          styles.indicator,
          { backgroundColor: isConnected ? '#10B981' : '#EF4444' },
        ]}
      />
      <Text style={styles.text}>
        {isConnected ? `Connected (${type || 'unknown'})` : 'Disconnected'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  indicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 6,
  },
  text: {
    fontSize: 12,
    color: '#6B7280',
  },
});
