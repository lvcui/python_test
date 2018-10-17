from redis import StrictRedis
import logging

class Config(object):
    """项目配置"""
    DEBUG = True
    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"
    # 配置数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@127.0.0.1:3306/information'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置redis
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # 配置session
    # 设置session保存到redis中
    SESSION_TYPE = "redis"
    # 设置session 设置中redis配置
    SESSION_REDIS = StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    # 设置session签名
    SESSION_USE_SIGNER = True
    # 设置session为可过期
    SESSION_PERMANENT = False
    # 设置过期时间
    PERMANENT_SESSION_LIFETIME = 86500 * 2

    # 设置日志等级  默认为debug
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发模式"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境"""
    DEBUG = False
    LOG_LEVEL = logging.ERROR

class TestingConfig(Config):
    """测试模式"""
    DEBUG = True

# 创建字典存入配置名
config = {
    "development" :DevelopmentConfig,
    "production":ProductionConfig,
    "testing":TestingConfig
}