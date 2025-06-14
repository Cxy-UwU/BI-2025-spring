import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:123456@localhost:5432/newsdb')
    # 对于docker环境，使用以下配置
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://hajimi:hajimi@localhost:5432/news?client_encoding=utf8')
    # SQLALCHEMY_TRACK_MODIFICATIONS = False