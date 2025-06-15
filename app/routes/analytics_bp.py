# analytics.py
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app import db
from datetime import datetime

analytics_bp = Blueprint('analytics', __name__)

def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except:
        return None

@analytics_bp.route('/topics', methods=['GET'])
def get_topics():
    rows = db.session.execute(text("SELECT DISTINCT category FROM category_click")).fetchall()
    return jsonify([r[0] for r in rows])



@analytics_bp.route('/query', methods=['POST'])
def query_news_clicks():
    data = request.get_json()
    conditions = []
    params = {}

    if data.get('start_time'):
        start_time = parse_datetime(data['start_time'])
        print(start_time)
        if start_time:
            conditions.append("c.time >= :start_time")
            params['start_time'] = start_time
    if data.get('end_time'):
        end_time = parse_datetime(data['end_time'])
        print(end_time)
        if end_time:
            conditions.append("c.time <= :end_time")
            params['end_time'] = end_time
    if data.get('topics'):
        conditions.append("n.category = ANY(:topics)")
        params['topics'] = data['topics']
    if data.get('title_length_min') is not None:
        conditions.append("char_length(n.title) >= :title_min")
        params['title_min'] = data['title_length_min']
    if data.get('title_length_max'):
        conditions.append("char_length(n.title) <= :title_max")
        params['title_max'] = data['title_length_max']
    if data.get('content_length_min') is not None:
        conditions.append("char_length(n.content) >= :content_min")
        params['content_min'] = data['content_length_min']
    if data.get('content_length_max'):
        conditions.append("char_length(n.content) <= :content_max")
        params['content_max'] = data['content_length_max']
    if data.get('users'):
        conditions.append("c.u_id = ANY(:user_ids)")
        params['user_ids'] = data['users']

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    print(where_clause)

    sql = text(f"""
        SELECT
            c.n_id AS news_id,
            n.title,
            n.category,
            char_length(n.content) AS content_length,
            COUNT(*) AS click_count,
            MIN(c.time) AS first_click,
            MAX(c.time) AS last_click
        FROM click c
        JOIN news n ON c.n_id = n.news_id
        WHERE {where_clause}
        GROUP BY c.n_id, n.title, n.category, n.content
        ORDER BY click_count DESC
    """)

    result = db.session.execute(sql, params).fetchall()
    return jsonify([
        {
            'news_id': row.news_id,
            'title': row.title,
            'category': row.category,
            'content_length': row.content_length,
            'click_count': row.click_count,
            'first_click': row.first_click.strftime('%Y-%m-%d %H:%M:%S'),
            'last_click': row.last_click.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for row in result
    ])

@analytics_bp.route('/current_hot_news')
def current_hot_news():
    sql = text("""
        SELECT n.news_id, n.title, n.category, COUNT(*) AS click_count
        FROM click c
        JOIN news n ON c.n_id = n.news_id
        WHERE c.time >= NOW() - INTERVAL '30 minutes'
        GROUP BY n.news_id, n.title, n.category
        ORDER BY click_count DESC
        LIMIT 10
    """)
    rows = db.session.execute(sql).fetchall()
    return jsonify([
        dict(news_id=r[0], title=r[1], category=r[2], click_count=r[3]) for r in rows
    ])

@analytics_bp.route('/long_term_hot_categories')
def long_term_hot_categories():
    sql = text("""
        SELECT n.category, ROUND(AVG(click_count), 2) AS avg_clicks FROM (
            SELECT c.n_id, COUNT(*) AS click_count
            FROM click c
            GROUP BY c.n_id
        ) t
        JOIN news n ON t.n_id = n.news_id
        GROUP BY n.category
        ORDER BY avg_clicks DESC
        LIMIT 10
    """)
    rows = db.session.execute(sql).fetchall()
    return jsonify([
        dict(category=r[0], avg_clicks=r[1]) for r in rows
    ])

