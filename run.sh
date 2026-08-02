#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ -z "$1" ]; then
  echo "Uso: ./run.sh <URL>"
  echo "Exemplo: ./run.sh https://example.com"
  exit 1
fi

URL="$1"
if [[ ! "$URL" =~ ^https?:// ]]; then
  URL="https://$URL"
fi

if [ -d "venv" ]; then
  source venv/bin/activate
fi

python main.py "$URL"
echo "Dashboard: http://localhost:5840"
