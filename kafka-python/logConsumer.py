from confluent_kafka import Consumer
import json

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'manual-spark-batch-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['logs'])

batch = []

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            break  # no more messages
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue

        value = msg.value().decode('utf-8')
        batch.append(value)

finally:
    consumer.close()

# Save to file to pass to Spark
with open('logs_batch.json', 'w') as f:
    for line in batch:
        f.write(json.dumps({'value': line}) + '\n')
