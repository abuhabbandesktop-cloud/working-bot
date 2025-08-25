"""
Secure Authentication Router

This module handles user authentication with comprehensive security features:
- Rate limiting and brute force protection
- Input validation and sanitization
- Secure login attempt tracking
- Proper error handling and logging
- Token generation and validation

Security Features:
- Failed login attempt tracking per IP
- Account lockout after multiple failures
- Secure password validation
- Rate limiting per endpoint
- Comprehensive audit logging
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Admin, AdminAction
from ..schemas import LoginRequest, TokenPair
from ..auth import (
    verify_password,
    create_access,
    create_refresh,
    check_login_attempts,
    record_failed_login,
    clear_login_attempts,
    require_admin
)
from ..security import rate_limit_check, validate_input_length, get_client_ip, hash_sensitive_data

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Secure user login endpoint with comprehensive protection.
    
    Security Features:
    - Rate limiting (5 attempts per minute per IP)
    - Brute force protection with account lockout
    - Input validation and sanitization
    - Audit logging of all attempts
    - Secure token generation
    
    Args:
        payload: Login credentials (username, password)
        request: HTTP request object for IP extraction
        db: Database session
        
    Returns:
        TokenPair: Access and refresh tokens
        
    Raises:
        HTTPException: For various authentication failures
    """
    client_ip = get_client_ip(request)
    
    # Apply rate limiting (5 attempts per minute per IP)
    rate_limit_check(request, max_requests=5, window_seconds=60)
    
    # Validate input lengths to prevent DoS
    validate_input_length(payload.username, max_length=50, field_name="username")
    validate_input_length(payload.password, max_length=128, field_name="password")
    
    # Check for too many failed login attempts
    try:
        check_login_attempts(payload.username, client_ip)
    except HTTPException:
        # Log the blocked attempt
        print(f"🚫 Blocked login attempt from {hash_sensitive_data(client_ip)} for user {hash_sensitive_data(payload.username)}")
        raise
    
    # Find admin user
    admin = db.query(Admin).filter(Admin.username == payload.username).first()
    
    # Verify credentials
    if not admin or not verify_password(payload.password, admin.password_hash):
        # Record failed attempt
        record_failed_login(payload.username, client_ip)
        
        # Log failed attempt
        print(f"❌ Failed login attempt from {hash_sensitive_data(client_ip)} for user {hash_sensitive_data(payload.username)}")
        
        # Create audit log entry
        if admin:  # Only log if user exists
            audit_entry = AdminAction(
                admin_id=admin.id,
                action="failed_login",
                details=f"Failed login from IP: {hash_sensitive_data(client_ip)}"
            )
            db.add(audit_entry)
            db.commit()
        
        # Generic error message to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Clear failed attempts on successful login
    clear_login_attempts(payload.username, client_ip)
    
    # Log successful login
    print(f"✅ Successful login from {hash_sensitive_data(client_ip)} for user {hash_sensitive_data(payload.username)}")
    
    # Create audit log entry for successful login
    audit_entry = AdminAction(
        admin_id=admin.id,
        action="successful_login",
        details=f"Successful login from IP: {hash_sensitive_data(client_ip)}"
    )
    db.add(audit_entry)
    db.commit()
    
    # Generate secure tokens
    access_token = create_access(admin.username)
    refresh_token = create_refresh(admin.username)
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/logout")
async def logout(request: Request, admin: Admin = Depends(require_admin), db: Session = Depends(get_db)):
    """
    Secure logout endpoint with audit logging.
    
    Args:
        request: HTTP request object
        admin: Authenticated admin user
        db: Database session
        
    Returns:
        dict: Success message
    """
    
    client_ip = get_client_ip(request)
    
    # Log logout
    print(f"👋 User logout: {hash_sensitive_data(admin.username)} from {hash_sensitive_data(client_ip)}")
    
    # Create audit log entry
    audit_entry = AdminAction(
        admin_id=admin.id,
        action="logout",
        details=f"Logout from IP: {hash_sensitive_data(client_ip)}"
    )
    db.add(audit_entry)
    db.commit()
    
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_current_user(admin: Admin = Depends(require_admin)):
    """
    Get current authenticated user information.
    
    Args:
        admin: Authenticated admin user
        
    Returns:
        dict: User information (sanitized)
    """
    
    return {
        "id": admin.id,
        "username": admin.username,
        "created_at": admin.created_at.isoformat()
    }
