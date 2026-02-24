FROM python:3.12-slim

# ── System deps (cron) ────────────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python deps ───────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Agent code ────────────────────────────────────────────────────────────────
COPY agent.py .

# ── Cron setup ────────────────────────────────────────────────────────────────
COPY crontab /etc/cron.d/youtube-agent
RUN chmod 0644 /etc/cron.d/youtube-agent \
    && crontab /etc/cron.d/youtube-agent \
    && touch /var/log/agent.log

# ── Entrypoint ────────────────────────────────────────────────────────────────
# Pass all env vars from the .env file into cron's environment, then tail logs.
CMD ["/bin/sh", "-c", \
     "printenv | grep -v '^_=' >> /etc/environment && cron && tail -F /var/log/agent.log"]
