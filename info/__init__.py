from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis
from config import config
import logging


db = SQLAlchemy()
# 设置redis_store为全局变量
redis_store = None # type:StrictRedis

def setup_log(log_level):
    # 配置日志
    # 设置日志的记录等级
    logging.basicConfig(level=log_level)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    # 设置日志
    setup_log(config[config_name].LOG_LEVEL)
    # 初始化项目
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])
    # 初始化数据库
    db.init_app(app)
    # 配置redis
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST,port=config[config_name].REDIS_PORT,decode_responses=True)
    # 开启csrf保护
    # csrf保护对cookie和表单中csrf_token的值进行校验，需要我们给cookie和表单中设置csrf_token的值
    CSRFProtect(app)
    # 由于表单使用ajax实现局部刷新，表单中csrf_token值，可在ajax中设置
    # 设置cookie中csrf_token
    @app.after_request
    def after_request(response):
        # 调用generate_csrf方法 生成crsf_token
        csrf_token = generate_csrf()
        response.set_cookie("csrf_token",csrf_token)
        return response
    # 设置session保存指定位置
    Session(app)
    # 注册蓝图
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)
    from info.modules.passport import password_blu
    app.register_blueprint(password_blu)
    return app
