#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

APP_DIR="${APP_DIR:-$HOME/climate-hazard-analyzer}"
ENV_DIR="/etc/climate-hazard-analyzer"
ENV_FILE="$ENV_DIR/backend.env"
WEB_ROOT="/var/www/climate-hazard-analyzer"
SERVICE_NAME="climate-hazard-analyzer"
SERVICE_USER="$(id -un)"
SERVICE_GROUP="$(id -gn)"

log() { printf '[%s] %s\n' "$(date -Is)" "$*"; }
die() { log "ERROR: $*"; exit 1; }

if [[ "$EUID" -eq 0 ]]; then
  die "Run this script as your normal EC2 user, not with sudo bash."
fi

[[ -d "$APP_DIR/.git" ]] || die "Repository not found at $APP_DIR"

OS_ID=""
source /etc/os-release
OS_ID="${ID:-}"

[[ "$OS_ID" == "amzn" ]] || die "This script targets Amazon Linux 2023."
[[ "$(uname -m)" == "x86_64" ]] || die "This script targets x86_64."

EXPECTED_ORIGIN="https://github.com/namespace7/Climate-hazard-analyzer.git"
ACTUAL_ORIGIN="$(git -C "$APP_DIR" remote get-url origin)"
[[ "$ACTUAL_ORIGIN" == "$EXPECTED_ORIGIN" ]] ||
  die "Unexpected Git remote: $ACTUAL_ORIGIN"

if [[ -n "$(git -C "$APP_DIR" status --porcelain)" ]]; then
  die "Repository has local changes. Commit or resolve them first."
fi

# Check available root-disk space before package installation and swap setup.
FREE_KB="$(df -Pk / | awk 'NR == 2 {print $4}')"
(( FREE_KB >= 3000000 )) ||
  die "Less than approximately 3 GB is free on /. Review disk capacity before continuing."

# Add a persistent 1 GiB swap file for this 1 GiB RAM instance.
# This helps with memory spikes but is slower than physical RAM.
if ! sudo swapon --noheadings --show=NAME | grep -Fxq /swapfile; then
  if [[ ! -e /swapfile ]]; then
    log "Creating a 1 GiB swap file..."
    sudo fallocate -l 1G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile >/dev/null
  fi
  sudo swapon /swapfile
fi

if ! grep -qE '^/swapfile[[:space:]]+none[[:space:]]+swap[[:space:]]' /etc/fstab; then
  printf '/swapfile none swap defaults 0 0\n' |
    sudo tee -a /etc/fstab >/dev/null
fi

log "Swap status:"
sudo swapon --show

log "Installing base packages and runtime versions..."
sudo dnf install -y \
  git curl rsync tar gzip openssl nginx \
  python3.11 python3.11-pip \
  nodejs22 nodejs22-npm

# Select Node 22 where versioned alternatives are available.
if [[ -x /usr/bin/node-22 ]]; then
  sudo alternatives --set node /usr/bin/node-22
fi
if [[ -x /usr/bin/npm-22 ]]; then
  sudo alternatives --set npm /usr/bin/npm-22
fi

PYTHON_VERSION="$(python3.11 --version)"
NODE_VERSION="$(node --version)"
log "Python runtime: $PYTHON_VERSION"
log "Node runtime: $NODE_VERSION"

NODE_NUM="${NODE_VERSION#v}"
NODE_MAJOR="${NODE_NUM%%.*}"
NODE_REST="${NODE_NUM#*.}"
NODE_MINOR="${NODE_REST%%.*}"

(( NODE_MAJOR == 22 && NODE_MINOR >= 12 )) ||
  die "Vite 8 requires Node.js 22.12+ (or 20.19+). Found $NODE_VERSION."

npm --version

log "Configuring the official MongoDB 8.0 repository..."
sudo tee /etc/yum.repos.d/mongodb-org-8.0.repo >/dev/null <<'REPO'
[mongodb-org-8.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/8.0/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-8.0.asc
REPO

sudo dnf install -y mongodb-org mongodb-mongosh

# Preserve the package-provided config once before setting the desired
# local-only, authenticated database configuration.
if [[ -f /etc/mongod.conf &&
      ! -e /etc/mongod.conf.before-climate-hazard-analyzer ]]; then
  sudo cp -a /etc/mongod.conf \
    /etc/mongod.conf.before-climate-hazard-analyzer
fi

sudo tee /etc/mongod.conf >/dev/null <<'MONGO'
storage:
  dbPath: /var/lib/mongo
  journal:
    enabled: true
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
net:
  port: 27017
  bindIp: 127.0.0.1
processManagement:
  timeZoneInfo: /usr/share/zoneinfo
security:
  authorization: enabled
MONGO

log "Enabling MongoDB..."
sudo systemctl enable --now mongod
sudo systemctl is-active --quiet mongod ||
  die "MongoDB failed to start; inspect journalctl -u mongod."

# The application database is only accessible on this instance's loopback
# interface. Do not add port 27017 to the EC2 security group's inbound rules.

log "Preparing protected configuration and web directories..."
sudo install -d -o root -g root -m 700 "$ENV_DIR"
sudo install -d -o root -g root -m 755 "$WEB_ROOT"
sudo install -d -o root -g root -m 755 "$WEB_ROOT/releases"

# Nginx should serve the active versioned release published by deploy-ec2.sh.
# Disable the packaged default site if present, preserving a backup outside
# the active *.conf include pattern.
if [[ -f /etc/nginx/conf.d/default.conf ]]; then
  if [[ ! -e /etc/nginx/default.conf.pre-climate-hazard-analyzer ]]; then
    sudo cp -a /etc/nginx/conf.d/default.conf \
      /etc/nginx/default.conf.pre-climate-hazard-analyzer
  fi
  sudo mv /etc/nginx/conf.d/default.conf \
    /etc/nginx/conf.d/default.conf.disabled
fi

sudo tee /etc/nginx/conf.d/climate-hazard-analyzer.conf >/dev/null <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    root /var/www/climate-hazard-analyzer/current;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000\;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX

log "Creating the FastAPI systemd unit..."
SERVICE_TEMP="$(mktemp)"
trap 'rm -f "$SERVICE_TEMP"' EXIT

cat > "$SERVICE_TEMP" <<UNIT
[Unit]
Description=Climate Hazard Trend Analyzer API
After=network-online.target mongod.service
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$APP_DIR/backend
EnvironmentFile=$ENV_FILE
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=$APP_DIR/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=3
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
UNIT

sudo install -o root -g root -m 644 "$SERVICE_TEMP" \
  "/etc/systemd/system/$SERVICE_NAME.service"
rm -f "$SERVICE_TEMP"
trap - EXIT

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

log "Validating and enabling Nginx..."
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx

log "Checking MongoDB listener..."
sudo ss -lntp | grep -E '127\.0\.0\.1:27017[[:space:]]' ||
  die "MongoDB is not listening on 127.0.0.1:27017 as expected."

log "One-time setup completed."
log "MongoDB is installed with authorization enabled and bound to localhost."
log "Next: create database users, then populate $ENV_FILE securely."
log "The FastAPI service has NOT been started because credentials are not set up yet."
