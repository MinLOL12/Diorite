import { useEffect, useRef } from 'react';
import { useMultiWebSocket } from '../hooks/useWebSocket';
import { useProjectStore } from '../stores/projectStore';

export function Terminal() {
  const { currentProjectId } = useProjectStore();
  const { allLogs, clear, connected } = useMultiWebSocket(currentProjectId);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [allLogs]);

  return (
    <div className="terminal">
      <div className="terminal-header">
        <span>CONSOLE • LIVE LOGS {connected ? '●' : '○'}</span>
        <div className="terminal-actions">
          <button onClick={clear}>Clear</button>
        </div>
      </div>
      <div className="terminal-body" ref={ref}>
        {allLogs.length === 0 && <div className="log-line muted">No logs yet. Press Play to build and launch Minecraft — logs stream live via WebSockets.</div>}
        {allLogs.slice(-1000).map((log, i) => (
          <div key={i} className={`log-line ${log.is_error ? 'error' : ''} ${log.type}`}>
            <span className="log-type">[{log.type}]</span>
            <span className="log-content">{log.line || log.clean || JSON.stringify(log)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
