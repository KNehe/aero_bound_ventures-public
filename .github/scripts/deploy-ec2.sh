#!/usr/bin/env bash
set -euo pipefail
trap 'echo "ERROR: deploy script failed at line ${LINENO}" >&2' ERR

: "${DOPPLER_TOKEN:?DOPPLER_TOKEN is required}"
: "${GH_PAT:?GH_PAT is required}"

# Set non-interactive to avoid prompts
export DEBIAN_FRONTEND=noninteractive

# 1. Create swap space (2GB) if not already present
if [ ! -f /swapfile ]; then
  echo 'Creating 2GB swap file...'
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo 'Swap created successfully'
else
  echo 'Swap already exists'
  sudo swapon /swapfile 2>/dev/null || true
fi
free -h

# 2. Install Dependencies (if missing)
if ! command -v docker &> /dev/null; then
  echo 'Docker not found. Installing...'
  sudo apt-get update -y
  sudo apt-get install -y docker.io docker-compose-v2 git
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -aG docker ubuntu
fi

if ! command -v doppler &> /dev/null; then
  echo 'Doppler CLI not found. Installing...'
  sudo apt-get update -y
  sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
  curl -sLf --retry 3 --tlsv1.2 --proto '=https' 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | sudo gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" | sudo tee /etc/apt/sources.list.d/doppler-cli.list > /dev/null
  sudo apt-get update -y
  sudo apt-get install -y doppler
fi

# Debug Info
echo 'Debug: Checking permissions...'
id
sudo id
sudo docker info

run_compose() {
  if docker compose version &> /dev/null; then
    sudo --preserve-env=DOPPLER_TOKEN doppler run -- docker compose "$@"
  else
    sudo --preserve-env=DOPPLER_TOKEN doppler run -- docker-compose "$@"
  fi
}

clear_guard_bans() {
  echo '--- Clearing guard ban state ---'
  local redis_ready=false
  local attempt=0
  local banned_keys=""
  local -a banned_key_args=()

  while [ "$attempt" -lt 30 ]; do
    if run_compose exec -T redis redis-cli PING >/dev/null 2>&1; then
      redis_ready=true
      echo 'Redis is ready'
      banned_keys="$(run_compose exec -T redis redis-cli --scan --pattern 'guard_core:banned_*' 2>/dev/null | tr -d '\r' || true)"
      break
    fi
    attempt=$((attempt + 1))
    echo "Waiting for Redis... attempt ${attempt}/30"
    sleep 1
  done

  if [ "$redis_ready" != true ]; then
    echo 'WARNING: Redis was not ready in time. Skipping guard ban cleanup.'
    return 0
  fi

  if [ -z "$banned_keys" ]; then
    echo 'No guard ban keys found'
    return 0
  fi

  while IFS= read -r key; do
    [ -n "$key" ] && banned_key_args+=("$key")
  done <<< "$banned_keys"

  echo "Deleting ${#banned_key_args[@]} guard ban key(s)"
  if run_compose exec -T redis redis-cli DEL "${banned_key_args[@]}" >/dev/null 2>&1; then
    echo 'Cleared guard ban keys'
  else
    echo 'WARNING: Could not clear guard ban state. Continuing deployment.'
  fi
}

# 3. Clone or Pull
if [ -d 'aero_bound_ventures' ]; then
  echo 'Repo exists, pulling...'
  cd aero_bound_ventures
  git remote set-url origin https://x-access-token:${GH_PAT}@github.com/KNehe/aero_bound_ventures.git
  git pull origin main
else
  echo 'Repo missing, cloning...'
  git clone https://x-access-token:${GH_PAT}@github.com/KNehe/aero_bound_ventures.git
  cd aero_bound_ventures
fi

cd backend

# 4. Use Doppler-managed runtime secrets for Docker Compose
CERTBOT_EMAIL=$(doppler secrets get MAIL_FROM --plain)

# 5. Deploy Docker containers
# Use 'docker compose' (v2) if available, otherwise 'docker-compose'
if docker compose version &> /dev/null; then
  echo 'Using docker compose v2'
  run_compose down
  run_compose up -d --build
else
  echo 'Using legacy docker-compose'
  run_compose down
  run_compose up -d --build
fi

# 6. Setup Nginx reverse proxy + SSL
echo '--- Setting up Nginx reverse proxy ---'

# Install Nginx and Certbot if not present
if ! command -v nginx &> /dev/null; then
  echo 'Installing Nginx...'
  sudo apt-get update -y
  sudo apt-get install -y nginx
fi

if ! command -v certbot &> /dev/null; then
  echo 'Installing Certbot...'
  sudo apt-get install -y certbot python3-certbot-nginx
fi

# Write Nginx config for api subdomain
sudo tee /etc/nginx/sites-available/api.aeroboundventures.com > /dev/null <<'NGINX_CONF'
server {
    listen 80;
    server_name api.aeroboundventures.com;

    location / {
        client_max_body_size 2M;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
NGINX_CONF

# Enable the site (idempotent)
sudo ln -sf /etc/nginx/sites-available/api.aeroboundventures.com /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t && sudo systemctl reload nginx
echo 'Nginx is running on port 80'

# Attempt SSL certificate (non-blocking — will fail gracefully if DNS not ready)
echo '--- Attempting SSL certificate ---'
sudo certbot --nginx \
  -d api.aeroboundventures.com \
  --non-interactive \
  --agree-tos \
  --email "${CERTBOT_EMAIL}" \
  --cert-name aeroboundventures-api \
  --redirect \
  || echo 'WARNING: Certbot failed. DNS may not be pointing to this server yet. Nginx is still running on HTTP.'

echo '--- Nginx setup complete ---'
sudo systemctl status nginx --no-pager

# 7. Clear stale guard bans after the proxy is back in place.
clear_guard_bans
echo '--- Guard ban cleanup complete ---'
