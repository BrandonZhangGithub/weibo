from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

# 建立连接与数据库的连接
engine = create_engine("mysql+pymysql://seamile:123@localhost:3306/weibo")
Base = declarative_base(bind=engine)  # 创建模型的基础类
Session = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    nickname = Column(String(20), unique=True)  # 昵称
    password = Column(String(128))              # 密码
    gender = Column(String(10))                 # 性别
    city = Column(String(10))                   # 城市
    bio = Column(String(256))                   # 个人简介


class Weibo(Base):
    __tablename__ = 'weibo'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)   # 作者
    content = Column(Text)      # 内容
    created = Column(DateTime)  # 创建时间


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)            # 作者
    wb_id = Column(Integer)              # 微博 ID
    cmt_id = Column(Integer, default=0)  # 其他评论的 ID
    content = Column(Text)               # 内容
    created = Column(DateTime)           # 创建时间

    @property
    def up_comment(self):
        '''当前评论的上游评论'''
        session = Session()
        return session.query(Comment).get(self.cmt_id)


class Like(Base):
    '''点赞表'''
    __tablename__ = 'like'

    # wb_id 和 user_id 构成联合主键
    wb_id = Column(Integer, primary_key=True)    # 微博 ID
    user_id = Column(Integer, primary_key=True)  # 点赞者的 ID

    status = Column(Boolean, default=True)  # 点赞的状态，False 时代表用户已取消点赞
    created = Column(DateTime)              # 创建的时间


class Follow(Base):
    '''关注表'''
    __tablename__ = 'follow'

    # wb_id 和 user_id 构成联合主键
    user_id = Column(Integer, primary_key=True)    # 用户 ID
    follow_id = Column(Integer, primary_key=True)  # 被关注者的 ID

    status = Column(Boolean, default=True)  # True 代表关注，False 代表已取消
    created = Column(DateTime)              # 首次关注的时间
