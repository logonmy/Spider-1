<template>
  <el-container>
    <el-container>
      <my-sidebar></my-sidebar>
      <el-container class="is-vertical">
        <my-header></my-header>    
        <el-main style="background-color: #F2F5FB; height: 570px;">
          <router-view/>
        </el-main>
        <!-- <el-footer>Footer</el-footer> -->
      </el-container>
    </el-container>
  </el-container>
</template>

<script>
import Header from '@/components/Header'
import SideBar from '@/components/SideBar'
export default {
  components: {
    'my-header': Header,
    'my-sidebar': SideBar
  }
}
</script>
