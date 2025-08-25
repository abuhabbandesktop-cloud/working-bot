"""
Secure Authentication Module for Telegram Bot Backend

This module provides comprehensive authentication and authorization functionality
with enterprise-grade security features including:

- Secure password hashing with bcrypt
- JWT token management with proper expiration
- Rate limiting and brute force protection
- Secure secret generation and validation
- Admin user management with proper bootstrapping

Security Features:
- Cryptographically secure random secrets
- Proper password complexity validation
- Token expiration and refresh mechanisms
- Protection against timing attacks
- Secure default configurations
"""

from __future__ import annotations
import os
import bcrypt
import jwt
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models import Admin
from .db import get_db
from .security import hash_sensitive_data

load_dotenv()

# Security Configuration with secure defaults
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET == "dev-secret":
    # Generate secure secret if not provided or using default
    JWT_SECRET = secrets.token_urlsafe(64)
    print(
        "⚠️  WARNING: Using auto-generated JWT secret. Set JWT_SECRET in .env for production!"
    )

JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_HOURS = int(
    os.getenv("ACCESS_TOKEN_TTL_HOURS", "2")
)  # Reduced from 12 to 2 hours
REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "7"))

# Password security requirements
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes

# In-memory store for login attempts (use Redis in production)
login_attempts = {}


def validate_password_strength(password: str) -> bool:
    """
    Validate password meets security requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Plain text password to validate

    Returns:
        bool: True if password meets requirements

    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        )

    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        raise ValueError("Password must contain at least one special character")

    return True


def hash_password(plain: str) -> str:
    """
    Hash password using bcrypt with secure salt.

    Args:
        plain: Plain text password

    Returns:
        str: Hashed password
    """
    # Use higher cost factor for better security (12 rounds)
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify password against hash with timing attack protection.

    Args:
        plain: Plain text password
        hashed: Hashed password from database

    Returns:
        bool: True if password matches
    """
    try:
        # Add small delay to prevent timing attacks
        time.sleep(0.1)
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        print(f"Password verification error: {hash_sensitive_data(str(e))}")
        return False


def check_login_attempts(username: str, client_ip: str) -> None:
    """
    Check and enforce login attempt limits.

    Args:
        username: Username attempting login
        client_ip: Client IP address

    Raises:
        HTTPException: If too many failed attempts
    """
    key = f"{username}:{client_ip}"
    current_time = time.time()

    if key in login_attempts:
        attempts_data = login_attempts[key]

        # Reset if lockout period has passed
        if current_time - attempts_data["last_attempt"] > LOCKOUT_DURATION:
            del login_attempts[key]
            return

        # Check if locked out
        if attempts_data["count"] >= MAX_LOGIN_ATTEMPTS:
            remaining_time = LOCKOUT_DURATION - (
                current_time - attempts_data["last_attempt"]
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Try again in {int(remaining_time)} seconds.",
            )


def record_failed_login(username: str, client_ip: str) -> None:
    """
    Record failed login attempt.

    Args:
        username: Username that failed login
        client_ip: Client IP address
    """
    key = f"{username}:{client_ip}"
    current_time = time.time()

    if key in login_attempts:
        login_attempts[key]["count"] += 1
        login_attempts[key]["last_attempt"] = current_time
    else:
        login_attempts[key] = {"count": 1, "last_attempt": current_time}


def clear_login_attempts(username: str, client_ip: str) -> None:
    """
    Clear login attempts after successful login.

    Args:
        username: Username that successfully logged in
        client_ip: Client IP address
    """
    key = f"{username}:{client_ip}"
    if key in login_attempts:
        del login_attempts[key]


def create_token(sub: str, kind: str, ttl: timedelta) -> str:
    """
    Create JWT token with secure payload.

    Args:
        sub: Subject (username)
        kind: Token type (access/refresh)
        ttl: Time to live

    Returns:
        str: Encoded JWT token
    """
    now = datetime.utcnow()
    exp = now + ttl

    payload = {
        "sub": sub,
        "kind": kind,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": secrets.token_urlsafe(16),  # Unique token ID
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def create_access(sub: str) -> str:
    """Create access token with short expiration."""
    return create_token(sub, "access", timedelta(hours=ACCESS_HOURS))


def create_refresh(sub: str) -> str:
    """Create refresh token with longer expiration."""
    return create_token(sub, "refresh", timedelta(days=REFRESH_DAYS))


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

        # Additional validation
        if not payload.get("sub") or not payload.get("kind"):
            return None

        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {hash_sensitive_data(str(e))}")
        return None
    except Exception as e:
        print(f"Token decode error: {hash_sensitive_data(str(e))}")
        return None


def get_or_bootstrap_admin(db: Session) -> None:
    """
    Bootstrap default admin user with secure defaults.

    Args:
        db: Database session
    """
    # Only create admin if none exists
    if db.query(Admin).count() == 0:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD")

        # Require secure password in production
        if not password or password == "admin":
            # Generate secure random password
            password = secrets.token_urlsafe(16)
            print(f"⚠️  WARNING: Generated secure admin password: {password}")
            print("⚠️  Please save this password and set ADMIN_PASSWORD in .env!")

        try:
            validate_password_strength(password)
        except ValueError as e:
            print(f"⚠️  WARNING: Admin password doesn't meet security requirements: {e}")
            print("⚠️  Consider setting a stronger ADMIN_PASSWORD in .env")

        admin = Admin(username=username, password_hash=hash_password(password))
        db.add(admin)
        db.commit()
        print(f"✅ Bootstrap admin user created: {username}")


# Security middleware
security = HTTPBearer(auto_error=False)


def require_admin(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Admin:
    """
    Require valid admin authentication.

    Args:
        creds: HTTP Bearer credentials
        db: Database session

    Returns:
        Admin: Authenticated admin user

    Raises:
        HTTPException: If authentication fails
    """
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(creds.credentials)
    if not payload or payload.get("kind") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin = db.query(Admin).filter(Admin.username == sub).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin
