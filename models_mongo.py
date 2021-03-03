from mongoengine import Document
from mongoengine import CASCADE, PULL, DENY
from mongoengine.errors import DoesNotExist
from mongoengine import StringField, IntField, DateTimeField, DictField, ReferenceField, BooleanField
from mongoengine import LazyReferenceField, ObjectIdField, FloatField, ListField, EmailField, EmbeddedDocumentField
from bson import objectid
from bson.dbref import DBRef
from .db import db
from flask_security import UserMixin, RoleMixin
import time
from datetime import date, datetime


class FMVCDocument:
    meta = {'abstract': True}

    def to_dict(self, fields=None):
        """
        document to dict 方式

        :param fields: 获取的字段列表, 默认为获取全部

        example:
            from datetime import datetime

            from mongoengine import StringField, DateTimeField, ReferenceField, connect


            class Person(BaseDocument):
                username = StringField()
                create_time = DateTimeField()
                blog = ReferenceField('Blog')


            class Blog(BaseDocument):
                title = StringField()
                content = StringField()

            connect("main", host="localhost", port=27017)

            person = Person()
            person.username = "xiaoming"
            person.create_time = datetime.now()

            blog = Blog()
            blog.title = 'blog title'
            blog.content = 'blog content'
            person.blog = blog

            blog.save()
            person.save()

            data = person.to_dict(fields=[
                 "id:person_id",
                 "username",
                 "create_time",
                 "blog.id:blog_id",
                 "blog.title:blog_title",
                 "blog.content"
            ])
            print(data)
            -----------------------------------------
            {
             'person_id': '5df321b482fb700f766f2f02',
             'username': 'xiaoming',
             'create_time': '2019-12-24 13:11:54',
             'blog': {'blog_id': '5df321b482fb700f766f2f03', 'blog_title': 'blog title', 'content': 'blog content'}
            }

            )
        """

        def _format_(value):
            if isinstance(value, objectid.ObjectId):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, date):
                value = value.strftime('%Y-%m-%d')
            elif isinstance(value, (BaseDocument, EmbeddedDocument)):
                value = value.to_dict()
            elif isinstance(value, DBRef):
                value = {'$oid': str(value.id)}
            return value

        def _set_dotted_value(dotted_key, value, item):

            parts = dotted_key.split(':')[-1].split('.')
            key = parts.pop(0)
            parent = item
            while parts:
                parent = parent.setdefault(key, {})
                key = parts.pop(0)
            parent[key] = value

        def _get_dotted_value(key, document):
            key = key.split(':')[0]
            parts = key.split('.')
            key = parts.pop(0)
            value = _get_field_value(key, document)
            try:
                while parts:
                    key = parts.pop(0)
                    value = _get_field_value(key, value)
            except AttributeError:
                value = None
            return _format_(value)

        def _get_field_value(key, document):
            try:
                if key in getattr(document, '_fields', {}):
                    return document[key]
            except (AttributeError, DoesNotExist):
                pass

        data = {}
        included_fields = []
        excluded_fields = []
        only_fields = []
        if fields is None:
            fields = []
        for f in fields:
            if f.startswith('+'):
                included_fields.append(f[1:])
            elif f.startswith('-'):
                excluded_fields.append(f[1:])
            else:
                only_fields.append(f)
        if only_fields:
            fields = only_fields
        else:
            all_fields = self._data.keys()
            include_set = set(all_fields).union(set(included_fields))
            fields = list(include_set - set(excluded_fields))
        for field_key in fields:
            if isinstance(field_key, str) and not field_key.startswith('_'):
                field_value = _get_dotted_value(field_key, self)
                _set_dotted_value(field_key, field_value, data)

        return data


class BaseDocument(db.Document, FMVCDocument):
    meta = {'abstract': True}


class EmbeddedDocument(db.EmbeddedDocument, FMVCDocument):
    meta = {'abstract': True}


class Role(BaseDocument, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

class PlatformInfo(EmbeddedDocument):
    open_id = db.StringField(max_length=50,null=True) # open
    union_id = db.StringField(max_length=50,null=True) # union
    platform = db.ListField(StringField(max_length=255,null=True)) # 平台
    login_info = db.ListField(StringField(max_length=50,null=True)) # 登录信息

class User(BaseDocument):
    name = db.StringField(max_length=50) # 姓名
    nickname = db.StringField(max_length=50) # 昵称
    number = db.StringField(max_length=100,unipue=True) # 手机
    password = db.StringField(max_length=100) # 密码
    sex = db.StringField(choices=('男','女')) # 性别
    area = db.StringField(max_length=255,null=True) # 地区
    city = db.StringField(max_length=255,null=True) # 城市
    tag = db.ListField(StringField(max_length=100,null=True)) # 标签
    income = db.StringField(max_length=50,null=True) # 收入
    platformInfo =db.ListField(EmbeddedDocumentField(PlatformInfo,null=True)) #平台信息数组

class Followee(BaseDocument):
    author_id = db.StringField(max_length=50) # 作者id
    source = db.StringField(choices=('', '', '', '')) # 作者所属平台
    followee = db.ListField(ReferenceField("User",max_length=255,null=True)) # 被关注列表

class UserInfo(BaseDocument):
    user_id = db.ReferenceField("User",max_length=255) # 用户id
    collect = db.ListField(StringField(max_length=255,null=True)) # 用户收藏
    follow = db.ListField(ReferenceField("Followee",max_length=255,null=True)) # 用户关注

class UserLog(BaseDocument):
    behavior_type = db.StringField(choices=('', '', '', '')) # 行为类型
    behavior_time = db.DateField() # 行为时间
    occ_time = db.DateField() # 发生时间
    obj_id = StringField(max_length=255) # 对象id
    obj_type = db.StringField(choices=('', '', '', ''))# 对象类型


class FinalUser(BaseDocument, UserMixin):
    date_created = db.FloatField(default=time.time())
    date_modified = db.DateTimeField()
    social_id = db.StringField(max_length=64, null=True, unique=True)
    email = db.StringField(max_length=64, unique=True)
    mobile = db.StringField(max_length=32, unique=True, null=True)
    password = db.StringField(c=255)
    last_login_at = db.DateTimeField()
    last_login_ip = db.StringField(max_length=45)
    login_count = db.IntField(default=0)
    active = db.BooleanField(default=True)
    balance = db.FloatField(default=0.0)
    roles = db.ReferenceField(Role, DBRef=True)


class RolesUsers(db.Document):
    final_user_id = db.ReferenceField(FinalUser, DBRef=True)
    role_id = db.ReferenceField(Role)


########################
# your models go below
########################

###
# Applied models

class ArticleProduct(EmbeddedDocument):
    title = StringField()
    img = StringField()
    mall = StringField()
    url = StringField()
    description = StringField()
    price = FloatField()


class Article(BaseDocument):
    meta = {
        'indexes': [
            {'fields': ['-published_time']},
        ]
    }

    cover_page = ListField(StringField(null=True))  # 封面
    title = StringField(max_length=128)  # 标题
    share_title = StringField(max_length=1024)  # 分享标题
    abstract = StringField(null=True)  # 摘要
    read_count = IntField()  # 阅读量
    category = ListField(StringField(), null=True)  # 分类
    category_hint = StringField(null=True)  # 来自平台的分类描述
    word_count = IntField(null=True)  # 字数
    published_time = DateTimeField(null=True)  # 源发布时间
    create_time = DateTimeField(default=datetime.now())  # 进库时间
    planned_published_time = DateTimeField(null=True)  # 计划发布时间
    publisher_image = StringField()  # 发布者头像
    publisher_name = StringField()  # 发布者名称
    publisher_id = StringField()  # 发布者在源的id
    source = StringField(max_length=64)  # 来源
    source_url = StringField(null=True)  # 来源url
    source_item_id = StringField(unique_with='source')  # 来源平台上的id
    content = StringField()  # 文章内容
    status = StringField(choices=('pending', 'passed', 'abandoned', 'edited'), default='pending')  # 状态
    comment_count = IntField()  # 评论数
    thumbs_up_count = IntField()  # 点赞数
    favor_count = IntField()  # 收藏数
    crawl_datetime = DateTimeField()  # 爬取时间
    product_data = ListField(EmbeddedDocumentField(ArticleProduct))
    editorial_topic = StringField(max_length=64)


class URL(EmbeddedDocument):
    source_url = StringField()
    cached_url = StringField()


class Resolution(EmbeddedDocument):
    R480P = EmbeddedDocumentField(URL)  # 不同的清晰度分类
    R720P = EmbeddedDocumentField(URL)
    R1080P = EmbeddedDocumentField(URL)
    R1080P60 = EmbeddedDocumentField(URL)
    R4K = EmbeddedDocumentField(URL)


class Video(BaseDocument):
    parent = ReferenceField('Video', null=True)  # 父封面
    cover_page = ListField(StringField())  # 子封面
    title = StringField(max_length=128)  # 标题
    view_count = IntField()  # 播放量
    complete_ratio = IntField()  # 完播率
    category = ListField(StringField())  # 分类
    length = StringField()  # 时长
    published_time = DateTimeField(null=True)  # 源发布时间
    create_time = DateTimeField()  # 进库时间
    planned_published_time = DateTimeField(null=True)  # 计划发布时间
    publisher_image = StringField()  # 发布者头像
    publisher_name = StringField()  # 发布者名称
    publisher_id = StringField()  # 发布者在源的id
    source = StringField(max_length=64)  # 来源
    source_url = StringField(null=True)  # 来源url
    source_item_id = StringField(unique_with='source')  # 来源平台上的id
    status = StringField(choices=('pending', 'passed', 'abandoned', 'edited'), default='pending')  # 状态
    url = EmbeddedDocumentField(Resolution)  # 存放地址,不同清晰度对应不同地址
    comment_count = IntField()  # 评论数
    thumbs_up_count = IntField()  # 点赞数


class PicInfo(EmbeddedDocument):
    width = IntField()
    pict_url = StringField()  # 图片url
    height = IntField()


class Goods(BaseDocument):
    cover_page = StringField(max_length=1024)  # 封面
    title = StringField(max_length=128)  # 标题
    share_title = StringField(max_length=64, null=True)  # 分享标题
    original_price = StringField(null=True)  # 原价
    price = StringField()  # 价格
    coupon_info = StringField(max_length=1024)  # 优惠券描述
    coupon_url = StringField(null=True)  # 购物津贴url
    coupon_time_start = DateTimeField(null=True)  # 优惠券期限
    coupon_time_end = DateTimeField(null=True)  # 优惠券期
    description = StringField()  # 商品描述
    view_count = IntField(default=0)  # 访问量
    deal_count = IntField(default=0)  # 成交
    category = ListField(StringField(), null=True)  # 分类
    category_hint = StringField(null=True)  # 来自数据源的分类描述
    published_time = DateTimeField(null=True)  # 源发布时间
    create_time = DateTimeField(default=datetime.now())  # 进库时间
    planned_published_time = DateTimeField(null=True)  # 计划发布时间
    publisher_image = StringField()  # 发布者头像
    publisher_name = StringField()  # 发布者名称
    publisher_id = StringField()  # 发布者在源的id
    source = StringField(max_length=64)  # 来源
    source_item_id = StringField(unique_with='source')  # 来源平台上的id
    status = StringField(choices=('pending', 'passed', 'abandoned', 'edited'), default='pending')  # 状态
    comment_count = IntField()  # 评论数，商品评论数不显示，源评论数加到点赞数中
    thumbs_up_count = IntField()  # 点赞数
    platform = StringField()  # 来源平台
    buyAllowance = StringField(null=True)  # 允许购买次数
    source_url = StringField()  # 来源url
    direct_url = StringField()  # 电商平台url
    shopName = StringField()  # 店铺名称
    shop_icon = StringField(null=True)  # 店铺图片
    shopScore = ListField(null=True)  # 店铺评分
    checkTime = StringField(null=True)  # 检查时间
    desPics = ListField(EmbeddedDocumentField(PicInfo), null=True)  # 介绍内容图片
    infoPics = ListField(EmbeddedDocumentField(PicInfo), null=True)  # 信息内容图片
    crawl_datetime = DateTimeField()  # 爬取时间


class Category(BaseDocument):
    name = StringField()  # 子分类
    parent = ReferenceField('self', null=True, default=None, required=False, reverse_delete_rule=DENY)  # 父节点
    article_count = IntField(min_value=0)  # 包含文章数
    create_time = DateTimeField()  # 创建时间
    status = StringField(choices=('enabled', 'disabled'), default='enabled')  # 分类状态


class BadWordsTarget(EmbeddedDocument):
    collection = StringField(choices=('article', 'video', 'goods'), null=False)
    fields = ListField(StringField())


class BadWords(BaseDocument):
    bad_words = StringField(unique_with='sources')  # 违禁词，可为正则
    # 发现违禁词时的策略：alert提醒，replace替换，abandon文章设为废弃
    strategy = StringField(choices=('replace', 'abandon'), default='replace')
    sources = ListField(StringField(), default=[])  # 查找违禁词的来源范围，默认为任意来源
    target = ListField(EmbeddedDocumentField(BadWordsTarget), null=True)  # 查找违禁词的字段范围，默认为全部实体表的全部字段
    modify_time = DateTimeField(default=datetime.now())  # 修改时间
    replacement = StringField(default="")  # 替换词，如果是正则替换，可用\1表示用group(1)替换
    status = StringField(choices=('enabled', 'disabled'), default='enabled')  # 违禁词状态


class Comment(BaseDocument):
    parent = ReferenceField('Comment', null=True)  # 父评论
    reply = StringField()  # 若父评论为不为null,则为追评
    thumbs_up_count = IntField()  # 评论点赞数
    create_time = DateTimeField()  # 创建时间
    article = ReferenceField('Article', null=True)  # 所属文章
    video = ReferenceField('Video', null=True)  # 所属视频
    goods = ReferenceField('Goods', null=True)  # 所属商品
    status = StringField(choices=('enabled', 'deleted'))  # 评论状态
    classification = StringField(choices=('article', 'video', 'goods'))  # 评论所属分类，文章，商品或短视频


###
# raw data models

class SMZDM(BaseDocument):
    meta = {
        'strict': False,
        "db_alias": "smzdm",
        "collection": "smzdm",
        'indexes': [
            {'fields': ['-publish_time']},
        ]
    }

    itemId = StringField(max_length=64)  # 商品ID
    platform = StringField()  # 商品平台
    goodPic = StringField()  # 商品图片
    goodName = StringField()  # 商品名称
    originPrice = StringField(null=True)  # 初始价格
    price = StringField(null=True)  # 价格，可能包括是否使用购买津贴
    freeSend = StringField(null=True)  # 是否包邮
    useCoupon = StringField(null=True)  # 是否使用购买津贴
    couponInfo = StringField(null=True)  # 购买津贴详情
    couponUrl = StringField(null=True)  # 购买津贴url
    shopPlatform = StringField()  # 消费平台
    publish_time = StringField()  # 发布时间
    value1 = IntField()
    goodDesc = StringField(null=True)  # 商品介绍
    smzdmPublicTime = DateTimeField(null=True)  # 发布日期
    checkTime = StringField(null=True)  # 检查时间
    relatGoods1 = DictField(null=True)  # 相关商品
    relatGoods2 = DictField(null=True)
    relatGoods3 = DictField(null=True)
    relatGoods4 = DictField(null=True)
    relatGoods5 = DictField(null=True)
    baoliaoUserInfo = DictField(null=True)
    value2 = IntField()
    collectNum = StringField(null=True)  # 收集数量
    directUrl = StringField(null=True)  # 网址
    other_info = DictField()
    crawlStartTime = StringField()  # 爬虫开始时间
    crawlTime = StringField()  # 爬虫时间


class SMZDMArti(BaseDocument):
    meta = {
        'strict': False,
        "db_alias": "smzdm",
        "collection": "smzdm_goods",
        'indexes': [
            {'fields': ['-crawlTime']},
        ]
    }

    itemId = StringField(max_length=64)  # 商品ID
    platform = StringField()  # 平台
    topic = StringField()  # 商品图片
    titlePage = StringField(null=True)  # 封面图
    title = StringField()  # 文章标题
    autherHeadSculpture = StringField(null=True)  # 作者头像
    autherNickName = StringField(null=True)  # 作者名
    collectNum = StringField(null=True)  # 收藏数
    updateTime = StringField(null=True)  # 更新时间
    topicFocusPersonNum = StringField()  # 关注描述
    content = StringField()  # 内容
    recommend = ListField(DictField())  # 相关推荐
    other_info = DictField()
    crawlStartTime = StringField()  # 爬虫开始时间
    crawlTime = StringField()  # 爬虫时间


class YangMao(BaseDocument):
    meta = {
        'strict': False,
        "db_alias": "yangmao",
        "collection": "yangmao",
        'indexes': [
            {'fields': ['-publish_time']},
        ]
    }

    platform = StringField()  # 来源平台
    itemId = StringField(max_length=32)  # 商品id
    title = StringField()  # 商品名称
    currentPrice = StringField()  # 价格
    publish_time = StringField()  # 时间
    tb_url = StringField()  # 淘宝url
    coupon = StringField()  # 购买津贴
    couponTime = StringField()  # 有效期
    buyAllowance = StringField()  # 允许购买次数
    coupon_url = StringField(null=True)  # 购买津贴url
    returnNum = StringField()  # 返现
    returnPrice = StringField()
    picInfo = ListField(EmbeddedDocumentField(PicInfo))  # 图片信息
    picUrl = StringField()  # 图片url
    origin = StringField()
    sold = StringField()  # 售出件数
    shopName = StringField()  # 店铺名称
    shopPic = StringField()  # 店铺图片
    shopScore = StringField()  # 店铺评分
    desPics = ListField(EmbeddedDocumentField(PicInfo))   # 介绍内容图片
    freeSend = StringField()  # 是否包邮
    other_info = DictField()  # 其他信息
    crawlStartTime = StringField()  # 爬虫开始时间
