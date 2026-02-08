#!/bin/bash

set -ex

# Force instance recreation: V2

# Update and Install dependencies
apt-get update -y
apt-get install -y docker.io docker-compose git

# Add the current user to the docker group
usermod -aG docker $(whoami)

#  Start and enable Docker
systemctl start docker
systemctl enable docker

#  Clone the repository
if [ -n "${repo_url}" ]; then
  git clone "https://${gh_pat}@github.com/${repo_url}.git"
  
  #  Create the .env file with all required environment variables
  cat <<EOF > aero_bound_ventures/backend/.env
# Email Configuration
MAIL_USERNAME=${mail_username}
MAIL_PASSWORD=${mail_password}
MAIL_FROM=${mail_from}
MAIL_PORT=${mail_port}
MAIL_SERVER=${mail_server}

# Authentication
ACCESS_TOKEN_EXPIRE_MINUTES=${access_token_expire_minutes}
SECRET_KEY=${secret_key}
ALGORITHM=${algorithm}

# Amadeus Flight API
AMADEUS_API_KEY=${amadeus_api_key}
AMADEUS_API_SECRET=${amadeus_api_secret}
AMADEUS_BASE_URL=${amadeus_base_url}

# Database
DATABASE_URL=${database_url}

# Pesapal Payment Gateway
PESAPAL_CONSUMER_KEY=${pesapal_consumer_key}
PESAPAL_CONSUMER_SECRET=${pesapal_consumer_secret}
PESAPAL_BASE_URL=${pesapal_base_url}
PESAPAL_IPN_ID=${pesapal_ipn_id}

# Cloudinary
CLOUDINARY_URL=${cloudinary_url}

# Redis
REDIS_URL=${redis_url}

# Google OAuth
GOOGLE_CLIENT_ID=${google_client_id}
GOOGLE_CLIENT_SECRET=${google_client_secret}
GOOGLE_REDIRECT_URI=${google_redirect_uri}

# CORS and Frontend
CORS_ORIGINS=${cors_origins}
FRONTEND_URL=${frontend_url}

# Environment
ENVIRONMENT=${environment}
EOF

  #  Run docker compose
  cd aero_bound_ventures/backend
  docker-compose up -d --build
fi