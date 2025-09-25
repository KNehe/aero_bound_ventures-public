#!/bin/bash

set -ex

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
#  Create the .env file
  cat <<EOF > aero_bound_ventures/backend/.env
MAIL_USERNAME=${mail_username}
MAIL_PASSWORD=${mail_password}
MAIL_FROM=${mail_from}
MAIL_PORT=${mail_port}
MAIL_SERVER=${mail_server}
ACCESS_TOKEN_EXPIRE_MINUTES=${access_token_expire_minutes}
SECRET_KEY=${secret_key}
ALGORITHM=${algorithm}
AMADEUS_API_KEY=${amadeus_api_key}
AMADEUS_API_SECRET=${amadeus_api_secret}
AMADEUS_BASE_URL=${amadeus_base_url}
EOF
#  Run docker compose
 cd aero_bound_ventures/backend
 docker-compose up -d --build
fi