import os
import time
import logging
import json
from datetime import datetime

from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask import request

# 自动创建 logs 目录
log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'query.log')

# 设置日志器
logger = logging.getLogger("query_logger")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(log_file_path, encoding='utf-8')
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

# SQLAlchemy 事件钩子中写日志
@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    duration = time.time() - context._query_start_time
    endpoint = request.path if request else "unknown"

    log_data = {
        "endpoint": endpoint,
        "query": statement,
        "duration": round(duration, 6),
        "created_at": datetime.utcnow().isoformat()
    }

    logger.info(json.dumps(log_data))



