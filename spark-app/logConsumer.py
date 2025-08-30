from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType

# Define schema
schema = StructType() \
    .add("timestamp", StringType()) \
    .add("status", StringType()) \
    .add("user", StringType())

# Spark session with Kafka and AWS packages
spark = SparkSession.builder \
    .appName("KafkaToMinIO") \
    .master("local[*]") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
            "org.apache.hadoop:hadoop-aws:3.3.6,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.528") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://host.docker.internal:9000")  \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")
print("✅ SparkSession created successfully")

# MinIO configuration
hadoop_conf = spark._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3a.access.key", "minioadmin")
hadoop_conf.set("fs.s3a.secret.key", "minioadmin")
hadoop_conf.set("fs.s3a.endpoint", "http://host.docker.internal:9000")  # Updated to host.docker.internal
hadoop_conf.set("fs.s3a.path.style.access", "true")
hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
print("✅ MinIO configuration set")

# Test MinIO connection
try:
    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_conf)
    if fs.exists(spark._jvm.org.apache.hadoop.fs.Path("s3a://logs/")):
        print("✅ MinIO bucket exists")
    else:
        print("⚠️ MinIO bucket 'logs' does NOT exist. Create it in MinIO console.")
except Exception as e:
    print("❌ Error connecting to MinIO:", e)

# Kafka configuration
kafka_bootstrap_servers = "kafka:9092" # Use host.docker.internal for Kafka too

# Read from Kafka
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", "logs") \
    .option("startingOffsets", "earliest") \
    .load()
print("✅ Kafka readStream created")

logs_df = raw_df.selectExpr("CAST(value AS STRING) as json_str")
parsed_df = logs_df.select(from_json(col("json_str"), schema).alias("data")).select("data.*")

# Console check
query_check = parsed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .trigger(processingTime="10 seconds") \
    .start()
print("✅ Console streaming started")

# Write streaming data to MinIO
minio_path = "s3a://logs/parquet_logs/"
query_minio = parsed_df.writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", minio_path) \
    .option("checkpointLocation", "/tmp/checkpoint_logs") \
    .trigger(processingTime="10 seconds") \
    .start()
print(f"✅ Streaming to MinIO started at {minio_path}")

# Wait for any termination without blocking each other
spark.streams.awaitAnyTermination()