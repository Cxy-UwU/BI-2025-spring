import re
import threading
import time
from datetime import datetime, timedelta

import psycopg2
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

from config import DB_URL, KAFKA_TOPIC, KAFKA_BOOTSTRAP_SERVERS


def get_conn():
    m = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', DB_URL)
    user, pwd, host, port, db = m.groups()
    return psycopg2.connect(
        dbname=db, user=user, password=pwd, host=host, port=port
    )


class KafkaPostgrePipe:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._conn = None
        self._cur = None
        self.click_counts = {}  # key: news_id, value: int
        self.stride_seconds = 600  # 10分钟窗口
        self.current_window_start = None

    def _create_topic_if_not_exists(self):
        try:
            admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                                    #  api_version=(3, 4, 0)
                                     )
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
        self._conn = get_conn()
        self._cur = self._conn.cursor()
        self._thread.start()

    def stop(self):
        print("[Kafka] Stopping consumer...")
        self._stop_event.set()
        self._thread.join()
        # 关闭数据库连接和 cursor
        if self._cur:
            self._cur.close()
        if self._conn:
            self._conn.close()
        print("[Kafka] Stopped.")

    def _consume_loop(self):
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="log_consumer_group",
            auto_offset_reset='earliest',
            # api_version=(3, 4, 1)
        )

        print(f"[Kafka] Started consuming from topic: {KAFKA_TOPIC}")

        try:
            while not self._stop_event.is_set():
                msg_pack = consumer.poll(timeout_ms=3000)
                consumer.commit()
                total = 0
                for tp, messages in msg_pack.items():
                    for msg in messages:
                        try:
                            value = msg.value.decode('utf-8')
                            self._import_into_database(value)
                        except Exception as e:
                            print(f"[Decode Error] {e}, raw: {msg.value}")
                    total += len(messages)
                    print(f"[DB Insert] Inserted {len(messages)} messages from topic {tp.topic}")
                if total > 0:
                    try:
                        self._conn.commit()
                    except Exception as e:
                        print(f"[DB Commit Error] {e}")
        finally:
            consumer.close()
            print("[Kafka] Consumer closed.")

    def _import_into_database(self, data):
        fields = data.strip().split(',')
        if len(fields) < 4:
            print(f"[Import Error] Invalid data: {data}")
            return
        u_id, n_id, action, time_str = fields[:4]
        dwell = fields[4] if len(fields) > 4 else None

        try:
            event_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            self._update_first_read_time(n_id, event_time)

            if action == 'click':
                self._cur.execute('''
                    INSERT INTO click (u_id, n_id, time, dwell)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (u_id, n_id, time) DO NOTHING
                ''', (u_id, n_id, event_time, int(dwell) if dwell else None))

                self._update_temperature(n_id, event_time)

            elif action == 'skip':
                self._cur.execute('''
                    INSERT INTO skip (u_id, n_id, time)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (u_id, n_id, time) DO NOTHING
                ''', (u_id, n_id, event_time))
            else:
                print(f"[Import Error] Unknown action: {action}")
        except Exception as e:
            print(f"[DB Insert Error] {e}, data: {data}")

    def _update_first_read_time(self, news_id, read_time):
        try:
            self._cur.execute('''
                UPDATE news
                SET first_read_time = %s
                WHERE news_id = %s AND first_read_time IS NULL
            ''', (read_time, news_id))
        except Exception as e:
            print(f"[First Read Time Update Error] {e}")

    def _update_temperature(self, news_id, click_time):
        try:
            if self.current_window_start is None:
                # 初始化窗口起点：对齐到整点10分钟
                self.current_window_start = self._align_time_to_stride(click_time)

            window_end = self.current_window_start + timedelta(seconds=self.stride_seconds)
            if click_time >= window_end:
                # 当前日志超出窗口，说明旧窗口统计期已结束，写入数据库
                print(f"[Temperature] Window expired, writing stats at {self.current_window_start}")
                for n_id, count in self.click_counts.items():
                    self._cur.execute('''
                        INSERT INTO news_temperature (news_id, temperature, time)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (news_id, time) DO NOTHING
                    ''', (n_id, count, self.current_window_start))

                # 重置窗口
                self.current_window_start = self._align_time_to_stride(click_time)
                self.click_counts.clear()

            # 累加本窗口点击量
            self.click_counts[news_id] = self.click_counts.get(news_id, 0) + 1

        except Exception as e:
            print(f"[Temperature Update Error] {e}")

    def _align_time_to_stride(self, dt):
        """将任意时间对齐到最接近的 stride 窗口起始时间"""
        seconds_since_hour = dt.minute * 60 + dt.second
        stride_start = seconds_since_hour // self.stride_seconds * self.stride_seconds
        aligned = dt.replace(minute=0, second=0, microsecond=0) + timedelta(seconds=stride_start)
        return aligned


pipe = KafkaPostgrePipe()
pipe.start()
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    pipe.stop()
