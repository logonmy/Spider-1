function Login (username, password) {
  let self = this
  let url = JSON.parse(localStorage.getItem('dev_config')).loginUrl
  this.$http.post(
    url, {
      userName: username,
      password: password,
      redirectUrl: url,
      isRedirect: false
    })
    .then(function (response) {
      if (response.status === 200) {
        let accessToken = response.data.data.token
        if (accessToken) {
          localStorage.setItem('user_info', JSON.stringify(response.data.data))
          self.$router.push('/accounts')
        } else {
          self.$message.error('登录失败：' + response.data.msg)
          console.log(response.data)
        }
      } else {
        self.$message.error('登录失败')
      }
    })
    .catch(function (error) {
      self.$message.error('登录异常：' + error.message)
    })
}

export default Login
