import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('diorite', {
  getVersion: () => ipcRenderer.invoke('get-app-version'),
  getPaths: () => ipcRenderer.invoke('get-paths'),
  showItemInFolder: (path: string) => ipcRenderer.invoke('show-item-in-folder', path),
  platform: process.platform
});
