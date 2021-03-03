from flask import request, url_for, redirect, render_template, current_app as app
from flask_restful import Resource as RestfulResource
# from ..models import *
from flask_security import current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .. import api, params
from wtforms import *
import json
from ..models_mongo import User

class APIRegister(RestfulResource):
    @params({
            "user.name" : StringField(
                description="姓名"
            ),
            "user.nickname" : StringField(
                description="昵称"
            ),
            "user.number" : StringField(
                description="输入有效的手机号码位数",
                validators=[validators.required(), validators.length(max=11)]
            ),
            "user.password" : StringField(
                description="密码"
            ),
            "user.sex" : StringField(
                description="只能输入男或者女",
                validators=[validators.optional(), validators.any_of(['男', '女'])]
            ),
            "user.area" : StringField(
                description="地区"
            ),
            "user.city" : StringField(
                description="城市"
            ),
            "user.tag" : FieldList(
                StringField(),
                description="标签"
            ),
            "user.income" : StringField(
                description="收入情况"
            )
    })
    @api
    def get(self):
        """
        用户注册
        :return:
            :success:
                {
                    user.id:603f3c861867cb5eb1d65776,
                    user.name : 东方不败,
                    user.nickname : dfbb,
                    user.number : 12365987452,
                    user.password : dfbb,
                    user.sex : 女，
                    user.area : 黑木崖，
                    user.city ：null
                    user.tag : 东方教主，千秋万代，
                    user.income : null
                }
             :failure:
               -1, "格式错误 ，请检查手机号码与性别"
        """
        user = User()
        user.name = request.args.get('name')
        user.nickname = request.args.get('nickname')
        user.number = request.args.get('number')
        user.password = request.args.get('password')
        user.sex = request.args.get('sex')
        user.area = request.args.get('area')
        user.city = request.args.get('city')
        user.tag = request.args.get('tag')
        user.income = request.args.get('income')
        hash_pwd=generate_password_hash(user.password)
        user.password=hash_pwd
        user.save()
        if user:
            return str(user.id)+"注册成功"
        else:
            return "未知错误"

class APISignin(RestfulResource):
    @api
    def post(self):
        """
        用户登录
        :return:
            :success:
                {
                "登陆成功"
                }
            :failure:
                -1, "登录失败 密码或用户名错误"
        """
        nickname = request.args.get('nickname')
        password = request.args.get('password')
        user = User.objects(nickname=nickname).first()
        if check_password_hash(user.password,password):
            return "登录成功"
        else:
            return "登录失败"

