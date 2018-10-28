<style>
.el-header {
  background-color: #ffffff;;
}
.user-info {
  color: white;
  text-align: right;
  padding-top: 8px;  
}
.line {
  border:1px solid rgba(178,178,178,0.50);
  width:-1px;
  height:10px;
}
.user-info li {
  display:inline-block;
  list-style:none;
  padding-left: 5px; 
}
</style>

<template>
  <el-header>
    <div class="user-info">
      <el-col :span="6" :offset="17">
        <ul>
          <li>
            <div style="color: #bbbbbb;">
                <i class="el-icon-mf-wode iconfont"></i>
                <span style="color: #333333;">{{ name }}</span>
            </div>
        </li>
        <li>
          <div class="line"></div>
        </li>
        <li>
          <div style="color: #bbbbbb;" @click="logout()">
            <i class="el-icon-mf-icon iconfont"></i>
            <span style="color: #333333;">退出</span>
          </div>
        </li>
        </ul>
      </el-col>
    </div>
  </el-header>
</template>

<script>
export default {
  name: 'my-header',
  data () {
    return {
      name: ''
    }
  },
  methods: {
    logout () {
      this.$db.set('user_info', '')
      this.$router.push('/login')
    }
  },
  mounted: function () {
    this.name = this.$db.get('user_info').user
  }
}
</script>

