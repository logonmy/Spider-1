'use strict'

import { app, BrowserWindow, Menu, dialog } from 'electron'

const serve = require('electron-serve')
const packageInfo = require('../../package.json')
/**
 * Set `__static` path to static files in production
 * https://simulatedgreg.gitbooks.io/electron-vue/content/en/using-static-assets.html
 */
if (process.env.NODE_ENV !== 'development') {
  global.__static = require('path').join(__dirname, '/static').replace(/\\/g, '\\\\')
}

let mainWindow
const winURL = process.env.NODE_ENV === 'development'
  ? `http://localhost:9080`
  // : `file://${__dirname}/index.html`
  : serve({directory: __dirname})

function createWindow () {
  /**
   * Initial window options
   */

  mainWindow = new BrowserWindow({
    height: 656,
    width: 999,
    title: '简历搜索平台',
    resizable: false
  })
  // BrowserWindow.addDevToolsExtension('/home/wuyue/Project/morgan-v3/morgan-spider/script/ResumeSearchPlugin')

  const template = [
    {
      label: '菜单',
      submenu: [
        {
          label: '开发者工具',
          accelerator: (function () {
            if (process.platform === 'darwin') {
              return 'Alt+Command+I'
            } else {
              return 'Ctrl+Shift+I'
            }
          })(),
          click: function (item, focusedWindow) {
            if (focusedWindow) {
              focusedWindow.toggleDevTools()
            }
          }
        },
        // {
        //   label: '登录页', role: 'reload'
        // },
        {
          label: '刷新', role: 'reload'
        }
      ]
    },
    {
      label: '关于',
      click: function () {
        dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: '关于',
          message: '简历搜索平台',
          detail: '版本： v' + packageInfo.version + '\n维护： 数据研究部'
        })
      }
    }
  ]
  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
  if (process.env.NODE_ENV !== 'development') {
    winURL(mainWindow)
  } else {
    mainWindow.loadURL(winURL)
    console.log(winURL)
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

const shouldQuit = app.makeSingleInstance(
  (commandLine, workingDirectory) => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore()
      }
      mainWindow.focus()
    }
  })

if (shouldQuit) {
  app.quit()
  // return // 没有这句话，会报错！
}

app.on('ready', createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})

/**
 * Auto Updater
 *
 * Uncomment the following code below and install `electron-updater` to
 * support auto updating. Code Signing with a valid certificate is required.
 * https://simulatedgreg.gitbooks.io/electron-vue/content/en/using-electron-builder.html#auto-updating
 */

/*
import { autoUpdater } from 'electron-updater'

autoUpdater.on('update-downloaded', () => {
  autoUpdater.quitAndInstall()
})

app.on('ready', () => {
  if (process.env.NODE_ENV === 'production') autoUpdater.checkForUpdates()
})
 */
