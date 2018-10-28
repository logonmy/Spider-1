class Db {
  // init () {
  //   if (!localStorage.getItem('dev_config')) {
  //     let devConfig = {
  //       loginUrl: 'http://morgan-gateway.mofanghr.com/api/user/login/v2/loginByUserName',
  //       baseUrl: 'http://morgan-gateway.mofanghr.com/api/autojob',
  //       cookieUploadUrl: 'http://morgan-autojob.mofanghr.com/update_cookie/',
  //       useragent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
  //       proxyWhiteList: 'localhost,morgan-autojob.mofanghr.com,morgan-gateway.mofanghr.com'
  //     }
  //     localStorage.setItem('dev_config', JSON.stringify(devConfig))
  //   }
  // }
  get (key) {
    return JSON.parse(localStorage.getItem(key))
  }
  set (key, value) {
    localStorage.setItem(key, JSON.stringify(value))
  }
  del (key) {
    localStorage.removeItem(key)
  }
}

export default new Db()
