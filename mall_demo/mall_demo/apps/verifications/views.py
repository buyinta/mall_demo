import random

from django import http
from django.shortcuts import render
import logging

from mall_demo.libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import ccp_send_sms_code
logger = logging.getLogger('django')
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
        return http.HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    '''短信验证码'''

    def get(self, request, mobile):
        """

        :param request:
        :param mobile:手机号
        :return: JSON
        """
        #校验是否已发送过短信验证码，避免重复发送
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 查看数据是否存在, 如果存在, 说明60s没过, 返回
        if send_flag:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '发送短信过于频繁'})

        # 接受参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 参数校验
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少必传参数'})

        # 链接redis库，提取图形验证码
        redis_conn = get_redis_connection('verify_code')
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            # 图形验证码过期
            return http.JsonResponse({'code': 400,
                                      'errmsg': '图形验证码失效'})

        # 删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        # 对比图形验证码
        image_code_server = image_code_server.decode()

        if image_code_client.lower() != image_code_server.lower():
            return http.JsonResponse({'code': 400,
                                      'errmsg': '输入图形验证码有误'})

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        #pipeline,减少客户端与redis的通信次数，降低往返延时
        pl=redis_conn.pipeline()

        # 保存短信验证码，为了注册时校验
        pl.setex('sms_%s' % mobile, 300, sms_code)

        #设置一个send_flag，用于访问接口时先校验是否存在，从而判断是否重复发送短信验证码
        pl.setex('send_flag_%s' % mobile, 60, 1)

        #执行和redis的请求
        pl.execute()

        # 调用celery发送短信验证码

        ccp_send_sms_code.delay(mobile, sms_code)

        # 10. 响应结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': '发送短信成功'})
