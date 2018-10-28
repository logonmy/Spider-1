# coding:utf8


class JdRaw:
    """
    职位原文对象
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
        self.pageNum = None
        self.pageIndex = None
        self.ajax = None
        self.contactInfo = None
        self.searchConditions = None
        self.jdLayoutTime = None
        self.ip = None

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

    def __init__(self, region_name=None, region_code=None, func_name=None, func_code=None):
        self.region_name = region_name
        self.region_code = region_code
        self.func_name = func_name
        self.func_code = func_code
        self.page_num = None

    def __str__(self):
        return 'region_name = ' + self.region_name + ',region_code = ' + self.region_code + ',func_name = ' + self.func_name + ',func_code = ' + self.func_code

    def to_dics(self):
        return {
            'region_name': self.region_name,
            'region_code': self.region_code,
            'func_name': self.func_name,
            'func_code': self.func_code,
            'page_num': self.page_num
        }


class ResourceData:
    """
    kafka 推送所需对象
    """

    def __init__(self, trackId, content, source='FIVE_ONE',
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
