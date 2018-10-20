from flask import Blueprint

password_blu = Blueprint('password',__name__,url_prefix='/passport')

from .views import *