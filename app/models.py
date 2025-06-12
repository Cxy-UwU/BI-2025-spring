from . import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String, primary_key=True)

class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.String, primary_key=True)
    category = db.Column(db.String(100))
    topic = db.Column(db.String(100))
    title = db.Column(db.String(1000))
    content = db.Column(db.Text)
    first_read_time = db.Column(db.DateTime)

class Entity(db.Model):
    __tablename__ = 'entity'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255)) 
    description = db.Column(db.Text)

class NewsEntity(db.Model):
    __tablename__ = 'news_entity'
    n_id = db.Column(db.String, db.ForeignKey('news.id'), primary_key=True)
    e_id = db.Column(db.Integer, db.ForeignKey('entity.id'), primary_key=True)

class Click(db.Model):
    __tablename__ = 'click'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.String, db.ForeignKey('user.id'), primary_key=True)
    n_id = db.Column(db.String, db.ForeignKey('news.id'), primary_key=True)
    time = db.Column(db.DateTime, primary_key=True)
    dwell = db.Column(db.Integer)

class Skip(db.Model):
    __tablename__ = 'skip'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.String, db.ForeignKey('user.id'), primary_key=True)
    n_id = db.Column(db.String, db.ForeignKey('news.id'), primary_key=True)
    time = db.Column(db.DateTime, primary_key=True)
