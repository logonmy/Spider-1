# coding:utf8


class JdRaw:
    """
    原文对象
    """

    def __init__(self):
        self.id = None
        self.source = None
        self.createTime = None
        self.content = None
        self.createBy = None
        self.trackId = None
        self.pageUrl = None
        self.jobCity = None
        self.ocrImg = None
        self.adTag = None
        self.ajax = None
        self.contactInfo = None
        self.searchConditions = None
        self.jdLayoutTime = None
        self.ip = None
        self.pageNum = None
        self.pageIndex = None

    def to_dics(self):
        return {
            'id': id,
            'source': self.source,
            'createTime': self.createTime,
            'content': self.content,
            'createBy': self.createBy,
            'trackId': self.trackId,
            'pageUrl': self.pageUrl,
            'jobCity': self.jobCity,
            'ocrImg': self.ocrImg,
            'adTag': self.adTag,
            'ip': self.ip,
            'pageNum': self.pageNum,
            'pageIndex': self.pageIndex,
            'ajax': self.ajax,
            'contactInfo': self.contactInfo,
            'searchConditions': self.searchConditions,
            'jdLayoutTime': self.jdLayoutTime
        }


class SearchCondition:
    """
    搜索参数module
    """

    def __init__(self, city_name=None, city_url=None, sec_name=None, third_name=None, third_url=None):
        self.city_name = city_name
        self.city_url = city_url
        self.sec_name = sec_name
        self.third_name = third_name
        self.third_url = third_url

    def __str__(self):
        return 'city_name = ' + self.city_name + ',city_url = ' + self.city_url + ',sec_name = ' + self.sec_name + ',third_name = ' + self.third_name + ',third_url = ' + self.third_url

    def to_dics(self):
        return {
            'city_name': self.city_name,
            'city_url': self.city_url,
            'sec_name': self.sec_name,
            'third_name': self.third_name,
            'third_url': self.third_url
        }


class ResourceData:
    """
    kafka 推送所需对象
    """

    def __init__(self, trackId, content, source='FIVE_EIGHT',
                 channelType='WEB', resourceType='JD_SEARCH',
                 resourceDataType='RAW', protocolType='HTTP'):
        self.trackId = trackId
        self.source = source
        self.channelType = channelType
        self.resourceType = resourceType
        self.resourceDataType = resourceDataType
        self.content = content
        self.protocolType = protocolType

    def to_dics(self):
        return {
            'trackId': self.trackId,
            'source': self.source,
            "channelType": self.channelType,
            'resourceType': self.resourceType,
            'resourceDataType': self.resourceDataType,
            'content': self.content,
            'protocolType': self.protocolType
        }
