# Technical details

Deep-dive notes that don't belong in the top-level README: design
rationale, the review history behind a few non-obvious decisions, current
limitations, and reference links.

## Architecture rationale

Two consumers read the same Kafka topic independently, so a failure in one
pipeline doesn't affect the other:

- **Spark → MinIO (Parquet)** is the analytics path: durable, columnar,
  queryable by any Athena/Presto/dbt-style engine later.
- **Kafka Connect → Elasticsearch** is the search/ops path: near-real-time,
  denormalized, built for Kibana dashboards and ad hoc querying.

Both are Kafka consumer groups reading the same `logs` topic from
`earliest`, so either can be stopped, changed, and restarted without
touching the other or reprocessing data twice for the other pipeline.

## Review history: what changed and why

**Jar version reconciliation.** The Spark job's Kafka/Hadoop-AWS
dependency versions used to be declared independently in three places —
`docker/spark-app/Dockerfile` (jars baked into the image), the old
`run.sh`'s `spark-submit --packages` flag, and a `spark.jars.packages`
config call inside `log_consumer.py` itself — and the last one had drifted
to different version numbers than the other two. Since `--packages`
triggers Ivy resolution before the driver JVM starts, setting
`spark.jars.packages` from inside the already-running Python script was
mostly inert; the two real sources of truth were the Dockerfile and
`run.sh`, and they already agreed. The fix: the Dockerfile is now the only
place these versions are declared (as `ARG`s), `run.sh` no longer passes
`--packages` at all (redundant network resolution of jars already baked
into the image), and `log_consumer.py` no longer declares them.

**Kafka Connect image was never built.** `docker-compose.yml` referenced
`kafka-connect-custom:7.5.0` with no `build:` key — `docker-compose up -d`
would try to pull that name from a registry and fail, since it only
exists as a local Dockerfile. Fixed by adding `build: ./docker/kafka-connect`
to the service definition.

**Removed Airflow + Postgres.** The original compose file included
`airflow-init`, `airflow-webserver`, and `postgres` services (and the
README's tech-stack table mentioned Airflow for "scheduling archival
jobs"), but no DAG, script, or config anywhere in the repo ever used them
— `airflow-webserver`'s `./airflow/dags` volume mount pointed at a
directory that didn't exist. Rather than leave unused services adding
~1GB+ of images and a dangling mount to `docker-compose up`, they were
removed. Reintroducing scheduled archival is a reasonable next step (see
below) but should come with an actual DAG.

**Producer/consumer schema check.** Audited what
`scripts/kafka/log_generator.py` emits against what
`src/spark/log_consumer.py` expects to parse — they already agreed
(`{"timestamp": str, "status": str, "user": str}`). This is now enforced
by `tests/test_log_generator.py::test_generate_log_record_matches_consumer_schema`
rather than left as an implicit assumption.

**Removed connector jar duplication.** `plugins/kafka-connect-elasticsearch-14.0.0.jar`
was a 92KB binary checked into git, providing the same Elasticsearch sink
connector that `docker/kafka-connect/Dockerfile` already installs via
`confluent-hub install`. It also wasn't on the container's
`CONNECT_PLUGIN_PATH`, so it was doing nothing. Removed; the Dockerfile
install is the only mechanism now.

## Known limitations

- **Single broker, single partition.** `KAFKA_LOGS_TOPIC_PARTITIONS=1` /
  `..._REPLICATION_FACTOR=1` (see `configs/pipeline.env`) is only safe for
  this local dev cluster — a real deployment needs more of both.
- **No persistent Spark checkpoint volume.** `SPARK_CHECKPOINT_LOCATION`
  defaults to `/tmp/checkpoint_logs` inside the container, which isn't
  backed by a docker volume — recreating the `spark` container loses
  streaming offset/state and Structured Streaming's exactly-once
  guarantees along with it.
- **Hardcoded local-dev credentials.** `MINIO_ACCESS_KEY` /
  `MINIO_SECRET_KEY` default to `minioadmin`/`minioadmin`, which is fine
  for this local demo but must never be reused as-is anywhere reachable
  outside your machine.
- **No live end-to-end test.** `tests/` covers the config loader and the
  producer/consumer schema contract as pure-function unit tests; there's
  no integration test that actually spins up Kafka + Spark + MinIO and
  checks a message flows end-to-end (would need `docker-compose up` in
  CI, which is a reasonable follow-up but wasn't in scope here).
- **Synthetic data only.** `scripts/kafka/log_generator.py` produces
  random `put`/`get`/`auth`/`rmi` events for demo purposes — it isn't
  wired to any real log source.

## Reference links

- [Kafka documentation](https://kafka.apache.org/documentation/)
- [Spark Structured Streaming programming guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [MinIO documentation](https://min.io/docs/minio/linux/index.html)
- [Kafka Connect Elasticsearch sink connector](https://docs.confluent.io/kafka-connectors/elasticsearch/current/overview.html)
