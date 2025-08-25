# Telegram Bot Features

This document outlines the features and capabilities of the Telegram bot.

## Core Functionality

The primary purpose of this bot is to act as an **echo and archive service**. It processes incoming messages, archives their content and media, and echoes back a confirmation to the user.

## Message Handling

The bot is designed to handle a variety of message types:

- **Text Messages**: Any text sent to the bot will be echoed back to the user.
- **Photos**: The bot can receive photos. It will download the highest resolution version of the photo and save it.
- **Videos**: The bot can receive videos and will download and store them.
- **Voice Messages**: Voice messages are captured and saved as `.ogg` files.
- **Documents**: The bot can handle any type of document, saving it with its original filename.

## Archiving

For every message it receives, the bot performs the following archiving actions:

1. **Media Storage**: All media files (photos, videos, voice messages, documents) are downloaded and stored in the `data/media` directory. The files are organized into subdirectories based on their type (`images`, `videos`, `voices`, `docs`).
2. **Backend Integration**: The bot sends a structured JSON payload to a backend API endpoint (`/internal/ingest/telegram`). This payload contains detailed information about the message, including:
    - Chat information (ID, type, title)
    - User ID
    - Telegram Message ID
    - Content-Type (e.g., `text`, `photo`, `video`)
    - Message text or caption
    - Relative path to the saved media file
    - Timestamp of the message

## Commands

- `/start`: Initiates a conversation with the bot and displays a welcome message: "Hello! I am your echo+archive bot."

## How it Works

1. A user sends a message (text or media) to the bot.
2. The bot identifies the message type.
3. If the message contains media, the bot downloads the file to the appropriate directory.
4. The bot constructs a JSON payload with all the relevant message data.
5. This payload is sent to the backend for storage and further processing.
6. The bot replies to the user, either by echoing the text or by sending a confirmation message for media.

## Backend API Interaction

The bot communicates with a FastAPI backend. This interaction is crucial for the archiving functionality.

- **Endpoint**: `POST /internal/ingest/telegram`
- **Authentication**: The bot uses a secret key (`API_INGEST_SECRET`) to authenticate with the backend, ensuring that only the bot can send data to the ingest endpoint.

This setup allows for a separation of concerns, where the bot is responsible for interfacing with Telegram and the backend is responsible for data storage, management, and potentially serving a web frontend.
