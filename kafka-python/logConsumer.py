from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType

# Define the schema of your log messages
schema = StructType() \
    .add("timestamp", StringType()) \
    .add("status", StringType()) \
    .add("user", StringType())

# Create Spark session
spark = SparkSession.builder \
    .appName("KafkaConsumer") \
    .master("local[*]") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()
# Kafka bootstrap servers - use localhost:29092 if Kafka runs in Docker but exposed to host
kafka_bootstrap_servers = "localhost:29092"

# Read from Kafka topic 'logs'
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", "logs") \
    .option("startingOffsets", "earliest") \
    .load()

# Kafka value is in bytes, cast to string
logs_df = raw_df.selectExpr("CAST(value AS STRING) as json_str")

# Parse JSON string to columns
parsed_df = logs_df.select(from_json(col("json_str"), schema).alias("data")).select("data.*")

# Output the streaming data to console
query = parsed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
