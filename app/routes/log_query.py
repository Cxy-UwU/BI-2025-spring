import os
import json
from flask import Blueprint, jsonify, request

log_query_bp = Blueprint("log_query", __name__)
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'query.log')

@log_query_bp.route('/', methods=['GET'])
def get_query_logs():
    try:
        # 获取 limit 参数，默认 500，最大 2000
        limit = request.args.get('limit', default=500, type=int)
        limit = min(max(limit, 1), 2000)  # 限制范围在 1~2000

        # 读取日志文件的最后 limit 条
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        recent_lines = lines[-limit:]

        # JSON 解析
        records = []
        for line in recent_lines:
            try:
                record = json.loads(line.strip())
                records.append(record)
            except json.JSONDecodeError:
                continue  # 跳过格式错误

        return jsonify(records)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
