# 🔧 SECURE CONFIGURATION GUIDE

## WHERE TO PUT YOUR ACTUAL API KEYS & SECRETS

### Step 1: Backend Environment Configuration

**File**: `tg-bot-web/backend/.env`

Replace the placeholders with your actual values:

```env
# Database and media paths (keep as is)
SQLITE_PATH=../data/app.db
MEDIA_DIR=../data/media

# 🔑 REPLACE THESE WITH YOUR ACTUAL SECRETS:
API_INGEST_SECRET=your_actual_secret_here_32_chars_long
JWT_SECRET=your_actual_jwt_secret_here_32_chars_long
JWT_ALG=HS256
ACCESS_TOKEN_TTL_HOURS=1
REFRESH_TOKEN_TTL_DAYS=7

# 👤 ADMIN CREDENTIALS (change after first login):
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here

# 🤖 YOUR BOT TOKEN FROM @BotFather:
BOT_TOKEN=8333859648:AAGuzqpQhExzKDx3dJO6Op1YvTGRkrtVSvQ

# Security settings (adjust domains as needed)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=../data/app.log
```

### Step 2: Bot Environment Configuration  

**File**: `tg-bot-web/bot/.env`

```env
# 🤖 YOUR BOT TOKEN (same as backend):
BOT_TOKEN=8333859648:AAGuzqpQhExzKDx3dJO6Op1YvTGRkrtVSvQ

# Backend connection
BACKEND_BASE_URL=http://127.0.0.1:8000

# 🔑 SAME SECRET AS BACKEND:
API_INGEST_SECRET=your_actual_secret_here_32_chars_long

# Media storage
MEDIA_DIR=../data/media

# Logging
LOG_LEVEL=INFO
LOG_FILE=../data/bot.log
```

## 🛡️ HOW TO GENERATE SECURE SECRETS

### Option 1: Using Python (Recommended)

```bash
python -c "import secrets; print('API_INGEST_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
```

### Option 2: Using OpenSSL

```bash
openssl rand -base64 32
```

### Option 3: Online Generator (Use with caution)

Visit: <https://www.uuidgenerator.net/random-string-generator>

## 📋 QUICK CONFIGURATION CHECKLIST

- [ ] Replace `API_INGEST_SECRET` in both backend/.env and bot/.env (must be identical)
- [ ] Replace `JWT_SECRET` in backend/.env
- [ ] Keep your bot token: `8333859648:AAGuzqpQhExzKDx3dJO6Op1YvTGRkrtVSvQ`
- [ ] Change admin password from "admin" to something secure
- [ ] Ensure both .env files are in .gitignore (never commit secrets!)

## ⚠️ SECURITY REMINDER

1. **Never commit .env files** to version control
2. **Keep your bot token secret** - if exposed, revoke it via @BotFather
3. **Use strong passwords** for admin account
4. **Generate cryptographically secure secrets** (don't use simple passwords)

## 🚀 AFTER CONFIGURATION

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start bot: `cd bot && python main.py`
3. Login with your admin credentials
4. Change admin password immediately after first login

## 🔍 TESTING YOUR CONFIGURATION

Your original test files should work:

- `test.py` - Tests admin login
- `test2.py` - Tests API endpoints (update the token after login)
