<style>
.item-box {
  width: 302px;
  height: 171px;
  margin-bottom: 20px;
  text-align: center
}
</style>


<template>
  <el-row :gutter="12" style="background-color: white; padding: 20px; height: 530px;" justify="space-around">
    <el-col :span="24" style="padding-left: 30px; padding-right: 30px;">
      <h1>简历下载渠道</h1>
      <el-row>
      <el-col :span="12">
        <el-card class="item-box" shadow="hover" @click.native="loadDetail('ZHI_LIAN')">
          <img :src="zhi_lian_log">
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="item-box" shadow="hover" @click.native="loadDetail('FIVE_ONE')">
          <img :src="five_one_log">
        </el-card>
      </el-col>
      </el-row>
      <el-row>
      <el-col :span="12" style="margin-top: 20px;">
        <el-card class="item-box" shadow="hover">
          <div style="padding-top: 50px; color: #999999">敬请期待...</div>
        </el-card>
      </el-col>
      </el-row>
      <!-- <el-col :span="12">
        <el-card shadow="hover" @click.native="loadDetail('LIE_100')">
          猎100
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover" @click.native="loadDetail('LIE_PIN')">
          猎聘
        </el-card>
      </el-col> -->
    </el-col> 
  </el-row>
</template>

<script>
export default {
  data () {
    return {
      map: {},
      zhi_lian_log: require('../../assets/img/logo_zhilian.png'),
      five_one_log: require('../../assets/img/logo_51.png')
    }
  },
  methods: {
    startNewWindow (source) {
      const url = process.env.NODE_ENV === 'development'
        ? `http://localhost:9080`
        : 'app://-'
      const {BrowserWindow} = this.$electron.remote
      // let currentWin = this.$electron.remote.getCurrentWindow()
      let win = new BrowserWindow({
        width: 1024,
        height: 798,
        // parent: currentWin,
        title: '简历搜索平台 | ' + source
      })
      // this.$router.push({name: 'detail', params: {id: accountId}})
      win.loadURL(url + '/#/main/detail/' + source)
      win.maximize()
      this.map[source] = win.id
      console.log(this.map)
    },
    loadDetail (source) {
      const {BrowserWindow} = this.$electron.remote
      // 通过字典控制单渠道仅能打开一个窗口
      if (this.map[source] !== undefined) {
        console.log(this.map[source])
        let win = BrowserWindow.fromId(this.map[source])
        // 当窗口关闭时，重新创建窗口，更新字典中win.id
        if (win === null) {
          this.startNewWindow(source)
        } else {
          win.focus()
        }
      } else {
        this.startNewWindow(source)
      }
    }
  }
}
</script>
