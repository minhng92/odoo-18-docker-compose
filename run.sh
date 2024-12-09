#!/bin/bash

source .env

# Clone Odoo directory
git clone --depth=1 https://github.com/Citrullin/odoo-18-docker-compose $ODOO_GIT_DEST
rm -rf $ODOO_GIT_DEST/.git

# Create PostgreSQL directory
mkdir -p $ODOO_GIT_DEST/postgresql

# Change ownership to current user and set restrictive permissions for security
sudo chown -R $USER:$USER $ODOO_GIT_DEST
sudo chmod -R 700 $ODOO_GIT_DEST  # Only the user has access

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Running on macOS. Skipping inotify configuration."
else
  # System configuration
  if grep -qF "fs.inotify.max_user_watches" /etc/sysctl.conf; then
    echo $(grep -F "fs.inotify.max_user_watches" /etc/sysctl.conf)
  else
    echo "fs.inotify.max_user_watches = 524288" | sudo tee -a /etc/sysctl.conf
  fi
  sudo sysctl -p
fi

# Set ports in docker-compose.yml
# Update docker-compose configuration
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS sed syntax
  sed -i '' 's/$ODOO_PORT/'$ODOO_PORT'/g' $ODOO_GIT_DEST/docker-compose.yml
  sed -i '' 's/$ODOO_PORT/'$ODOO_CHAT_PORT'/g' $ODOO_GIT_DEST/docker-compose.yml
  sed -i '' 's/$POSTGRES_USER/'$POSTGRES_USER'/g' $ODOO_GIT_DEST/docker-compose.yml
  sed -i '' 's/$POSTGRES_PASSWORD/'$POSTGRES_PASSWORD'/g' $ODOO_GIT_DEST/docker-compose.yml
  sed -i '' 's/$POSTGRES_DB/'$POSTGRES_DB'/g' $ODOO_GIT_DEST/docker-compose.yml
else
  # Linux sed syntax
  sed -i 's/$ODOO_PORT/'$ODOO_PORT'/g' $ODOO_GIT_DEST/docker-compose.yml
  sed -i 's/$ODOO_CHAT_PORT/'$ODOO_CHAT_PORT'/g' $ODOO_GIT_DEST/docker-compose.yml
  sed -i 's/$POSTGRES_USER/'$POSTGRES_USER'/g' $ODOO_GIT_DEST/docker-compose.yml
  sed -i 's/$POSTGRES_PASSWORD/'$POSTGRES_PASSWORD'/g' $ODOO_GIT_DEST/docker-compose.yml
  sed -i 's/$POSTGRES_DB/'$POSTGRES_DB'/g' $ODOO_GIT_DEST/docker-compose.yml
fi

# Set file and directory permissions after installation
find $ODOO_GIT_DEST -type f -exec chmod 644 {} \;
find $ODOO_GIT_DEST -type d -exec chmod 755 {} \;

# Run Odoo
if ! is_present="$(type -p "docker-compose")" || [[ -z $is_present ]]; then
  docker compose -f $ODOO_GIT_DEST/docker-compose.yml up -d
else
  docker-compose -f $ODOO_GIT_DEST/docker-compose.yml up -d
fi

echo "Odoo started at http://localhost:$ODOO_PORT | Master Password: minhng.info | Live chat port: $ODOO_CHAT_PORT"
