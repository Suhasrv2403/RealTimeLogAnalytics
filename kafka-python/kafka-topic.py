from kafka.admin import KafkaAdminClient, NewTopic

admin_client = KafkaAdminClient(bootstrap_servers="kafka:9092")

topic = NewTopic(name="logs", num_partitions=1, replication_factor=1)

try:
    admin_client.create_topics(new_topics=[topic], validate_only=False)
    print("✅ Topic 'logs' created.")
except Exception as e:
    print(f"⚠️ Topic creation failed (maybe it already exists): {e}")
