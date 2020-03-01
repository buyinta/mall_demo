from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

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
        return http.JsonResponse({'code':0,
                                  'errmsg':'ok',
                                  'count':count})