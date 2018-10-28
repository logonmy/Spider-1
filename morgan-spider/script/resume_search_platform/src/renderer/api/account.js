import fetch from '../utils/fetch'
import { morganAccountUrl } from '../utils/api-path'

/**
 * 说明: getAccount
 * 返回: 渠道账号
 */
export function getAccount (source) {
  let params = {
    source: source
  }
  let resultData = {}
  return fetch({
    url: morganAccountUrl + '/crm/getAccount.json',
    method: 'get',
    params: params,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response.data
    // return Promise.reject(new Error('getAccount Error'))
    return resultData
  })
}
