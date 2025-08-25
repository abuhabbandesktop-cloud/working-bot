'use client';

import { memo } from 'react';
import clsx from 'clsx';
import { format, isToday, isYesterday, formatDistanceToNow } from 'date-fns';
import Avatar from '@/components/ui/Avatar';
import StatusIndicator from '@/components/ui/StatusIndicator';
import Badge from '@/components/ui/Badge';

export interface ChatData {
  id: string;
  type: 'private' | 'group' | 'supergroup' | 'channel';
  title: string;
  description?: string;
  last_message?: string;
  last_activity?: string;
  unread_count?: number;
  is_pinned?: boolean;
  is_muted?: boolean;
  member_count?: number;
  user_info?: {
    first_name?: string;
    last_name?: string;
    username?: string;
    is_online?: boolean;
    last_seen?: string;
    avatar_url?: string;
  };
  created_at?: string;
}

interface ChatListItemProps {
  chat: ChatData;
  isSelected: boolean;
  onClick: (chatId: string) => void;
}

function formatTimestamp(timestamp?: string): string {
  if (!timestamp) return '';
  
  const date = new Date(timestamp);
  
  if (isToday(date)) {
    return format(date, 'HH:mm');
  } else if (isYesterday(date)) {
    return 'Yesterday';
  } else {
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays < 7) {
      return format(date, 'EEE'); // Mon, Tue, etc.
    } else {
      return format(date, 'dd/MM');
    }
  }
}

function getChatIcon(type: ChatData['type']): string {
  switch (type) {
    case 'private':
      return '👤';
    case 'group':
    case 'supergroup':
      return '👥';
    case 'channel':
      return '📢';
    default:
      return '💬';
  }
}

function truncateMessage(message: string, maxLength: number = 50): string {
  if (message.length <= maxLength) return message;
  return message.substring(0, maxLength) + '...';
}

const ChatListItem = memo(({ chat, isSelected, onClick }: ChatListItemProps) => {
  const displayName = chat.title || 
    (chat.user_info ? 
      `${chat.user_info.first_name || ''} ${chat.user_info.last_name || ''}`.trim() || 
      chat.user_info.username || 
      `User ${chat.id}` 
      : `Chat ${chat.id}`);

  const isOnline = chat.type === 'private' && chat.user_info?.is_online;
  const lastSeen = chat.user_info?.last_seen;

  return (
    <div
      onClick={() => onClick(chat.id)}
      className={clsx(
        'relative flex items-center p-3 cursor-pointer transition-all duration-200 border-l-4',
        'hover:bg-gray-700 active:bg-gray-600',
        {
          'bg-gray-700 border-l-blue-500': isSelected,
          'border-l-transparent': !isSelected,
          'opacity-60': chat.is_muted,
        }
      )}
    >
      {/* Pin indicator */}
      {chat.is_pinned && (
        <div className="absolute left-1 top-1">
          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
        </div>
      )}

      {/* Avatar */}
      <div className="relative flex-shrink-0">
        <Avatar
          src={chat.user_info?.avatar_url}
          name={displayName}
          size="md"
          type={chat.type}
        />
        {chat.type === 'private' && (
          <StatusIndicator
            isOnline={isOnline}
            lastSeen={lastSeen}
            className="absolute -bottom-0.5 -right-0.5"
          />
        )}
      </div>

      {/* Chat info */}
      <div className="flex-1 min-w-0 ml-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 min-w-0">
            <h3 className={clsx(
              'font-semibold text-sm truncate',
              {
                'text-white': !chat.is_muted,
                'text-gray-400': chat.is_muted,
              }
            )}>
              {displayName}
            </h3>
            
            {/* Chat type icon for groups/channels */}
            {chat.type !== 'private' && (
              <span className="text-xs text-gray-400 flex-shrink-0">
                {getChatIcon(chat.type)}
              </span>
            )}
            
            {/* Muted indicator */}
            {chat.is_muted && (
              <span className="text-xs text-gray-500 flex-shrink-0">🔇</span>
            )}
          </div>

          <div className="flex items-center space-x-2 flex-shrink-0">
            {/* Timestamp */}
            <span className="text-xs text-gray-400">
              {formatTimestamp(chat.last_activity)}
            </span>
            
            {/* Unread badge */}
            {chat.unread_count && chat.unread_count > 0 && (
              <Badge count={chat.unread_count} />
            )}
          </div>
        </div>

        {/* Last message preview */}
        <div className="flex items-center justify-between mt-1">
          <p className={clsx(
            'text-sm truncate',
            {
              'text-gray-300': chat.unread_count && chat.unread_count > 0,
              'text-gray-400': !chat.unread_count || chat.unread_count === 0,
            }
          )}>
            {chat.last_message ? truncateMessage(chat.last_message) : 'No messages yet'}
          </p>
          
          {/* Member count for groups */}
          {chat.type !== 'private' && chat.member_count && chat.member_count > 0 && (
            <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
              {chat.member_count} members
            </span>
          )}
        </div>

        {/* Online status text for private chats */}
        {chat.type === 'private' && !isOnline && lastSeen && (
          <p className="text-xs text-gray-500 mt-0.5">
            Last seen {(() => {
              try {
                return formatDistanceToNow(new Date(lastSeen), { addSuffix: true });
              } catch {
                return 'recently';
              }
            })()}
          </p>
        )}
      </div>
    </div>
  );
});

ChatListItem.displayName = 'ChatListItem';

export default ChatListItem;