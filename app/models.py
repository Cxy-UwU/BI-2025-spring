from . import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)

class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))
    topic = db.Column(db.String(50))
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    first_read_time = db.Column(db.DateTime)

class Entity(db.Model):
    __tablename__ = 'entity'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)

class NewsEntity(db.Model):
    __tablename__ = 'news_entity'
    n_id = db.Column(db.Integer, db.ForeignKey('news.id'), primary_key=True)
    e_id = db.Column(db.Integer, db.ForeignKey('entity.id'), primary_key=True)

class Click(db.Model):
    __tablename__ = 'click'
    u_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    n_id = db.Column(db.Integer, db.ForeignKey('news.id'), primary_key=True)
    time = db.Column(db.DateTime)
    dwell = db.Column(db.Integer) 

class Skip(db.Model):
    __tablename__ = 'skip'
    u_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    n_id = db.Column(db.Integer, db.ForeignKey('news.id'), primary_key=True)
    time = db.Column(db.DateTime)
