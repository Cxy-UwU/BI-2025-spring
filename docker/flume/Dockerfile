FROM openjdk:8-jre

# Install Flume
ENV FLUME_VERSION=1.11.0
RUN apt-get update && apt-get install -y wget && \
    wget https://downloads.apache.org/flume/${FLUME_VERSION}/apache-flume-${FLUME_VERSION}-bin.tar.gz && \
    tar -xzf apache-flume-${FLUME_VERSION}-bin.tar.gz && \
    mv apache-flume-${FLUME_VERSION}-bin /opt/flume && \
    rm apache-flume-${FLUME_VERSION}-bin.tar.gz

WORKDIR /opt/flume
ENV PATH="$PATH:/opt/flume/bin"
