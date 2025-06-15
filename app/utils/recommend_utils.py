from app.models import Click, News, Skip, User
from app import db
import numpy as np
from sqlalchemy import desc, text

from openai import OpenAI

client = OpenAI(
    api_key="sk-9kuXfFaU4SsLeEsUgNwyVG0zeNgvvet6kQublgg7N6eY5t47",
    base_url="https://api.nuwaapi.com/v1"
)

def get_top_hot_news(num):
    import json, os
    from datetime import datetime
    config_path = 'input_config.json'
    ts = None
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                ts = json.load(f).get('current_time')
        except Exception:
            ts = None
    if ts is None:
        ts = datetime.now().timestamp()
    # 计算48小时前时间戳
    ts_48h_ago = ts - 48*3600
    sql = text('''
    SELECT n.news_id, n.title, SUM(t.temperature) AS temperature_48h
    FROM news n
    JOIN news_temperature t ON n.news_id = t.news_id
    WHERE EXTRACT(EPOCH FROM t."time") >= :ts_48h_ago
    AND n.embedding IS NOT NULL
    GROUP BY n.news_id, n.title
    ORDER BY temperature_48h DESC
    LIMIT :limit;
    ''')
    result = db.session.execute(sql, {'ts_48h_ago': ts_48h_ago, 'limit': num})
    return [
    {'news_id': row.news_id, 'title': row.title, 'temperature_48h': row.temperature_48h}
    for row in result
    ]

def get_random_news(num):
    sql = text('''
    SELECT news_id, title
    FROM news
    WHERE embedding IS NOT NULL
    ORDER BY RANDOM()
    LIMIT :limit;
    ''')
    result = db.session.execute(sql, {'limit': num})
    return [
    {'news_id': row.news_id, 'title': row.title, 'temperature_48h': 0}
    for row in result
    ]

def get_embedding_array(embedding):
    # 支持 pgvector 返回的 numpy.ndarray 或字符串形式的 embedding
    if isinstance(embedding, str):
        return np.array([float(x) for x in embedding.split(',')])
    # 已经是序列或 numpy 数组
    return np.array(embedding)

def clean_history(user_id):
    user_id = str(user_id)  # 确保 user_id 是字符串类型
    db.session.query(Click).filter_by(u_id=user_id).delete()
    db.session.query(Skip).filter_by(u_id=user_id).delete()
    db.session.commit()

def get_recommendations(user_id, topk=10):
    user_id = str(user_id)  # 确保 user_id 是字符串类型
    if user_id == "Utest":
        create_utest_if_not_exists()
    from sqlalchemy import text
    # 1. 拉取用户最近25次点击及其dwell, topic, embedding
    clicks = (
        db.session.query(Click.n_id, Click.dwell, News.topic, News.embedding)
        .join(News, Click.n_id == News.news_id)
        .filter(Click.u_id == user_id, News.embedding != None)
        .order_by(desc(Click.time))
        .limit(25)
        .all()
    )
    if not clicks:
      

        topk_half = max(1, topk // 2)
        hot_news = get_top_hot_news(topk_half)
        random_news = get_random_news(topk - len(hot_news))
        # 去重，按 news_id
        seen_ids = set()
        recs = []
        for item in hot_news + random_news:
            if item['news_id'] not in seen_ids:
                recs.append(item)   
                seen_ids.add(item['news_id'])
        return recs[:topk]
    # 排除已点击新闻
    seen_ids = {nid for nid, _, _, _ in clicks}
    # 2. 按topic分组，收集embeddings和dwell
    topic_data = {}
    for nid, dwell, topic, emb in clicks:
        arr = get_embedding_array(emb)
        if topic not in topic_data:
            topic_data[topic] = {'embs': [], 'dwell_sum': 0}
        topic_data[topic]['embs'].append(arr)
        topic_data[topic]['dwell_sum'] += dwell or 0
    # 3. 计算每个topic权重，按dwell_sum分配
    total_w = sum(data['dwell_sum'] for data in topic_data.values())
    weights = {t: data['dwell_sum'] for t, data in topic_data.items()}
    # 4. 为每个topic分配推荐条数
    alloc = {topic: max(1, int(round(topk * (w / total_w)))) for topic, w in weights.items()} if total_w > 0 else {topic: 1 for topic in topic_data}
    # 5. 分topic检索推荐
    recs = []
    for topic, data in topic_data.items():
        n = alloc.get(topic, 0)
        if n <= 0:
            continue
        # 平均embedding
        center = np.mean(data['embs'], axis=0)
        embedding_sql = "ARRAY[{}]::vector".format(
            ",".join(str(x) for x in center.tolist())
        )
        # SQL检索
        sql = text(f'''
            SELECT news_id, title, embedding <#> {embedding_sql} AS distance
            FROM news
            WHERE embedding IS NOT NULL AND topic = :topic AND news_id NOT IN :seen
            ORDER BY distance ASC
            LIMIT :limit;
        ''')
        result = db.session.execute(sql, {'topic': topic, 'seen': tuple(seen_ids), 'limit': n})
        for row in result:
            recs.append({'news_id': row.news_id, 'title': row.title, 'distance': float(row.distance), 'topic': topic})
    # 6. 获取48小时温度，按temperature_48h排序返回topk
    import json, os
    from datetime import datetime
    from sqlalchemy import text
    # 获取当前时间戳
    config_path = 'input_config.json'
    ts = None
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                ts = json.load(f).get('current_time')
        except Exception:
            ts = None
    if ts is None:
        ts = datetime.now().timestamp()
    ts_48h_ago = ts - 48*3600
    rec_ids = [r['news_id'] for r in recs]
    temp_dict = {}
    if rec_ids:
        sql_temp = text('''
            SELECT news_id, SUM(temperature) AS temperature_48h
            FROM news_temperature
            WHERE EXTRACT(EPOCH FROM "time") >= :ts_48h_ago
              AND news_id IN :ids
            GROUP BY news_id;
        ''')
        temp_result = db.session.execute(sql_temp, {'ts_48h_ago': ts_48h_ago, 'ids': tuple(rec_ids)})
        temp_dict = {row.news_id: row.temperature_48h for row in temp_result}
    for r in recs:
        r['temperature_48h'] = temp_dict.get(r['news_id'], 0)
    # 按热度排序并返回topk
    recs.sort(key=lambda x: x['temperature_48h'], reverse=True)
    # X. 计算每个推荐与历史点击的最近3条新闻
    # 构建历史点击embedding映射
    history_embeddings = {nid: get_embedding_array(emb) for nid, _, _, emb in clicks}
    # 为每条推荐计算最近的3个历史news_id
    for r in recs:
        # 获取推荐新闻embedding
        emb_row = db.session.query(News.embedding).filter_by(news_id=r['news_id']).first()
        if emb_row and emb_row[0] is not None:
            target_arr = get_embedding_array(emb_row[0])
            dists = [(hid, np.linalg.norm(hist_emb - target_arr)) for hid, hist_emb in history_embeddings.items()]
            dists.sort(key=lambda x: x[1])
            r['nearest_history'] = [hid for hid, _ in dists[:3]]
        else:
            r['nearest_history'] = []
    return recs[:topk]

def get_user_click_history(user_id, limit=25):
    clicks = (
        db.session.query(Click.n_id, Click.time, Click.dwell, News.title, News.category)
        .join(News, Click.n_id == News.news_id)
        .filter(Click.u_id == user_id)
        .order_by(desc(Click.time))
        .limit(limit)
        .all()
    )
    return [
        {'news_id': n_id, 'title': title,'dwell':dwell, 'category': category, 'time': str(time)}
        for n_id, time, dwell, title, category in clicks
    ]

def search_news(target_title, limit=500):
    import json
    from datetime import datetime
    import os
    from sqlalchemy import text

    # 1. 获取当前系统时间戳
    config_path = 'input_config.json'
    ts = None
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ts = data.get('current_time')
        except Exception:
            ts = None
    # 2. 获取输入标题的embedding
    response = client.embeddings.create(
        input=target_title,
        model="text-embedding-3-small"
    )
    input_embedding = np.array(response.data[0].embedding)  # shape: (1536,)
    # 3. 查询数据库，找余弦相似度最高的新闻
    embedding_list = input_embedding.tolist()
    embedding_sql = "ARRAY[{}]::vector".format(
        ",".join(str(x) for x in embedding_list)
    )
    sql = text(f'''
        SELECT news_id, title, embedding <#> {embedding_sql} AS cosine_distance
        FROM news
        WHERE embedding IS NOT NULL
        ORDER BY cosine_distance ASC
        LIMIT :limit;
    ''')
    result = db.session.execute(sql, {'limit': limit})
    news_list = [
        {'news_id': row.news_id, 'title': row.title, 'cosine_distance': float(row.cosine_distance)}
        for row in result
    ]
    # 4. 查询 news_temperature 表近48小时点击量，按news_id聚合
    temp_dict = {}
    if ts is not None:
        ts_48h_ago = ts - 48*3600
        sql_temp = text('''
            SELECT news_id, SUM(temperature) as temperature_48h
            FROM news_temperature
            WHERE EXTRACT(EPOCH FROM "time") >= :ts_48h_ago
            GROUP BY news_id
        ''')
        temp_result = db.session.execute(sql_temp, {'ts_48h_ago': ts_48h_ago})
        temp_dict = {row.news_id: row.temperature_48h for row in temp_result}
    # 5. 合并点击量到news_list
    for news in news_list:
        news['temperature_48h'] = temp_dict.get(news['news_id'], 0)
    return news_list

def simulate_click(news_id, dwell=10):
    """
    模拟用户点击新闻，记录点击时间和停留时间。
    """
    create_utest_if_not_exists()
    click = Click(u_id="Utest", n_id=news_id, dwell=dwell)
    db.session.add(click)
    db.session.commit()
    return {'status': 'success', 'message': 'Click recorded successfully'}

def create_utest_if_not_exists():
    """
    确保存在 Utest 用户。
    """
    utest_user = db.session.query(User).filter_by(user_id="Utest").first()
    if not utest_user:
        utest_user = User(user_id="Utest")
        db.session.add(utest_user)
        db.session.commit()
    return utest_user.user_id