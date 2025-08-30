FROM bitnami/spark:3.5.0

USER root

# Install curl, netcat, and Python requests
RUN apt-get update && apt-get install -y curl netcat-openbsd python3 python3-pip && \
    pip3 install requests && \
    rm -rf /var/lib/apt/lists/*

# Create jars directory
RUN mkdir -p /opt/spark/jars

# Canonical Kafka/Hadoop-AWS jar versions for this image. This is the
# single source of truth for these versions — src/spark/log_consumer.py
# deliberately does NOT redeclare spark.jars.packages, since these jars
# are baked in below and placed on Spark's default classpath
# ($SPARK_HOME/jars). Previously this version set was declared three
# times (here, in run.sh's --packages flag, and again inside
# log_consumer.py) and had drifted out of sync between them; now there's
# one place to bump a version: `docker build --build-arg
# HADOOP_AWS_VERSION=... .`
ARG SPARK_KAFKA_VERSION=3.5.0
ARG KAFKA_CLIENTS_VERSION=3.4.1
ARG HADOOP_AWS_VERSION=3.3.4
ARG AWS_SDK_BUNDLE_VERSION=1.12.262

# Download compatible versions
RUN curl -L -o /opt/spark/jars/spark-sql-kafka-0-10_2.12-${SPARK_KAFKA_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/${SPARK_KAFKA_VERSION}/spark-sql-kafka-0-10_2.12-${SPARK_KAFKA_VERSION}.jar && \
    curl -L -o /opt/spark/jars/kafka-clients-${KAFKA_CLIENTS_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/${KAFKA_CLIENTS_VERSION}/kafka-clients-${KAFKA_CLIENTS_VERSION}.jar && \
    curl -L -o /opt/spark/jars/spark-token-provider-kafka-0-10_2.12-${SPARK_KAFKA_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/${SPARK_KAFKA_VERSION}/spark-token-provider-kafka-0-10_2.12-${SPARK_KAFKA_VERSION}.jar && \
    curl -L -o /opt/spark/jars/hadoop-aws-${HADOOP_AWS_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar && \
    curl -L -o /opt/spark/jars/aws-java-sdk-bundle-${AWS_SDK_BUNDLE_VERSION}.jar \
    https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_BUNDLE_VERSION}/aws-java-sdk-bundle-${AWS_SDK_BUNDLE_VERSION}.jar

# Copy application files. The src/ layout is preserved inside the image
# (rather than flattened into /app) so log_consumer.py's sys.path-based
# import of src/common/env_config.py resolves the same way it does
# outside Docker. Built with context: . (repo root) — see docker-compose.yml.
COPY src/spark/log_consumer.py /app/src/spark/log_consumer.py
COPY src/common /app/src/common
COPY configs/pipeline.env /app/configs/pipeline.env
COPY docker/spark-app/run.sh /app/run.sh
RUN chmod +x /app/run.sh

USER 1001

WORKDIR /app

CMD ["/bin/bash", "run.sh"]
