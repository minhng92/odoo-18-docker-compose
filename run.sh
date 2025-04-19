#!/bin/bash
DESTINATION=$1
PORT=$2
CHAT=$3

# Clone Odoo directory
echo "Clonning the repository" 
git clone --depth=1 https://github.com/andreiboyanov/emf-1995-docker-compose $DESTINATION
rm -rf $DESTINATION/.git

# Create PostgreSQL directory
echo "Creating the poostgresql folder $DESTINATION/postgresql"
mkdir -p $DESTINATION/postgresql

# Change ownership to current user and set restrictive permissions for security
echo "Configuring permissions"
sudo chown -R $USER:$USER $DESTINATION
sudo chmod -R 700 $DESTINATION  # Only the user has access

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Running on macOS. Skipping inotify configuration."
else
  # System configuration
  echo "Configuring sysctl.conf"
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
  sed -i '' 's/10018/'$PORT'/g' $DESTINATION/docker-compose.yml
  sed -i '' 's/20018/'$CHAT'/g' $DESTINATION/docker-compose.yml
else
  # Linux sed syntax
  echo "Configuring the Odoo ports"
  sed -i 's/10018/'$PORT'/g' $DESTINATION/docker-compose.yml
  sed -i 's/20018/'$CHAT'/g' $DESTINATION/docker-compose.yml
fi

# Set file and directory permissions after installation
echo "Configuring $DESTINATION permissions"
find $DESTINATION -type f -exec chmod 644 {} \;
find $DESTINATION -type d -exec chmod 755 {} \;

echo "Making the entrypoint executable"
chmod +x $DESTINATION/entrypoint.sh

# Run Odoo
"Running the EMF-1995 social app"
docker compose -f $DESTINATION/docker-compose.yml up -d && echo "Odoo started at http://localhost:$PORT | Master Password: minhng.info | Live chat port: $CHAT"
