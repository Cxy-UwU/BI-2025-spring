import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:123456@localhost:5432/newsdb')
    SQLALCHEMY_TRACK_MODIFICATIONS = False