from sqlalchemy.sql import text
from datetime import datetime, timedelta

def _query_interest_trend(user_id=None, granularity='5d', by='topic', limit_days=None):
    interest_field = 'n.topic' if by == 'topic' else 'n.category'

    if granularity == '1d':
        time_expr = "date_trunc('day', c.time)"
        max_days = 30
    elif granularity == '5d':
        time_expr = "date_trunc('day', c.time) - (EXTRACT(DOY FROM c.time)::int % 5) * interval '1 day'"
        max_days = 90
    elif granularity == '1h':
        time_expr = "date_trunc('hour', c.time)"
        max_days = 1
    else:
        raise ValueError("Unsupported granularity")

    from app import db
    # 查询表中最大时间（如果click表按时间降序，也可以直接取第一个）
    max_time_sql = "SELECT MAX(c.time) FROM click c"
    max_time = db.session.execute(text(max_time_sql)).scalar()
    if not max_time:
        return []

    # 计算起始时间
    from_time = max_time - timedelta(days=limit_days or max_days)

    where_clauses = ["c.time >= :from_time"]
    if user_id:
        where_clauses.append("c.u_id = :user_id")
    where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = f"""
        SELECT
            {time_expr} AS time_window,
            {interest_field} AS interest,
            COUNT(*) AS click_count,
            SUM(c.dwell) AS total_dwell
        FROM click c
        JOIN news n ON c.n_id = n.id
        {where_sql}
        GROUP BY time_window, interest
        ORDER BY time_window
    """

    params = {'from_time': from_time}
    if user_id:
        params['user_id'] = user_id

    result = db.session.execute(text(sql), params)
    return [
        {
            key: (
                value.strftime('%Y-%m-%d %H:%M') if isinstance(value, datetime) and granularity == '1h'
                else value.strftime('%Y-%m-%d') if isinstance(value, datetime)
                else value
            )
            for key, value in row.items()
        }
        for row in result.mappings()
    ]

def query_user_interest_trend(user_id=None, granularity='5d', by='topic'):
    return _query_interest_trend(user_id=user_id, granularity=granularity, by=by)

def query_all_users_interest_trend(granularity='5d', by='topic'):
    return _query_interest_trend(user_id=None, granularity=granularity, by=by)

