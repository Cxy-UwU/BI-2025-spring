from . import db
from pgvector.sqlalchemy import Vector

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.String, primary_key=True)


class News(db.Model):
    __tablename__ = 'news'
    news_id = db.Column(db.String, primary_key=True)
    category = db.Column(db.String(100))
    topic = db.Column(db.String(100))
    title = db.Column(db.String(1000))
    content = db.Column(db.Text)
    title_length = db.Column(db.Integer)
    content_length = db.Column(db.Integer)
    first_read_time = db.Column(db.DateTime)
    embedding = db.Column(Vector(1536))


class Entity(db.Model):
    __tablename__ = 'entity'
    entity_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)


class NewsEntity(db.Model):
    __tablename__ = 'news_entity'
    news_id = db.Column(db.String, db.ForeignKey('news.news_id'), primary_key=True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.entity_id'), primary_key=True)


class Click(db.Model):
    __tablename__ = 'click'
    c_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.String, db.ForeignKey('user.user_id'))
    n_id = db.Column(db.String, db.ForeignKey('news.news_id'))
    time = db.Column(db.DateTime)
    u_id = db.Column(db.String, db.ForeignKey('user.user_id'))
    n_id = db.Column(db.String, db.ForeignKey('news.news_id'))
    time = db.Column(db.DateTime)
    dwell = db.Column(db.Integer)
    __table_args__ = (
        db.UniqueConstraint('u_id', 'n_id', 'time'),
    )


class Skip(db.Model):
    __tablename__ = 'skip'
    s_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.String, db.ForeignKey('user.user_id'))
    n_id = db.Column(db.String, db.ForeignKey('news.news_id'))
    time = db.Column(db.DateTime)
    __table_args__ = (
        db.UniqueConstraint('u_id', 'n_id', 'time'),
    )


class NewsTemperature(db.Model):
    __tablename__ = 'news_temperature'
    news_id = db.Column(db.String, db.ForeignKey('news.news_id'), primary_key=True)
    temperature = db.Column(db.Integer)
    time = db.Column(db.DateTime, primary_key=True)


class NewsHot(db.Model):
    __tablename__ = 'news_hot'
    news_id = db.Column(db.String, primary_key=True)
    click_count = db.Column(db.Integer)
    window_time = db.Column(db.DateTime, primary_key=True)


class CategoryClick(db.Model):
    __tablename__ = 'category_click'
    category = db.Column(db.String, primary_key=True)
    click_count = db.Column(db.Integer)
    window_time = db.Column(db.DateTime, primary_key=True)