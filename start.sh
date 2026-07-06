#!/bin/bash
/usr/local/bin/xray run -c /app/xray-config.json &
sleep 3
HTTPS_PROXY=socks5://127.0.0.1:1080 node dist/index.js
