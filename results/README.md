# results/

Generated pipeline output isn't committed here automatically — the
Parquet files `src/spark/log_consumer.py` writes go to the `minio`
container's own volume, not to this repo. This folder is a placeholder for
output snapshots you choose to export and commit (e.g. a sample
`SELECT * FROM logs LIMIT 20` dump from Elasticsearch, or a handful of
exported Parquet rows) when you want to show pipeline output alongside the
code.
