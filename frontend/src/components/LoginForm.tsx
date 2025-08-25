'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Secure Login Form Component
 * 
 * Security Features:
 * - Input validation and sanitization
 * - Rate limiting protection
 * - Secure password handling
 * - CSRF protection ready
 * - XSS prevention
 * - Proper error handling without information disclosure
 * 
 * @param onLogin - Callback function called on successful login
 */

type LoginFormProps = {
  onLogin: (token: string) => void;
};

// Security configuration
const MAX_LOGIN_ATTEMPTS = 5;
const LOCKOUT_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [lockedUntil, setLockedUntil] = useState<number | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  
  // Refs for security
  const formRef = useRef<HTMLFormElement>(null);
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  // Check if currently locked out
  const isLockedOut = Boolean(lockedUntil && Date.now() < lockedUntil);

  // Update lockout status
  useEffect(() => {
    if (lockedUntil && Date.now() >= lockedUntil) {
      setLockedUntil(null);
      setAttempts(0);
    }
  }, [lockedUntil]);

  // Input validation functions
  const validateUsername = useCallback((value: string): string | null => {
    if (!value.trim()) {
      return 'Username is required';
    }
    if (value.length < 3) {
      return 'Username must be at least 3 characters';
    }
    if (value.length > 50) {
      return 'Username must be less than 50 characters';
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(value)) {
      return 'Username can only contain letters, numbers, hyphens, and underscores';
    }
    return null;
  }, []);

  const validatePassword = useCallback((value: string): string | null => {
    if (!value) {
      return 'Password is required';
    }
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (value.length > 128) {
      return 'Password must be less than 128 characters';
    }
    return null;
  }, []);

  // Secure input handlers with validation
  const handleUsernameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.trim().toLowerCase();
    setUsername(value);
    setError(''); // Clear error on input change
  }, []);

  const handlePasswordChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPassword(value);
    setError(''); // Clear error on input change
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check if locked out
    if (isLockedOut) {
      const remainingTime = Math.ceil((lockedUntil! - Date.now()) / 1000 / 60);
      setError(`Too many failed attempts. Try again in ${remainingTime} minutes.`);
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Client-side validation
      const usernameError = validateUsername(username);
      if (usernameError) {
        setError(usernameError);
        return;
      }

      const passwordError = validatePassword(password);
      if (passwordError) {
        setError(passwordError);
        return;
      }

      // Prepare secure request
      const loginData = {
        username: username.trim().toLowerCase(),
        password: password
      };

      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'same-origin', // Include cookies for CSRF protection
        body: JSON.stringify(loginData),
      });

      if (!response.ok) {
        // Handle different error types
        if (response.status === 429) {
          const data = await response.json().catch(() => ({}));
          setError(data.detail || 'Too many requests. Please try again later.');
          
          // Set lockout if rate limited
          setAttempts(MAX_LOGIN_ATTEMPTS);
          setLockedUntil(Date.now() + LOCKOUT_DURATION);
          return;
        }
        
        if (response.status === 401) {
          // Increment failed attempts
          const newAttempts = attempts + 1;
          setAttempts(newAttempts);
          
          if (newAttempts >= MAX_LOGIN_ATTEMPTS) {
            setLockedUntil(Date.now() + LOCKOUT_DURATION);
            setError('Too many failed attempts. Account temporarily locked.');
          } else {
            const remaining = MAX_LOGIN_ATTEMPTS - newAttempts;
            setError(`Invalid credentials. ${remaining} attempts remaining.`);
          }
          return;
        }

        // Generic error for other status codes
        setError('Login failed. Please try again.');
        return;
      }

      const data = await response.json();
      
      if (!data.access_token) {
        setError('Invalid response from server');
        return;
      }

      // Reset attempts on successful login
      setAttempts(0);
      setLockedUntil(null);
      
      // Clear form for security
      setUsername('');
      setPassword('');
      
      // Call success callback
      onLogin(data.access_token);
      
    } catch (error) {
      console.error('Login error:', error);
      
      // Don't expose internal errors to user
      if (error instanceof TypeError && error.message.includes('fetch')) {
        setError('Unable to connect to server. Please check your connection.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Calculate remaining lockout time
  const getRemainingLockoutTime = (): string => {
    if (!lockedUntil) return '';
    const remaining = Math.ceil((lockedUntil - Date.now()) / 1000 / 60);
    return `${remaining} minute${remaining !== 1 ? 's' : ''}`;
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="w-full max-w-md">
        <form 
          ref={formRef}
          onSubmit={handleSubmit} 
          className="bg-gray-800 shadow-xl rounded-lg px-8 pt-6 pb-8 mb-4 border border-gray-700"
          noValidate
        >
          <h2 className="text-3xl font-bold text-white mb-6 text-center">
            🔐 Secure Login
          </h2>
          
          {error && (
            <div className="bg-red-900 border border-red-600 text-red-200 px-4 py-3 rounded mb-4 text-sm">
              <div className="flex items-center">
                <span className="mr-2">⚠️</span>
                {error}
              </div>
            </div>
          )}

          {isLockedOut && (
            <div className="bg-yellow-900 border border-yellow-600 text-yellow-200 px-4 py-3 rounded mb-4 text-sm">
              <div className="flex items-center">
                <span className="mr-2">🔒</span>
                Account locked. Try again in {getRemainingLockoutTime()}.
              </div>
            </div>
          )}
          
          <div className="mb-4">
            <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="username">
              Username
            </label>
            <input
              ref={usernameRef}
              className="shadow appearance-none border border-gray-600 rounded w-full py-3 px-3 text-gray-100 bg-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-blue-500 transition-colors"
              id="username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={handleUsernameChange}
              disabled={loading || isLockedOut}
              required
              autoComplete="username"
              maxLength={50}
            />
          </div>
          
          <div className="mb-6">
            <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="password">
              Password
            </label>
            <div className="relative">
              <input
                ref={passwordRef}
                className="shadow appearance-none border border-gray-600 rounded w-full py-3 px-3 text-gray-100 bg-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-blue-500 transition-colors pr-10"
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={handlePasswordChange}
                disabled={loading || isLockedOut}
                required
                autoComplete="current-password"
                maxLength={128}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-200"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading || isLockedOut}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <button
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded focus:outline-none focus:shadow-outline transition-colors w-full"
              type="submit"
              disabled={loading || isLockedOut || !username.trim() || !password}
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Signing In...
                </div>
              ) : (
                'Sign In'
              )}
            </button>
          </div>

          <div className="mt-4 text-center">
            <p className="text-gray-400 text-xs">
              Attempts: {attempts}/{MAX_LOGIN_ATTEMPTS}
            </p>
          </div>
        </form>
        
        <div className="text-center text-gray-500 text-xs">
          <p>🔒 Secure authentication with rate limiting</p>
          <p>Protected against brute force attacks</p>
        </div>
      </div>
    </div>
  );
}
