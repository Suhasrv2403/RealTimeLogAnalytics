"""Spark Structured Streaming consumer: Kafka logs topic -> console + MinIO.

Reads the JSON log events published by scripts/kafka/log_generator.py from
the configured Kafka topic, parses them against a fixed schema, and writes
the result to two streaming sinks in parallel:
  1. the console (for local debugging), and
  2. MinIO (S3-compatible object storage) as Parquet, for downstream
     analytics (see README.md architecture diagram).

Inputs: JSON records read from Kafka, each shaped like
{"timestamp": str, "status": str, "user": str} — this must stay in sync
with scripts/kafka/log_generator.py's generate_log_record() output.
Reads KAFKA_BOOTSTRAP_SERVERS_INTERNAL, KAFKA_LOGS_TOPIC, MINIO_*,
SPARK_TRIGGER_INTERVAL_SECONDS and SPARK_CHECKPOINT_LOCATION from
configs/pipeline.env (or the environment), falling back to sane
local-dev defaults.
Outputs: none returned (this is a long-running streaming job); writes
Parquet files under the configured MinIO path and mirrors the same
parsed rows to stdout. Blocks forever via awaitAnyTermination().

Intended to run inside the 'spark' service defined in docker-compose.yml
(started via docker/spark-app/run.sh), not standalone.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from common.env_config import get_int, get_str, load_env_file  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_env_file(_REPO_ROOT / "configs" / "pipeline.env")

from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql.functions import col, from_json  # noqa: E402
from pyspark.sql.types import StringType, StructType  # noqa: E402

# Schema mirrors the log dict shape produced by
# scripts/kafka/log_generator.py's generate_log_record().
schema = StructType().add("timestamp", StringType()).add("status", StringType()).add("user", StringType())

kafka_bootstrap_servers = get_str("KAFKA_BOOTSTRAP_SERVERS_INTERNAL", "kafka:9092")
kafka_topic = get_str("KAFKA_LOGS_TOPIC", "logs")
minio_endpoint = get_str("MINIO_ENDPOINT", "http://host.docker.internal:9000")
minio_access_key = get_str("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = get_str("MINIO_SECRET_KEY", "minioadmin")
minio_bucket = get_str("MINIO_BUCKET", "logs")
minio_parquet_path = get_str("MINIO_PARQUET_PATH", "s3a://logs/parquet_logs/")
trigger_interval = f"{get_int('SPARK_TRIGGER_INTERVAL_SECONDS', 10)} seconds"
checkpoint_location = get_str("SPARK_CHECKPOINT_LOCATION", "/tmp/checkpoint_logs")

# Spark session with MinIO/S3A settings.
# NOTE: Kafka/Hadoop-AWS jar versions are deliberately NOT declared here.
# They are baked into the image at build time by docker/spark-app/Dockerfile
# (the single canonical source of truth for these versions — see the
# JAR_* build args there) and land on Spark's default classpath
# ($SPARK_HOME/jars), so no --packages / spark.jars.packages is needed or
# set at runtime. This used to be declared a second time here with
# different version numbers than the Dockerfile/run.sh used, which was a
# real bug (two different dependency resolutions for the same job) —
# fixed by removing the duplicate declaration rather than reconciling the
# numbers, since the Dockerfile-baked jars are the ones actually used.
spark = (
    SparkSession.builder.appName("KafkaToMinIO")
    .master("local[*]")
    .config("spark.hadoop.fs.s3a.access.key", minio_access_key)
    .config("spark.hadoop.fs.s3a.secret.key", minio_secret_key)
    .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("INFO")
print("✅ SparkSession created successfully")

# Test MinIO connection: confirms the bucket exists before starting the
# streaming writes below, so a missing bucket fails fast with a clear
# message instead of surfacing as an opaque streaming-query error later.
hadoop_conf = spark._jsc.hadoopConfiguration()
try:
    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_conf)
    if fs.exists(spark._jvm.org.apache.hadoop.fs.Path(f"s3a://{minio_bucket}/")):
        print("✅ MinIO bucket exists")
    else:
        print(f"⚠️ MinIO bucket '{minio_bucket}' does NOT exist. Create it in MinIO console.")
except Exception as e:
    print("❌ Error connecting to MinIO:", e)

# Read from Kafka
raw_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
    .option("subscribe", kafka_topic)
    .option("startingOffsets", "earliest")
    .load()
)
print("✅ Kafka readStream created")

logs_df = raw_df.selectExpr("CAST(value AS STRING) as json_str")
parsed_df = logs_df.select(from_json(col("json_str"), schema).alias("data")).select("data.*")

# Console check: mirrors parsed rows to stdout every micro-batch, purely
# for local visibility that data is flowing — not a required part of the
# pipeline output.
query_check = (
    parsed_df.writeStream.outputMode("append")
    .format("console")
    .option("truncate", "false")
    .trigger(processingTime=trigger_interval)
    .start()
)
print("✅ Console streaming started")

# Write streaming data to MinIO.
# checkpointLocation is required by Structured Streaming to track processed
# offsets/state for exactly-once semantics across restarts; the default
# "/tmp/..." means progress is lost if the container is recreated (no
# persistent volume is mounted for it in docker-compose.yml) — fine for a
# demo, not for production durability (see docs/DETAILS.md).
query_minio = (
    parsed_df.writeStream.outputMode("append")
    .format("parquet")
    .option("path", minio_parquet_path)
    .option("checkpointLocation", checkpoint_location)
    .trigger(processingTime=trigger_interval)
    .start()
)
print(f"✅ Streaming to MinIO started at {minio_parquet_path}")

# Wait for any termination without blocking each other: exits the process
# as soon as either streaming query (console or MinIO) stops/fails, rather
# than only after both have.
spark.streams.awaitAnyTermination()
