# YouTube Downloader Bot 🎬

Production-grade Telegram bot for downloading YouTube videos and audio.

## Features

- 🎥 Download videos in 360p, 480p, 720p, 1080p
- 🎵 Download audio as MP3 (128k, 192k, 320k, Best)
- ⚡ Smart caching - instant re-downloads
- 📊 Download progress tracking
- 🛡️ Rate limiting & spam protection
- 🔧 Admin panel with stats
- 🐳 Docker support

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| Framework | Aiogram 3.x |
| Downloader | yt-dlp |
| Media | FFmpeg |
| Database | SQLite (SQLAlchemy) |
| Config | Pydantic Settings |
| Logging | Loguru |

## Installation

### Local Setup

```bash
# Clone the repository
git clone <repository-url>
cd youtube-downloader-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .

# Copy and configure environment
cp .env.example .env
# Edit .env with your BOT_TOKEN

# Run the bot
python main.py
```

### Docker Setup

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your BOT_TOKEN

# Build and run
docker compose up -d

# View logs
docker compose logs -f
```

### Linux Deployment (systemd)

```bash
# Create service file
sudo nano /etc/systemd/system/youtube-bot.service

# Add configuration (see linux-deployment.md)
sudo systemctl enable youtube-bot
sudo systemctl start youtube-bot
```

### Windows Deployment

```bash
# Use NSSM to run as Windows Service
nssm install YouTubeBot "C:\path\to\venv\Scripts\python.exe"
nssm set YouTubeBot AppParameters "C:\path\to\main.py"
nssm start YouTubeBot
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| BOT_TOKEN | Telegram bot token | Required |
| ADMIN_TELEGRAM_ID | Admin user ID | Optional |
| DOWNLOAD_DIR | Download storage path | ./data/downloads |
| CACHE_DIR | Cache storage path | ./data/cache |
| MAX_FILE_SIZE_MB | Max upload size | 2000 |
| RATE_LIMIT_PER_USER | Requests per window | 5 |
| RATE_LIMIT_WINDOW_SECONDS | Rate limit window | 60 |

## YouTube Cookies (Important!)

YouTube may block your bot with "Sign in to confirm you're not a bot" error. To fix this:

1. Install the **"Get cookies.txt LOCALLY"** browser extension ([Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) / [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/))
2. Go to [youtube.com](https://www.youtube.com) and make sure you're logged in
3. Click the extension icon and export cookies
4. Upload the `cookies.txt` file to the project root (same folder as `main.py`)

The bot will automatically use this cookies file for all YouTube requests.

## Admin Commands

| Command | Description |
|---------|-------------|
| /admin | Show bot statistics |
| /broadcast <msg> | Send message to all users |
| /clearcache | Clear download cache |

## Architecture

```
app/
├── bot/              # Telegram bot layer
│   ├── handlers/     # Message & callback handlers
│   ├── middlewares/   # Rate limiting, DB sessions
│   ├── keyboards/    # Inline keyboards
│   ├── states/       # FSM states
│   └── filters/      # URL & admin filters
├── services/         # Business logic
│   ├── youtube/      # Metadata extraction
│   ├── downloader/   # Video/audio downloaders
│   └── ffmpeg/       # Media processing
├── database/         # SQLAlchemy models & repos
├── cache/            # File caching
├── config/           # Settings management
└── utils/            # Helper functions
```

## License

MIT
