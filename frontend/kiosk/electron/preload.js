const { contextBridge, ipcRenderer } = require('electron')

// Expose safe IPC methods to renderer via window.electron
contextBridge.exposeInMainWorld('electron', {
  // WiFi management via nmcli
  scanWifi: () => ipcRenderer.invoke('scan-wifi'),
  connectWifi: (ssid, password) => ipcRenderer.invoke('connect-wifi', ssid, password),
  wifiStatus: () => ipcRenderer.invoke('wifi-status'),
  getIp: () => ipcRenderer.invoke('get-ip'),

  // App lifecycle
  quit: () => ipcRenderer.send('app-quit'),
})
