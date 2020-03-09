def get_breadcrumb(category):
    """
    封装面包屑导航代码:
    :param category: 商品类别
    :return: 面包屑导航字典
    """

    # 定义一个字典:
    breadcrumb = {
        'cat1':'',
        'cat2':'',
        'cat3':''
    }
    # 判断 category 是哪一个级别的.
    # 注意: 这里的 category 是 GoodsCategory对象
    if category.parent is None:
        # 当前类别为一级类别
        breadcrumb['cat1'] = category.name
    # 因为当前这个表示自关联表, 所以关联的对象还是自己:
    elif category.parent.parent is None:
        # 当前类别为二级
        breadcrumb['cat2'] = category.name
        breadcrumb['cat1'] = category.parent.name
    else:
        # 当前类别为三级
        breadcrumb['cat3'] = category.name
        cat2 = category.parent
        breadcrumb['cat2'] = cat2.name
        breadcrumb['cat1'] = cat2.parent.name

    return breadcrumb