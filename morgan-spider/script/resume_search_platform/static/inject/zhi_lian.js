// inyector.js// Get the ipcRenderer of electron
const {ipcRenderer} = require('electron')

// Do something according to a request of your mainview
ipcRenderer.on('getPageContent', function () {
  ipcRenderer.sendToHost('getPageContent', getPageContent())
})

ipcRenderer.on('fillLoginBlank', function (e, username, password) {
  document.getElementById('loginName').value = username
  document.getElementById('password').value = password
})

ipcRenderer.on('hideDownloadButton', function () {
  try {
    document.getElementsByClassName('resume-content__button is-download no-print')[0].style = 'display:none;'
    document.getElementsByClassName('k-button resume-actions__button resume-tomb')[0].style = 'display:none;'
  } catch (error) {
    document.getElementById('downloadResumeBtn').style = 'display:none;'
  }
})

ipcRenderer.on('clickDownloadButton', function () {
  try {
    document.getElementsByClassName('resume-content__button is-download no-print')[0].click()
  } catch (error) {
    document.getElementById('downloadResumeBtn').click()
  }
})

function getPageContent () {
  return document.body.innerHTML
}

function getMobile () {
  try {
    let p1 = document.getElementsByClassName('telephone')[0]
    if (p1) {
      return p1.innerText.split('：')[1]
    } else {
      let p2 = document.getElementsByClassName('telephone')[0]
      if (p2) {
        return p2.innerText
      } else {
        let p3 = document.getElementsByClassName('resume-content__mobile-phone')[0].innerText
        if (p3) {
          return p3
        }
      }
    }
  } catch (error) {
    return ''
  }
}

ipcRenderer.on('getMobile', function () {
  ipcRenderer.sendToHost('getMobile', getMobile())
})

function getId () {
  try {
    return document.getElementsByClassName('resume-content--letter-spacing resume-tomb')[0].innerHTML.replace('ID：', '')
  } catch (error) {
    if (document.getElementsByTagName('span')[1]) {
      return document.getElementsByTagName('span')[1].innerHTML
    } else {
      return ''
    }
  }
}

ipcRenderer.on('getId', function () {
  ipcRenderer.sendToHost('getId', getId())
})
