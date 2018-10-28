// detail页，各渠道配置文件

import electron from 'electron'

export const dev = {
  'ZHI_LIAN': {
    name: '智联',
    id: 3,
    preload: `file:${require('path').resolve(__dirname, '../../../static/inject/zhi_lian.js')}`,
    login_url: 'https://passport.zhaopin.com/org/login',
    rule: {
      login: 'passport.zhaopin.com/org/login',
      detail: [
        'ihr.zhaopin.com/resume/details',
        'rd5.zhaopin.com/resume/detail',
        'ihr.zhaopin.com/api/redirect.do?searchresume=1',
        'ihrsearch.zhaopin.com/home/RedirectToRd'
      ],
      publish: [
        'rd5.zhaopin.com/job/publish'
      ],
      list: 'ihr.zhaopin.com/resumesearch/searchlist'
    }
  },
  'FIVE_ONE': {
    name: '前程',
    id: 2,
    preload: `file:${require('path').resolve(__dirname, '../../../static/inject/five_one.js')}`,
    login_url: 'https://ehire.51job.com/MainLogin.aspx',
    rule: {
      login: 'ehire.51job.com/MainLogin.aspx',
      detail: [
        'ehire.51job.com/Candidate/ResumeView.aspx',
        'ehire.51job.com/Candidate/ResumeViewFolder.aspx'
      ],
      publish: [
        'ehire.51job.com/Jobs/JobEdit.aspx?Mark=New'
      ],
      list: 'ehire.51job.com/Candidate/SearchResumeNew.aspx'
    }
  }
}

export const pro = {
  'ZHI_LIAN': {
    name: '智联',
    id: 3,
    preload: `file:` + electron.remote.app.getAppPath() + `/dist/electron/static/inject/zhi_lian.js`,
    login_url: 'https://passport.zhaopin.com/org/login',
    rule: {
      login: 'passport.zhaopin.com/org/login',
      detail: [
        'ihr.zhaopin.com/resume/details',
        'rd5.zhaopin.com/resume/detail',
        'ihr.zhaopin.com/api/redirect.do?searchresume=1',
        'ihrsearch.zhaopin.com/home/RedirectToRd'
      ],
      publish: [
        'rd5.zhaopin.com/job/publish'
      ],
      list: 'ihr.zhaopin.com/resumesearch/searchlist'
    }
  },
  'FIVE_ONE': {
    name: '前程',
    id: 2,
    preload: `file:` + electron.remote.app.getAppPath() + `/dist/electron/static/inject/five_one.js`,
    login_url: 'https://ehire.51job.com/MainLogin.aspx',
    rule: {
      login: 'ehire.51job.com/MainLogin.aspx',
      detail: [
        'ehire.51job.com/Candidate/ResumeView.aspx',
        'ehire.51job.com/Candidate/ResumeViewFolder.aspx'
      ],
      publish: [
        'ehire.51job.com/Jobs/JobEdit.aspx?Mark=New'
      ],
      list: 'ehire.51job.com/Candidate/SearchResumeNew.aspx'
    }
  }
}
