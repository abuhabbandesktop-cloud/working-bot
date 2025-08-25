"""
Secure media file handler
"""
from __future__ import annotations
import os
from pathlib import Path
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from .security import sanitize_filename
import mimetypes

ALLOWED_MEDIA_TYPES = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
    '.mp4', '.avi', '.mov', '.webm',           # Videos
    '.ogg', '.mp3', '.wav', '.m4a',            # Audio
    '.pdf', '.txt', '.doc', '.docx'            # Documents
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_media_file(file_path: str) -> bool:
    """Validate media file for security"""
    path_obj = Path(file_path)
    
    # Check file extension
    if path_obj.suffix.lower() not in ALLOWED_MEDIA_TYPES:
        return False
    
    # Check file size
    try:
        if path_obj.stat().st_size > MAX_FILE_SIZE:
            return False
    except FileNotFoundError:
        return False
    
    return True

def secure_media_response(file_path: str, media_dir: str) -> FileResponse:
    """Serve media file securely with proper headers"""
    # Normalize and validate paths
    media_dir_path = Path(media_dir).resolve()
    requested_path = (media_dir_path / file_path).resolve()
    
    # Ensure file is within media directory (prevent path traversal)
    if not str(requested_path).startswith(str(media_dir_path)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file exists and is valid
    if not requested_path.exists() or not validate_media_file(str(requested_path)):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get MIME type
    content_type, _ = mimetypes.guess_type(str(requested_path))
    if not content_type:
        content_type = "application/octet-stream"
    
    # Create secure response with proper headers
    response = FileResponse(
        path=str(requested_path),
        media_type=content_type,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600",
            "X-Frame-Options": "DENY"
        }
    )
    
    return response
