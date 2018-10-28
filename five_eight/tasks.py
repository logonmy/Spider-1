from crwy.utils.no_sql.redis_m import get_redis_client
from five_eight.spiders.search import settings as search_settings

server = get_redis_client(
    url='redis://root:uV2ngVk9AC@'
        'r-2ze0889fc8e3c784.redis.rds.aliyuncs.com:6379/6')


def search_test():
    task_key = 'task:search:FIVE_EIGHT'
    task_value = {
        'city': 'bj',
        'city_name': '北京',
        'keyword': '销售代表',
        'username': 'a13126697607',
        'degree': '4'
    }
    server.lpush(task_key, task_value)


if __name__ == '__main__':
    search_test()
