import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

export function StatusBar() {
  const { currentProject } = useProjectStore();
  const [cache, setCache] = useState<any>(null);
  const [backendOk, setBackendOk] = useState(false);

  useEffect(() => {
    api.getCacheStatus().then(setCache).catch(()=>{});
    fetch('http://127.0.0.1:7331/api/health').then(r=> r.ok ? setBackendOk(true) : setBackendOk(false)).catch(()=> setBackendOk(false));
    const id = setInterval(() => {
      api.getCacheStatus().then(setCache).catch(()=>{});
    }, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="statusbar">
      <span className={`status-dot ${backendOk ? 'ok' : 'down'}`} /> Backend {backendOk ? 'online' : 'offline'} • API :7331 • Editor :7332
      {currentProject && <span> • Project: {currentProject.id} • {currentProject.path}</span>}
      {cache && <span> • Cache: {cache.total_size_mb} MB • {Object.keys(cache.entries).length} categories • Reuse: Java/Gradle/MC/mappings/loaders</span>}
      <span className="spacer" />
      <span>Diorite • Zero-setup Minecraft IDE • Cursor-like experience</span>
    </div>
  )
}
