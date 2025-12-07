/**
 * Stats Component
 */

import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import type { SyncStatus } from '../shared/types';

interface StatsProps {
  syncStatus: SyncStatus | null;
}

export const Stats: React.FC<StatsProps> = ({ syncStatus }) => {
  if (!syncStatus) return null;

  return (
    <div className="stats">
      <div className="stat">
        <div className="stat-label">Status</div>
        <div className={`stat-value ${syncStatus.isOnline ? 'online' : 'offline'}`}>
          {syncStatus.isOnline ? 'Online' : 'Offline'}
        </div>
      </div>

      {syncStatus.lastSync && (
        <div className="stat">
          <div className="stat-label">Last Sync</div>
          <div className="stat-value">
            {formatDistanceToNow(new Date(syncStatus.lastSync), { addSuffix: true })}
          </div>
        </div>
      )}

      {syncStatus.pendingItems > 0 && (
        <div className="stat">
          <div className="stat-label">Pending</div>
          <div className="stat-value">{syncStatus.pendingItems}</div>
        </div>
      )}
    </div>
  );
};
