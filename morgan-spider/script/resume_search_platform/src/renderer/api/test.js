import fetch from '../utils/fetch'
import { morganAccountUrl } from '../utils/api-path'

export function startAwake () {
  console.log('startAwake')
  let params = {
    source: 'ZHI_LIAN'
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

export function saveFlow () {
  console.log('saveFlow')
  let params = {
    source: 'ZHI_LIAN'
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

export function checkCrmDistribute () {
  console.log('checkCrmDistribute')
  let params = {
    source: 'ZHI_LIAN'
  }
  let resultData = {}
  return fetch({
    url: morganAccountUrl + '/crm/getAccount.json',
    method: 'get',
    params: params,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = ''
    // return Promise.reject(new Error('getAccount Error'))
    return resultData
  })
}

export function checkScoreDownload () {
  console.log('checkScoreDownload')
  let params = {
    source: 'ZHI_LIAN'
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

export function checkCrmScore () {
  console.log('checkCrmScore')
  let params = {
    source: 'ZHI_LIAN'
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

export async function saveResume (messages) {
  console.log(messages)
  await startAwake()
  if (messages.trackId) {
    console.log(messages.trackId)
    await saveFlow()
  } else {
    console.log('else')
    let name = await checkCrmDistribute()
    console.log(name)
    if (name) {
      return Promise.reject(new Error('简历已在[' + name + ']名下.'))
    } else if (await checkScoreDownload() <= 0) {
      return Promise.reject(new Error('您的当日简历下载量已达到限额，暂时不能将此简历分配到您的名下.'))
    } else if (await checkCrmScore() <= 0) {
      return Promise.reject(new Error('crm系统中，您名下的简历已达到限额，暂时不能将此简历分配到您的名下.'))
    }
    return Promise.resolve(true)
  }
  console.log('上传成功 0.5 -> ')
}
