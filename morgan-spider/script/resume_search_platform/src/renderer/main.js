import Vue from 'vue'
import App from './App'
import router from './router'
import store from './store'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
// import 'font-awesome/css/font-awesome.min.css'
import './assets/icon/iconfont.css'
import Login from './utils/common'
import axios from './utils/http'
import Db from './utils/db'
// import fs from 'fs'
// import path from 'path'

Vue.use(ElementUI)

if (!process.env.IS_WEB) Vue.use(require('vue-electron'))

Vue.config.productionTip = false

/* init localstore */
Vue.prototype.$db = Db
// Db.init()

Vue.prototype.$http = axios
Vue.prototype.$login = Login

router.beforeEach((to, from, next) => {
  let userInfo = Db.get('user_info')
  if (!userInfo && to.name !== 'login') {
    next('/login')
  } else {
    next()
  }
})

/* eslint-disable no-new */
new Vue({
  components: { App },
  router,
  store,
  template: '<App/>'
}).$mount('#app')
