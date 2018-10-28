# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import base64
import gzip
import json
import time
import uuid
from io import StringIO

from mns.account import Account
from mns.queue import Message
from crwy.utils.scrapy_plugs.pipelines import SqlalchemySavePipeline
from five_eight.models import spider_search


MNS_ENDPOINT = 'http://1315265288610488.mns.' \
               'cn-beijing-internal-vpc.aliyuncs.com'
MNS_ACCID = 'LTAIf2I0xlEogGx5'
MNS_ACCKEY = '14EJ0FhqZL5czEdw5E54pAjyVkdtbI'
MNS_TOKEN = ''
MNS_QUEUE = 'morgan-queue-jd-raw'


class SpiderSearchResumeRawSavePipeline(SqlalchemySavePipeline):
    def insert_db(self, item):
        try:
            self.sqlalchemy_handle.session.execute(
                spider_search.ResumeRaw.__table__.insert(), item
            )
            self.sqlalchemy_handle.session.commit()
        except Exception as e:
            self.sqlalchemy_handle.session.rollback()
            self.logger.exception("入库失败, 回滚： %s" % e)
            raise e
        sql_id = self.sqlalchemy_handle.session.execute(
            "select last_insert_id()").first()[0]

        self.logger.info("入库成功. %s" % str(sql_id))

        try:
            resume_uuid = uuid.uuid1()
            mns_data = {
                "channelType": "WEB",
                "content": {
                    "content": item['content'],
                    "id": sql_id,
                    "createBy": "python",
                    "createTime": int(time.time() * 1000),
                    "ip": '',
                    'emailJobType': item['emailJobType'],
                    'emailCity': item['emailCity'],
                    'deliverJobName': '',
                    'deliverJobCity': '',
                    "resumeSubmitTime": '',
                    "resumeUpdateTime": '',
                    "source": item['source'],
                    "trackId": str(resume_uuid),
                    "avatarUrl": '',
                },
                "interfaceType": "PARSE",
                "resourceDataType": "RAW",
                "resourceType": "RESUME_SEARCH",
                "source": item['source'],
                "trackId": resume_uuid,
                "traceID": resume_uuid,
                "callSystemID": 'five_one_python3_scrapy'
            }
            dumps = json.dumps(mns_data, ensure_ascii=False)

            buf = StringIO()
            f = gzip.GzipFile(mode='wb', fileobj=buf)
            f.write(dumps)
            f.close()
            msg_body = base64.b64encode(buf.getvalue())
            msg = Message(msg_body)
            # 初始化MNS
            mns_account = Account(MNS_ENDPOINT, MNS_ACCID, MNS_ACCKEY,
                                  MNS_TOKEN)
            mns_client = mns_account.get_queue(MNS_QUEUE)
            mns_client.send_message(msg)
            self.logger.info("推送mns成功. %s" % str(sql_id))
        except Exception as e:
            self.logger.exception("推送mns失败: %s" % e)
