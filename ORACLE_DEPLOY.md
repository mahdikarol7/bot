# Oracle Cloud Deployment Guide

## Step 1: Create Oracle Cloud Account
1. Go to https://cloud.oracle.com/free
2. Sign up for Free Tier (no credit card charge)
3. Create a VM instance:
   - Shape: **VM.Standard.A1.Flex** (4 CPU, 24GB RAM) - FREE
   - Image: **Ubuntu 22.04**
   - Create SSH key pair (save the private key)

## Step 2: Connect to your VM
```bash
ssh -i your-key.pem ubuntu@YOUR_VM_IP
```

## Step 3: Install dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nodejs npm ffmpeg python3 python3-pip git
sudo pip3 install yt-dlp
```

## Step 4: Clone and setup bot
```bash
git clone https://github.com/mahdikarol7/bot.git
cd bot
npm install
npm run build
```

## Step 5: Create .env file
```bash
nano .env
```
Add your variables:
```
BOT_TOKEN=your_token_here
ADMIN_IDS=your_telegram_id
MAX_FILE_SIZE_MB=150
```

## Step 6: Run with PM2 (keeps bot alive 24/7)
```bash
sudo npm install -g pm2
pm2 start dist/index.js --name youtube-bot
pm2 save
pm2 startup
```

## Done!
Your bot now runs 24/7 on a free VPS with real IP.
YouTube downloads will work without blocking.

## Useful commands:
- `pm2 logs youtube-bot` - see bot logs
- `pm2 restart youtube-bot` - restart bot
- `pm2 stop youtube-bot` - stop bot
