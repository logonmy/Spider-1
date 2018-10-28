#!coding:utf8
from __future__ import print_function
import json
import time
import datetime

from mf_utils.core import InitCore
from settings import project_settings


class CreateTask(InitCore):
    def __init__(self):
        super(CreateTask, self).__init__(
            # project_name='resume_youzi_task_create',
            local_setting=project_settings,
            # 测试环境配置
            # common_settings_path='/data/config/morgan/'
            #                      'morgan_spider_common_settings_test.cfg'
        )
        self.mysql_handler = self.init_mysql()

    def get_city_order(self):
        sql = """
        select cityName from spider.city_entrence WHERE source='YOU_ZI' and 
        valid=1
        """
        res = self.mysql_handler.query_by_sql(sql)
        city_order = [item[0] for item in res]
        self.logger.info('city_order 初始化完成: %s' % '/'.join(
            city_order).encode('utf-8'))
        return city_order

    def create_task_from_mysql(self, use_keyword='0'):
        self.logger.info("开始推送任务.")
        city_order = self.get_city_order()
        cities = self.mysql_handler.query_by_sql(
            'select * from spider.city_entrence where source="YOU_ZI" '
            'and valid=1')
        functions = self.mysql_handler.query_by_sql(
            'select * from spider.function_entrence where '
            'source="YOU_ZI" '
            'and valid=1')
        self.logger.info('共加载城市： %s个 职能： %s个' % (
            len(cities), len(functions)))
        if not cities or not functions:
            self.logger.info('城市/职能加载失败.')
            return

        today = datetime.datetime.today()
        next_datetime = datetime.datetime(today.year, today.month, today.day,
                                          0, 0, 0) + datetime.timedelta(days=1)
        deadline = int(time.mktime(
            time.strptime(next_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                          '%Y-%m-%d %H:%M:%S'))) * 1000

        city_result = []
        # use_keyword = '0' if datetime.datetime.now().hour < 12 else '1'

        if cities:
            city_dict = {i[1]: i for i in cities}
            for i in city_order:
                if i in city_dict:
                    city_result.append(city_dict[i])
                    city_dict.pop(i)
            city_result = city_result + city_dict.values()

        for city in city_result:
            for func in functions:
                param = json.dumps({
                    'jobTitle': func[7],
                    'locationid': city[6],
                    'locationname': city[1],
                    'use_keyword': use_keyword
                }, ensure_ascii=False)
                res = self.add_task(param, deadline=deadline)
                if res.json().get('code') != 200:
                    self.logger.warning('任务推送失败： %s|%s'
                                        % (city[1].encode('utf-8'),
                                           func[7].encode('utf-8')))

                self.logger.info('任务推送成功： %s|%s'
                                 % (city[1].encode('utf-8'),
                                    func[7].encode('utf-8')))

        self.logger.info('执行完毕.')


if __name__ == '__main__':
    runner = CreateTask()
    # runner.preview_settings()
    runner.create_task_from_mysql()