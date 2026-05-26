const { app, BrowserWindow, ipcMain, globalShortcut } = require('electron')
const path = require('path')
const fs = require('fs')
const { exec } = require('child_process')

// Disable all GPU on RPi — fixes GBM/DRM errors
app.commandLine.appendSwitch('disable-gpu')
app.commandLine.appendSwitch('disable-software-rasterizer')
app.disableHardwareAcceleration()

let mainWindow = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 480,
    fullscreen: true,
    frame: false,
    resizable: false,
    // kiosk: true blocks OS on-screen keyboard — keep it disabled
    alwaysOnTop: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // Prefer built dist, fall back to dev server
  const distPath = path.join(__dirname, '../dist/index.html')
  if (fs.existsSync(distPath)) {
    mainWindow.loadFile(distPath)
  } else {
    mainWindow.loadURL('http://localhost:3000')
  }

  mainWindow.on('closed', () => { mainWindow = null })
}

// --- WiFi IPC handlers (call nmcli on Raspberry Pi) ---

ipcMain.handle('scan-wifi', () => {
  return new Promise((resolve, reject) => {
    exec('nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list --rescan yes', (err, stdout) => {
      if (err) { reject(err); return }
      const networks = []
      for (const line of stdout.trim().split('\n')) {
        const parts = line.split(':')
        if (parts.length >= 3 && parts[0]) {
          networks.push({
            ssid: parts[0],
            signal: parseInt(parts[1]) || 0,
            security: parts.slice(2).join(':'),
          })
        }
      }
      // Deduplicate by SSID (keep strongest signal)
      const seen = new Map()
      for (const n of networks) {
        if (!seen.has(n.ssid) || seen.get(n.ssid).signal < n.signal) {
          seen.set(n.ssid, n)
        }
      }
      resolve(Array.from(seen.values()).sort((a, b) => b.signal - a.signal))
    })
  })
})

ipcMain.handle('connect-wifi', (_event, ssid, password) => {
  return new Promise((resolve, reject) => {
    const cmd = password
      ? `nmcli dev wifi connect "${ssid}" password "${password}"`
      : `nmcli dev wifi connect "${ssid}"`
    exec(cmd, (err, stdout) => {
      if (err) { reject(new Error(stdout || err.message)); return }
      resolve({ success: true })
    })
  })
})

ipcMain.handle('wifi-status', () => {
  return new Promise((resolve) => {
    exec('nmcli -t -f ACTIVE,SSID,SIGNAL dev wifi', (err, stdout) => {
      if (err) { resolve({ connected: false }); return }
      for (const line of stdout.trim().split('\n')) {
        const [active, ssid, signal] = line.split(':')
        if (active === 'yes') {
          resolve({ connected: true, ssid, signal: parseInt(signal) || 0 })
          return
        }
      }
      resolve({ connected: false })
    })
  })
})

ipcMain.handle('get-ip', () => {
  return new Promise((resolve) => {
    exec("hostname -I | awk '{print $1}'", (err, stdout) => {
      resolve(err ? 'unknown' : stdout.trim())
    })
  })
})

// App lifecycle
app.whenReady().then(() => {
  createWindow()
  // Ctrl+Q to quit kiosk
  globalShortcut.register('CommandOrControl+Q', () => app.quit())
})

app.on('window-all-closed', () => {
  app.quit()
})

app.on('before-quit', () => {
  // Graceful cleanup
})

app.on('activate', () => {
  if (mainWindow === null) createWindow()
})
