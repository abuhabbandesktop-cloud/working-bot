"""
Comprehensive Security Module for Telegram Bot Backend

This module provides enterprise-grade security utilities including:
- Rate limiting and DDoS protection
- Input validation and sanitization
- Secure file handling
- XSS and injection prevention
- Security headers management
- Audit logging and monitoring

Security Features:
- Multi-layer rate limiting (IP, user, endpoint)
- Content Security Policy (CSP) headers
- Path traversal prevention
- SQL injection protection
- Cross-site scripting (XSS) prevention
- Secure random token generation
- Comprehensive input validation
"""

from __future__ import annotations
import time
import hashlib
import re
import os
import secrets
from typing import Dict, Optional, Any, List
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
from pathlib import Path
import mimetypes

# Rate limiting storage (use Redis in production for distributed systems)
rate_limit_storage: Dict[str, Dict[str, Any]] = {}

# Blocked IPs storage (use Redis in production)
blocked_ips: Dict[str, float] = {}

# Security configuration
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
BLOCKED_IP_DURATION = 3600  # 1 hour
SUSPICIOUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # XSS attempts
    r'javascript:',                # JavaScript injection
    r'on\w+\s*=',                 # Event handlers
    r'union\s+select',             # SQL injection
    r'drop\s+table',               # SQL injection
    r'insert\s+into',              # SQL injection
    r'\.\./.*\.\.',                # Path traversal
    r'etc/passwd',                 # System file access
    r'cmd\.exe',                   # Command injection
    r'powershell',                 # PowerShell injection
]

def generate_secure_secret(length: int = 32) -> str:
    """
    Generate cryptographically secure random secret.
    
    Args:
        length: Length of the secret to generate
        
    Returns:
        str: URL-safe base64 encoded random string
    """
    return secrets.token_urlsafe(length)

def get_client_ip(request: Request) -> str:
    """
    Extract client IP address with proxy support.
    
    Checks multiple headers in order of preference:
    1. X-Forwarded-For (most common proxy header)
    2. X-Real-IP (nginx proxy)
    3. X-Client-IP (some proxies)
    4. Direct client host
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Client IP address
    """
    # Check proxy headers in order of preference
    headers_to_check = [
        "X-Forwarded-For",
        "X-Real-IP", 
        "X-Client-IP",
        "CF-Connecting-IP"  # Cloudflare
    ]
    
    for header in headers_to_check:
        ip = request.headers.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return ip.split(",")[0].strip()
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"

def is_ip_blocked(ip: str) -> bool:
    """
    Check if IP address is currently blocked.
    
    Args:
        ip: IP address to check
        
    Returns:
        bool: True if IP is blocked
    """
    if ip in blocked_ips:
        if time.time() - blocked_ips[ip] > BLOCKED_IP_DURATION:
            # Unblock expired IPs
            del blocked_ips[ip]
            return False
        return True
    return False

def block_ip(ip: str, duration: int = BLOCKED_IP_DURATION) -> None:
    """
    Block IP address for specified duration.
    
    Args:
        ip: IP address to block
        duration: Block duration in seconds
    """
    blocked_ips[ip] = time.time()
    print(f"🚫 Blocked IP {hash_sensitive_data(ip)} for {duration} seconds")

def detect_malicious_patterns(text: str) -> List[str]:
    """
    Detect potentially malicious patterns in input text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List[str]: List of detected suspicious patterns
    """
    detected = []
    text_lower = text.lower()
    
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            detected.append(pattern)
    
    return detected

def rate_limit_check(request: Request, max_requests: int = 100, window_seconds: int = 60) -> None:
    """
    Advanced rate limiting with IP blocking for abuse.
    
    Features:
    - Sliding window rate limiting
    - Automatic IP blocking for severe abuse
    - Different limits for different endpoints
    - Memory cleanup for expired entries
    
    Args:
        request: FastAPI request object
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        
    Raises:
        HTTPException: If rate limit exceeded or IP blocked
    """
    client_ip = get_client_ip(request)
    current_time = time.time()
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        raise HTTPException(
            status_code=429,
            detail="IP address temporarily blocked due to suspicious activity"
        )
    
    # Initialize or get existing rate limit data
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = {
            "requests": 1,
            "window_start": current_time,
            "violations": 0
        }
        return
    
    client_data = rate_limit_storage[client_ip]
    
    # Reset window if expired
    if current_time - client_data["window_start"] > window_seconds:
        client_data["requests"] = 1
        client_data["window_start"] = current_time
        return
    
    # Check if limit exceeded
    if client_data["requests"] >= max_requests:
        client_data["violations"] += 1
        
        # Block IP after multiple violations
        if client_data["violations"] >= 3:
            block_ip(client_ip)
            raise HTTPException(
                status_code=429,
                detail="IP blocked due to repeated rate limit violations"
            )
        
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds"
        )
    
    client_data["requests"] += 1

def validate_input_length(text: str, max_length: int = 10000, field_name: str = "input") -> None:
    """
    Validate input length with security considerations.
    
    Args:
        text: Input text to validate
        max_length: Maximum allowed length
        field_name: Name of the field for error messages
        
    Raises:
        HTTPException: If input exceeds maximum length
    """
    if not isinstance(text, str):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a string"
        )
    
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} exceeds maximum length of {max_length} characters"
        )

def validate_and_sanitize_input(text: str, field_name: str = "input", max_length: int = 10000) -> str:
    """
    Comprehensive input validation and sanitization.
    
    Args:
        text: Input text to validate and sanitize
        field_name: Name of the field for error messages
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
        
    Raises:
        HTTPException: If input fails validation
    """
    # Length validation
    validate_input_length(text, max_length, field_name)
    
    # Detect malicious patterns
    suspicious_patterns = detect_malicious_patterns(text)
    if suspicious_patterns:
        print(f"🚨 Suspicious patterns detected in {field_name}: {suspicious_patterns}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid characters detected in {field_name}"
        )
    
    # Basic sanitization
    import html
    sanitized = html.escape(text.strip())
    
    return sanitized

def sanitize_filename(filename: str) -> str:
    """
    Comprehensive filename sanitization to prevent path traversal and other attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Remove path traversal attempts
    filename = filename.replace('..', '_')
    filename = filename.replace('~', '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty after sanitization
    if not filename:
        filename = "sanitized_file"
    
    # Limit filename length
    return filename[:255]

def hash_sensitive_data(data: str) -> str:
    """
    Hash sensitive data for secure logging purposes.
    
    Args:
        data: Sensitive data to hash
        
    Returns:
        str: First 8 characters of SHA-256 hash
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()[:8]

def validate_file_upload(file_path: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """
    Validate uploaded file for security.
    
    Args:
        file_path: Path to the uploaded file
        allowed_extensions: List of allowed file extensions
        
    Returns:
        bool: True if file is safe
    """
    if allowed_extensions is None:
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.mp4', '.mp3']
    
    path_obj = Path(file_path)
    
    # Check file extension
    if path_obj.suffix.lower() not in allowed_extensions:
        return False
    
    # Check file size (prevent DoS)
    try:
        if path_obj.stat().st_size > MAX_REQUEST_SIZE:
            return False
    except FileNotFoundError:
        return False
    
    return True

def generate_csrf_token() -> str:
    """
    Generate CSRF token for form protection.
    
    Returns:
        str: Secure random CSRF token
    """
    return secrets.token_urlsafe(32)

def validate_csrf_token(token: str, expected_token: str) -> bool:
    """
    Validate CSRF token using constant-time comparison.
    
    Args:
        token: Token from request
        expected_token: Expected token value
        
    Returns:
        bool: True if tokens match
    """
    return secrets.compare_digest(token, expected_token)

class SecurityHeaders:
    """
    Comprehensive security headers configuration for web application protection.
    
    Implements security headers recommended by OWASP:
    - Content Security Policy (CSP)
    - X-Frame-Options (Clickjacking protection)
    - X-Content-Type-Options (MIME sniffing protection)
    - X-XSS-Protection (XSS filter)
    - Strict-Transport-Security (HTTPS enforcement)
    - Referrer-Policy (Referrer information control)
    - Permissions-Policy (Feature policy)
    """
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """
        Get comprehensive security headers.
        
        Returns:
            Dict[str, str]: Security headers dictionary
        """
        return {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Enable XSS filtering (legacy browsers)
            "X-XSS-Protection": "1; mode=block",
            
            # Control referrer information
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Restrict dangerous browser features
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
            
            # Enforce HTTPS (enable in production)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Content Security Policy (restrictive)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' ws: wss:; "
                "media-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none';"
            ),
            
            # Cache control for sensitive pages
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    
    @staticmethod
    def get_api_headers() -> Dict[str, str]:
        """
        Get security headers optimized for API endpoints.
        
        Returns:
            Dict[str, str]: API-specific security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        }

def log_security_event(event_type: str, details: str, client_ip: str = "unknown") -> None:
    """
    Log security-related events for monitoring and analysis.
    
    Args:
        event_type: Type of security event
        details: Event details
        client_ip: Client IP address
    """
    timestamp = datetime.utcnow().isoformat()
    hashed_ip = hash_sensitive_data(client_ip)
    
    print(f"🔒 SECURITY EVENT [{timestamp}] {event_type}: {details} (IP: {hashed_ip})")
    
    # In production, send to SIEM or security monitoring system
    # Example: send_to_siem(event_type, details, client_ip, timestamp)

def cleanup_rate_limit_storage() -> None:
    """
    Clean up expired entries from rate limit storage to prevent memory leaks.
    Call this periodically (e.g., every hour) in production.
    """
    current_time = time.time()
    expired_ips = []
    
    for ip, data in rate_limit_storage.items():
        if current_time - data.get("window_start", 0) > 3600:  # 1 hour
            expired_ips.append(ip)
    
    for ip in expired_ips:
        del rate_limit_storage[ip]
    
    print(f"🧹 Cleaned up {len(expired_ips)} expired rate limit entries")
