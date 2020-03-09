from django import http
from django.shortcuts import render
from django.core.paginator import Paginator,EmptyPage
from django.views import View
from haystack.views import SearchView

from goods.models import GoodsCategory, SKU
from goods.utils import get_breadcrumb


class ListView(View):
    '''商品列表页'''
    def get(self,request,category_id):
        """提供商品列表页"""
        # 获取参数:
        page_num = request.GET.get('page')
        page_size = request.GET.get('page_size')
        sort = request.GET.get('ordering')

        #判断category_id是否正确
        try:
            # 获取三级菜单分类信息:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.JsonResponse({'code':400,
                                        'errmsg': '获取mysql数据出错'})

        #查询面包屑导航
        breadcrumb=get_breadcrumb(category)

        # 排序方式:
        try:
            skus = SKU.objects.filter(category=category,
                                      is_launched=True).order_by(sort)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code':400,
                                    'errmsg': '获取mysql数据出错'})

        paginator = Paginator(skus, 5)
        # 获取每页商品数据
        # 获取每页商品数据
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            # 如果page_num不正确，默认给用户400
            return http.JsonResponse({'code':400,
                                        'errmsg': 'page数据出错'})
            # 获取列表页总页数
        total_page = paginator.num_pages

        # 定义列表:
        list = []
        # 整理格式:
        for sku in page_skus:
            list.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url,
                'name': sku.name,
                'price': sku.price
            })

        # 把数据变为 json 发送给前端
        return http.JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,  # 面包屑导航
            'list': list,
            'count': total_page
        })


class HotGoodsView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行 JSON 数据"""
        # 根据销量倒序
        try:
            skus = SKU.objects.filter(category_id=category_id,
                                      is_launched=True).order_by('-sales')[:2]


        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '获取商品出错'})
        # 转换格式:
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url,
                'name': sku.name,
                'price': sku.price
            })

        return http.JsonResponse({'code': 0,
                                  'errmsg': 'OK',
                                  'hot_skus': hot_skus})


class MySearchView(SearchView):
    '''重写SearchView类'''
    def create_response(self):
        page = self.request.GET.get('page')
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id':sku.object.id,
                'name':sku.object.name,
                'price':sku.object.price,
                'default_image_url':sku.object.default_image_url,
                'searchkey':context.get('query'),
                'page_size':context['page'].paginator.num_pages,
                'count':context['page'].paginator.count
            })
        # 拼接参数, 返回
        return http.JsonResponse(data_list, safe=False)