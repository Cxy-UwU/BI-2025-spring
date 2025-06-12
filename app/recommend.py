from .models import Click, News
from . import db

def get_recommendations(user_id):
    clicked_news_ids = db.session.query(Click.n_id).filter_by(u_id=user_id).all()
    clicked_ids = [id for (id,) in clicked_news_ids]

    if not clicked_ids:
        return []

    categories = db.session.query(News.category).filter(News.id.in_(clicked_ids)).distinct().all()
    category_list = [c for (c,) in categories]
    recommended = News.query.filter(
        News.category.in_(category_list),
        ~News.id.in_(clicked_ids)
    ).limit(10).all()

    return [{'id': n.id, 'title': n.title, 'category': n.category} for n in recommended]
