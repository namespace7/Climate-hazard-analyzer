#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 027

APP_DIR="${APP_DIR:-$HOME/climate-hazard-analyzer}"
BRANCH="${BRANCH:-main}"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
ENV_FILE="/etc/climate-hazard-analyzer/backend.env"
WEB_ROOT="/var/www/climate-hazard-analyzer"
SERVICE_NAME="${SERVICE_NAME:-climate-hazard-analyzer}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/}"
LOG_DIR="${LOG_DIR:-$HOME/deploy-logs}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*"
}

die() {
  log "ERROR: $*"
  exit 1
}

on_error() {
  local code=$?
  log "ERROR: command failed with exit code $code at line $1."
  exit "$code"
}
trap 'on_error $LINENO' ERR

require_command() {
  command -v "$1" >/dev/null 2>&1 ||
    die "Required command not found: $1"
}

log "Checking deployment prerequisites..."

for cmd in git python3.11 node npm curl rsync sudo systemctl; do
  require_command "$cmd"
done

[[ -d "$APP_DIR/.git" ]] || die "Not a Git checkout: $APP_DIR"
EXPECTED_ORIGIN="https://github.com/namespace7/Climate-hazard-analyzer.git"
ACTUAL_ORIGIN="$(git -C "$APP_DIR" remote get-url origin)" ||
  die "Git remote 'origin' is not configured."

[[ "$ACTUAL_ORIGIN" == "$EXPECTED_ORIGIN" ]] ||
  die "Unexpected Git origin: $ACTUAL_ORIGIN"
[[ -f "$BACKEND_DIR/requirements.txt" ]] ||
  die "Missing backend/requirements.txt"
[[ -f "$FRONTEND_DIR/package-lock.json" ]] ||
  die "Missing frontend/package-lock.json"

# Require a protected, root-owned production environment file.
sudo -n true || die "Passwordless sudo is required for deployment."

sudo test -s "$ENV_FILE" ||
  die "Missing or empty $ENV_FILE. Configure it during server setup."

ENV_DIRECTORY="/etc/climate-hazard-analyzer"
DIR_METADATA="$(sudo stat -c '%U:%G:%a' "$ENV_DIRECTORY")"
FILE_METADATA="$(sudo stat -c '%U:%G:%a' "$ENV_FILE")"

[[ "$DIR_METADATA" == "root:root:700" ]] ||
  die "$ENV_DIRECTORY must be owned by root with mode 700."
[[ "$FILE_METADATA" == "root:root:600" ]] ||
  die "$ENV_FILE must be owned by root with mode 600."

# The one-time setup must create this service and load ENV_FILE via systemd.
UNIT_CONTENT="$(sudo systemctl cat "$SERVICE_NAME" 2>/dev/null)" ||
  die "systemd service '$SERVICE_NAME' is not configured yet."

grep -Fq "EnvironmentFile=$ENV_FILE" <<< "$UNIT_CONTENT" ||
  die "The service must load $ENV_FILE through systemd."

sudo nginx -t >/dev/null ||
  die "Nginx configuration is invalid."

NODE_VERSION="$(node -p 'process.versions.node')"
NODE_MAJOR="${NODE_VERSION%%.*}"
NODE_REST="${NODE_VERSION#*.}"
NODE_MINOR="${NODE_REST%%.*}"

if (( NODE_MAJOR < 20 ||
      (NODE_MAJOR == 20 && NODE_MINOR < 19) ||
      (NODE_MAJOR == 21) ||
      (NODE_MAJOR == 22 && NODE_MINOR < 12) )); then
  die "Node.js $NODE_VERSION is too old for this Vite build. Use Node 20.19+ or 22.12+."
fi

mkdir -p "$LOG_DIR"
chmod 750 "$LOG_DIR"
LOG_FILE="$LOG_DIR/deploy-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1
log "Deployment log: $LOG_FILE"

# Refuse to overwrite any uncommitted server changes.
if [[ -n "$(git -C "$APP_DIR" status --porcelain)" ]]; then
  die "Git working tree is not clean. Resolve local changes before deployment."
fi

CURRENT_BRANCH="$(git -C "$APP_DIR" branch --show-current)"
[[ "$CURRENT_BRANCH" == "$BRANCH" ]] ||
  die "Expected branch '$BRANCH'; found '$CURRENT_BRANCH'."

PREVIOUS_COMMIT="$(git -C "$APP_DIR" rev-parse HEAD)"
PREVIOUS_LINK=""

if sudo test -L "$WEB_ROOT/current"; then
  PREVIOUS_LINK="$(sudo readlink "$WEB_ROOT/current")"
elif sudo test -e "$WEB_ROOT/current"; then
  die "$WEB_ROOT/current exists but is not a symlink. Review it manually."
fi

log "Fetching origin/$BRANCH..."
git -C "$APP_DIR" fetch --prune origin \
  "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
TARGET_COMMIT="$(git -C "$APP_DIR" rev-parse "origin/$BRANCH")"

git -C "$APP_DIR" merge-base --is-ancestor \
  "$PREVIOUS_COMMIT" "$TARGET_COMMIT" ||
  die "Remote branch is not a fast-forward. Resolve Git history manually."

log "Updating source to $TARGET_COMMIT..."
git -C "$APP_DIR" merge --ff-only "$TARGET_COMMIT"

# Keep test imports isolated from production database credentials.
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  log "Creating Python virtual environment..."
  python3.11 -m venv "$BACKEND_DIR/.venv"
fi

log "Installing backend dependencies..."
"$VENV_PYTHON" -m pip install \
  --disable-pip-version-check \
  -r "$BACKEND_DIR/requirements.txt"

log "Running backend tests..."
(
  cd "$BACKEND_DIR"
  MONGODB_URI="mongodb://127.0.0.1:27017" \
  MONGODB_DATABASE="climate_hazard_analyzer_test" \
    "$VENV_PYTHON" -m pytest -q
)

log "Installing locked frontend dependencies..."
(
  cd "$FRONTEND_DIR"
  npm ci --no-audit --no-fund
  npm run lint
  npm run build
)

[[ -s "$FRONTEND_DIR/dist/index.html" ]] ||
  die "Frontend build did not produce dist/index.html."

# Publish to a new release directory before changing the live symlink.
RELEASE_ID="$(git -C "$APP_DIR" rev-parse --short=12 HEAD)-$(date +%Y%m%d%H%M%S)"
RELEASE_DIR="$WEB_ROOT/releases/$RELEASE_ID"

log "Preparing frontend release $RELEASE_ID..."
sudo install -d -o root -g root -m 755 "$WEB_ROOT/releases"
sudo install -d -o root -g root -m 755 "$RELEASE_DIR"
sudo rsync -a --delete "$FRONTEND_DIR/dist/" "$RELEASE_DIR/"
sudo find "$RELEASE_DIR" -type d -exec chmod 755 {} +
sudo find "$RELEASE_DIR" -type f -exec chmod 644 {} +

# The symlink switch lets Nginx serve either the previous or new release.
TEMP_LINK="$WEB_ROOT/.current-$RELEASE_ID-$$"
sudo ln -s "releases/$RELEASE_ID" "$TEMP_LINK"
sudo mv -Tf "$TEMP_LINK" "$WEB_ROOT/current"

log "Restarting backend service $SERVICE_NAME..."
if ! sudo systemctl restart "$SERVICE_NAME"; then
  log "Backend restart failed; attempting rollback."
  sudo journalctl -u "$SERVICE_NAME" -n 60 --no-pager || true

  if [[ -n "$PREVIOUS_LINK" ]]; then
    ROLLBACK_LINK="$WEB_ROOT/.rollback-$$"
    sudo ln -s "$PREVIOUS_LINK" "$ROLLBACK_LINK"
    sudo mv -Tf "$ROLLBACK_LINK" "$WEB_ROOT/current"
  else
    sudo rm -f "$WEB_ROOT/current"
  fi

  git -C "$APP_DIR" reset --hard "$PREVIOUS_COMMIT" || true
  sudo systemctl restart "$SERVICE_NAME" || true
  die "Backend restart failed. Rollback was attempted; inspect service logs."
fi

log "Checking backend health..."
HEALTH_OK=0

for attempt in {1..10}; do
  if curl --fail --silent --max-time 5 "$HEALTH_URL"; then
    HEALTH_OK=1
    printf '\n'
    break
  fi
  sleep 2
done

if [[ "$HEALTH_OK" -ne 1 ]]; then
  log "Health check failed; attempting rollback."
  sudo journalctl -u "$SERVICE_NAME" -n 60 --no-pager || true

  if [[ -n "$PREVIOUS_LINK" ]]; then
    ROLLBACK_LINK="$WEB_ROOT/.rollback-$$"
    sudo ln -s "$PREVIOUS_LINK" "$ROLLBACK_LINK"
    sudo mv -Tf "$ROLLBACK_LINK" "$WEB_ROOT/current"
  else
    sudo rm -f "$WEB_ROOT/current"
  fi

  git -C "$APP_DIR" reset --hard "$PREVIOUS_COMMIT" || true
  sudo systemctl restart "$SERVICE_NAME" || true
  die "Health check failed. Rollback was attempted; inspect service logs."
fi

sudo systemctl is-active --quiet "$SERVICE_NAME" ||
  die "The backend service is not active."

log "Deployment succeeded at commit $TARGET_COMMIT"
