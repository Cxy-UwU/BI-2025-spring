from flask import Blueprint, request, jsonify
from app.models import News, NewsTemperature
from app.utils.recommend import get_recommendations

news_bp = Blueprint('news', __name__)


@news_bp.route('/get', methods=['GET'])
def get_all_news():
    news_list = News.query.limit(50).all()
    return jsonify([{
        'id': n.news_id,
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


@news_bp.route('/lifecycle/<string:news_id>', methods=['GET'])
def get_news_lifecycle(news_id):
    news = News.query.filter_by(news_id=news_id).first()
    if not news:
        return jsonify({'error': 'News not found'}), 404

    temps = NewsTemperature.query.filter_by(news_id=news_id).order_by(NewsTemperature.time).all()
    times = [t.time.isoformat() for t in temps]
    clicks = [t.temperature for t in temps]

    return jsonify({
        'times': times,
        'clicks': clicks
    }), 200
