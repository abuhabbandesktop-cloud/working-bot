'use client';

import { useState, useEffect } from 'react';
import EnhancedChatSidebar from '@/components/chat/EnhancedChatSidebar';
import EnhancedChatWindow from '@/components/chat/EnhancedChatWindow';
import LoginForm from '@/components/LoginForm';

/**
 * Main Application Page with Secure Authentication and Real-time Communication
 *
 * Security Features:
 * - Token-based authentication with secure storage
 * - WebSocket connection with authentication
 * - Session management with proper cleanup
 * - Secure localStorage handling
 * - Input validation and sanitization
 *
 * Architecture:
 * - Authentication flow with login/logout
 * - Chat selection and management
 * - Real-time messaging with WebSocket
 * - Responsive UI with sidebar and chat window
 */

export default function Home() {
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing auth token on page load
  useEffect(() => {
    const initializeAuth = () => {
      try {
        // Get token from secure storage
        const token = localStorage.getItem('authToken');
        if (token) {
          // Basic token validation
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            // Check if token is expired
            if (payload.exp && payload.exp * 1000 > Date.now()) {
              setAuthToken(token);
              setIsAuthenticated(true);
            } else {
              // Token expired, remove it
              localStorage.removeItem('authToken');
            }
          } catch (e) {
            // Invalid token format, remove it
            localStorage.removeItem('authToken');
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const handleChatSelect = (chatId: string) => {
    setSelectedChatId(chatId);
  };

  const handleLogin = (token: string) => {
    try {
      // Validate token format
      const payload = JSON.parse(atob(token.split('.')[1]));
      
      // Store token securely
      localStorage.setItem('authToken', token);
      
      setAuthToken(token);
      setIsAuthenticated(true);
      
      console.log('✅ User successfully authenticated');
    } catch (error) {
      console.error('Invalid token format:', error);
    }
  };

  const handleLogout = () => {
    // Clear authentication state
    setAuthToken(null);
    setIsAuthenticated(false);
    setSelectedChatId(null);
    
    // Clear secure storage
    localStorage.removeItem('authToken');
    
    console.log('👋 User logged out successfully');
  };

  // Show loading state while initializing auth
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  // Show login form if not authenticated
  if (!isAuthenticated) {
    return <LoginForm onLogin={handleLogin} />;
  }

  // Main application interface
  return (
    <main className="flex h-screen bg-gray-900">
      <EnhancedChatSidebar
        onChatSelect={handleChatSelect}
        selectedChatId={selectedChatId}
        authToken={authToken}
        onLogout={handleLogout}
      />
      <EnhancedChatWindow
        chatId={selectedChatId}
        authToken={authToken}
      />
    </main>
  );
}
