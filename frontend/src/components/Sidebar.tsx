import { ProjectExplorer } from './ProjectExplorer';
import { ScaffoldMenu } from './ScaffoldMenu';

export function Sidebar({ onTreeRefresh }: { onTreeRefresh: () => void }) {
  return (
    <div className="sidebar">
      <ProjectExplorer />
      <div className="sidebar-divider" />
      <ScaffoldMenu onCreated={onTreeRefresh} />
    </div>
  )
}
