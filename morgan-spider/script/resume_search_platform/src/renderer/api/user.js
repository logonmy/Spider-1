import fetch from '../utils/fetch'
import { morganParseUrl } from '../utils/api-path'

/**
 * 说明: 获取leaders
 * 返回:
 */
export function getLeader () {
  let resultData = {}
  return fetch({
    url: morganParseUrl + '/crm/getCrmAccount',
    method: 'post',
    data: {source: 'ZHI_LIAN'},
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response.data
    console.log('返回结果：' + resultData)
    return resultData
  })
}

/**
 * 说明: getUser
 * 返回:
 */
export function getUser (leader) {
  let resultData = {}
  return fetch({
    url: morganParseUrl + '/crm/getCrmAccount',
    method: 'post',
    data: {email: leader},
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response.data
    console.log('返回结果：' + resultData)
    return resultData
  })
}
