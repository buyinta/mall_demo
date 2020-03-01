from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from mall_demo.libs.captcha.captcha import captcha


class ImageCodeView(View):
    '''返回图形验证码的类视图'''

    def get(self, request, uuid):
        """
        生产图形验证码，保存到Redis中，另外返回图片
        :param request:
        :return: image
        """
        # 调用captcha生成图形验证码
        text, image = captcha.generate_captcha()

        # 链接redis，获取链接对象，存储text
        redis_conn = get_redis_connection('verify_code')

        # 利用链接对象, 保存数据到 redis, 使用 setex 函数
        redis_conn.setex('img_%s' % uuid, 300, text)
        return http.HttpResponse(image,content_type='image/jpg')
