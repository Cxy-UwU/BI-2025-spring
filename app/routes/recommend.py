from flask import Blueprint, request, jsonify
from app.utils.recommend_utils import get_recommendations, get_user_click_history, search_news, simulate_click
from app import db
from app.models import Click, Skip

recommend_bp = Blueprint('recommend', __name__)

@recommend_bp.route('/user', methods=['GET'])
def user_recommend():
    user_id = request.args.get('user_id')
    topk = int(request.args.get('topk', 10))
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    result = get_recommendations(user_id, topk=topk)
    return jsonify(result), 200

@recommend_bp.route('/user/history', methods=['GET'])
def user_click_history():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    result = get_user_click_history(user_id)
    return jsonify(result), 200

@recommend_bp.route('/search', methods=['GET'])
def vector_search():
    keyword = request.args.get('target_title')
    result = search_news(keyword)
    return jsonify(result), 200

@recommend_bp.route('/click', methods=['GET'])
def click_news():
    nid = request.args.get('news_id')
    if not nid:
        return jsonify({'error': 'news_id is required'}), 400
    result = simulate_click(nid)
    return jsonify(result), 200

@recommend_bp.route('/clear', methods=['DELETE'])
def clear_user_data():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        db.session.query(Click).filter_by(u_id=user_id).delete()
        db.session.query(Skip).filter_by(u_id=user_id).delete()
        db.session.commit()
        return jsonify({'message': 'User data cleared successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@recommend_bp.route('/random', methods=['GET'])
def random_recommend():
    """
    获取随机推荐的新闻
    """
    from app.utils.recommend_utils import get_random_news
    topk = 10
    result = get_random_news(topk)
    return jsonify(result), 200
