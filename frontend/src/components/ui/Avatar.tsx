'use client';

import { memo } from 'react';
import clsx from 'clsx';
import Image from 'next/image';

interface AvatarProps {
  src?: string;
  name: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  type?: 'private' | 'group' | 'supergroup' | 'channel';
  className?: string;
}

const sizeClasses = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
  xl: 'w-16 h-16 text-lg',
};

const typeColors = {
  private: 'bg-blue-500',
  group: 'bg-green-500',
  supergroup: 'bg-green-500',
  channel: 'bg-purple-500',
};

const typeIcons = {
  private: '👤',
  group: '👥',
  supergroup: '👥',
  channel: '📢',
};

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

function generateColorFromName(name: string): string {
  const colors = [
    'bg-red-500',
    'bg-blue-500',
    'bg-green-500',
    'bg-yellow-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-indigo-500',
    'bg-teal-500',
  ];
  
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  return colors[Math.abs(hash) % colors.length];
}

const Avatar = memo(({ src, name, size = 'md', type = 'private', className }: AvatarProps) => {
  const initials = getInitials(name);
  const colorClass = type ? typeColors[type] : generateColorFromName(name);

  if (src) {
    return (
      <div className={clsx('relative', className)}>
        <div className={clsx('relative overflow-hidden rounded-full border-2 border-gray-600', sizeClasses[size])}>
          <Image
            src={src}
            alt={name}
            fill
            className="object-cover"
            onError={() => {
              // This will be handled by Next.js Image component
              console.log('Image failed to load, showing fallback');
            }}
          />
        </div>
        {type !== 'private' && (
          <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-gray-800 rounded-full flex items-center justify-center">
            <span className="text-xs">{typeIcons[type]}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={clsx('relative', className)}>
      <div
        className={clsx(
          'rounded-full flex items-center justify-center text-white font-semibold border-2 border-gray-600',
          sizeClasses[size],
          colorClass
        )}
      >
        {initials}
      </div>
      {type !== 'private' && (
        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-gray-800 rounded-full flex items-center justify-center">
          <span className="text-xs">{typeIcons[type]}</span>
        </div>
      )}
    </div>
  );
});

Avatar.displayName = 'Avatar';

export default Avatar;