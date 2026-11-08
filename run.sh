#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "Starting Splendor..."
(sleep 2; (xdg-open http://127.0.0.1:8000 || open http://127.0.0.1:8000) >/dev/null 2>&1) &
python3 server.py
