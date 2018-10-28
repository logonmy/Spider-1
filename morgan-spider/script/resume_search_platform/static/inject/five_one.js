// inyector.js// Get the ipcRenderer of electron
const {ipcRenderer} = require('electron')

// Do something according to a request of your mainview
ipcRenderer.on('getPageContent', function () {
  ipcRenderer.sendToHost('getPageContent', getPageContent())
})

ipcRenderer.on('fillLoginBlank', function (e, username, password, accountName) {
  document.getElementById('txtUserNameCN').value = username
  document.getElementById('txtPasswordCN').value = password
  document.getElementById('txtMemberNameCN').value = accountName
})

ipcRenderer.on('hideDownloadButton', function () {
  document.getElementById('UndownloadLink').style = 'display:none;'
  document.getElementById('RersumeView_btnDownLoad_link').style = 'display:none;'
  document.getElementsByClassName('rself_listoff')[1].style = 'display:none;'
})

ipcRenderer.on('clickDownloadButton', function () {
  document.getElementById('UndownloadLink').click()
})

function getPageContent () {
  return document.body.innerHTML
}

function getMobile () {
  try {
    let table = document.getElementsByClassName('infr')[0]
    let tr = table.getElementsByTagName('tr')[1]
    let td = tr.getElementsByTagName('td')[1]
    let mobile = td.innerText.replace(' ', '')
    return mobile
  } catch (error) {
    return ''
  }
}

ipcRenderer.on('getMobile', function () {
  ipcRenderer.sendToHost('getMobile', getMobile())
})

function getId () {
  try {
    return document.getElementById('hidUserID').value
  } catch (error) {
    return ''
  }
}

ipcRenderer.on('getId', function () {
  ipcRenderer.sendToHost('getId', getId())
})
