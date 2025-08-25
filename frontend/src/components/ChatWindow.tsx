'use client';

import { useState, useEffect, useRef } from 'react';
import clsx from 'clsx';
import { format } from 'date-fns';
import { useWebSocket } from '@/hooks/useWebSocket';

type ChatWindowProps = {
  chatId: string | null;
  authToken: string | null;
};

export default function ChatWindow({ chatId, authToken }: ChatWindowProps) {
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsUrl = chatId ? `ws://localhost:8000/ws/${encodeURIComponent(chatId)}` : undefined;
  console.log('WebSocket URL:', wsUrl);
  const { messages, sendMessage, isConnected } = useWebSocket(wsUrl);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !chatId || !isConnected) return;

    sendMessage(chatId, newMessage);
    setNewMessage('');
  };

  const [chatHistory, setChatHistory] = useState<Record<string, unknown>[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!chatId || !authToken) return;
      setLoadingHistory(true);
      try {
        const response = await fetch(`http://localhost:8000/api/messages?chat_id=${chatId}`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        });
        const data: Record<string, unknown>[] = await response.json();
        setChatHistory(data);
      } catch (error) {
        console.error("Failed to fetch chat history:", error);
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchHistory();
  }, [chatId, authToken]);

  const allMessages = [...chatHistory, ...messages.filter(msg => msg.chatId === chatId)].sort((a, b) => {
    const aTime = (a as Record<string, unknown>).created_at || (a as Record<string, unknown>).timestamp;
    const bTime = (b as Record<string, unknown>).created_at || (b as Record<string, unknown>).timestamp;
    return new Date(String(aTime)).getTime() - new Date(String(bTime)).getTime();
  });
  const uniqueMessages = allMessages.filter((v, i, a) => a.findIndex(t => String((t as Record<string, unknown>).id) === String((v as Record<string, unknown>).id)) === i);

  if (!chatId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-900">
        <p className="text-gray-400">Select a chat to start messaging</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-900">
      <div className="p-2 border-b border-gray-700 flex items-center justify-between">
        <span className="text-white">Chat ID: {chatId}</span>
        <span className={clsx('px-2 py-1 rounded text-sm', {
          'bg-green-600 text-white': isConnected,
          'bg-red-600 text-white': !isConnected,
        })}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {loadingHistory ? (
          <div className="text-gray-400 text-center mt-4">Loading history...</div>
        ) : uniqueMessages.length === 0 ? (
          <div className="text-gray-400 text-center mt-4">No messages yet</div>
        ) : (
          uniqueMessages.map((message) => {
            const msg = message as Record<string, unknown>;
            return (
              <div
                key={String(msg.id)}
                className={clsx('mb-4 flex', {
                  'justify-end': msg.sender === 'You' || !msg.from_user_id,
                })}
              >
                <div
                  className={clsx('rounded-lg p-3 max-w-[70%]', {
                    'bg-blue-600 text-white': msg.sender === 'You' || !msg.from_user_id,
                    'bg-gray-700 text-white': msg.sender !== 'You' && msg.from_user_id,
                  })}
                >
                  <p>{String(msg.content || msg.text || '')}</p>
                  <span className="text-xs text-gray-300 mt-1 block">
                    {format(new Date(String(msg.timestamp || msg.created_at)), 'HH:mm')}
                  </span>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-700">
        <div className="flex space-x-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder={isConnected ? "Type a message..." : "Connecting..."}
            disabled={!isConnected}
            className="flex-1 rounded-lg bg-gray-700 text-white px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!isConnected}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
