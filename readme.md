# 🧠 Real-Time Log Analytics Pipeline

This project implements a real-time log analytics pipeline using Apache Kafka, Apache Spark Structured Streaming, MinIO, and Elasticsearch.

Logs flow through Kafka and are processed in two ways:

Stream Processing → Spark consumes Kafka topics, transforms logs, and writes them into MinIO (S3-compatible storage) in Parquet format.

Search & Monitoring → Kafka Connect pushes logs directly from Kafka to Elasticsearch for fast indexing, querying, and visualization in Kibana.

---

## ⚡ Architecture

+-------------------+
|   Log Producers   |
+-------------------+
          |
          v
+-------------------+         +-------------------+
|      Kafka        | ----->  | Kafka Connect ES  | ---> Elasticsearch + Kibana
+-------------------+         +-------------------+
          |
          v
+-------------------+
| Spark Streaming   |
| (Transform logs)  |
+-------------------+
          |
          v
+-------------------+
|      MinIO        |
|   (Parquet S3a)   |
+-------------------+



---







## 🚀 Features

Real-time log ingestion with Kafka

Two pipelines in parallel:

MinIO (S3a/Parquet) for analytics

Elasticsearch for search & dashboards

Kafka Connect integration with Elasticsearch sink connector

Fully containerized with Docker Compose

Works with BI tools (Athena, Presto, dbt) and Observability tools (Grafana, Kibana)



---
---

## 🚀 Setup

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/log-analytics-pipeline.git
cd log-analytics-pipeline
```

### 2. Run all services
```bash
docker-compose up -d
```
This will start:

Kafka at localhost:9092

MinIO at localhost:9000 (console: localhost:9001)

Elasticsearch at localhost:9200

Kibana at localhost:5601

Kafka Connect at localhost:8083



### 3. Deploy Connector for Kafka to ElasticSearch
```bash
sh deploy-connectors.sh
```
This will push Kafka topic logs → Elasticsearch index logs.

### 🖥️ Run Log Producer

Inside kafka-producer/, run:
```bash
python logProducer.py
```

### 📊 Verify

In MinIO: Check Parquet logs in bucket logs/parquet_logs/ at http://localhost:9001
In Elasticsearch: Query logs index:
```bash
curl http://localhost:9200/logs/_search?pretty
```
In Kibana: Open http://localhost:5601
 → Create an index pattern for logs*


## 🔧 Tech Stack

| Layer            | Tool                  | Purpose                               |
|------------------|------------------------|----------------------------------------|
| Ingestion        | Kafka + Python Producer| Stream logs in real time               |
| Processing       | Apache Spark           | Transform/filter logs via Spark Streaming |
| Storage          | Elasticsearch          | Index logs for fast search             |
| Visualization    | Kibana                 | Create dashboards from logs            |
| Orchestration    | Apache Airflow         | Schedule archiving and cleanup         |
| Archival | MinIO + Airflow      | Long-term log storage                  |
| Containerization | Docker + Docker Compose| Service management                     |

