import { useProjectStore } from '../stores/projectStore';
import { PlayButton } from './PlayButton';
import { Box, Settings, FolderGit2 } from 'lucide-react';

export function TopBar({ onNewProject, onToggleAI, showAI, onOpenSettings }: { onNewProject: () => void, onToggleAI: () => void, showAI: boolean, onOpenSettings?: () => void }) {
  const { currentProject, projects, setCurrentProjectId, currentProjectId } = useProjectStore();

  return (
    <div className="topbar">
      <div className="topbar-left">
        <div className="logo">
          <div className="logo-icon">◧</div>
          <span className="logo-text">Diorite</span>
          <span className="logo-badge">IDE</span>
        </div>

        <div className="project-selector">
          <FolderGit2 size={14} />
          <select value={currentProjectId || ''} onChange={e => setCurrentProjectId(e.target.value || null)}>
            <option value="">Select project</option>
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name} ({p.loader} {p.mc_version})</option>
            ))}
          </select>
        </div>

        <button className="btn secondary" onClick={onNewProject}>+ New Project</button>
      </div>

      <div className="topbar-center">
        {currentProject && <PlayButton projectId={currentProject.id} />}
        {currentProject && (
          <div className="project-meta">
            <span className="meta-chip">{currentProject.loader}</span>
            <span className="meta-chip">{currentProject.mc_version}</span>
            <span className="meta-chip modid">{currentProject.mod_id}</span>
          </div>
        )}
      </div>

      <div className="topbar-right">
        <button className={`btn icon-btn ${showAI ? 'active' : ''}`} onClick={onToggleAI} title="Toggle AI Chat">
          <Box size={16} /> AI
        </button>
        <button className="btn icon-btn" onClick={onOpenSettings} title="Settings">
          <Settings size={16} />
        </button>
      </div>
    </div>
  )
}
