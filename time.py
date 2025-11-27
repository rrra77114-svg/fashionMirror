from datetime import datetime
import time


def get_current_time():
    """
    获取当前时间的基本函数
    返回格式化的时间字符串
    """
    # 获取当前日期时间
    now = datetime.now()

    # 格式化为字符串
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    return current_time


# 使用示例
print("当前时间:", get_current_time())