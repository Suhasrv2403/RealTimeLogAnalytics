#!/bin/bash

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
while ! nc -z kafka 9092; do
  sleep 1
done
echo "Kafka is ready!"

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
while ! nc -z minio 9000; do
  sleep 1
done
echo "MinIO is ready!"

# Create the logs bucket in MinIO using curl
echo "Creating MinIO bucket if needed..."
curl -s -X PUT -u minioadmin:minioadmin http://minio:9000/logs > /dev/null 2>&1 || echo "Bucket may already exist or creation failed"

# Run the Spark application
echo "Starting Spark application..."
/opt/bitnami/spark/bin/spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
    /app/logConsumer.py