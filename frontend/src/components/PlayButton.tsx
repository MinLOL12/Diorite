import { useState } from 'react';
import { api } from '../api/client';
import { Play, Square, Loader2 } from 'lucide-react';

export function PlayButton({ projectId }: { projectId: string }) {
  const [state, setState] = useState<'idle' | 'building' | 'running'>('idle');

  const handlePlay = async () => {
    if (state !== 'idle') return;
    setState('building');
    try {
      // Trigger run which does build + launch
      await api.runProject(projectId, ['runClient']);
      setState('running');
      // After some time, go back to idle? Actually running state until stopped
      setTimeout(() => setState('idle'), 1000);
    } catch (e) {
      console.error(e);
      setState('idle');
    }
  };

  const handleStop = async () => {
    try {
      await api.stopProcess(projectId);
      setState('idle');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="play-area">
      {state === 'idle' && (
        <button className="btn play-btn" onClick={handlePlay}>
          <Play size={18} fill="white" /> Play
        </button>
      )}
      {state === 'building' && (
        <button className="btn play-btn building" disabled>
          <Loader2 size={18} className="spin" /> Building...
        </button>
      )}
      {state === 'running' && (
        <button className="btn play-btn running" onClick={handleStop}>
          <Square size={16} fill="white" /> Stop
        </button>
      )}
      <button className="btn icon-btn small" onClick={handleStop} title="Stop Minecraft">
        <Square size={14} />
      </button>
    </div>
  )
}
