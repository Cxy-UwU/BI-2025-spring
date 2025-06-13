-- 启用向量拓展
CREATE EXTENSION IF NOT EXISTS vector;

-- 用户表
CREATE TABLE IF NOT EXISTS "user"
(
    user_id VARCHAR PRIMARY KEY
);

-- 新闻表
CREATE TABLE IF NOT EXISTS news
(
    news_id         VARCHAR PRIMARY KEY,
    category        VARCHAR(100),
    topic           VARCHAR(100),
    title           VARCHAR(1000),
    content         TEXT,
    title_length    INTEGER,
    content_length  INTEGER,
    first_read_time TIMESTAMP
);

-- 实体表
CREATE TABLE IF NOT EXISTS entity
(
    entity_id   SERIAL PRIMARY KEY,
    name        VARCHAR(255),
    description TEXT
);

-- 新闻-实体关联表
CREATE TABLE IF NOT EXISTS news_entity
(
    news_id   VARCHAR REFERENCES news (news_id) ON DELETE CASCADE,
    entity_id INTEGER REFERENCES entity (entity_id) ON DELETE CASCADE,
    PRIMARY KEY (news_id, entity_id)
);

-- 点击表
CREATE TABLE IF NOT EXISTS click
(
    c_id  SERIAL PRIMARY KEY,
    u_id  VARCHAR REFERENCES "user" (user_id),
    n_id  VARCHAR REFERENCES news (news_id),
    time  TIMESTAMP,
    dwell INTEGER,
    UNIQUE (u_id, n_id, time)
);

-- 跳过表
CREATE TABLE IF NOT EXISTS skip
(
    s_id SERIAL PRIMARY KEY,
    u_id VARCHAR REFERENCES "user" (user_id),
    n_id VARCHAR REFERENCES news (news_id),
    time TIMESTAMP,
    UNIQUE (u_id, n_id, time)
);

-- 新闻热度表
CREATE TABLE IF NOT EXISTS news_temperature
(
    news_id     VARCHAR REFERENCES news (news_id) ON DELETE CASCADE,
    temperature INTEGER,
    time        TIMESTAMP,
    PRIMARY KEY (news_id, time)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_news_category_topic ON news(category, topic);
CREATE INDEX IF NOT EXISTS idx_news_category ON news(category);
CREATE INDEX IF NOT EXISTS idx_news_temperature_news_id ON news_temperature(news_id);
CREATE INDEX IF NOT EXISTS idx_news_temperature_time ON news_temperature(time);
CREATE INDEX IF NOT EXISTS idx_news_temperature_news_id_time ON news_temperature(news_id, time);