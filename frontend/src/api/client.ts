const API_BASE = ((import.meta as any).env?.VITE_API_URL) || 'http://127.0.0.1:7331';

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  listProjects: () => request<any[]>('/api/projects'),
  createProject: (data: any) => request<any>('/api/projects', { method: 'POST', body: JSON.stringify(data) }),
  getProject: (id: string) => request<any>(`/api/projects/${id}`),
  deleteProject: (id: string) => request<any>(`/api/projects/${id}`, { method: 'DELETE' }),
  listTemplates: () => request<any[]>('/api/templates'),
  getTree: (projectId: string) => request<any>(`/api/projects/${projectId}/files/tree`),
  listFiles: (projectId: string, path: string = '') => request<any[]>(`/api/projects/${projectId}/files?path=${encodeURIComponent(path)}`),
  readFile: (projectId: string, path: string) => request<any>(`/api/projects/${projectId}/files/content?path=${encodeURIComponent(path)}`),
  saveFile: (projectId: string, path: string, content: string) => request<any>(`/api/projects/${projectId}/files/save`, { method: 'POST', body: JSON.stringify({ path, content }) }),
  createFile: (projectId: string, path: string, isDir: boolean, content?: string) => request<any>(`/api/projects/${projectId}/files/create`, { method: 'POST', body: JSON.stringify({ path, is_directory: isDir, content }) }),
  renameFile: (projectId: string, oldPath: string, newPath: string) => request<any>(`/api/projects/${projectId}/files/rename`, { method: 'POST', body: JSON.stringify({ old_path: oldPath, new_path: newPath }) }),
  deleteFile: (projectId: string, path: string) => request<any>(`/api/projects/${projectId}/files?path=${encodeURIComponent(path)}`, { method: 'DELETE' }),
  buildProject: (projectId: string, tasks?: string[]) => request<any>(`/api/projects/${projectId}/build`, { method: 'POST', body: JSON.stringify({ tasks }) }),
  runProject: (projectId: string, tasks?: string[]) => request<any>(`/api/projects/${projectId}/run`, { method: 'POST', body: JSON.stringify({ tasks, stop_existing: true }) }),
  stopProcess: (projectId: string) => request<any>(`/api/projects/${projectId}/process/stop`, { method: 'POST' }),
  listProcesses: () => request<any[]>('/api/processes'),
  getCacheStatus: () => request<any>('/api/cache/status'),
  getSettings: () => request<any>('/api/settings'),
  updateSettings: (s: any) => request<any>('/api/settings', { method: 'PUT', body: JSON.stringify(s) }),
  aiContext: (data: any) => request<any>('/api/ai/context', { method: 'POST', body: JSON.stringify(data) }),
  aiChat: (data: any) => request<any>('/api/ai/chat', { method: 'POST', body: JSON.stringify(data) }),
  scaffold: (projectId: string, type: string, data: any) => request<any>(`/api/projects/${projectId}/scaffold/${type}`, { method: 'POST', body: JSON.stringify(data) }),
};

export function getWsUrl(channel: string, projectId: string) {
  const base = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://');
  if (projectId === 'global') return `${base}/ws/global`;
  return `${base}/ws/${channel}/${projectId}`;
}
