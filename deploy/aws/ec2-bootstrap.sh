#!/usr/bin/env bash
set -euo pipefail

# Bootstrap an Ubuntu EC2 instance for KeepContext AI
# Tested target: Ubuntu 22.04/24.04

sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Install Docker
if ! command -v docker >/dev/null 2>&1; then
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Let ubuntu user run docker without sudo
sudo usermod -aG docker ubuntu || true

echo "Bootstrap complete. Re-login to apply docker group membership."
