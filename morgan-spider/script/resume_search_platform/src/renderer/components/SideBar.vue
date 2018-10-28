<template>
  <el-aside :class="isCollapse?'menu-collapsed':'menu-expanded'">
    <el-menu class="logo">
      <li>
        <slot>
          <img :src="logo" style="padding-top: 20px;">
        </slot>
      </li>
      <li>
        <slot v-if="isCollapse"></slot>
        <slot v-else>
          <div style="display:table-cell;vertical-align:middle;text-align:center; padding-bottom: 2px;"><span>简历搜索平台</span></div>
        </slot>
      </li>
    </el-menu>
    <el-menu class="sidebar" default-active="1" @open="handleOpen" @close="handleClose" :collapse="isCollapse" router>
      <el-menu-item index="1" :route="{path: '/main'}">
        <i class="el-icon-mf-fenlei iconfont"></i>
        <span slot="title">操作中心</span>
      </el-menu-item>
      <!-- <el-submenu index="2">
        <template slot="title">
          <i class="el-icon-location"></i>
          <span slot="title">资源管理</span>
        </template>
        <el-menu-item-group>
          <el-menu-item index="2-1">地址词典</el-menu-item>
          <el-menu-item index="2-2">职位模板</el-menu-item>
          <el-menu-item index="2-3">小职能集合</el-menu-item>
        </el-menu-item-group>
      </el-submenu> -->

      <!-- <el-menu-item index="3" :route="{path: '/accounts'}">
        <i class="el-icon-document"></i>
        <span slot="title">日志管理</span>
      </el-menu-item>
      <el-menu-item index="4" :route="{path: '/accounts'}">
        <i class="el-icon-fa fa-calendar-minus-o"></i>
        <span slot="title">职位刷新记录</span>
      </el-menu-item>
      <el-menu-item index="5" :route="{path: '/accounts'}">
        <i class="el-icon-fa fa-folder-open"></i>
        <span slot="title">资源统计</span>
      </el-menu-item>
      <el-menu-item index="6" :route="{path: '/accounts'}">
        <i class="el-icon-fa fa-eye"></i>
        <span slot="title">发布统计</span>
      </el-menu-item> -->
      <!-- <el-menu-item index="7" :route="{path: '#'}">
        <i class="el-icon iconfont icon-gerenzhongxin"></i>
        <span slot="title">设置</span>
      </el-menu-item> -->
<!--      <el-menu-item index="7" :route="{path: '/test'}">
        <i class="el-icon-setting"></i>
        <span slot="title">测试</span>
      </el-menu-item>-->
      <el-menu-item index="" @click="isCollapse=!isCollapse" class="test">
        <i v-if='isCollapse' class="el-icon-mf-jiantouyou iconfont"></i>
        <i v-else class="el-icon-mf-fanhui iconfont"></i>
        <span v-if='isCollapse' slot="title">展开</span>
        <span v-else slot="title">收起</span>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script>
export default {
  name: 'my-sidebar',
  data () {
    return {
      isCollapse: false,
      logo: require('../assets/img/logo.png')
    }
  },
  methods: {
    handleOpen (key, keyPath) {
      console.log(key, keyPath)
    },
    handleClose (key, keyPath) {
      console.log(key, keyPath)
    }
  }
}
</script>

<style>
  .menu-collapsed {
    padding-left: 0px;
    width: 65px !important;
  }
  .menu-expanded {
    padding-left: 0px;
    width: 190px !important;
  }
  .logo {
    font-size: 16px;
    padding-left: 15px !important;
    padding-right: 15px !important;
    height: 60px;
    background-color: #00beff !important;
    color: white
  }
  .logo li {
    display:inline-block;
    list-style:none;
    padding-left: 5px; 
  }
  el-menu-item i {
    font-size: 18px !important;
  }
</style>
