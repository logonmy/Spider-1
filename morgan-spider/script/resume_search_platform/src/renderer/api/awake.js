import fetch from '../utils/fetch'
import { morganParseUrl, morganPickUrl, morganAccountUrl, morganYoubenUrl } from '../utils/api-path'

/**
 * 参数：source, content, resourceType, mobile, trackId, userName, email, name
 * 说明：启动唤醒
 * 返回：true
 */
export function startAwake (requestData) {
  let resultData = {}
  return fetch({
    url: morganParseUrl + '/crm/parse.json',
    method: 'post',
    data: requestData,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response
    console.log('启动唤醒结果:' + JSON.stringify(resultData))
    if (resultData.code === 500) {
      return Promise.reject(new Error(resultData.msg))
    } else if (resultData.code !== 200) {
      return Promise.resolve({error: true, message: '服务器异常'})
      // return Promise.reject(new Error('服务器异常'))
    }
    return Promise.resolve(resultData.data)
  })
}

/**
 * 参数：source, trackId
 * 说明：检查唤醒进度
 * 返回：code 200 唤醒成功
 *      code 107 猎100唤醒成功
 *      code 100 唤醒失败
 *      data 结果数据
 */
export function checkAwake (requestData) {
  let resultData = {}
  return fetch({
    url: morganPickUrl + '/crm/checkBuy',
    params: requestData,
    method: 'get',
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response
    console.log('简历check结果:' + JSON.stringify(resultData))
    return Promise.resolve(resultData)
  })
}

/**
 * 参数：flowNo, code, message, userName, resumeId, source, account, mobile, distributeSource
 * 说明：保存流水
 * 返回：void
 */
export function saveFlow (requestData) {
  let resultData = {}
  return fetch({
    url: morganAccountUrl + '/crm/addFlow.json',
    method: 'post',
    data: requestData,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response
    console.log('流水添加结果:' + JSON.stringify(resultData))
    return Promise.resolve(resultData)
  })
}

/**
 * 参数：mobile
 * 说明：检查简历归属人
 * 返回：归属人姓名
 */
export function checkCrmDistribute (requestData) {
  let resultData = {}
  return fetch({
    url: morganAccountUrl + '/crm/checkDistribute',
    method: 'post',
    data: requestData,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response
    console.log('简历归属结果:' + JSON.stringify(resultData))
    if (resultData.code === 100) {
      return Promise.resolve(resultData.data)
    } else if (resultData.code === 200) {
      return Promise.resolve(resultData.data)
    } else {
      return Promise.resolve({error: true, message: '简历归属查询失败'})
      // Promise.reject(new Error('简历归属查询失败'))
    }
  })
}

/**
 * 参数：userName, resumeId
 * 说明：分配简历
 * 返回：分配简历结果
 * code 200 正常 msg 消息
 * code !200 异常 msg 异常消息
 */
export function forceCrmDistribute (requestData) {
  let resultData = {}
  return fetch({
    url: morganAccountUrl + '/crm/forceDistribute',
    method: 'post',
    data: requestData,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response
    console.log('crm强分配结果:' + JSON.stringify(resultData))
    return Promise.resolve(resultData)
  })
}

/**
 * 参数：userName, source [string]
 * 说明：下载额度
 * 返回：下载额度
 */
export function checkScoreDownload (requestData) {
  let resultData = {}
  return fetch({
    url: morganAccountUrl + '/crm/downloadScore',
    method: 'post',
    data: requestData,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response
    console.log('下载额度查询结果:' + JSON.stringify(resultData))
    if (resultData.code === 200) {
      if (resultData.data > 0) {
        return Promise.resolve(resultData.data)
      } else {
        return Promise.resolve({error: true, message: '下载剩余额度不足'})
        // Promise.reject(new Error('下载剩余额度不足'))
      }
    } else {
      return Promise.resolve({error: true, message: '查询下载额度失败'})
      // Promise.reject(new Error('查询下载额度失败'))
    }
  })
}

/**
 * 参数：userName, source
 * 说明：CRM额度
 * 返回：CRM额度
 */
export function checkCrmScore (requestData) {
  let resultData = {}
  return fetch({
    url: morganAccountUrl + '/crm/score',
    method: 'post',
    data: requestData,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response
    console.log('CRM额度查询结果:' + JSON.stringify(resultData))
    if (resultData.code === 200) {
      if (resultData.data > 0) {
        return Promise.resolve(resultData.data)
      } else {
        return Promise.resolve({error: true, message: 'CRM剩余额度不足'})
        // Promise.reject(new Error('CRM剩余额度不足'))
      }
    } else {
      return Promise.resolve({error: true, message: '查询CRM额度失败'})
      // Promise.reject(new Error('查询CRM额度失败'))
    }
  })
}

/**
 * 参数：userName, resumeId, callType（‘CRM_BUY’）
 * 说明：有本购买
 * 返回：联系方式
 */

export function downloadLie100Resume (requestData) {
  let resultData = {}
  return fetch({
    url: morganYoubenUrl + '/resume/buy',
    method: 'post',
    data: requestData,
    dataType: 'json',
    async: false
  }).then((response) => {
    resultData = response
    console.log('有本购买结果:' + JSON.stringify(resultData))
    if (resultData.code === 200) {
      return Promise.resolve(resultData.data)
    } else {
      return Promise.resolve({error: true, message: '有本购买失败，请尝试直接在当前所在渠道进行下载'})
      // Promise.reject(new Error('查询CRM额度失败'))
    }
  })
}

/**
 * 参数：messages
 * 说明：上传简历
 * 返回：true
 */
export async function saveResume (messages) {
  console.log('start saveResume')
  let requestData = {
    source: messages.Target,
    content: messages.Message.toString(),
    resourceType: 'RESUME_INBOX',
    mobile: messages.mobile,
    trackId: messages.trackId,
    userName: messages.userName
  }
  await startAwake(requestData)
  if (messages.trackId) {
    let requestData1 = {
      flowNo: messages.trackId,
      code: '104',
      message: '下载成功',
      userName: messages.userName,
      resumeId: messages.ResumeId,
      source: messages.source,
      account: messages.account,
      mobile: messages.mobile
    }
    await saveFlow(requestData1)
  } else {
    let requestData2 = {
      mobile: messages.mobile
    }
    let name = await checkCrmDistribute(requestData2)
    console.log(name)
    let requestData3 = {
      userName: messages.userName,
      source: messages.source
    }
    if (name) {
      return Promise.reject(new Error('简历已在[' + name + ']名下.'))
    } else if (await checkScoreDownload(requestData3) <= 0) {
      return Promise.reject(new Error('您的当日简历下载量已达到限额，暂时不能将此简历分配到您的名下.'))
    } else if (await checkCrmScore(requestData3) <= 0) {
      return Promise.reject(new Error('crm系统中，您名下的简历已达到限额，暂时不能将此简历分配到您的名下.'))
    }
    return Promise.resolve(true)
  }
  console.log('上传成功 0.5 -> ' + messages.source + ' ' + messages.ResumeId)
}

/**
 * 参数：messages
 * 说明：唤醒成功处理·
 * 返回：true
 */
export async function doAwakeSuccess (messages) {
  let requestData2 = {
    mobile: messages.mobile
  }
  let name = await checkCrmDistribute(requestData2)
  console.log(name)
  let requestData3 = {
    userName: messages.userName,
    source: messages.source
  }
  if (name) {
    return Promise.reject(new Error('简历已在[' + name + ']名下.'))
  } else if (await checkScoreDownload(requestData3) <= 0) {
    return Promise.reject(new Error('您的当日简历下载量已达到限额，暂时不能将此简历分配到您的名下.'))
  } else if (await checkCrmScore(requestData3) <= 0) {
    return Promise.reject(new Error('crm系统中，您名下的简历已达到限额，暂时不能将此简历分配到您的名下.'))
  }
  console.log('唤醒成功 -> ' + messages.source + ' ' + messages.ResumeId)
  return Promise.resolve(true)
}
