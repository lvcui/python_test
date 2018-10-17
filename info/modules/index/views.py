from flask import render_template, current_app

from . import index_blu

# 首页视图函数
@index_blu.route('/')
def index():
    return render_template('index.html')

# 加载网页图标
@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')