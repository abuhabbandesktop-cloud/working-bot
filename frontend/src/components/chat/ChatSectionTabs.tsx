'use client';

import clsx from 'clsx';

export type ChatSection = 'users' | 'groups' | 'channels' | 'saved';

interface ChatSectionTabsProps {
  activeSection: ChatSection;
  onSectionChange: (section: ChatSection) => void;
  counts: {
    users: number;
    groups: number;
    channels: number;
    saved: number;
  };
}

const sections = [
  { key: 'users' as ChatSection, label: 'Users', icon: '👤' },
  { key: 'groups' as ChatSection, label: 'Groups', icon: '👥' },
  { key: 'channels' as ChatSection, label: 'Channels', icon: '📢' },
  { key: 'saved' as ChatSection, label: 'Saved', icon: '🔖' },
];

export default function ChatSectionTabs({ activeSection, onSectionChange, counts }: ChatSectionTabsProps) {
  return (
    <div className="flex border-b border-gray-700 bg-gray-800">
      {sections.map((section) => (
        <button
          key={section.key}
          onClick={() => onSectionChange(section.key)}
          className={clsx(
            'flex-1 px-3 py-3 text-sm font-medium transition-colors relative',
            'hover:bg-gray-700 focus:outline-none focus:bg-gray-700',
            {
              'text-blue-400 bg-gray-700': activeSection === section.key,
              'text-gray-300': activeSection !== section.key,
            }
          )}
        >
          <div className="flex items-center justify-center space-x-1">
            <span className="text-base">{section.icon}</span>
            <span className="hidden sm:inline">{section.label}</span>
            {counts[section.key] > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-600 text-white rounded-full min-w-[18px] text-center">
                {counts[section.key]}
              </span>
            )}
          </div>
          {activeSection === section.key && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400" />
          )}
        </button>
      ))}
    </div>
  );
}