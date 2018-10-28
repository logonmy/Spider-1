#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25

# sys.path.append("..")

project_settings = {
"PROJECT_NAME": 'chinahr',
"CALLSYSTEMID": 'morgan-chinahr-jd-1',
"TASK_TYPE": 'JD_FETCH',
'RESOURCE_TYPE': 'JD_SEARCH',
"SOURCE": 'CH_HR',
'PROXY_PATH': 'test',

'DOWNLOAD_RETRY_TIMES': 5,

"DOWNLOAD_THREAD_NUMBER": 20,
# 'PROXY_URL' : 'http://172.16.25.35:9010/module-proxy/proxy/one.json?systemId=morgan-chinahr-jd-1&isStatic=1',
'GET_ACCOUNT_URL':  'http://172.16.25.41:8002/acc/getCookie.json?source=%s&useType=%s',
'SET_INVALID_URL': 'http://172.16.25.41:8002/acc/invalidCookie.json?userName=%s&password=%s&source=%s'
}