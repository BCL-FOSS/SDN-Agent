#!/bin/bash

container_setup() {

  # Find the running Caddy container ID
  CADDY_CONTAINER=$(docker ps --filter "ancestor=caddy" --format "{{.ID}}")

  if [ -z "$CADDY_CONTAINER" ]; then
      echo "No running Caddy container found."
      exit 1
  fi

  echo "Caddy container found: $CADDY_CONTAINER"

  # Format caddyfile
  docker exec "$CADDY_CONTAINER" sh -c "caddy fmt /etc/caddy/Caddyfile"

  echo "Permissions and ownership updated successfully."
}

sudo docker-compose down

sudo docker-compose up --build --remove-orphans