from flask import Blueprint, request, jsonify
from app.models import News
from app.utils.recommend import get_recommendations

news_bp = Blueprint('news', __name__)


@news_bp.route('/get', methods=['GET'])
def get_all_news():
    news_list = News.query.limit(50).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'category': n.category,
        'topic': n.topic
    } for n in news_list])


@news_bp.route('/recommend', methods=['GET'])
def recommend_news():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    recommendations = get_recommendations(int(user_id))
    return jsonify(recommendations)
