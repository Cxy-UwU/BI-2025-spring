import os
from config import DB_URL

class Config:
    # 对于docker环境，使用以下配置
    SQLALCHEMY_DATABASE_URI = DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
