import qs from 'qs'
import axios from 'axios'
import {Message} from 'element-ui'

// axios.defaults.baseURL = 'http://172.16.25.8:5000/api/autojob'
axios.defaults.baseURL = 'http://morgan-gateway.mofanghr.com/api/autojob'
axios.defaults.headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8'

axios.interceptors.request.use(function (config) {
  // 在发送请求之前做些什么
  let userInfo = JSON.parse(localStorage.getItem('user_info'))
  if (!userInfo) {
    var accessToken = ''
  } else {
    accessToken = userInfo.token
  }

  if (config.method === 'post') {
    // if (config.data.accessToken !== undefined) {
    // config.data.accessToken = accessToken
    // }
    config.data = qs.stringify(config.data)
  } else {
    config.params.accessToken = accessToken
  }
  return config
}, function (error) {
  // 对请求错误做些什么
  Message.error('Request错误信息: ' + error.message)
  return Promise.reject(error)
})

axios.interceptors.response.use(function (response) {
  // 对响应数据做点什么

  if (response.data.code === 10099) {
    Message.error('服务器错误消息: ' + response.data.msg)
  }

  return response
}, function (error) {
  // 对响应错误做点什么
  Message.error('Response错误信息: ' + error.message)
  return Promise.reject(error)
})

export default axios
