'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Secure WebSocket Hook for Real-time Communication
 * 
 * Security Features:
 * - Token-based authentication
 * - Input validation and sanitization
 * - Rate limiting protection
 * - Automatic reconnection with exponential backoff
 * - Message validation and filtering
 * - XSS prevention
 * - Connection state management
 * 
 * @param url - WebSocket URL (undefined to disable connection)
 * @param authToken - Authentication token for secure connection
 */

type Message = {
  id: string;
  content: string;
  sender: string;
  timestamp: Date;
  chatId: string;
  content_type?: string;
};

type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error' | 'reconnecting';

// Security and performance configuration
const MAX_MESSAGE_LENGTH = 4000;
const MAX_MESSAGES_BUFFER = 1000;
const RECONNECT_INTERVALS = [1000, 2000, 5000, 10000, 30000]; // Exponential backoff
const MAX_RECONNECT_ATTEMPTS = 5;
const HEARTBEAT_INTERVAL = 30000; // 30 seconds

export function useWebSocket(url: string | undefined, authToken?: string) {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const messageQueue = useRef<string[]>([]);

  // Computed state
  const isConnected = connectionState === 'connected';

  // Utility functions
  const sanitizeMessage = useCallback((content: string): string => {
    // Basic XSS prevention
    return content
      .replace(/</g, '<')
      .replace(/>/g, '>')
      .replace(/"/g, '"')
      .replace(/'/g, '&#x27;')
      .trim();
  }, []);

  const validateMessage = useCallback((message: any): message is Message => {
    return (
      typeof message === 'object' &&
      message !== null &&
      typeof message.id === 'string' &&
      typeof message.content === 'string' &&
      typeof message.sender === 'string' &&
      typeof message.chatId === 'string' &&
      message.content.length <= MAX_MESSAGE_LENGTH
    );
  }, []);

  const buildSecureWebSocketUrl = useCallback((baseUrl: string, token?: string): string => {
    try {
      const urlObj = new URL(baseUrl);
      if (token) {
        urlObj.searchParams.set('token', token);
      }
      return urlObj.toString();
    } catch (error) {
      console.error('Invalid WebSocket URL:', error);
      throw new Error('Invalid WebSocket URL');
    }
  }, []);

  // Heartbeat mechanism
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL);
  }, []);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Connection management
  const connect = useCallback(() => {
    if (!url) {
      console.log('No URL provided, skipping WebSocket connection');
      setConnectionState('disconnected');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      setConnectionState('connecting');
      setError(null);

      const secureUrl = buildSecureWebSocketUrl(url, authToken);
      console.log('Connecting to secure WebSocket...');
      
      const ws = new WebSocket(secureUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionState('connected');
        setError(null);
        reconnectAttempts.current = 0;
        console.log('✅ Successfully connected to WebSocket server');
        
        // Start heartbeat
        startHeartbeat();
        
        // Send queued messages
        while (messageQueue.current.length > 0) {
          const queuedMessage = messageQueue.current.shift();
          if (queuedMessage && ws.readyState === WebSocket.OPEN) {
            ws.send(queuedMessage);
          }
        }
      };

      ws.onclose = (event) => {
        setConnectionState('disconnected');
        stopHeartbeat();
        
        console.log(`WebSocket connection closed: ${event.code} - ${event.reason}`);
        
        // Handle different close codes
        if (event.code === 4001) {
          setError('Authentication failed. Please log in again.');
          return;
        }
        
        if (event.code === 4003) {
          setError('Rate limit exceeded. Please slow down.');
          return;
        }

        // Attempt reconnection for normal closures
        if (event.code !== 1000 && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_INTERVALS[Math.min(reconnectAttempts.current, RECONNECT_INTERVALS.length - 1)];
          console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${MAX_RECONNECT_ATTEMPTS})`);
          
          setConnectionState('reconnecting');
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
          setError('Connection failed after multiple attempts. Please refresh the page.');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionState('error');
        setError('Connection error occurred');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle ping/pong
          if (data.type === 'pong') {
            return;
          }
          
          // Validate message structure
          if (!validateMessage(data)) {
            console.warn('Invalid message received:', data);
            return;
          }

          // Sanitize content
          const sanitizedMessage: Message = {
            ...data,
            content: sanitizeMessage(data.content),
            timestamp: new Date(data.timestamp || Date.now())
          };

          console.log('📨 Received valid message:', sanitizedMessage.id);
          
          // Add to messages with buffer limit
          setMessages((prev) => {
            const newMessages = [...prev, sanitizedMessage];
            return newMessages.slice(-MAX_MESSAGES_BUFFER);
          });
          
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionState('error');
      setError('Failed to establish connection');
    }
  }, [url, authToken, buildSecureWebSocketUrl, validateMessage, sanitizeMessage, startHeartbeat, stopHeartbeat]);

  // Disconnect function
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    stopHeartbeat();
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    
    setConnectionState('disconnected');
    reconnectAttempts.current = 0;
  }, [stopHeartbeat]);

  // Send message function with validation
  const sendMessage = useCallback((chatId: string, content: string) => {
    // Input validation
    if (!content.trim()) {
      console.warn('Cannot send empty message');
      return false;
    }

    if (content.length > MAX_MESSAGE_LENGTH) {
      console.warn(`Message too long: ${content.length} > ${MAX_MESSAGE_LENGTH}`);
      setError(`Message too long. Maximum ${MAX_MESSAGE_LENGTH} characters.`);
      return false;
    }

    // Sanitize content
    const sanitizedContent = sanitizeMessage(content);
    
    const message = {
      id: crypto.randomUUID(),
      chatId,
      content: sanitizedContent,
      timestamp: new Date().toISOString(),
      sender: 'You'
    };

    const messageStr = JSON.stringify(message);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(messageStr);
      console.log('📤 Sent message:', message.id);
      return true;
    } else {
      // Queue message for when connection is restored
      messageQueue.current.push(messageStr);
      console.log('📋 Queued message for later sending');
      return false;
    }
  }, [sanitizeMessage]);

  // Clear messages function
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Effect for connection management
  useEffect(() => {
    if (url) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [url, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    // Connection state
    isConnected,
    connectionState,
    error,
    
    // Messages
    messages,
    
    // Actions
    sendMessage,
    clearMessages,
    connect,
    disconnect,
  };
}
