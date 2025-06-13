import time
import threading
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

KAFKA_TOPIC = "log_topic"
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9094'


class KafkaPostgrePipe:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)

    def _create_topic_if_not_exists(self):
        try:
            admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                                     api_version=(3, 4, 0))
            topic = NewTopic(name=KAFKA_TOPIC, num_partitions=1, replication_factor=1)
            admin.create_topics([topic], validate_only=False)
            admin.close()
            print(f"[Kafka] Created topic: {KAFKA_TOPIC}")
        except TopicAlreadyExistsError:
            print(f"[Kafka] Topic already exists: {KAFKA_TOPIC}")
        except Exception as e:
            print(f"[Kafka] Topic creation error: {e}")

    def start(self):
        self._create_topic_if_not_exists()
        self._thread.start()

    def stop(self):
        print("[Kafka] Stopping consumer...")
        self._stop_event.set()
        self._thread.join()
        print("[Kafka] Stopped.")

    def _consume_loop(self):
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            api_version=(3, 4, 0)
        )

        print(f"[Kafka] Started consuming from topic: {KAFKA_TOPIC}")

        try:
            while not self._stop_event.is_set():
                msg_pack = consumer.poll(timeout_ms=1000)
                for tp, messages in msg_pack.items():
                    for msg in messages:
                        try:
                            value = msg.value.decode('utf-8')
                            print("Received:", value)
                        except Exception as e:
                            print(f"[Decode Error] {e}, raw: {msg.value}")
        finally:
            consumer.close()
            print("[Kafka] Consumer closed.")


# 运行期间应该保持kafka->postgres的管道持续运行，通过控制exposure -> target.log来添加数据
# flume和fakfa需要预热，确保看到提示再开始请求
pipe = KafkaPostgrePipe()
pipe.start()
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    pipe.stop()
