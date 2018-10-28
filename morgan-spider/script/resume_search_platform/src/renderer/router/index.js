import Vue from 'vue'
import Router from 'vue-router'
import Login from '../components/pages/Login'
import Home from '../components/pages/Home'
import Main from '../components/pages/Main'
import Detail from '../components/pages/Detail'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/',
      name: 'index',
      component: Login,
      redirect: '/main'
    },
    {
      path: '/home',
      name: 'home',
      component: Home,
      children: [
        {
          path: '/main',
          name: 'main',
          component: Main
        }
      ]
    },
    {
      path: '/main/detail/:source',
      name: 'detail',
      component: Detail
    },
    {
      path: '*',
      redirect: '/'
    }
  ]
})
