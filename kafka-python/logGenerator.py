import random
import datetime
import time
from kafka import KafkaProducer
import json

# Define a list of possible log operation types
log_status = ["put", "get", "auth", "rmi"]

# Initialize the Kafka producer with JSON serialization
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',  # Kafka broker address
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize dictionary to JSON bytes
)

# Continuously generate and send log messages to the Kafka topic
while True:
    # Randomly select a log status and user ID for simulation
    status = random.choice(log_status)
    user_number = random.randint(1, 100)

    # Construct a log message as a dictionary
    log = {
        "timestamp": str(datetime.datetime.now()),  # Current timestamp
        "status": status,                           # Operation type
        "user": str(user_number)                    # Simulated user ID
    }

    # Send the log message to the 'logs' topic
    producer.send('logs', log)

    # Immediately send all buffered records to Kafka
    producer.flush()

    # Wait 1 second before generating the next log
    time.sleep(1)
