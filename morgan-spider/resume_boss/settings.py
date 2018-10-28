MYSQL_HOST = '172.16.25.1'
MYSQL_PORT = 3306
MYSQL_USER = 'bi_admin'
MYSQL_PASSWD = 'bi_admin#@1mofanghr'
MYSQL_DB = 'spider'
KAFKA_HOSTS = '172.16.25.35:19092'
KAFKA_TOPIC = 'morgan-resume-raw'
PROJECT_NAME = 'resume_boss'
GET_ACCOUNT_URL = 'http://172.16.25.35:8002/acc/getCookie.json?source=BOSS_HR&useType=POSITION_PUBLISH&all=true'

CHECK_URL = 'http://10.0.4.223:8108/boss/check.json?uid=%s&userAccount=%s'
ADD_URL = 'http://10.0.4.223:8108/boss/add.json?uid=%s&userAccount=%s&type=%s'
UPLOAD_RESUME_URL = 'http://10.0.4.223:8108/boss/upload.json'
SET_INVALID_URL = 'http://172.16.25.35:8002/acc/invalidCookie.json?userName=%s&password=%s'
