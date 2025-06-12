from flask import Blueprint, request, jsonify
from .models import News
from .recommend import get_recommendations

api = Blueprint('api', __name__)

@api.route('/api/news', methods=['GET'])
def get_all_news():
    news_list = News.query.limit(50).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'category': n.category,
        'topic': n.topic
    } for n in news_list])

@api.route('/api/recommend', methods=['GET'])
def recommend_news():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    recommendations = get_recommendations(int(user_id))
    return jsonify(recommendations)
