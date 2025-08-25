# 🚀 Enhanced Telegram Bot Setup Guide

This guide will help you set up the beautiful new Telegram-like chat interface with organized sections for Users, Groups, and Channels.

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## 🔧 Installation Steps

### 1. Clone and Setup Backend

```bash
# Navigate to backend directory
cd tg-bot-web/backend

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env file with your settings
nano .env
```

**Required .env variables:**

```env
BOT_TOKEN=your_telegram_bot_token_here
BACKEND_BASE_URL=http://127.0.0.1:8000
API_INGEST_SECRET=your_secure_secret_here
MEDIA_DIR=../data/media
SQLITE_PATH=../data/app.db
JWT_SECRET=your_jwt_secret_here
JWT_ALG=HS256
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here
```

### 2. Setup Bot

```bash
# Navigate to bot directory
cd ../bot

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env file (use same values as backend)
nano .env
```

### 3. Setup Frontend

```bash
# Navigate to frontend directory
cd ../frontend

# Install Node.js dependencies
npm install

# Build the frontend
npm run build
```

### 4. Database Migration

```bash
# Navigate to scripts directory
cd ../scripts

# Run the database migration
python migrate_database.py
```

## 🚀 Running the Application

### Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Start Telegram Bot

```bash
cd bot
python main.py
```

### Start Frontend (Development)

```bash
cd frontend
npm run dev
```

### Start Frontend (Production)

```bash
cd frontend
npm run build
npm start
```

## 🎯 New Features

### ✨ Enhanced UI Components

- **Organized Chat Sections**: Users, Groups, Channels, and Saved messages
- **Beautiful Chat List Items**: With avatars, last message preview, and timestamps
- **Status Indicators**: Online/offline status for users
- **Unread Message Badges**: Visual indicators for unread messages
- **Search Functionality**: Search across all chats and messages
- **Responsive Design**: Works perfectly on desktop and mobile

### 🤖 Enhanced Bot Features

- **Command Recording**: All commands including `/start`, `/help`, `/info`, `/settings` are now recorded
- **Better Message Handling**: Improved media support and error handling
- **Real-time Updates**: Enhanced WebSocket communication

### 🔧 Backend Improvements

- **Organized Chat API**: New `/api/chats/organized` endpoint
- **Enhanced Database Models**: Better chat categorization and user relationships
- **Message Status Tracking**: Sent, delivered, and seen status indicators
- **Media Support**: Better handling of photos, videos, documents, and voice messages

## 📱 Using the Interface

### Chat Organization

1. **Users Tab**: Shows all private conversations with individual users
2. **Groups Tab**: Shows group chats and supergroups
3. **Channels Tab**: Shows broadcast channels
4. **Saved Tab**: Shows saved messages (future feature)

### Chat Features

- **Click any chat** to open the conversation
- **Search chats** using the search bar at the top
- **Send messages** directly through the web interface
- **View message status** (✓ sent, ✓✓ delivered, ✓✓ read)
- **See online status** for users in private chats

### Message Types

- **Text Messages**: Regular text with emoji support
- **Commands**: Special styling for bot commands (⚡ indicator)
- **Media Messages**: Photos, videos, documents, voice messages
- **Status Messages**: Delivery and read receipts

## 🔍 Troubleshooting

### Common Issues

1. **Database Errors**

   ```bash
   # Run the migration script
   python scripts/migrate_database.py
   ```

2. **Bot Not Responding**
   - Check your `BOT_TOKEN` in `.env` files
   - Ensure the bot is running: `python bot/main.py`
   - Check backend logs for errors

3. **Frontend Not Loading Chats**
   - Verify backend is running on port 8000
   - Check browser console for errors
   - Ensure you're logged in with correct credentials

4. **WebSocket Connection Issues**
   - Check CORS settings in backend
   - Verify WebSocket URL in frontend
   - Check browser developer tools for connection errors

### Debug Mode

Enable debug logging in the bot:

```python
# In bot/main.py
logging.basicConfig(level=logging.DEBUG)
```

Enable debug mode in backend:

```bash
uvicorn app.main:app --reload --log-level debug
```

## 🔒 Security Notes

- **Change default admin credentials** after first login
- **Use strong JWT secrets** in production
- **Configure CORS** for your domain
- **Keep bot token secure** and never commit to version control
- **Use HTTPS** in production

## 📊 Performance Tips

- **Database Optimization**: The new schema includes indexes for better performance
- **Media Storage**: Large media files are stored locally, not in database
- **WebSocket Efficiency**: Messages are only sent to relevant chat participants
- **Frontend Optimization**: Components are memoized to prevent unnecessary re-renders

## 🎨 Customization

### Themes

The interface uses a dark theme by default. You can customize colors in:

- `frontend/src/app/globals.css`
- Component-specific styling in each `.tsx` file

### Chat Organization

Modify chat categorization logic in:

- `backend/app/routers/chats.py` (organized endpoint)
- `frontend/src/components/chat/EnhancedChatSidebar.tsx`

### Message Styling

Customize message appearance in:

- `frontend/src/components/messages/MessageBubble.tsx`

## 🚀 What's Next?

Future enhancements planned:

- [ ] Message reactions with emojis
- [ ] Message forwarding between chats
- [ ] Voice message recording in browser
- [ ] File drag & drop upload
- [ ] Message search within chats
- [ ] Chat export functionality
- [ ] Multi-language support
- [ ] Push notifications

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

If you encounter any issues:

1. Check this setup guide
2. Review the troubleshooting section
3. Check existing GitHub issues
4. Create a new issue with detailed information

---

**Enjoy your beautiful new Telegram-like chat interface! 🎉**
