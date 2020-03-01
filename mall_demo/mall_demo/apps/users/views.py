import json
import re
import logging
logger=logging.getLogger('django')

from django import http
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
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
        # mobile检验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'mobile格式有误'})
        # allow检验
        if allow != 'true':
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'allow格式有误'})
        # sms_code检验 (链接redis数据库)
        redis_conn = get_redis_connection('verify_code')

        # 从redis中取值
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        if not sms_code_server:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '短信验证码过期'})
        # 把redis中取得值和前端发的值对比
        if sms_code_client != sms_code_server.decode():
            return http.JsonResponse({'code': 400,
                                      'errmsg': '验证码有误'})

        # 保存到数据库(usernamepasswordmobile)
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


class LoginView(View):

    def post(self, request):
        '''登录接口'''
        # 接收参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        remembered = dict.get('remembered')

        # 校验(整体 + 单个)
        if not all([username, password]):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少必传参数'})

        # 验证是否能够登录
        user = authenticate(username=username,
                            password=password)

        # 判断是否为空，如果为空，则直接返回
        if user is None:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '用户名或者密码错误'})

        # 状态保持
        login(request, user)

        # 判断是否记住用户
        if remembered != True:
            # 不记住用户，则浏览器关闭立刻生效
            request.session.set_expiry(0)

        else:
            # 记住用户，设置两周的有效期
            request.session.set_expiry(None)

        # 生成响应对象
        response = http.JsonResponse({'code': 0,
                                      'errmsg': 'ok'})

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 14 天
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        # 返回响应结果
        return response


class LogoutView(View):
    def delete(self, request):
        '''退出登录接口'''
        # logout函数实现清理 session 会话信息
        logout(request)
        # 创建 response 对象.
        response = http.JsonResponse({'code': 0,
                                      'errmsg': 'ok'})

        # 调用对象的 delete_cookie 方法, 清除cookie
        response.delete_cookie('username')

        # 返回响应
        return response


class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""

    def get(self, request):
        """提供个人信息界面"""

        # 获取界面需要的数据,进行拼接
        info_data = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }

        # 返回响应
        return http.JsonResponse({'code':0,
                                  'errmsg':'ok',
                                  'info_data':info_data})


class EmailView(View):
    """添加邮箱"""

    def put(self, request):
        """实现添加邮箱逻辑"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '参数email有误'})


        # 赋值 email 字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                      'errmsg': '添加邮箱失败'})

        from celery_tasks.email.tasks import send_verify_email
        # 调用发送的函数:
        verify_url = request.user.generate_verify_email_url()
        send_verify_email.delay(email, verify_url)

        return http.JsonResponse({'code': 0,
                                  'errmsg': '添加邮箱成功'})


class VerifyEmailView(View):
    """验证邮箱"""

    def put(self, request):
        """实现邮箱验证逻辑"""
        # 接收参数
        token = request.GET.get('token')

        # 校验参数：判断 token 是否为空和过期，提取 user
        if not token:
            return http.JsonResponse({'code':400,
                                  'errmsg':'缺少token'})

        # 调用上面封装好的方法, 将 token 传入
        user = User.check_verify_email_token(token)
        if not user:
            return http.JsonResponse({'code':400,
                                  'errmsg':'无效的token'})

        # 修改 email_active 的值为 True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':400,
                                  'errmsg':'激活邮件失败'})

        # 返回邮箱验证结果
        return http.JsonResponse({'code':0,
                                  'errmsg':'ok'})