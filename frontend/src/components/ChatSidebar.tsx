'use client';

import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { format } from 'date-fns';

type Chat = {
  id: string;
  name: string;
  lastMessage?: string;
  timestamp?: Date;
};

type ChatSidebarProps = {
  onChatSelect: (chatId: string) => void;
  selectedChatId: string | null;
  authToken: string | null;
  onLogout: () => void;
};

export default function ChatSidebar({ onChatSelect, selectedChatId, authToken, onLogout }: ChatSidebarProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch chats from the API
  useEffect(() => {
    const fetchChats = async () => {
      if (!authToken) {
        setLoading(false);
        return;
      }

      try {
        console.log('Fetching chats...');
        const response = await fetch('http://localhost:8000/api/chats', {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
        });
        console.log('Response status:', response.status);
        
        if (response.status === 401) {
          // Token expired or invalid, logout
          onLogout();
          return;
        }
        
        const data = await response.json();
        console.log('Received chats:', data);
        
        // If no chats exist, create a default one
        if (data.length === 0) {
          console.log('No chats found, creating default chat...');
          const defaultChat = { id: '1', name: 'General Chat' };
          setChats([defaultChat]);
        } else {
          setChats(data.map((chat: Record<string, unknown>) => ({
            id: String(chat.id),
            name: String(chat.title) || `Chat ${chat.id}`,
          })));
        }
      } catch (error) {
        console.error('Error fetching chats:', error);
        // Set default chat on error
        setChats([{ id: '1', name: 'General Chat' }]);
      } finally {
        setLoading(false);
      }
    };
    fetchChats();
  }, [authToken, onLogout]);

  // Add loading state to UI
  if (loading) {
    return (
      <div className="w-64 h-full bg-gray-800 border-r border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Loading chats...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="w-64 h-full bg-gray-800 border-r border-gray-700 flex flex-col">
      <div className="p-4 border-b border-gray-700 flex justify-between items-center">
        <h2 className="text-xl font-bold text-white">Chats</h2>
        <button 
          onClick={onLogout}
          className="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm"
        >
          Logout
        </button>
      </div>
      <div className="overflow-y-auto flex-1">
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={clsx(
              'p-4 cursor-pointer hover:bg-gray-700 transition-colors',
              {
                'bg-gray-700': selectedChatId === chat.id,
              }
            )}
            onClick={() => onChatSelect(chat.id)}
          >
            <h3 className="text-white font-medium">{chat.name}</h3>
            {chat.lastMessage && (
              <p className="text-gray-400 text-sm truncate">
                {chat.lastMessage}
              </p>
            )}
            {chat.timestamp && (
              <span className="text-xs text-gray-500">
                {format(chat.timestamp, 'HH:mm')}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
