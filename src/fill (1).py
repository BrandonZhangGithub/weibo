"""数据填充脚本"""

import random
import string
from models import *

citys = ['北京', '上海', '广州', '深圳', '大连', '沈阳', '保定', '济南', '武汉',
         '郑州', '长沙', '贵州', '成都', '重庆', '苏州', '合肥', '西安', '兰州']


def gen_name():
    if random.choice([0, 1]):
        m = random.randint(5, 19)
        n = random.randrange(2, m - 1)
        chars = random.sample(string.ascii_lowercase * 2, m)
        name = '%s %s' % (''.join(chars[:n]), ''.join(chars[n:]))
        return name.title()
    else:
        codes = random.sample(range(20000, 40000), random.randint(3, 5))
        return ''.join([chr(c) for c in codes])


def fill_users(num):
    def _gen(n):
        users = []
        for i in range(n):
            u = User(nickname=gen_name(),
                     password='123',
                     gender=random.choice(['male', 'female']),
                     city=random.choice(citys),
                     bio='... ...')
            users.append(u)
        session = Session()
        session.add_all(users)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

    while num > 1000:
        try:
            _gen(1000)
            num -= 1000
            print(f'remain {num}')
        except Exception as e:
            print(f'raise an error: {e}')
    else:
        _gen(num)


def fill_weibo(num):
    def _gen(n):
        wb_list = []
        for i in range(n):
            y = random.randint(2010, 2019)
            m = random.randint(1, 12)
            d = random.randint(1, 28)
            h = random.randint(0, 23)
            _m = random.randint(0, 59)
            s = random.randint(0, 59)
            dt = '%s-%s-%s %s:%s:%s' % (y, m, d, h, _m, s)
            wb = Weibo(user_id=random.randrange(1, 50000),
                       content=''.join(random.sample(string.ascii_letters * 10, 140)),
                       created=dt)
            wb_list.append(wb)
        session = Session()
        session.add_all(wb_list)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

    while num > 3000:
        try:
            _gen(3000)
            num -= 3000
            print(f'remain {num}')
        except Exception as e:
            print(f'raise an error: {e}')
    else:
        _gen(num)


if __name__ == "__main__":
    fill_users(3000000)
    fill_weibo(5000000)
