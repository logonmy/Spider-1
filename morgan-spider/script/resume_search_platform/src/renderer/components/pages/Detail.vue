/*
 * @Author: wuyue 
 * @Date: 2018-04-02 15:19:35 
 * @Last Modified by: wuyue
 * @Last Modified time: 2018-06-15 18:15:40
 */
<template>
  <el-row>
    <ul class="action-list">
      <li><el-button type="primary" class='action detail-button' circle  @click="goBackWebView()"><i class="el-icon-mf-fanhui iconfont"></i></el-button></li>
      <li><el-button type="primary" class='action detail-button' circle  @click="reloadWebView()"><i class="el-icon-mf-huanyihuan iconfont"></i></el-button></li>
    </ul>
    <el-card class="box-card" id="message-box">
      <el-col :span="16">
        <!-- <div class="text item">渠道： {{ common_setting.name }}</div>
        <div class="text item">用户名： {{ username }}</div>
        <div class="text item">代理地址：{{ proxy }}</div> -->
        <div class="text item">消息提示：{{ message }}</div>
      </el-col>
      <!-- <el-col :span="4">
        <el-dropdown split-button type="primary" @click.native="updateCookie()">
            上传Cookie
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item @click.native="checkProxy()">代理地址有效性检查</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </el-col>
      <el-col :span="2">
        <el-button @click="testWebView()">test</el-button>
      </el-col> -->
      <el-col :span="2">
        <el-button v-if="can_download" class="detail-button" @click="executeResumeDownload()" type="primary">下载</el-button>
      </el-col>
      <el-col :span="2">
        <el-button v-if="can_download_lie100" class="detail-button" @click="executeLie100ResumeDownload()" type="primary">下载（有本）</el-button>
      </el-col>
      <el-col :span="2">
        <el-button v-if="can_distribute" class="detail-button" @click="executeForceCrmDistribute()" type="primary">分配</el-button>
      </el-col>
    </el-card>
    <div style="margin-bottom: 60px;" v-loading="loading">
      <webview id='first' :src="common_setting.login_url" partition="persist:webviewsession" autosize="on" :style="webview_place_1" :useragent="useragent" :preload="common_setting.preload"></webview>
      <webview id='second' class="hide" :src="common_setting.login_url" partition="persist:webviewsession" autosize="on" :style="webview_place_2" :useragent="useragent" :preload="common_setting.preload"></webview>
    </div>
  </el-row>
</template>

<script>
import * as apiPath from '../../utils/api-path.js'
import * as cfg from '../../utils/config.js'
import * as api from '../../api/awake.js'
const {shell} = require('electron')
const packageInfo = require('../../../../package.json')
export default {
  name: 'detail',
  data () {
    return {
      view: '',
      view2: '',
      source: '',
      // 登录帐号
      user: '',
      email: '',
      // 业务帐号
      accountName: '',
      username: '',
      password: '',
      useragent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
      proxy: '',
      webview_place_1: 'width: 100%; height:' + window.screen.height + 'px;',
      webview_place_2: 'width: 0px; height: 0px; flex: 0 1;',
      common_setting: {
        id: '',
        name: '',
        preload: '',
        login_url: ''
      },
      // need init
      trackId: '',
      resourceType: '',
      message: '初始化完成',
      crm_resume_id: '',
      resumeExtId: '',
      Lie100ResumeDownloadId: '',
      can_download: false,
      can_download_lie100: false,
      can_distribute: false,
      isBlank: false,
      loading: false
    }
  },
  methods: {
    checkProxy () {
      let url = 'https://httpbin.org/ip'
      this.view.loadURL(url)
    },
    getAccountInfo () {
      let self = this
      this.$http.get(
        apiPath.morganAccountUrl + '/crm/getAccount.json', {
          params: {
            source: self.source,
            email: 'test@test.com',
            version: packageInfo.version
          }
        })
        .then(function (response) {
          if (response.data.code === 200) {
            let proxy = JSON.parse(response.data.data.proxy)
            // console.log(proxy)
            self.proxy = 'http://' + proxy.ip + ':' + proxy.port
            self.username = response.data.data.userName
            self.password = response.data.data.password
            self.accountName = response.data.data.accountName
            self.initView()
          } else if (response.data.code === 300) {
            self.$alert('<strong>版本校验失败，前往下载新版？<strong>', '警告', {
              confirmButtonText: '确定',
              dangerouslyUseHTMLString: true,
              callback: action => {
                shell.openExternal('http://crm.mofanghr.com')
                window.close()
              }
            })
          }
        })
        .catch(function (error) {
          self.$message.error(error.message)
        })
    },
    updateCookie (url) {
      // this.view.webContents.
      this.view.getWebContents().webContents.session.cookies.get({url: url}, (error, cookies) => {
        console.log(error, cookies)
        let cookieStr = ''
        for (let item in cookies) {
          cookieStr += cookies[item]['name'] + '=' + cookies[item]['value'] + '; '
        }
        console.log(cookieStr)
        let self = this
        this.$http.post(
          self.$db.get('dev_config').cookieUploadUrl, {
            source: self.source,
            username: self.username,
            cookie_str: cookieStr
          })
          .then(function (response) {
            if (response.data.code === 200) {
              self.$message.success(response.data.msg)
            } else {
              self.$message.error(response.data.msg)
            }
          })
      })
    },
    exchangeDisplayView () {
      let middle
      middle = this.webview_place_1
      this.webview_place_1 = this.webview_place_2
      this.webview_place_2 = middle
    },
    goBackWebView () {
      if (this.isBlank) {
        this.mobile = ''
        this.trackId = ''
        this.resumeExtId = ''
        this.resourceType = ''
        this.message = '初始化完成'
        this.crm_resume_id = ''
        this.can_download = false
        this.can_distribute = false
        this.isBlank = false
        this.exchangeDisplayView()
      } else {
        if (this.view.canGoBack()) {
          this.view.goBack()
        } else {
          this.$message.warning('无法后退.')
        }
      }
    },
    reloadWebView () {
      if (this.isBlank) {
        this.view2.reload()
      } else {
        this.view.reload()
      }
    },
    testWebView () {
      this.view.send('hideDownloadButton')
      this.view.send('getPageContent')
    },
    executeSaveResume () {
      console.log('测试：' + this.trackId)
      this.message = '开始执行唤醒操作'
      let self = this
      var i = 1
      let _interval = setInterval(async function () {
        console.log(_interval, i)
        try {
          let response = await api.checkAwake({
            trackId: self.trackId,
            source: self.common_setting.id
          })
          if (response.code === 0) {
            if (i >= 10) {
              self.message = '唤醒超时了，请刷新页面重新尝试'
              clearInterval(_interval)
            } else {
              i++
            }
          } else if (response.code === 200) {
            console.log('唤醒成功')
            await self.executeAwakeSuccess(response.data)
            clearInterval(_interval)
          } else if (response.code === 100) {
            try {
              let res2 = await api.checkCrmScore({
                userName: self.user,
                source: self.common_setting.id
              })
              if (res2.error != null) {
                self.message = res2.message
                return
              }
            } catch (error) {
              self.message = error
              console.log(error)
            }
            try {
              let res3 = await api.checkScoreDownload({
                userName: self.user,
                source: self.source
              })
              if (res3.error != null) {
                self.message = res3.message
              } else {
                self.can_download = true
                console.log('唤醒失败')
                self.message = '唤醒失败'
              }
            } catch (error) {
              self.message = error
              console.log(error)
            }
            clearInterval(_interval)
          } else if (response.code === 107) {
            try {
              let res2 = await api.checkCrmScore({
                userName: self.user,
                source: self.common_setting.id
              })
              if (res2.error != null) {
                self.message = res2.message
                return
              }
            } catch (error) {
              self.message = error
              console.log(error)
            }
            try {
              let res3 = await api.checkScoreDownload({
                userName: self.user,
                source: self.source
              })
              if (res3.error != null) {
                self.message = res3.message
              } else {
                self.can_download_lie100 = true
                self.Lie100ResumeDownloadId = response.data
                self.message = '唤醒失败, 在（有本）找到了相匹配的简历'
                console.log('猎100唤醒成功')
              }
            } catch (error) {
              self.message = error
              console.log(error)
            }
            clearInterval(_interval)
          } else {
            console.log('错误的code: ' + response.code)
            clearInterval(_interval)
          }
        } catch (error) {
          console.log('error: ' + error)
          clearInterval(_interval)
        }
      }, 5000)
    },
    async executeAwakeSuccess (info, fromDownload) {
      try {
        this.mobile = info.mobile
        let res1 = await api.checkCrmDistribute({
          mobile: info.mobile
        })
        if (res1.error != null) {
          this.message = res1.message
        } else if (res1.name === '') {
          this.crm_resume_id = res1.resumeId
          console.log('未分配')
        } else {
          this.message = '该简历手机号为（' + info.mobile + '）已分配到（' + res1.name + '）名下'
          console.log('已分配: ' + res1.name)
          return
        }
      } catch (error) {
        this.message = error
        console.log(error)
      }
      try {
        let res2 = await api.checkCrmScore({
          userName: this.user,
          source: this.common_setting.id
        })
        if (res2.error != null) {
          this.message = res2.message
          return
        }
      } catch (error) {
        this.message = error
        console.log(error)
      }
      try {
        let res3 = await api.checkScoreDownload({
          userName: this.user,
          source: this.source
        })
        if (res3.error != null) {
          this.message = res3.message
        } else {
          if (fromDownload) {
            this.message = '下载成功'
          } else {
            this.message = '唤醒成功，请手动点击分配，联系方式为（' + info.name + ' | ' + info.mobile + ' | ' + info.email + '）'
          }
          this.can_distribute = true
        }
        // this.can_distribute = true
      } catch (error) {
        this.message = error
        console.log(error)
      }
    },
    async executeForceCrmDistribute () {
      try {
        api.saveFlow({
          flowNo: this.trackId,
          code: '106',
          message: '开始分配',
          userName: this.user,
          source: this.source,
          resumeId: this.resumeExtId,
          mobile: this.mobile,
          account: this.email,
          distributeSource: ''
        })
        this.$confirm('确认将手机号为（' + this.mobile + '）的简历分配到你的名下么?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(async () => {
          let response = await api.forceCrmDistribute({
            userName: this.user,
            resumeId: this.crm_resume_id
          })
          if (response.code === 200) {
            this.message = '该简历成功分配到你（' + this.user + '）的名下'
            this.can_distribute = false
          } else {
            this.message = response.msg
          }
          console.log(response)
          this.$message({
            type: 'success',
            message: '分配成功!'
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '分配已取消'
          })
        })
      } catch (error) {
        console.log(error)
      }
    },
    executeResumeDownload () {
      this.view2.send('clickDownloadButton')
      api.saveFlow({
        flowNo: this.trackId,
        code: '103',
        message: '开始下载',
        userName: this.user,
        source: this.source,
        resumeId: this.resumeExtId,
        mobile: this.mobile,
        account: this.email,
        distributeSource: ''
      })
      let params = {
        trackId: this.trackId
      }
      this.$db.set(this.resumeExtId, params)
    },
    async executeLie100ResumeDownload () {
      api.saveFlow({
        flowNo: this.trackId,
        code: '103',
        message: '开始下载',
        userName: this.user,
        source: 'LIE_100',
        resumeId: this.Lie100ResumeDownloadId,
        mobile: this.mobile,
        account: this.email,
        distributeSource: this.source
      })
      let res = await api.downloadLie100Resume({
        userName: this.user,
        resumeId: this.Lie100ResumeDownloadId,
        callType: 'CRM_BUY'
      })
      if (res.error != null) {
        this.message = res.message
        this.can_download_lie100 = false
        this.can_download = true
      } else {
        let info = JSON.parse(res)
        api.saveFlow({
          flowNo: this.trackId,
          code: '104',
          message: '下载成功',
          userName: this.user,
          source: 'LIE_100',
          resumeId: this.Lie100ResumeDownloadId,
          mobile: info.mobile,
          account: this.email,
          distributeSource: this.source
        })
        this.message = '从有本下载成功，已分配到你名下，联系方式为（' + info.name + ' | ' + info.mobile + ' | ' + info.email + '）'
        this.can_download_lie100 = false
      }
    },
    match_detail (url) {
      var flag = false
      for (let i in this.common_setting.rule.detail) {
        if (url.indexOf(this.common_setting.rule.detail[i]) >= 0) {
          flag = true
          return flag
        }
      }
      return flag
    },
    match_publish (url) {
      var flag = false
      for (let i in this.common_setting.rule.publish) {
        if (url.indexOf(this.common_setting.rule.publish[i]) >= 0) {
          flag = true
          return flag
        }
      }
      return flag
    },
    initView () {
      const { session } = this.$electron.remote
      // const { session, app } = this.$electron.remote
      // const { shell, session } = require('electron').remote

      const filter = {
        urls: ['*://.*/']
      }
      let ses = session.fromPartition('persist:webviewsession')
      ses.webRequest.onBeforeSendHeaders(filter, (details, callback) => {
        // console.log(details.url)
        if (details.url.indexOf('stats.g.doubleclick.net') >= 1) {
          let response = {cancel: true}
          callback(response)
        } else {
          let response = {cancel: false}
          callback(response)
        }
      })
      ses.clearStorageData({storages: ['cookies']})
      ses.setProxy({
        proxyRules: this.proxy,
        // proxyBypassRules: this.$db.get('dev_config').proxyWhiteList
        // proxyRules: 'http://127.0.0.1:1080',
        proxyBypassRules: 'localhost,morgan-parse.mofanghr.com,morgan-youben.mofanghr.com,morgan-pick.mofanghr.com,morgan-account.mofanghr.com,172.16.25.43,172.16.25.41'
      }, function () {
        console.log('proxy is ready!')
      })
      this.view = document.getElementById('first')
      this.view2 = document.getElementById('second')

      // view 逻辑
      this.view.addEventListener('dom-ready', () => {
        this.mobile = ''
        this.trackId = ''
        this.resumeExtId = ''
        this.resourceType = ''
        this.message = '初始化完成'
        this.crm_resume_id = ''
        this.can_download = false
        this.can_download_lie100 = false
        this.can_distribute = false
        this.Lie100ResumeDownloadId = ''
        this.isBlank = false
        console.log('view1 is ready! ' + this.view.getURL())
        if (process.env.NODE_ENV === 'development') {
          this.view.openDevTools({mode: 'buttom'})
        }
        // const webContents = this.view.getWebContents()
        // webContents.on('new-window', (e, url, frameName, disposition, options) => {
        //   e.preventDefault()
        //   console.log(e, url, frameName, disposition, options)
        //   console.log(this.match_detail(url))
        //   options.close()
        //   e.preventDefault()
        //   if (this.match_detail(url)) {
        //     this.view2.loadURL(url)
        //     let self = this
        //     setTimeout(function () {
        //       self.exchangeDisplayView()
        //     }, 1000)
        //   } else {
        //     this.view.loadURL(url)
        //   }
        // })
      })
      this.view.addEventListener('load-commit', (e) => {
        let currentUrl = this.view.getURL()
        if (this.match_publish(currentUrl)) {
          this.view.stop()
          this.$alert('禁止手动发布职位！', '警告', {
            confirmButtonText: '确定',
            callback: action => {
              this.view.goBack()
            }
          })
        }
      })
      this.view.addEventListener('did-finish-load', (e) => {
      // this.view.addEventListener('load-commit', (e) => {
        this.$message.success('页面加载完毕.')
        const currentUrl = this.view.getURL()
        if (currentUrl.indexOf(this.common_setting.rule.login) >= 0) {
          if (this.source === 'FIVE_ONE') {
            this.view.send('fillLoginBlank', this.username, this.password, this.accountName)
          } else {
            this.view.send('fillLoginBlank', this.username, this.password)
          }
          console.log('自动填充登录表单完毕')
        }
        if (currentUrl.indexOf('rd5.zhaopin.com') >= 0) {
          this.view.executeJavaScript("document.getElementsByClassName('k-button is-primary')[1].style='display: none;'")
        }
      })
      this.view.addEventListener('new-window', (e) => {
        if (this.match_detail(e.url)) {
          this.view2.loadURL(e.url)
          let self = this
          setTimeout(function () {
            self.exchangeDisplayView()
          }, 1000)
        } else {
          this.view.loadURL(e.url)
        }
      })
      // view2 逻辑 用于处理_blank页
      this.view2.addEventListener('dom-ready', () => {
        this.mobile = ''
        this.trackId = ''
        this.resumeExtId = ''
        this.resourceType = ''
        this.message = '初始化完成'
        this.crm_resume_id = ''
        this.can_download = false
        this.can_download_lie100 = false
        this.can_distribute = false
        this.Lie100ResumeDownloadId = ''
        if (process.env.NODE_ENV === 'development') {
          this.view.openDevTools({mode: 'buttom'})
        }
        console.log('view2 is ready! ' + this.view2.getURL())
      })
      this.view2.addEventListener('new-window', (e) => {
        this.isBlank = false
        this.view2.loadURL(e.url)
        // if (this.match_detail(e.url)) {
        //   this.view2.loadURL(e.url)
        //   let self = this
        //   setTimeout(function () {
        //     self.exchangeDisplayView()
        //   }, 1000)
        //   e.preventDefault()
        // } else {
        //   this.view.loadURL(e.url)
        //   e.preventDefault()
        // }
      })
      this.view2.addEventListener('did-finish-load', (e) => {
      // this.view2.addEventListener('load-commit', (e) => {
        this.isBlank = true
        let currentUrl = this.view2.getURL()
        if (this.match_detail(currentUrl)) {
          this.loading = true
          let self = this
          setTimeout(function () {
            self.view2.send('hideDownloadButton')
            self.view2.send('getMobile')
            self.view2.send('getId')
            self.view2.send('getPageContent')
            self.loading = false
          }, 3000)
          console.log('捕捉到一个详情页')
        }
      })
      this.view2.addEventListener('ipc-message', (e) => {
        if (e.channel === 'getId') {
          this.resumeExtId = e.args[0]
          console.log('简历ID:' + this.resumeExtId)
        }
        if (e.channel === 'getMobile') {
          let mobile = e.args[0]
          console.log('手机号: ' + mobile)
          if (mobile === '' | mobile.indexOf('*') >= 0) {
            console.log('0.1的简历')
            this.resourceType = 'CRM_SEARCH'
            this.$db.del(this.resumeExtId)
          } else {
            console.log('0.5的简历')
            this.mobile = mobile
            this.resourceType = 'RESUME_INBOX'
          }
        }

        if (e.channel === 'getPageContent') {
          let params = {
            source: this.source,
            content: e.args[0],
            resourceType: this.resourceType,
            userName: this.user
          }
          if (this.$db.get(this.resumeExtId) !== null) {
            let trackId = this.$db.get(this.resumeExtId).trackId
            api.saveFlow({
              flowNo: trackId,
              code: '104',
              message: '下载成功',
              userName: this.user,
              source: this.source,
              resumeId: this.resumeExtId,
              mobile: this.mobile,
              account: this.email,
              distributeSource: ''
            })
            // this.executeAwakeSuccess(this.mobile, true)
            let self = this
            api.startAwake(params)
              .then((response) => {
                // response为返回的trackID
                console.log(self.mobile)
                if (self.mobile) {
                  self.message = '下载成功，简历将自动分配到你的名下'
                  return ''
                }
              })
            console.log(trackId)
            this.$db.del(this.resumeExtId)
          } else {
            let self = this
            params['userName'] = ''
            let trackId = api.startAwake(params)
              .then((response) => {
                // response为返回的trackID
                console.log(self.mobile)
                if (self.mobile) {
                  self.message = '简历保存成功'
                  return ''
                } else {
                  self.trackId = response
                  self.executeSaveResume()
                }
              })
            console.log(trackId)
          }
        }
      })
      // app.on('web-contents-created', (event, contents) => {
      //   console.log(event)
      //   console.log(contents.getType())
      //   if (contents.getType() === 'remote') {
      //     contents.on('new-window', (event, url) => {
      //       event.preventDefault()
      //       console.log(url)
      //       console.log(this.match_detail(url))
      //       if (this.match_detail(url)) {
      //         this.view2.loadURL(url)
      //         let self = this
      //         setTimeout(function () {
      //           self.exchangeDisplayView()
      //         }, 1000)
      //       } else {
      //         this.view.loadURL(url)
      //       }
      //     })
      //   }
      // })
    }
  },
  mounted: function () {
    // 配置preload路径
    this.user = this.$db.get('user_info').user
    this.email = this.$db.get('user_info').email

    this.source = this.$route.params.source
    if (this.source === '') {
      this.$message.error('页面打开错误')
      return
    }
    if (process.env.NODE_ENV === 'development') {
      this.common_setting = cfg.dev[this.source]
      // this.preload = `file:` + this.$electron.remote.app.getAppPath() + `/dist/electron/static/inject/zhi_lian.js`
    } else {
      this.common_setting = cfg.pro[this.source]
      // this.preload = `file:` + this.$electron.remote.app.getAppPath() + `/dist/electron/static/inject/zhi_lian.js`
    }
    // console.log(this.common_setting)

    this.getAccountInfo()
  }
}
</script>
<style>
.action-list {
  list-style-type: none;
  position: fixed;
  top: 60%;
  right: 40px;
}
.action-list li {
  padding-bottom: 20px;
}

.el-button--primary:focus, .el-button--primary:hover {
    background: #00beff;
    border-color: #00beff;
    color: #fff;
}

.detail-button {
  color: white;
  background:#00beff;
}

#message-box {
  position: fixed;
  width: 100%;
  bottom: 0px;
  padding-bottom: 20px;
}
</style>
