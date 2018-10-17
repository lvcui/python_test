# 创建蓝图
from flask import Blueprint

index_blu = Blueprint('index',__name__)

from .views import *