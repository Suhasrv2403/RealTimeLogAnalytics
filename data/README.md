# data/

`sample_logs.json` — five example log records in the exact shape
`scripts/kafka/log_generator.py`'s `generate_log_record()` produces and
`src/spark/log_consumer.py`'s Spark schema expects
(`{"timestamp": str, "status": str, "user": str}`). Useful as a quick
manual sanity check of the schema, or for `kafka-console-producer.sh` if
you want to feed the topic without running the live generator.
