import re
import threading
import time
from datetime import datetime, timedelta
import traceback

import psycopg2
from kafka import KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

KAFKA_TOPIC = "log_topic"
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9094'
DB_URL = "postgresql://postgres:123456@localhost:5432/newsdb"


def get_conn():
    m = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', DB_URL)
    user, pwd, host, port, db = m.groups()
    return psycopg2.connect(
        dbname=db, user=user, password=pwd, host=host, port=port
    )


def align_to_minute(dt):
    return dt.replace(second=0, microsecond=0)


class KafkaPostgrePipe:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._conn = None
        self._cur = None
        self.temperature_counts = {}  # news_id -> count in 10-minute window
        self.click_counter = {}       # news_id -> count in 1-minute window
        self.category_counter = {}    # category -> count in 1-minute window
        self.temp_window_start = None
        self.hot_window_start = None
        self.temp_stride_seconds = 600

    def _create_topic_if_not_exists(self):
        try:
            admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
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
            auto_offset_reset='earliest'
        )

        print(f"[Kafka] Started consuming from topic: {KAFKA_TOPIC}")

        try:
            for message in consumer:
                if self._stop_event.is_set():
                    break
                try:
                    self._process_message(message.value.decode('utf-8'))
                    self._conn.commit()
                except Exception as e:
                    print("[ERROR]", e)
                    self._conn.rollback()
        finally:
            consumer.close()
            print("[Kafka] Consumer closed.")

    def _process_message(self, data):
        parts = data.strip().split(',')
        if len(parts) < 4:
            return

        u_id, n_id, action, time_str = parts[:4]
        dwell = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else None
        ts = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

        self._update_first_read_time(n_id, ts)

        if action == "click":
            self._cur.execute('''
                INSERT INTO click (u_id, n_id, time, dwell)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (u_id, n_id, time) DO NOTHING
            ''', (u_id, n_id, ts, dwell))

            self._update_temperature(n_id, ts)
            self._update_hot_data(n_id, ts)
            self._update_category_click(n_id, ts)

        elif action == "skip":
            self._cur.execute('''
                INSERT INTO skip (u_id, n_id, time)
                VALUES (%s, %s, %s)
                ON CONFLICT (u_id, n_id, time) DO NOTHING
            ''', (u_id, n_id, ts))

    def _update_first_read_time(self, news_id, read_time):
        self._cur.execute('''
            UPDATE news
            SET first_read_time = %s
            WHERE news_id = %s AND first_read_time IS NULL
        ''', (read_time, news_id))

    def _update_temperature(self, news_id, ts):
        if self.temp_window_start is None:
            self.temp_window_start = self._align_time_to_stride(ts)

        window_end = self.temp_window_start + timedelta(seconds=self.temp_stride_seconds)
        if ts >= window_end:
            print(f"[Temperature] Finalizing 10-min window at {self.temp_window_start}")
            for n_id, count in self.temperature_counts.items():
                self._cur.execute('''
                    INSERT INTO news_temperature (news_id, temperature, time)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (news_id, time) DO NOTHING
                ''', (n_id, count, self.temp_window_start))
            self.temperature_counts.clear()
            self.temp_window_start = self._align_time_to_stride(ts)

        self.temperature_counts[news_id] = self.temperature_counts.get(news_id, 0) + 1

    def _update_hot_data(self, news_id, ts):
        window = align_to_minute(ts)
        if self.hot_window_start is None:
            self.hot_window_start = window

        if window > self.hot_window_start:
            print(f"[Hot] Writing news_hot and category_click at {self.hot_window_start}")
            for nid, count in self.click_counter.items():
                self._cur.execute('''
                    INSERT INTO news_hot (news_id, click_count, window_time)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (news_id, window_time)
                    DO UPDATE SET click_count = EXCLUDED.click_count
                ''', (nid, count, self.hot_window_start))

            for cat, count in self.category_counter.items():
                self._cur.execute('''
                    INSERT INTO category_click (category, click_count, window_time)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (category, window_time)
                    DO UPDATE SET click_count = EXCLUDED.click_count
                ''', (cat, count, self.hot_window_start))

            self.click_counter.clear()
            self.category_counter.clear()
            self.hot_window_start = window

        self.click_counter[news_id] = self.click_counter.get(news_id, 0) + 1

    def _update_category_click(self, news_id, ts):
        self._cur.execute('SELECT category FROM news WHERE news_id = %s', (news_id,))
        result = self._cur.fetchone()
        if result:
            category = result[0]
            self.category_counter[category] = self.category_counter.get(category, 0) + 1

    def _align_time_to_stride(self, dt):
        seconds_since_hour = dt.minute * 60 + dt.second
        stride_start = seconds_since_hour // self.temp_stride_seconds * self.temp_stride_seconds
        return dt.replace(minute=0, second=0, microsecond=0) + timedelta(seconds=stride_start)


if __name__ == '__main__':
    pipe = KafkaPostgrePipe()
    pipe.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        pipe.stop()
