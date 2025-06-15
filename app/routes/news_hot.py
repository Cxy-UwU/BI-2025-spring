from flask import Blueprint, jsonify, request
from sqlalchemy import text
from app import db
from app.models import NewsHot, CategoryClick
from collections import defaultdict
from datetime import timedelta

chart_bp = Blueprint('chart', __name__)

@chart_bp.route('/news_hot', methods=['GET'])
def get_news_hot_grouped():
    granularity = request.args.get('granularity', 'minute')  # minute/hour/day

    if granularity == 'minute':
        time_format = 'YYYY-MM-DD HH24:MI'
        interval = '1 minute'
        limit = 30
    elif granularity == 'hour':
        time_format = 'YYYY-MM-DD HH24'
        interval = '1 hour'
        limit = 24
    elif granularity == 'day':
        time_format = 'YYYY-MM-DD'
        interval = '1 day'
        limit = 7
    else:
        return jsonify({'error': 'Invalid granularity'}), 400

    sql = text(f"""
        WITH max_time AS (
            SELECT MAX(window_time) AS max_time FROM news_hot
        ), filtered AS (
            SELECT *, to_char(window_time, '{time_format}') AS time_group
            FROM news_hot, max_time
            WHERE window_time >= max_time - INTERVAL '{limit} {granularity}'
        ), ranked AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY time_group ORDER BY click_count DESC) as rk
            FROM filtered
        )
        SELECT news_id, time_group, click_count
        FROM ranked
        WHERE rk <= 10
        ORDER BY time_group, click_count DESC
    """)

    rows = db.session.execute(sql).fetchall()

    result = {}
    for news_id, time_group, click_count in rows:
        news_id = str(news_id)
        result.setdefault(news_id, {})[time_group] = click_count

    return jsonify(result)


@chart_bp.route('/category_click', methods=['GET'])
def get_category_click_grouped():
    granularity = request.args.get('granularity', 'minute')  # minute/hour/day

    if granularity == 'minute':
        time_format = '%Y-%m-%d %H:%M'
        group_sql = "to_char(window_time, 'YYYY-MM-DD HH24:MI')"
        interval = '1 minute'
        limit = 30
    elif granularity == 'hour':
        time_format = '%Y-%m-%d %H'
        group_sql = "to_char(window_time, 'YYYY-MM-DD HH24')"
        interval = '1 hour'
        limit = 24
    elif granularity == 'day':
        time_format = '%Y-%m-%d'
        group_sql = "to_char(window_time, 'YYYY-MM-DD')"
        interval = '1 day'
        limit = 7
    else:
        return jsonify({'error': 'Invalid granularity'}), 400

    sql = text(f"""
        WITH max_time AS (
            SELECT MAX(window_time) AS max_time FROM category_click
        )
        SELECT category, {group_sql} AS time_group, SUM(click_count) as total_click
        FROM category_click, max_time
        WHERE window_time >= max_time - INTERVAL '{limit} {granularity}'
        GROUP BY category, time_group
        ORDER BY time_group
    """)

    rows = db.session.execute(sql).fetchall()
    grouped = defaultdict(lambda: defaultdict(int))
    for category, time_group, count in rows:
        grouped[category][time_group] = count

    return jsonify(grouped)

@chart_bp.route('/current_hot', methods=['GET'])
def get_current_hot_news():
    sql = text("""
        SELECT c.n_id, n.title, n.category, COUNT(*) AS click_count
        FROM click c
        JOIN news n ON c.n_id = n.news_id
        WHERE c.time >= (
            SELECT MAX(time)::timestamp(0) - INTERVAL '1 minute' FROM click
        ) AND c.time <= (
            SELECT MAX(time)::timestamp(0) FROM click
        )
        GROUP BY c.n_id, n.title, n.category
        ORDER BY click_count DESC
        LIMIT 1
    """)
    row = db.session.execute(sql).fetchone()

    if row:
        return jsonify({
            "news_id": row.n_id,
            "title": row.title,
            "category": row.category,
            "click_count": row.click_count
        })
    else:
        return jsonify({}), 204
