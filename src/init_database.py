"""创建初始化数据脚本"""

from models import Base

Base.metadata.create_all(checkfirst=True)  # 创建表
