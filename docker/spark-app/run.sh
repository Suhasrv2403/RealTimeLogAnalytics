#!/bin/bash
set -e

# Load pipeline config baked/mounted into the image (see
# docker/spark-app/Dockerfile and configs/pipeline.env); falls back to the
# hardcoded defaults below if it's missing, so this still works standalone.
set -a
[ -f /app/configs/pipeline.env ] && source /app/configs/pipeline.env
set +a

KAFKA_HOST="${KAFKA_HOST:-kafka}"
KAFKA_PORT="${KAFKA_PORT:-9092}"
MINIO_HOST="${MINIO_HOST:-minio}"
MINIO_PORT="${MINIO_PORT:-9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin}"
MINIO_BUCKET="${MINIO_BUCKET:-logs}"

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
while ! nc -z "$KAFKA_HOST" "$KAFKA_PORT"; do
  sleep 1
done
echo "Kafka is ready!"

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
while ! nc -z "$MINIO_HOST" "$MINIO_PORT"; do
  sleep 1
done
echo "MinIO is ready!"

# Create the logs bucket in MinIO using curl
echo "Creating MinIO bucket if needed..."
curl -s -X PUT -u "${MINIO_ACCESS_KEY}:${MINIO_SECRET_KEY}" "http://${MINIO_HOST}:${MINIO_PORT}/${MINIO_BUCKET}" \
    > /dev/null 2>&1 || echo "Bucket may already exist or creation failed"

# Run the Spark application.
# NOTE: no --packages flag here — the required Kafka/Hadoop-AWS jars are
# already baked into /opt/spark/jars by docker/spark-app/Dockerfile (the
# canonical source for these versions), so nothing needs to be resolved
# over the network at container start. Previously this flag pulled a
# *different* version set than the one baked into the image, which is
# fixed by removing the redundant flag rather than reconciling the numbers.
echo "Starting Spark application..."
/opt/bitnami/spark/bin/spark-submit /app/src/spark/log_consumer.py
