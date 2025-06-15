from flask import Blueprint, request, jsonify
from app.utils.interest_utils import query_user_interest_trend, query_all_users_interest_trend

interest_bp = Blueprint('interest', __name__)

@interest_bp.route('/trend', methods=['GET'])
def user_interest_trend():
    user_id = request.args.get('user_id')
    granularity = request.args.get('granularity', '5d')
    by = request.args.get('by', 'topic')

    data = query_user_interest_trend(user_id=user_id, granularity=granularity, by=by)
    return jsonify(data), 200

@interest_bp.route('/trend_all', methods=['GET'])
def all_user_interest_trend():
    granularity = request.args.get('granularity', '5d')
    by = request.args.get('by', 'topic')

    data = query_all_users_interest_trend(granularity=granularity, by=by)
    return jsonify(data), 200
