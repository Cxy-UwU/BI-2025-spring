import os
from datetime import datetime
from kafka import KafkaConsumer
import psycopg2

# Kafka 配置
KAFKA_TOPIC = "log_topic"
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9094'

# PostgreSQL 配置
PG_URL = {
    "host": "localhost",
    "port": 5432,
    "dbname": "newsdb",
    "user": "postgres",
    "password": "123456"
}

# 时间窗口对齐到分钟
def align_to_window(dt):
    return dt.replace(second=0, microsecond=0)

def get_conn():
    return psycopg2.connect(**PG_URL)

def main():
    print("✅ 启动 Kafka 消费者并连接数据库...")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        group_id='news_consumer_group',
        enable_auto_commit=True
    )

    conn = get_conn()
    cur = conn.cursor()

    click_counter = {}
    category_counter = {}
    window_start = None

    print("🔁 正在监听 Kafka 数据流...")

    for message in consumer:
        try:
            parts = message.value.decode('utf-8').strip().split(',')
            if len(parts) < 4:
                continue

            u_id, n_id, action, time_str = parts[:4]
            dwell = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else None
            ts = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            window = align_to_window(ts)

            if window_start is None:
                window_start = window

            # 时间窗口切换，写入上一窗口数据
            if window > window_start:
                print(f"\n📝 写入窗口数据 {window_start.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  🔸 NewsHot 条数: {len(click_counter)}")
                print(f"  🔸 CategoryClick 条数: {len(category_counter)}")

                for nid, count in click_counter.items():
                    cur.execute('''
                        INSERT INTO news_hot (news_id, click_count, window_time)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (news_id, window_time)
                        DO UPDATE SET click_count = EXCLUDED.click_count
                    ''', (nid, count, window_start))
                for cat, count in category_counter.items():
                    cur.execute('''
                        INSERT INTO category_click (category, click_count, window_time)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (category, window_time)
                        DO UPDATE SET click_count = EXCLUDED.click_count
                    ''', (cat, count, window_start))
                conn.commit()
                click_counter.clear()
                category_counter.clear()
                window_start = window

            # 插入 click 或 skip 行为记录
            if action == "click":
                cur.execute('''
                    INSERT INTO click (u_id, n_id, time, dwell)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (u_id, n_id, time) DO NOTHING
                ''', (u_id, n_id, ts, dwell))
                click_counter[n_id] = click_counter.get(n_id, 0) + 1

                cur.execute('SELECT category FROM news WHERE news_id = %s', (n_id,))
                result = cur.fetchone()
                if result:
                    category = result[0]
                    category_counter[category] = category_counter.get(category, 0) + 1

            elif action == "skip":
                cur.execute('''
                    INSERT INTO skip (u_id, n_id, time)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (u_id, n_id, time) DO NOTHING
                ''', (u_id, n_id, ts))

            conn.commit()

        except Exception as e:
            print("[ERROR]", e)
            conn.rollback()

if __name__ == "__main__":
    main()
