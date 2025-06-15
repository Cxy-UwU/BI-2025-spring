import os
import psycopg2

DB_URL = "postgresql://xy:212369@localhost:5432/bi?client_encoding=utf8"


def get_conn():
    import re
    m = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', DB_URL)
    user, pwd, host, port, db = m.groups()
    return psycopg2.connect(
        dbname=db, user=user, password=pwd, host=host, port=port
    )


def clear_tables(cur):
    cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                """)
    tables = [row[0] for row in cur.fetchall()]
    if tables:
        truncate_sql = "TRUNCATE TABLE {} RESTART IDENTITY CASCADE;".format(
            ', '.join(f'"{t}"' for t in tables)
        )
        cur.execute(truncate_sql)


def import_users_fast(cur, csv_path):
    import tempfile
    import csv

    # 提取唯一 user_id，写入临时 CSV 文件供 COPY 使用
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        users = {row['user_id'] for row in reader}

    with tempfile.NamedTemporaryFile("w+", delete=False, encoding='utf-8', newline='') as tmp:
        tmp.write("id\n")
        for uid in users:
            tmp.write(f"{uid}\n")
        tmp_path = tmp.name

    with open(tmp_path, encoding='utf-8') as f:
        cur.copy_expert(
            'COPY "user"(user_id) FROM STDIN WITH CSV HEADER',
            f
        )


def import_news_fast(cur, csv_path):
    with open(csv_path, encoding='utf-8') as f:
        cur.copy_expert(
            '''
            COPY news(news_id, topic, category, title, content, title_length, content_length)
            FROM STDIN WITH CSV HEADER
            ''',
            f
        )

def insert_embeddings_fast(cur, csv_path):
    # 1. 创建临时表
    cur.execute('''
        CREATE TEMP TABLE temp_embedding (
            news_id TEXT PRIMARY KEY,
            embedding TEXT
        ) ON COMMIT DROP;
    ''')
    # 2. COPY 导入临时表
    with open(csv_path, encoding='utf-8') as f:
        cur.copy_expert('COPY temp_embedding(news_id, embedding) FROM STDIN WITH CSV HEADER', f)
    # 3. 批量更新主表
    cur.execute('''
        UPDATE news
        SET embedding = temp_embedding.embedding::vector
        FROM temp_embedding
        WHERE news.news_id = temp_embedding.news_id;
    ''')

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    users_csv = os.path.join(base_dir, 'users.csv')
    news_csv = os.path.join(base_dir, 'news.csv')
    embedding_csv = os.path.join(base_dir, 'embedding.csv')
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                clear_tables(cur)
                import_users_fast(cur, users_csv)
                import_news_fast(cur, news_csv)
                insert_embeddings_fast(cur, embedding_csv)
        print("✅ 数据导入完成。")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
