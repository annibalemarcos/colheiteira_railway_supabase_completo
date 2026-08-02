#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "===================================="
echo " Colheiteira - instalação Linux/macOS"
echo "===================================="

command -v python3 >/dev/null 2>&1 || { echo "[ERRO] Python 3 não encontrado."; exit 1; }

if [ ! -d venv ]; then
  python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if command -v npm >/dev/null 2>&1; then
  npm install -g lighthouse@13 || echo "[AVISO] Lighthouse não pôde ser instalado globalmente."
else
  echo "[AVISO] Node.js/npm não encontrados; o plugin Lighthouse ficará indisponível."
fi

if ! command -v java >/dev/null 2>&1; then
  echo "[AVISO] Java não encontrado; o plugin de ortografia pode ficar indisponível."
fi

mkdir -p output/history
chmod +x run.sh run_dashboard.sh start.sh scripts/run.sh scripts/setup.sh

echo "[OK] Instalação concluída. Rode ./run_dashboard.sh"
