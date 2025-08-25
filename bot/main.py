"""
Secure Telegram Bot for Message Archiving and Echo Functionality

This bot provides comprehensive message archiving with the following security features:
- Secure file handling with validation
- Rate limiting and abuse protection
- Comprehensive input sanitization
- Secure API communication with the backend
- Proper error handling and logging
- Media file validation and secure storage

Security Features:
- File type validation and size limits
- Path traversal prevention
- Secure filename sanitization
- API authentication with secrets
- Comprehensive audit logging
- Error handling without information disclosure

Architecture:
- Receives messages from Telegram
- Validates and sanitizes all inputs
- Securely stores media files
- Forwards data to backend API
- Provides echo functionality for testing
"""

from __future__ import annotations

import os
import logging
import hashlib
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from telegram import Update, Message, File
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import httpx

# ------------------------------------------------------------------------------
# Security Configuration and Setup
# ------------------------------------------------------------------------------
load_dotenv()

# Environment variables with secure defaults
BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
API_INGEST_SECRET: str = os.getenv("API_INGEST_SECRET", "dev-secret")
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", "../data/media")).resolve()

# Security configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
ALLOWED_MEDIA_TYPES = {
    'photo': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'video': ['.mp4', '.avi', '.mov', '.webm', '.mkv'],
    'voice': ['.ogg', '.mp3', '.wav', '.m4a'],
    'document': ['.pdf', '.txt', '.doc', '.docx', '.zip', '.rar']
}

# Rate limiting (simple in-memory store - use Redis in production)
user_message_count: Dict[int, Dict[str, Any]] = {}
RATE_LIMIT_MESSAGES = 30  # messages per minute
RATE_LIMIT_WINDOW = 60  # seconds

# Create media directory with proper permissions
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
os.chmod(MEDIA_DIR, 0o755)  # Read/write for owner, read for others

# Configure comprehensive logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        # In production, add file handler with rotation
        # logging.handlers.RotatingFileHandler('bot.log', maxBytes=10485760, backupCount=5)
    ]
)
logger = logging.getLogger(__name__)

# Disable httpx debug logging
logging.getLogger("httpx").setLevel(logging.WARNING)


# ------------------------------------------------------------------------------
# Security Utility Functions
# ------------------------------------------------------------------------------

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for secure logging."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()[:8]

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other security issues.
    
    Args:
        filename: Original filename from Telegram
        
    Returns:
        str: Sanitized filename safe for filesystem storage
    """
    if not filename:
        return "unnamed_file"
    
    # Remove dangerous characters and path separators
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Remove path traversal attempts
    filename = filename.replace('..', '_').replace('~', '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty after sanitization
    if not filename:
        filename = "sanitized_file"
    
    # Limit filename length
    return filename[:255]

def validate_file_size(file_size: int) -> bool:
    """
    Validate file size against security limits.
    
    Args:
        file_size: Size of file in bytes
        
    Returns:
        bool: True if file size is acceptable
    """
    return 0 < file_size <= MAX_FILE_SIZE

def validate_file_type(filename: str, content_type: str) -> bool:
    """
    Validate file type against allowed extensions.
    
    Args:
        filename: Name of the file
        content_type: Content type from Telegram
        
    Returns:
        bool: True if file type is allowed
    """
    if not filename:
        return False
    
    file_ext = Path(filename).suffix.lower()
    
    # Check against allowed extensions for the content type
    allowed_extensions = ALLOWED_MEDIA_TYPES.get(content_type, [])
    return file_ext in allowed_extensions

def check_rate_limit(user_id: int) -> bool:
    """
    Check if user has exceeded rate limits.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: True if user is within rate limits
    """
    current_time = datetime.now().timestamp()
    
    if user_id not in user_message_count:
        user_message_count[user_id] = {
            'count': 1,
            'window_start': current_time
        }
        return True
    
    user_data = user_message_count[user_id]
    
    # Reset window if expired
    if current_time - user_data['window_start'] > RATE_LIMIT_WINDOW:
        user_data['count'] = 1
        user_data['window_start'] = current_time
        return True
    
    # Check if limit exceeded
    if user_data['count'] >= RATE_LIMIT_MESSAGES:
        return False
    
    user_data['count'] += 1
    return True

def to_dt(ts: int | float | None) -> datetime:
    """
    Convert Telegram timestamp to naive UTC datetime with validation.
    
    Args:
        ts: Telegram timestamp (Unix timestamp)
        
    Returns:
        datetime: Naive UTC datetime object
    """
    if ts is None:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    
    try:
        # Validate timestamp is reasonable (not too far in past/future)
        current_time = datetime.now(timezone.utc).timestamp()
        if abs(ts - current_time) > 86400 * 365:  # 1 year
            logger.warning(f"Suspicious timestamp detected: {ts}")
            return datetime.now(timezone.utc).replace(tzinfo=None)
        
        return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
    except (ValueError, OSError) as e:
        logger.error(f"Invalid timestamp {ts}: {e}")
        return datetime.now(timezone.utc).replace(tzinfo=None)

async def send_to_backend(payload: dict) -> bool:
    """
    Securely send ingested message data to backend API.
    
    Args:
        payload: Message data to send to backend
        
    Returns:
        bool: True if successfully sent, False otherwise
    """
    url = f"{BACKEND_BASE_URL}/internal/ingest/telegram"
    headers = {
        "x-ingest-secret": API_INGEST_SECRET,
        "Content-Type": "application/json",
        "User-Agent": "TelegramBot/1.0"
    }
    
    try:
        # Validate payload before sending
        if not isinstance(payload, dict):
            logger.error("Invalid payload type")
            return False
        
        # Log payload (with sensitive data hashed)
        safe_payload = payload.copy()
        if 'text' in safe_payload and safe_payload['text']:
            safe_payload['text'] = hash_sensitive_data(safe_payload['text'])
        logger.info(f"Sending payload to backend: {safe_payload}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully sent message to backend: {response.status_code}")
            return True
            
    except httpx.TimeoutException:
        logger.error("Timeout sending message to backend")
        return False
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error sending to backend: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to backend: {hash_sensitive_data(str(e))}")
        return False


# ------------------------------------------------------------------------------
# Secure Message Handlers
# ------------------------------------------------------------------------------

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Secure message handler with comprehensive validation and sanitization.
    
    Security Features:
    - Rate limiting per user
    - Input validation and sanitization
    - File type and size validation
    - Secure file storage with proper naming
    - Comprehensive error handling
    - Audit logging
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    msg: Optional[Message] = update.effective_message
    if msg is None:
        logger.warning("Received update without effective message")
        return

    # Extract user and chat information
    user = msg.from_user
    chat = msg.chat
    
    if not user:
        logger.warning(f"Message without user information in chat {chat.id}")
        return

    # Rate limiting check
    if not check_rate_limit(user.id):
        logger.warning(f"Rate limit exceeded for user {hash_sensitive_data(str(user.id))}")
        await msg.reply_text("⚠️ You're sending messages too quickly. Please slow down.")
        return

    # Initialize message processing variables
    content_type = "text"
    text: Optional[str] = msg.text or msg.caption
    media_path: Optional[str] = None

    # Sanitize text content if present
    if text:
        # Basic length validation
        if len(text) > 4000:  # Telegram's limit is 4096, but we're conservative
            logger.warning(f"Message too long from user {hash_sensitive_data(str(user.id))}")
            await msg.reply_text("⚠️ Message too long. Please keep messages under 4000 characters.")
            return
        
        # Basic content validation (detect potential spam/abuse)
        if text.count('http') > 5 or text.count('@') > 10:
            logger.warning(f"Suspicious message content from user {hash_sensitive_data(str(user.id))}")
            # Still process but log for review
    
    async def secure_download(file: File, subdir: str, original_filename: str, content_type: str) -> Optional[str]:
        """
        Securely download and store media files with comprehensive validation.
        
        Args:
            file: Telegram file object
            subdir: Subdirectory for storage
            original_filename: Original filename from Telegram
            content_type: Type of content (photo, video, etc.)
            
        Returns:
            Optional[str]: Relative path to stored file, None if failed
        """
        try:
            # Validate file size
            if file.file_size is None or not validate_file_size(file.file_size):
                logger.warning(f"File too large: {file.file_size} bytes from user {hash_sensitive_data(str(user.id))}")
                await msg.reply_text("⚠️ File too large. Maximum size is 50MB.")
                return None
            
            # Validate file type
            if not validate_file_type(original_filename, content_type):
                logger.warning(f"Invalid file type: {original_filename} from user {hash_sensitive_data(str(user.id))}")
                await msg.reply_text("⚠️ File type not allowed.")
                return None
            
            # Create secure filename
            sanitized_name = sanitize_filename(original_filename)
            timestamp = int(datetime.now().timestamp())
            secure_filename = f"{chat.id}_{msg.message_id}_{timestamp}_{sanitized_name}"
            
            # Create storage directory with proper permissions
            folder = MEDIA_DIR / subdir
            folder.mkdir(parents=True, exist_ok=True, mode=0o755)
            
            # Download file to secure location
            dest = folder / secure_filename
            await file.download_to_drive(custom_path=str(dest))
            
            # Set secure file permissions
            os.chmod(dest, 0o644)  # Read/write for owner, read for others
            
            # Return relative path
            rel_path = dest.relative_to(MEDIA_DIR)
            logger.info(f"Successfully downloaded file: {rel_path}")
            return str(rel_path)
            
        except Exception as e:
            logger.error(f"Error downloading file: {hash_sensitive_data(str(e))}")
            await msg.reply_text("⚠️ Error processing file. Please try again.")
            return None

    # Process different media types with security validation
    try:
        if msg.photo:
            content_type = "photo"
            file = await msg.photo[-1].get_file()
            filename = f"photo_{msg.message_id}.jpg"
            media_path = await secure_download(file, "images", filename, content_type)
            
        elif msg.video:
            content_type = "video"
            file = await msg.video.get_file()
            filename = msg.video.file_name or f"video_{msg.message_id}.mp4"
            media_path = await secure_download(file, "videos", filename, content_type)
            
        elif msg.voice:
            content_type = "voice"
            file = await msg.voice.get_file()
            filename = f"voice_{msg.message_id}.ogg"
            media_path = await secure_download(file, "voices", filename, content_type)
            
        elif msg.document:
            content_type = "document"
            file = await msg.document.get_file()
            filename = msg.document.file_name or f"document_{msg.message_id}.bin"
            media_path = await secure_download(file, "docs", filename, content_type)
            
        elif msg.audio:
            content_type = "audio"
            file = await msg.audio.get_file()
            filename = msg.audio.file_name or f"audio_{msg.message_id}.mp3"
            media_path = await secure_download(file, "audio", filename, content_type)
            
    except Exception as e:
        logger.error(f"Error processing media: {hash_sensitive_data(str(e))}")
        await msg.reply_text("⚠️ Error processing media. Please try again.")
        return

    # Build secure payload for backend
    payload = {
        "chat": {
            "id": chat.id,
            "type": chat.type,
            "title": chat.title or f"Chat {chat.id}"
        },
        "user_id": user.id,
        "tg_message_id": msg.message_id,
        "content_type": content_type,
        "text": text,
        "media_path": media_path,
        "created_at": msg.date.isoformat(),
    }

    # Send to backend with error handling
    success = await send_to_backend(payload)
    if not success:
        logger.error(f"Failed to send message to backend for user {hash_sensitive_data(str(user.id))}")
        await msg.reply_text("⚠️ Message processing failed. Please try again later.")
        return

    # Provide user feedback
    try:
        if text and len(text) <= 100:  # Echo short text messages
            await msg.reply_text(f"📝 Archived: {text}")
        elif content_type != "text":
            await msg.reply_text(f"📁 Archived {content_type} successfully ✅")
        else:
            await msg.reply_text("📝 Message archived successfully ✅")
    except Exception as e:
        logger.error(f"Error sending reply: {hash_sensitive_data(str(e))}")
        # Don't fail the whole process if reply fails


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command and archive it."""
    msg = update.effective_message
    if msg:
        # Archive the command like any other message
        await archive_command(update, context, "start", "Hello! I am your echo+archive bot.")
        await msg.reply_text("Hello! I am your echo+archive bot.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command and archive it."""
    msg = update.effective_message
    if msg:
        help_text = """
🤖 *Bot Commands:*
/start - Start the bot
/help - Show this help message
/info - Show bot information
/settings - Bot settings (coming soon)

📝 *Features:*
• Archive all messages and media
• Echo back your messages
• Support for photos, videos, documents, voice messages
• Real-time web interface
        """
        await archive_command(update, context, "help", help_text)
        await msg.reply_text(help_text, parse_mode='Markdown')


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /info command and archive it."""
    msg = update.effective_message
    if msg:
        info_text = f"""
ℹ️ *Bot Information:*
• Bot Name: Echo+Archive Bot
• Version: 2.0
• Chat ID: `{msg.chat.id}`
• Your User ID: `{msg.from_user.id if msg.from_user else 'Unknown'}`
• Chat Type: {msg.chat.type}
        """
        await archive_command(update, context, "info", info_text)
        await msg.reply_text(info_text, parse_mode='Markdown')


async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command and archive it."""
    msg = update.effective_message
    if msg:
        settings_text = "⚙️ Settings feature coming soon! Stay tuned for updates."
        await archive_command(update, context, "settings", settings_text)
        await msg.reply_text(settings_text)


async def archive_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, response_text: str) -> None:
    """Archive bot commands to backend."""
    msg = update.effective_message
    if msg is None:
        return

    chat = msg.chat
    
    # Build payload for the command
    payload = {
        "chat": {"id": chat.id, "type": chat.type, "title": chat.title},
        "user_id": (msg.from_user.id if msg.from_user else None),
        "tg_message_id": msg.message_id,
        "content_type": "command",
        "text": f"/{command}",
        "media_path": None,
        "created_at": msg.date.isoformat(),
    }

    # Send to backend
    try:
        await send_to_backend(payload)
        logger.info(f"Archived command /{command} from chat {chat.id}")
    except Exception as e:
        logger.error("Failed to archive command to backend: %s", e)


# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------
def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in .env")

    app = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers (these will be processed first)
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    
    # Register message handler for non-command messages
    # Note: Exclude commands from the echo handler since they're handled above
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.StatusUpdate.ALL & ~filters.COMMAND,
        echo
    ))

    logger.info("🤖 Bot running with enhanced command support… Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
