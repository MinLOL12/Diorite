import { useEffect, useRef, useState, useCallback } from 'react';
import { getWsUrl } from '../api/client';

export interface LogEntry {
  type: string;
  line?: string;
  clean?: string;
  is_error?: boolean;
  task?: string;
  exit_code?: number;
  success?: boolean;
  projectId?: string;
  timestamp?: number;
  source?: string;
  [key: string]: any;
}

export function useWebSocket(channel: string, projectId: string | null, onMessage?: (data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const connect = useCallback(() => {
    if (!projectId) return;
    // For global, projectId is "global" string inside getWsUrl handling
    const url = projectId === 'global' ? getWsUrl(channel, 'global') : getWsUrl(channel, projectId);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // reconnect after 2s
      setTimeout(() => {
        if (wsRef.current === ws) connect();
      }, 2000);
    };
    ws.onerror = () => {
      setConnected(false);
    };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        const entry = { ...data, timestamp: Date.now() };
        setLogs(prev => {
          const next = [...prev, entry];
          // keep only last 5000
          if (next.length > 5000) return next.slice(-5000);
          return next;
        });
        if (onMessage) onMessage(data);
      } catch {
        // plain text?
        const entry: LogEntry = { type: 'stdout', line: ev.data, timestamp: Date.now() };
        setLogs(prev => [...prev.slice(-4999), entry]);
        if (onMessage) onMessage(entry);
      }
    };
  }, [channel, projectId, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const clear = useCallback(() => setLogs([]), []);
  const send = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  return { connected, logs, clear, send, ws: wsRef.current };
}

export function useMultiWebSocket(projectId: string | null) {
  const [buildLogs, setBuildLogs] = useState<LogEntry[]>([]);
  const [mcLogs, setMcLogs] = useState<LogEntry[]>([]);
  const [allLogs, setAllLogs] = useState<LogEntry[]>([]);

  // We'll use single logs channel that gets both build and process logs as backend broadcasts to logs:{projectId}
  const { logs, connected, clear } = useWebSocket('logs', projectId);

  useEffect(() => {
    setAllLogs(logs);
    // split heuristics
    const builds = logs.filter(l => l.type === 'build_start' || l.type === 'build_end' || l.type === 'progress' || (l.line && l.line.includes('> Task')));
    const mcs = logs.filter(l => l.source === 'minecraft' || (l.line && (l.line.includes('[Client]') || l.line.includes('Minecraft'))));
    setBuildLogs(builds);
    setMcLogs(mcs);
  }, [logs]);

  return { allLogs, buildLogs, mcLogs, connected, clear, rawLogs: logs };
}
