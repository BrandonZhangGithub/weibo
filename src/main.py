#!/usr/bin/env python

import tornado.web
import tornado.ioloop
from tornado.options import parse_command_line

import views

# 绑定路由
route = [
    (r'/', views.HomePageHandler),  # 主页

    # 用户相关的页面
    (r'/user/register', views.RegisterHandler),
    (r'/user/login', views.LoginHandler),
    (r'/user/info', views.UserinfoHandler),
    (r'/user/follow', views.FollowHandler),
    (r'/user/unfollow', views.UnfollowHandler),
    (r'/user/fans', views.FansHandler),

    # 微博相关接口
    (r'/weibo/post', views.PostWeiboHandler),
    (r'/weibo/show', views.ShowWeiboHandler),
    (r'/weibo/like', views.LikeHandler),
    (r'/weibo/dislike', views.DislikeHandler),
    (r'/weibo/follow', views.FollowWeiboHandler),

    # 评论相关接口
    (r'/comment/commit', views.CommentCommitHandler),
    (r'/comment/reply', views.ReplyCommentHandler),
]

# 定义 App
web_app = tornado.web.Application(
    route,
    template_path='./templates',
    static_path='./statics',
)


parse_command_line()
web_app.listen(8000, '0.0.0.0')  # 绑定服务器运行的地址和端口
print('Server running on 0.0.0.0:8000')
tornado.ioloop.IOLoop.current().start()  # 启动服务器
