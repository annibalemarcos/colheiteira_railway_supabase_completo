FROM node:22-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    CHROME_PATH=/usr/bin/chromium \
    LIGHTHOUSE_BIN=lighthouse

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        chromium \
        default-jre-headless \
        fonts-liberation \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Pin de major para evitar que uma atualização futura quebre o plugin sem aviso.
RUN npm install --global lighthouse@13

COPY . .
RUN chmod +x start.sh run.sh run_dashboard.sh scripts/run.sh scripts/setup.sh || true \
    && mkdir -p output/history

EXPOSE 5840

CMD ["./start.sh"]
