<style>
.login {
  margin-top: 122px;
  background:#ffffff;
  box-shadow:0 2px 10px 0 rgba(204,204,204,0.50);
  border-radius:4px;
  width:332px;
  height:400px;
}
.login-title {
  margin-top: 30px;
  font-family: MicrosoftYaHei;
  font-size:22px;
  color:#333333;
  letter-spacing:0;
  text-align:center;
  line-height:24px;
}
.el-input .el-input__inner {
  border: 0px;
  font-family: MicrosoftYaHei;
  font-size: 14px;
  padding-left: 0px;
  border-style: initial; 
  border-color: initial; 
  border-image: initial;
}

.el-form-item {
    margin-bottom: 0px !important;
}

.hr {
  background:#eeeeee;
  width:272px;
  height:1px;
  padding-left: 15px;
}

.el-button--primary:focus, .el-button--primary:hover {
    background: #00beff;
    border-color: #00beff;
    color: #fff;
}

.login-button {
  font-size: 16px;
  color: white;
  background:#00beff;
  border-radius:2px;
  width:272px;
  height:51px;
}
.login-error {
  margin-top: 10px;
  font-family:MicrosoftYaHei;
  font-size:14px;
  color:#f25751;
  letter-spacing:0;
  line-height:14px;
  text-align:left;
}
</style>


<template>
    <el-row>
        <el-col :span="8" :offset="8">
            <el-card  class="login">
                <el-form>
                    <div class="login-title">系统登录</div>
                    <el-form-item style="margin-top: 50px;">
                      <el-input class="login-input" type="text" v-model="email" placeholder="用户名"></el-input>
                    </el-form-item>
                    <div class="hr"></div>
                    <el-form-item style="margin-top: 30px;">
                      <el-input class="login-input" type="password" v-model="password" placeholder="密码"></el-input>
                    </el-form-item>
                    <div class="hr"></div>
                    <div v-if="error" class="login-error">{{ error }}</div>
                    <el-form-item style="margin-top: 40px;">
                      <el-button class="login-button" type="primary" style="width: 100%" @click="login">登录</el-button>
                    </el-form-item>
                </el-form>
            </el-card>
        </el-col>
    </el-row>
</template>

<script>
import * as apiPath from '../../utils/api-path.js'
export default {
  name: 'login',
  data () {
    return {
      email: '',
      password: '',
      error: ''
    }
  },
  methods: {
    login () {
      let self = this
      this.$http({
        method: 'post',
        url: apiPath.morganAccountUrl + '/crm/login.json',
        data: {
          username: self.email,
          password: self.password
        }
      }).then((response) => {
        if (response.data.code === 200) {
          let data = JSON.parse(response.data.data)
          self.$db.set('user_info', {
            'user': data.data.name,
            'email': self.email
          })
          self.$router.push('/main')
        } else {
          self.error = '用户名或密码错误'
        }
      })
    }
  }
}
</script>
