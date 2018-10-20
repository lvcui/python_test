import random
import re
from datetime import datetime
from flask import request, current_app, make_response, jsonify, session
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import password_blu
from info import redis_store, db
# 导入常量模块
from info import constants

@password_blu.route('/image_code')
def get_image_code():
    """获取图片验证码"""
    # 1、获取图片编号
    image_code_id = request.args.get('imageCodeId')
    # 2、生成图片验证码 使用工具captcha
    name, text,image = captcha.generate_captcha()
    print(text)
    # 3、在redis中保存验证码内容，并设置有效时间
    try:
        redis_store.set('image_code_'+ image_code_id,text,ex=constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as a:
        current_app.logger.error(a)
        return jsonify(errno=RET.DATAERR,errmsg='保存图片验证码错误')
    # 返回响应内容
    res = make_response(image)
    # 设置返回文件的响应头
    res.headers['Content-Type'] = 'image/jpg'
    return  res

@password_blu.route('/sms_code',methods=['POST'])
def send_sms():
    """获取手机验证码"""

    # 1、获取参数 图片验证码 图片编号 用户手机号码
    param_dict = request.json  # 直接获取参数为json格式
    image_code = param_dict['image_code']
    image_code_id = param_dict['image_code_id']
    mobile = param_dict['mobile']

    # 2、判断参数是否为空
    if not all([image_code,image_code_id,mobile]):
        # 若存在空值，则返回错误
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 3、判断手机号码是否符合规则
    if not re.match(r"^1[34578][0-9]{9}",mobile):
        # 若电话号码不符合规则，则返回错误
        return jsonify(errno=RET.DATAERR,errmsg='电话号码不符合规范')

    # 4、获取redis中image_code是否一致
    try:
       real_image_code = redis_store.get('image_code_'+ image_code_id)
    except Exception as a:
        current_app.logger.error(a)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询错误')
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="验证码已过期")

    # 5、判断验证码输入是否正确
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR,errmsg='验证码输入错误')

    # 6、判断该号码是否已注册
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as a:
        current_app.logger.error(a)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询错误')
    if user:
        return jsonify(errno=RET.DATAEXIST,errmsg='该号码已注册，请直接登录')

    # 7、生成短信验证码
    str_num = "%06d" %random.randint(0,999999)
    print(str_num)
    # result = CCP().send_template_sms(mobile, [str_num, constants.SMS_CODE_REDIS_EXPIRES/60], 1)
    # if result != 0: # 发送短信失败
    #     return jsonify(errno=RET.THIRDERR, errmsg='第三方系统错误')

    # 8、保存短信验证码
    try:
        redis_store.set("sms_"+mobile,str_num,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as a:
        current_app.logger.error(a)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码失败")
    return jsonify(errno=RET.OK, errmsg='发送成功')

@password_blu.route('/register',methods=['POST'])
def register():
    """
    注册提交功能实现
    :return:
    """
    # 1、获取参数 用户手机号码、短信验证码、用户密码
    param_dict = request.json
    mobile = param_dict.get('mobile')
    smscode = param_dict.get('smscode')
    password = param_dict.get('password')
    # 2、校验参数
    if not all([mobile,smscode,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    # 判断手机号码是否符合规则
    if not re.match(r"^1[34578][0-9]{9}", mobile):
        # 若电话号码不符合规则，则返回错误
        return jsonify(errno=RET.DATAERR, errmsg='电话号码不符合规范')
    # 3、校验用户输入的短信验证码
    # 从redis数据库中取出
    try:
        real_sms_code =redis_store.get("sms_"+mobile)
    except Exception as a:
        current_app.logger.error(a)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询错误')
    if not real_sms_code:
        return jsonify(errno=RET.DATAERR,errmsg='验证码过期了')
    # 与数据库存储的验证码进行对比
    if real_sms_code != smscode:
        return jsonify(errno=RET.DATAERR,errmsg='输入验证码错误')
    # 4、创建user模型，将数据存入user表中
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    # 密码加密处理
    user.password = password
    user.last_login = datetime.now()
    # 将数据提交到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as a:
        current_app.logger.error(a)
        db.session.rollback()
    # 5、将用户信息保存到session中
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    session['user_id'] = user.id
    # 6、返回注册结果
    return jsonify(errno=RET.OK,errmsg='注册成功')

@password_blu.route('/login',methods=['POST'])
def login():
    """
    登录功能实现
    :return:
    """
    # 1、获取参数 用户手机号码，密码
    param_dict = request.json
    mobile = param_dict.get('mobile')
    password = param_dict.get('password')
    # 2、校验参数
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 判断手机号码是否符合规则
    if not re.match(r"^1[34578][0-9]{9}", mobile):
        # 若电话号码不符合规则，则返回错误
        return jsonify(errno=RET.DATAERR, errmsg='电话号码不符合规范')
    # 3、查询数据库是否有该条数据
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as a:
        current_app.logger.error(a)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询错误')
    if not user:
        return jsonify(errno=RET.DATAERR, errmsg='该用户不存在')
    # 4、校验密码是否正确
    if not user.check_passowrd(password):
        return jsonify(errno=RET.DATAERR, errmsg='用户名或密码错误')
    # 5、将用户登录信息存入session中
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    session['user_id'] = user.id
    # 6、返回登录结果
    return jsonify(errno=RET.OK,errmsg='登录成功')

@password_blu.route('/logout')
def logout():
    """
    退出登录功能实现
    :return:
    """
    session.pop('user_id')
    session.pop('mobile')
    session.pop('nick_name')

    return jsonify(errno=RET.OK,errmsg='退出成功')




