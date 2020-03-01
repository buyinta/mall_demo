import json
import re

from django import http
from django.contrib.auth import login
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from users.models import User


class UsernameCountView(View):
    '''注册时统计用户名个数，判断是否重复'''

    def get(self, request, username):
        """
        :param username: 用户名
        :return: JSON
        """
        try:
            count = User.objects.filter(username=username).count()

        except Exception as e:
            return http.JsonResponse({{'code': 400,
                                       'errmsg': '数据库查询失败',
                                       }})

        return http.JsonResponse({'code': 0,
                                  'errmsg': '查询成功',
                                  'count': count})


class MobileCountView(View):
    '''手机号重复查询接口'''

    def get(self, request, mobile):
        '''
        判断电话是否重复, 返回对应的个数
        :param request:
        :param mobile:
        :return:
        '''
        # 1.从数据库中查询 mobile 对应的个数
        count = User.objects.filter(mobile=mobile).count()

        # 2.拼接参数, 返回
        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok',
                                  'count': count})


class RegisterView(View):
    '''注册接口'''

    def post(self, request):

        # 接收参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        sms_code_client = dict.get('sms_code')

        # 校验(整体)
        if not all([username, password, password2, mobile, allow, sms_code_client]):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少必传参数'})
        # username校验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'username格式有误'})
        # password检验
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'password格式有误'})

        # password2 和 password
        if password != password2:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '两次输入不对'})
        #mobile检验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'mobile格式有误'})
        #allow检验
        if allow != 'true':
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'allow格式有误'})
        #sms_code检验 (链接redis数据库)
        redis_conn = get_redis_connection('verify_code')

        #从redis中取值
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        if not sms_code_server:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '短信验证码过期'})
        #把redis中取得值和前端发的值对比
        if sms_code_client != sms_code_server.decode():
            return http.JsonResponse({'code': 400,
                                      'errmsg': '验证码有误'})

        #保存到数据库(usernamepasswordmobile)
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)

        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '保存到数据库出错'})

        # 补充: 要实现状态保持:
        login(request, user)

        # 13.拼接json返回
        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})