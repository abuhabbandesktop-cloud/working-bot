'use client';

import { memo } from 'react';
import clsx from 'clsx';
import { format } from 'date-fns';
import Avatar from '../ui/Avatar';

export interface MessageData {
  id: string;
  tg_message_id?: number;
  chat_id: string;
  from_user_id?: number;
  content_type: string;
  text?: string;
  media_path?: string;
  created_at: string;
  sent: boolean;
  delivered: boolean;
  seen: boolean;
  sender?: string;
  timestamp?: string;
  content?: string;
  reply_to_message_id?: number;
  is_edited?: boolean;
  edit_date?: string;
}

interface MessageBubbleProps {
  message: MessageData;
  isOwn: boolean;
  showAvatar?: boolean;
  userName?: string;
  userAvatar?: string;
  isGrouped?: boolean; // If this message is grouped with previous message from same sender
}

const MessageBubble = memo(({ 
  message, 
  isOwn, 
  showAvatar = true, 
  userName, 
  userAvatar,
  isGrouped = false 
}: MessageBubbleProps) => {
  const messageText = message.text || message.content || '';
  const timestamp = message.created_at || message.timestamp || '';
  const isCommand = message.content_type === 'command';
  const isMedia = ['photo', 'video', 'voice', 'document'].includes(message.content_type);

  const getStatusIcon = () => {
    if (!isOwn) return null;
    
    if (!message.sent) return '⏳';
    if (message.seen) return '✓✓';
    if (message.delivered) return '✓✓';
    return '✓';
  };

  const getStatusColor = () => {
    if (!isOwn) return '';
    
    if (!message.sent) return 'text-gray-400';
    if (message.seen) return 'text-blue-400';
    if (message.delivered) return 'text-gray-300';
    return 'text-gray-300';
  };

  const getMediaIcon = (contentType: string) => {
    switch (contentType) {
      case 'photo': return '📷';
      case 'video': return '🎥';
      case 'voice': return '🎤';
      case 'document': return '📄';
      default: return '📎';
    }
  };

  return (
    <div className={clsx(
      'flex mb-4 group',
      {
        'justify-end': isOwn,
        'justify-start': !isOwn,
        'mb-1': isGrouped,
      }
    )}>
      {/* Avatar for received messages */}
      {!isOwn && showAvatar && !isGrouped && (
        <div className="flex-shrink-0 mr-3">
          <Avatar
            src={userAvatar}
            name={userName || 'User'}
            size="sm"
            type="private"
          />
        </div>
      )}
      
      {/* Spacer when avatar is hidden but needed for alignment */}
      {!isOwn && (!showAvatar || isGrouped) && (
        <div className="w-8 mr-3 flex-shrink-0" />
      )}

      {/* Message content */}
      <div className={clsx(
        'max-w-[70%] flex flex-col',
        {
          'items-end': isOwn,
          'items-start': !isOwn,
        }
      )}>
        {/* Sender name for received messages in groups */}
        {!isOwn && !isGrouped && userName && (
          <div className="text-xs text-blue-400 font-medium mb-1 px-1">
            {userName}
          </div>
        )}

        {/* Message bubble */}
        <div
          className={clsx(
            'relative px-4 py-2 rounded-2xl shadow-sm',
            'transition-all duration-200 hover:shadow-md',
            {
              // Own messages (sent)
              'bg-blue-600 text-white': isOwn && !isCommand,
              'bg-blue-500 text-white': isOwn && isCommand,
              
              // Received messages
              'bg-gray-700 text-white': !isOwn && !isCommand,
              'bg-gray-600 text-white': !isOwn && isCommand,
              
              // Rounded corners based on position
              'rounded-br-md': isOwn,
              'rounded-bl-md': !isOwn,
            }
          )}
        >
          {/* Command indicator */}
          {isCommand && (
            <div className="flex items-center space-x-1 mb-1">
              <span className="text-xs">⚡</span>
              <span className="text-xs font-medium opacity-75">Command</span>
            </div>
          )}

          {/* Media indicator */}
          {isMedia && (
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-lg">{getMediaIcon(message.content_type)}</span>
              <div className="flex-1">
                <div className="text-sm font-medium capitalize">
                  {message.content_type}
                </div>
                {message.media_path && (
                  <div className="text-xs opacity-75">
                    {message.media_path.split('/').pop()}
                  </div>
                )}
              </div>
              <button className="text-xs bg-black bg-opacity-20 px-2 py-1 rounded hover:bg-opacity-30 transition-colors">
                View
              </button>
            </div>
          )}

          {/* Message text */}
          {messageText && (
            <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
              {messageText}
            </div>
          )}

          {/* Edited indicator */}
          {message.is_edited && (
            <div className="text-xs opacity-60 mt-1">
              edited
            </div>
          )}

          {/* Timestamp and status */}
          <div className={clsx(
            'flex items-center justify-end space-x-1 mt-1',
            {
              'justify-between': !isOwn,
              'justify-end': isOwn,
            }
          )}>
            <span className="text-xs opacity-60">
              {format(new Date(timestamp), 'HH:mm')}
            </span>
            
            {/* Message status for own messages */}
            {isOwn && (
              <span className={clsx('text-xs', getStatusColor())}>
                {getStatusIcon()}
              </span>
            )}
          </div>

          {/* Message tail */}
          <div
            className={clsx(
              'absolute top-0 w-0 h-0',
              {
                // Own message tail (right side)
                'right-0 translate-x-1 border-l-8 border-t-8 border-l-transparent': isOwn && !isCommand,
                'border-t-blue-600': isOwn && !isCommand,
                'border-t-blue-500': isOwn && isCommand,
                
                // Received message tail (left side)
                'left-0 -translate-x-1 border-r-8 border-t-8 border-r-transparent': !isOwn && !isCommand,
                'border-t-gray-700': !isOwn && !isCommand,
                'border-t-gray-600': !isOwn && isCommand,
              }
            )}
          />
        </div>
      </div>
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';

export default MessageBubble;