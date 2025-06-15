from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from .config import Config

from app.utils import query_logger

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
        from .routes.log_query import log_query_bp
        from .routes.news_hot import chart_bp
        from .routes.analytics_bp import analytics_bp
        app.register_blueprint(news_bp, url_prefix='/api/news')
        app.register_blueprint(exposure_bp, url_prefix='/api/exposure')
        app.register_blueprint(users_bp, url_prefix='/api/users')
        app.register_blueprint(interest_bp, url_prefix='/api/interest')
        app.register_blueprint(log_query_bp, url_prefix='/api/logs')
        app.register_blueprint(chart_bp, url_prefix='/api/chart')
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')


    return app
