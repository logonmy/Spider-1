import axios from 'axios'
import qs from 'qs'
import {
  Message
} from 'element-ui'

// 创建axios实例
const service = axios.create({
  // baseURL: process.env.BASE_API, // api的base_url
  // timeout: 5000 // 请求超时时间
})

// request拦截器
service.interceptors.request.use(config => {
  console.log('before request')
  //   if (store.getters.token) {
  //     config.headers['Authorization'] = getToken() // 让每个请求携带token--['X-Token']为自定义key 请根据实际情况自行修改
  //   }
  //   return config
  if (config.params) {
    console.log('url: ' + config.url + ';请求参数：' + JSON.stringify(config.params))
  }
  if (config.data) {
    console.log('url: ' + config.url + ';请求参数：' + JSON.stringify(config.data))
  }
  if (config.method === 'post') {
    config.data = qs.stringify(config.data)
  }
  return config
}, error => {
  console.log(error)
  Promise.reject(error)
})

// respone拦截器
service.interceptors.response.use(
  response => {
    // response:
    // {
    //     // XHR对象
    //     request: {},
    //     // 由服务器提供的响应
    //     data: {},
    //     // 来自服务器响应的 HTTP 状态码
    //     status: 200,
    //     // 来自服务器响应的 HTTP 状态信息
    //     statusText: 'OK',
    //     // 服务器响应的头
    //     headers: {},
    //     // 请求提供的配置信息
    //     config: {}
    // }
    // const res = response.data
    // if (response.status === 401 || res.status === 40101) {
    //   MessageBox.confirm('你已被登出，可以取消继续留在该页面，或者重新登录', '确定登出', {
    //     confirmButtonText: '重新登录',
    //     cancelButtonText: '取消',
    //     type: 'warning'
    //   }).then(() => {
    //     store.dispatch('FedLogOut').then(() => {
    //       location.reload() // 为了重新实例化vue-router对象 避免bug
    //     })
    //   })
    //   return Promise.reject('error')
    // }
    // if (res.status === 40301) {
    //   Message({
    //     message: '当前用户无相关操作权限！',
    //     type: 'error',
    //     duration: 5 * 1000
    //   })
    //   return Promise.reject('error')
    // }
    // if (response.status !== 200 && res.status !== 200) {
    //   Message({
    //     message: res.message,
    //     type: 'error',
    //     duration: 5 * 1000
    //   })
    // } else {
    //   return response.data
    // }
    const res = response.data
    console.log('url: ' + response.config.url + ';响应数据：' + JSON.stringify(res))
    if (res.code === 10099) {
      Message({
        message: '系统异常，请联系管理员',
        type: 'error',
        duration: 3 * 1000
      })
      return Promise.reject(new Error('系统异常，请联系管理员'))
    }
    return Promise.resolve(response.data)
  },
  error => {
  // if (error.response) {
  //     // 请求已发出，但服务器响应的状态码不在 2xx 范围内
  //     console.log(error.response.data)
  //     console.log(error.response.status)
  //     console.log(error.response.headers)
  //   } else {
  //     // Something happened in setting up the request that triggered an Error
  //     console.log('Error', error.message)
  //   }
  //   console.log(error.config)
    console.log('err' + error) // for debug
    Message({
      message: error.message,
      type: 'error',
      duration: 5 * 1000
    })
    return Promise.reject(error)
  }
)

export default service
