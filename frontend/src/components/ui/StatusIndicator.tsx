'use client';

import { memo } from 'react';
import clsx from 'clsx';

interface StatusIndicatorProps {
  isOnline?: boolean;
  lastSeen?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'w-2 h-2',
  md: 'w-3 h-3',
  lg: 'w-4 h-4',
};

const StatusIndicator = memo(({ isOnline, lastSeen, className, size = 'md' }: StatusIndicatorProps) => {
  if (!isOnline && !lastSeen) {
    return null;
  }

  return (
    <div
      className={clsx(
        'rounded-full border-2 border-gray-800 flex items-center justify-center',
        sizeClasses[size],
        {
          'bg-green-500': isOnline,
          'bg-gray-500': !isOnline,
        },
        className
      )}
      title={isOnline ? 'Online' : lastSeen ? `Last seen ${lastSeen}` : 'Offline'}
    >
      {isOnline && (
        <div className="w-full h-full rounded-full bg-green-400 animate-pulse" />
      )}
    </div>
  );
});

StatusIndicator.displayName = 'StatusIndicator';

export default StatusIndicator;