#!/bin/bash

# URL for Kafka Connect REST API
CONNECT_URL="http://localhost:18083"

# Directory containing connector JSON files
CONNECTOR_DIR="./connectors"

# Enable nullglob so the loop doesn’t fail if no files match
shopt -s nullglob

# Wait until Kafka Connect REST API is available
echo "Waiting for Kafka Connect REST API..."
until curl --output /dev/null --silent --head --fail $CONNECT_URL; do
    printf '.'
    sleep 2
done
echo -e "\nKafka Connect REST API is up!"

# Deploy all connector JSONs
FILES=("$CONNECTOR_DIR"/*.json)
if [ ${#FILES[@]} -eq 0 ]; then
    echo "No connector JSON files found in $CONNECTOR_DIR"
else
    for f in "${FILES[@]}"; do
        if [ -f "$f" ]; then
            echo "Deploying connector $f"
            curl -X POST -H "Content-Type: application/json" --data @"$f" "$CONNECT_URL/connectors" \
                && echo "Connector $f deployed successfully" \
                || echo "Connector $f may already exist or failed to deploy"
        fi
    done
fi