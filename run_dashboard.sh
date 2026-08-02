#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ -d "venv" ]; then
  source venv/bin/activate
fi

mkdir -p output/history
echo "Dashboard: http://localhost:5840"
python server/app.py
