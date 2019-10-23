import datetime
from math import ceil
from hashlib import sha256

import tornado.web
from pymysql import err
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from models import User, Weibo, Comment, Session, Like, Follow


def login_required(view_func):
    '''检查用户是否登陆'''

    def wrapper(self, *args, **kwargs):
        user_id = self.get_cookie('user_id')  # 取出用户 ID
        if user_id is None:
            # user_id 是 None 值，说明用户没有登陆
            return self.redirect('/user/login')
        else:
            return view_func(self, *args, **kwargs)
    return wrapper


class RegisterHandler(tornado.web.RequestHandler):
    '''用户注册视图类'''
    @staticmethod
    def gen_password(password):
        '''产生一个安全的密码'''
        bytes_code = password.encode('utf8')  # 将密码转成 bytes 类型
        hash_code = sha256(bytes_code)        # 对上一步结果进行 sha256 的 hash 运算
        return hash_code.hexdigest()          # 返回 16 进制的 hash 值

    def get(self):
        '''显示注册页面'''
        return self.render('register.html', top10=top10())

    def post(self):
        '''接收用户提交的信息，写入到数据库'''
        # 获取参数
        nickname = self.get_argument('nickname')
        password = self.get_argument('password')
        gender = self.get_argument('gender')
        city = self.get_argument('city')
        bio = self.get_argument('bio')

        safe_password = self.gen_password(password)  # 产生安全密码

        # 将用户数据写入数据库
        session = Session()
        user = User(nickname=nickname, password=safe_password,
                    gender=gender, city=city, bio=bio)
        session.add(user)
        session.commit()

        # 注册完成后，跳转到登陆页面
        return self.redirect('/user/login')


class LoginHandler(tornado.web.RequestHandler):
    '''用户登陆视图类'''

    def get(self):
        '''显示登陆页面'''
        return self.render('login.html', warning='', top10=top10())

    def post(self):
        '''登陆过程'''
        # 获取参数
        nickname = self.get_argument('nickname')
        password = self.get_argument('password')

        safe_password = RegisterHandler.gen_password(password)  # 产生安全密码

        # 获取用户
        session = Session()
        q_user = session.query(User)
        try:
            user = q_user.filter_by(nickname=nickname).one()
        except NoResultFound:
            return self.render('login.html', warning='您的用户名错误！', top10=top10())

        # 检查密码
        if user.password == safe_password:
            self.set_cookie('user_id', str(user.id))  # 服务器通知客户端设置一个叫 'uid' 的 cookie 值
            # 跳转到用户信息页
            return self.redirect('/user/info')
        else:
            return self.render('login.html', warning='您的密码错误！', top10=top10())


class UserinfoHandler(tornado.web.RequestHandler):
    '''用户个人信息视图类'''

    def get(self):
        user_id = self.get_cookie('user_id')           # 取出自己的 ID
        other_id = self.get_argument('user_id', None)  # 取出要查看的其他人的 ID

        session = Session()
        q_user = session.query(User)

        if user_id is None and other_id is None:
            # 如果用户未登陆，查看自己页面时，直接跳到登陆页面
            return self.redirect('/user/login')
        elif user_id is None and other_id is not None:
            # 未登陆时查看别人的主页
            user = q_user.get(other_id)
            is_followed = False
        elif user_id is not None and other_id is None:
            # 登陆的情况下查看自己的页面
            user = q_user.get(user_id)
            is_followed = None
        elif user_id is not None and other_id is not None:
            # 登陆时查看别人的主页
            user = q_user.get(other_id)
            # 检查自己是否关注过该用户
            exists = session.query(Follow) \
                            .filter_by(user_id=user_id, follow_id=other_id, status=True) \
                            .exists()
            is_followed = session.query(exists).scalar()

        return self.render('info.html', user=user, is_followed=is_followed, top10=top10())


class PostWeiboHandler(tornado.web.RequestHandler):
    '''发送微博页面'''

    def get(self):
        return self.render('post_wb.html', top10=top10())

    @login_required
    def post(self):
        user_id = int(self.get_cookie('user_id'))
        content = self.get_argument('content')

        # 保存微博数据
        session = Session()
        weibo = Weibo(user_id=user_id, content=content, created=datetime.datetime.now())
        session.add(weibo)
        session.commit()

        # 创建完成后，跳到显示页面
        return self.redirect('/weibo/show?weibo_id=%s' % weibo.id)


class ShowWeiboHandler(tornado.web.RequestHandler):
    '''查看单条微博页面'''

    def get(self):
        weibo_id = int(self.get_argument('weibo_id'))  # 提取参数

        session = Session()
        weibo = session.query(Weibo).get(weibo_id)       # 从数据库获取微博数据
        author = session.query(User).get(weibo.user_id)  # 根据微博记录的作者 id 获取用户数据

        # 取出当前微博所有的评论
        all_comments = session.query(Comment)\
                              .filter_by(wb_id=weibo.id)\
                              .order_by(Comment.created.desc())

        # 取出所有评论的作者的 user_id
        comment_author_id_list = {cmt.user_id for cmt in all_comments}

        # 根据评论作者的 ID 取出所有评论的作者
        comment_authors_list = session.query(User).filter(User.id.in_(comment_author_id_list))
        comment_authors = {u.id: u for u in comment_authors_list}  # 将数据转成字典形式

        # 取出用户点赞状态
        user_id = self.get_cookie('user_id')
        if user_id is None:
            is_liked = False  # 用户未登陆时，按未点赞看待
        else:
            # 从数据库取出点赞记录
            like_record = session.query(Like).get((weibo_id, int(user_id)))
            # is_liked = False if like_record is None else like_record.status  # 三元表达式的写法
            if like_record is None:
                is_liked = False
            else:
                is_liked = like_record.status
        n_like = session.query(Like).filter_by(wb_id=weibo_id, status=True).count()

        return self.render('show_wb.html',
                           weibo=weibo, user=author,
                           all_comments=all_comments,
                           comment_authors=comment_authors,
                           is_liked=is_liked,
                           n_like=n_like,
                           top10=top10())


class HomePageHandler(tornado.web.RequestHandler):
    '''首页'''

    def get(self):
        page = int(self.get_argument('page', 1))  # 获取页码
        per_page_size = 10                        # 每页显示的数量

        # 取出所有的微博
        session = Session()
        q_weibo = session.query(Weibo)
        all_pages = ceil(q_weibo.count() / per_page_size)  # 总页数
        # 按时间降序取出指定页数的微博
        wb_list = q_weibo.filter()\
                         .order_by(Weibo.created.desc())\
                         .limit(per_page_size)\
                         .offset((page - 1) * per_page_size)

        # 取出对应的用户
        q_user = session.query(User)
        user_id_list = {wb.user_id for wb in wb_list}  # 取出所有的作者的 ID
        # 取出用户，并将数据整理成字典形式, key 为 user_id, value 为 user 对象
        users = {u.id: u for u in q_user.filter(User.id.in_(user_id_list))}

        # 获取每条微博的点赞数量
        wb_id_list = [wb.id for wb in wb_list]
        like_dict = dict(session.query(Like.wb_id, func.count(1))
                                .filter(Like.status.is_(True), Like.wb_id.in_(wb_id_list))
                                .group_by(Like.wb_id).all())

        return self.render('home.html',
                           wb_list=wb_list, users=users,
                           all_pages=all_pages, cur_page=page,
                           like_dict=like_dict, top10=top10())


class CommentCommitHandler(tornado.web.RequestHandler):
    '''发表评论'''

    @login_required
    def post(self):
        # 取出参数
        content = self.get_argument('content')
        wb_id = int(self.get_argument('wb_id'))
        user_id = int(self.get_cookie('user_id'))

        # 插入评论内容
        session = Session()
        comment = Comment(user_id=user_id, wb_id=wb_id, content=content,
                          created=datetime.datetime.now())  # 创建 comment 对象
        session.add(comment)  # 插入单条数据
        session.commit()

        # 跳回原来的页面
        return self.redirect('/weibo/show?weibo_id=%s' % wb_id)


class ReplyCommentHandler(tornado.web.RequestHandler):
    '''回复其他评论'''

    def get(self):
        cmt_id = int(self.get_argument('cmt_id'))  # 要回复的评论的 ID

        session = Session()
        comment = session.query(Comment).get(cmt_id)     # 要回复的 Comment 对象
        user = session.query(User).get(comment.user_id)  # 原评论的作者

        return self.render('reply_comment.html', comment=comment, user=user, top10=top10())

    @login_required
    def post(self):
        # 获取参数
        content = self.get_argument('content')     # 回复内容
        cmt_id = int(self.get_argument('cmt_id'))  # 所回复的原评论的 ID
        wb_id = int(self.get_argument('wb_id'))    # 对应的微博 ID
        user_id = int(self.get_cookie('user_id'))       # 当前用户的 ID

        # 添加数据
        session = Session()
        comment = Comment(user_id=user_id, wb_id=wb_id, cmt_id=cmt_id,
                          content=content, created=datetime.datetime.now())
        session.add(comment)
        session.commit()

        # 发表完回复以后，页面回到原微博下
        return self.redirect('/weibo/show?weibo_id=%s' % wb_id)


class LikeHandler(tornado.web.RequestHandler):
    '''点赞接口'''
    @login_required
    def get(self):
        user_id = self.get_cookie('user_id')
        wb_id = self.get_argument('wb_id')

        # 第一次点赞的操作
        like = Like(wb_id=wb_id, user_id=user_id, created=datetime.datetime.now())
        session = Session()
        session.add(like)
        try:
            session.commit()
        except (IntegrityError, err.IntegrityError):
            session.rollback()  # 回滚之前的操作

            # 产生冲突，说明用户重复点赞，或者想将取消的赞改回来
            # 如果冲突，需要将状态修改为 True
            session.query(Like).get((wb_id, user_id)).status = True
            session.commit()

        return self.redirect('/weibo/show?weibo_id=%s' % wb_id)


class DislikeHandler(tornado.web.RequestHandler):
    '''取消点赞接口'''
    @login_required
    def get(self):
        user_id = self.get_cookie('user_id')
        wb_id = self.get_argument('wb_id')

        session = Session()
        try:
            session.query(Like).get((wb_id, user_id)).status = False
            session.commit()
        except AttributeError:
            pass

        return self.redirect('/weibo/show?weibo_id=%s' % wb_id)


class FollowHandler(tornado.web.RequestHandler):
    '''关注'''

    @login_required
    def get(self):
        # 获取参数
        user_id = int(self.get_cookie('user_id'))
        follow_id = int(self.get_argument('follow_id'))

        # 定义数据模型
        follow = Follow(user_id=user_id, follow_id=follow_id,
                        created=datetime.datetime.now())
        # 插入数据
        session = Session()
        session.add(follow)
        try:
            session.commit()  # 提交修改
        except (IntegrityError, err.IntegrityError):
            session.rollback()  # 回滚之前的操作

            # 数据有冲突，说明用户重复提交关注，或者用户想将“取消关注”的状态重新修改为“关注”
            session.query(Follow).get((user_id, follow_id)).status = True
            session.commit()

        # 跳回用户信息页
        return self.redirect('/user/info?user_id=%s' % follow_id)


class UnfollowHandler(tornado.web.RequestHandler):
    '''取消关注'''

    @login_required
    def get(self):
        # 获取参数
        user_id = int(self.get_cookie('user_id'))
        follow_id = int(self.get_argument('follow_id'))

        # 找到关注的数据
        session = Session()
        try:
            session.query(Follow).get((user_id, follow_id)).status = False
            session.commit()
        except AttributeError:
            pass

        # 跳回用户信息页
        return self.redirect('/user/info?user_id=%s' % follow_id)


class FollowWeiboHandler(tornado.web.RequestHandler):
    @login_required
    def get(self):
        user_id = int(self.get_cookie('user_id'))

        # 取出关注的人的 ID
        session = Session()
        follow_ids = session.query(Follow)\
                            .filter_by(user_id=user_id, status=True)\
                            .values('follow_id')
        follow_id_list = [fid for (fid, ) in follow_ids]

        # 取出对应的用户对象
        users = session.query(User).filter(User.id.in_(follow_id_list))
        users = {u.id: u for u in users}  # 将结果整理成字典格式

        # 根据用户 ID 取出微博
        wb_list = session.query(Weibo)\
                            .filter(Weibo.user_id.in_(follow_id_list))\
                            .order_by(Weibo.created.desc())

        # 获取每条微博的点赞数量
        wb_id_list = [wb.id for wb in wb_list]
        like_dict = dict(session.query(Like.wb_id, func.count(1))
                                .filter(Like.status.is_(True), Like.wb_id.in_(wb_id_list))
                                .group_by(Like.wb_id).all())

        return self.render('follow_weibo.html',
                           wb_list=wb_list, users=users, like_dict=like_dict, top10=top10())


class FansHandler(tornado.web.RequestHandler):
    '''粉丝接口'''
    @login_required
    def get(self):
        user_id = self.get_cookie('user_id')

        # 取出自己粉丝的 ID
        session = Session()
        fans_ids = session.query(Follow)\
                            .filter_by(follow_id=user_id, status=True)\
                            .values('user_id')
        fans_id_list = [fid for (fid, ) in fans_ids]

        # 取出对应的用户对象
        fans_list = session.query(User).filter(User.id.in_(fans_id_list))

        return self.render('fans.html', fans_list=fans_list, top10=top10())


def top10():
    '''获取热度前 10 的微博'''
    session = Session()

    # 取出热度前10的微博的 ID 及其点赞数量
    top10_weibo = session.query(Like.wb_id, func.count(1)) \
                         .filter(Like.status.is_(True)) \
                         .group_by(Like.wb_id) \
                         .order_by(func.count(1).desc()) \
                         .limit(10)

    # 根据微博的 id 取出相应的微博
    wb_id_list = [wb_id for (wb_id, _) in top10_weibo]
    weibo_dict = dict(session.query(Weibo)\
                             .filter(Weibo.id.in_(wb_id_list))\
                             .values('id', 'content'))

    # 组装结果数据
    result = []
    for wb_id, n_like in top10_weibo:
        content = weibo_dict[wb_id]  # 取出微博的内容
        item = (wb_id, content, n_like)
        result.append(item)

    return result
