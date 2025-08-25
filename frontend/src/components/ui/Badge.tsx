'use client';

import { memo } from 'react';
import clsx from 'clsx';

interface BadgeProps {
  count: number;
  variant?: 'default' | 'muted' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const variantClasses = {
  default: 'bg-blue-600 text-white',
  muted: 'bg-gray-600 text-white',
  success: 'bg-green-600 text-white',
  warning: 'bg-yellow-600 text-white',
  error: 'bg-red-600 text-white',
};

const sizeClasses = {
  sm: 'text-xs px-1.5 py-0.5 min-w-[16px] h-4',
  md: 'text-xs px-2 py-1 min-w-[20px] h-5',
  lg: 'text-sm px-2.5 py-1 min-w-[24px] h-6',
};

const Badge = memo(({ count, variant = 'default', size = 'sm', className }: BadgeProps) => {
  if (count <= 0) return null;

  const displayCount = count > 99 ? '99+' : count.toString();

  return (
    <span
      className={clsx(
        'inline-flex items-center justify-center font-medium rounded-full text-center',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {displayCount}
    </span>
  );
});

Badge.displayName = 'Badge';

export default Badge;