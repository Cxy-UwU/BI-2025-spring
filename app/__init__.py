from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from .config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)

    with app.app_context():
        from . import models
        db.create_all()

        from .routes.news import news_bp
        from .routes.exposure import exposure_bp
        from .routes.users import users_bp
        from .routes.interest import interest_bp
        app.register_blueprint(news_bp, url_prefix='/api/news')
        app.register_blueprint(exposure_bp, url_prefix='/api/exposure')
        app.register_blueprint(users_bp, url_prefix='/api/users')
        app.register_blueprint(interest_bp, url_prefix='/api/interest')


    return app
