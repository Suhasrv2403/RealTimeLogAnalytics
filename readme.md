# 🧠 Real-Time Log Analytics Pipeline

This project implements a real-time log analytics pipeline using modern data engineering tools:  
**Kafka, Spark Structured Streaming, Elasticsearch, Kibana, Airflow**, and **Python**.

Logs are ingested from a simulated log producer, processed in real time using Spark, indexed in Elasticsearch, and visualized via Kibana dashboards. Logs are archived to S3 using Airflow.

---

## 🔧 Tech Stack

| Layer            | Tool                  | Purpose                               |
|------------------|------------------------|----------------------------------------|
| Ingestion        | Kafka + Python Producer| Stream logs in real time               |
| Processing       | Apache Spark           | Transform/filter logs via Spark Streaming |
| Storage          | Elasticsearch          | Index logs for fast search             |
| Visualization    | Kibana                 | Create dashboards from logs            |
| Orchestration    | Apache Airflow         | Schedule archiving and cleanup         |
| Archival (optional)| AWS S3 + Airflow      | Long-term log storage                  |
| Containerization | Docker + Docker Compose| Service management                     |

---
---

## 🚀 Quick Start

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/log-analytics-pipeline.git
cd log-analytics-pipeline
```

### 2. Run all services
```bash
docker-compose up -d
```
