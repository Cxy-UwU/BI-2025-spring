from flask import Blueprint, request, jsonify
from app.models import News, NewsTemperature
from app.utils.recommend_utils import get_recommendations
from sqlalchemy import func

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


@news_bp.route('/temperature', methods=['GET'])
def get_news_type_temperature():
    category = request.args.get('category')
    topic = request.args.get('topic')
    if not category:
        return jsonify({'error': 'category required'}), 400

    # 查询目标新闻
    news_query = News.query.filter_by(category=category)
    if topic:
        news_query = news_query.filter_by(topic=topic)
    news_ids = [n.news_id for n in news_query.all()]
    if not news_ids:
        return jsonify({'times': [], 'clicks': []}), 200

    # 按时间分组求和
    temps = (
        NewsTemperature.query
        .filter(NewsTemperature.news_id.in_(news_ids))
        .with_entities(NewsTemperature.time, func.sum(NewsTemperature.temperature))
        .group_by(NewsTemperature.time)
        .order_by(NewsTemperature.time)
        .all()
    )
    times = [t[0].isoformat() for t in temps]
    clicks = [t[1] for t in temps]

    return jsonify({
        'times': times,
        'clicks': clicks
    }), 200