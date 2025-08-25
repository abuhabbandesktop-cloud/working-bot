'use client';

import { useState, useEffect, useMemo } from 'react';
import ChatSectionTabs, { ChatSection } from './ChatSectionTabs';
import ChatListItem, { ChatData } from './ChatListItem';

interface OrganizedChats {
  users: ChatData[];
  groups: ChatData[];
  channels: ChatData[];
  saved: ChatData[];
}

interface EnhancedChatSidebarProps {
  onChatSelect: (chatId: string) => void;
  selectedChatId: string | null;
  authToken: string | null;
  onLogout: () => void;
}

export default function EnhancedChatSidebar({ 
  onChatSelect, 
  selectedChatId, 
  authToken, 
  onLogout 
}: EnhancedChatSidebarProps) {
  const [organizedChats, setOrganizedChats] = useState<OrganizedChats>({
    users: [],
    groups: [],
    channels: [],
    saved: []
  });
  const [activeSection, setActiveSection] = useState<ChatSection>('users');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch organized chats from the new API endpoint
  useEffect(() => {
    const fetchOrganizedChats = async () => {
      if (!authToken) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        console.log('Fetching organized chats...');
        
        const response = await fetch('http://localhost:8000/api/chats/organized', {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.status === 401) {
          onLogout();
          return;
        }

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Received organized chats:', data);
        
        // Transform the data to match our ChatData interface
        const transformedData: OrganizedChats = {
          users: data.users?.map((chat: Record<string, unknown>) => ({
            ...chat,
            id: String(chat.id),
          })) as ChatData[] || [],
          groups: data.groups?.map((chat: Record<string, unknown>) => ({
            ...chat,
            id: String(chat.id),
          })) as ChatData[] || [],
          channels: data.channels?.map((chat: Record<string, unknown>) => ({
            ...chat,
            id: String(chat.id),
          })) as ChatData[] || [],
          saved: data.saved?.map((chat: Record<string, unknown>) => ({
            ...chat,
            id: String(chat.id),
          })) as ChatData[] || []
        };

        setOrganizedChats(transformedData);
      } catch (error) {
        console.error('Error fetching organized chats:', error);
        setError('Failed to load chats');
        // Fallback to empty state
        setOrganizedChats({
          users: [],
          groups: [],
          channels: [],
          saved: []
        });
      } finally {
        setLoading(false);
      }
    };

    fetchOrganizedChats();
  }, [authToken, onLogout]);

  // Calculate counts for each section
  const sectionCounts = useMemo(() => ({
    users: organizedChats.users.length,
    groups: organizedChats.groups.length,
    channels: organizedChats.channels.length,
    saved: organizedChats.saved.length,
  }), [organizedChats]);

  // Filter chats based on search query
  const filteredChats = useMemo(() => {
    const chats = organizedChats[activeSection];
    if (!searchQuery.trim()) return chats;

    return chats.filter(chat => 
      chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      chat.last_message?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      chat.user_info?.username?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [organizedChats, activeSection, searchQuery]);

  if (loading) {
    return (
      <div className="w-80 h-full bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <div className="flex justify-between items-center">
            <div className="h-6 bg-gray-600 rounded w-20 animate-pulse"></div>
            <button 
              onClick={onLogout}
              className="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm"
            >
              Logout
            </button>
          </div>
        </div>
        
        <div className="flex border-b border-gray-700">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="flex-1 p-3">
              <div className="h-4 bg-gray-600 rounded animate-pulse"></div>
            </div>
          ))}
        </div>
        
        <div className="flex-1 p-4 space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gray-600 rounded-full animate-pulse"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-600 rounded animate-pulse"></div>
                <div className="h-3 bg-gray-600 rounded w-3/4 animate-pulse"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 h-full bg-gray-800 border-r border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-xl font-bold text-white">Telegram</h2>
          <button 
            onClick={onLogout}
            className="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-2 rounded text-sm transition-colors"
          >
            Logout
          </button>
        </div>
        
        {/* Search Bar */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-gray-700 text-white placeholder-gray-400 rounded-lg px-4 py-2 pl-10 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
            <span className="text-gray-400">🔍</span>
          </div>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Section Tabs */}
      <ChatSectionTabs
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        counts={sectionCounts}
      />

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {error ? (
          <div className="p-4 text-center">
            <p className="text-red-400 mb-2">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="text-blue-400 hover:text-blue-300 underline"
            >
              Retry
            </button>
          </div>
        ) : filteredChats.length === 0 ? (
          <div className="p-4 text-center text-gray-400">
            {searchQuery ? 'No chats found' : `No ${activeSection} yet`}
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {filteredChats.map((chat) => (
              <ChatListItem
                key={chat.id}
                chat={chat}
                isSelected={selectedChatId === chat.id}
                onClick={onChatSelect}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}