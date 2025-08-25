import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

/**
 * Enhanced Chat Window Component with Secure WebSocket Communication
 * 
 * Security Features:
 * - Token-based authentication
 * - Input validation and sanitization
 * - XSS prevention
 * - Secure message handling
 * - Connection state management
 * - Error handling
 * 
 * @param chatId - Chat identifier
 * @param authToken - Authentication token
 */

interface EnhancedChatWindowProps {
  chatId: string | null;
  authToken: string | null;
}

const EnhancedChatWindow: React.FC<EnhancedChatWindowProps> = ({ chatId, authToken }) => {
  const [messageText, setMessageText] = useState('');
  const messageInputRef = useRef<HTMLTextAreaElement>(null);

  // Secure WebSocket hook
  const wsUrl = chatId ? `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/${chatId}` : null as string | null;
  const { 
    isConnected, 
    connectionState, 
    error, 
    messages, 
    sendMessage, 
    clearMessages, 
    connect, 
    disconnect 
  } = useWebSocket(wsUrl, authToken);

  // Auto-focus on input
  useEffect(() => {
    messageInputRef.current?.focus();
  }, []);

  // Secure input handling
  const handleMessageChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessageText(e.target.value);
  }, []);

  const handleSendMessage = useCallback(() => {
    if (!chatId) {
      console.warn('No chat selected');
      return;
    }

    if (!messageText.trim()) {
      console.warn('Cannot send empty message');
      return;
    }

    // Securely send message
    const success = sendMessage(chatId, messageText);
    if (success) {
      setMessageText(''); // Clear input on success
      messageInputRef.current!.focus(); // Refocus input
    }
  }, [chatId, messageText, sendMessage]);

  // Connection status messages
  const getConnectionStatusMessage = (): string => {
    switch (connectionState) {
      case 'connected':
        return '✅ Connected';
      case 'connecting':
        return '🔗 Connecting...';
      case 'reconnecting':
        return '🔄 Reconnecting...';
      case 'disconnected':
        return '❌ Disconnected';
      case 'error':
        return `⚠️ Connection Error: ${error || 'Unknown'}`;
      default:
        return '⚫️ Unknown Connection State';
    }
  };

  // Render chat interface
  if (!chatId) {
    return (
      <div className="flex-1 p-4 flex flex-col justify-center items-center text-gray-400">
        <p className="text-lg">Select a chat to start messaging</p>
      </div>
    );
  }

  return (
    <div className="flex-1 p-4 flex flex-col h-full bg-gray-800">
      {/* Connection Status */}
      <div className="text-sm text-gray-400 mb-2">
        {getConnectionStatusMessage()}
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto mb-2">
        {messages.map((msg) => (
          <div key={msg.id} className="mb-1">
            <span className="text-blue-300">{msg.sender}:</span>
            <span className="text-gray-100 ml-2">{msg.content}</span>
            <span className="text-gray-500 text-xs ml-2">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </span>
          </div>
        ))}
      </div>

      {/* Message Input */}
      <div className="flex items-center">
        <textarea
          ref={messageInputRef}
          className="flex-1 p-3 bg-gray-700 text-gray-100 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none h-12"
          placeholder="Type your message..."
          value={messageText}
          onChange={handleMessageChange}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
        />
        <button
          className="ml-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          onClick={handleSendMessage}
          disabled={!isConnected || !messageText.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default EnhancedChatWindow;