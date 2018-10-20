from flask import render_template, current_app, session

from info.models import User
from . import index_blu

# 首页视图函数
@index_blu.route('/')
def index():
    # 1、获取session中用户信息
    user_id = session.get("user_id",None)
    # 根据用户id获取用户信息
    user = None
    try:
        user = User.query.get(user_id)
    except Exception as a:
        current_app.logger.error(a)

    # 将数据存入字典中，并将其返回给模板
    data = {
        'user': user.to_dict() if user else None
    }
    return render_template('index.html',data=data)

# 加载网页图标
@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')