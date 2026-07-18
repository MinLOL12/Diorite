import { useEffect, useState } from 'react';
import { TopBar } from './components/TopBar';
import { Sidebar } from './components/Sidebar';
import { Editor } from './components/Editor';
import { Terminal } from './components/Terminal';
import { NewProjectModal } from './components/NewProjectModal';
import { AIChatPanel } from './components/AIChatPanel';
import { StatusBar } from './components/StatusBar';
import { useProjectStore } from './stores/projectStore';
import { api } from './api/client';
import './App.css';

function App() {
  const { setProjects, setCurrentProjectId, currentProjectId, setCurrentProject, projects } = useProjectStore();
  const [showNewProject, setShowNewProject] = useState(false);
  const [showAI, setShowAI] = useState(true);
  const [treeKey, setTreeKey] = useState(0);

  const loadProjects = async () => {
    try {
      const projs = await api.listProjects();
      setProjects(projs);
      if (currentProjectId) {
        const cur = projs.find(p => p.id === currentProjectId);
        if (cur) setCurrentProject(cur);
      } else if (projs.length > 0) {
        setCurrentProjectId(projs[0].id);
        setCurrentProject(projs[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (currentProjectId) {
      const p = projects.find(pr => pr.id === currentProjectId);
      if (p) setCurrentProject(p);
      // Also fetch full
      api.getProject(currentProjectId).then(setCurrentProject).catch(()=>{});
    }
  }, [currentProjectId, projects]);

  return (
    <div className="app">
      <TopBar
        onNewProject={() => setShowNewProject(true)}
        onToggleAI={() => setShowAI(!showAI)}
        showAI={showAI}
      />

      <div className="main">
        <div className="left">
          <Sidebar key={treeKey} onTreeRefresh={() => setTreeKey(k => k+1)} />
        </div>

        <div className="center">
          <div className="editor-area">
            <Editor />
          </div>
          <div className="terminal-area">
            <Terminal />
          </div>
        </div>

        {showAI && (
          <div className="right">
            <AIChatPanel />
          </div>
        )}
      </div>

      <StatusBar />

      <NewProjectModal
        open={showNewProject}
        onClose={() => setShowNewProject(false)}
        onCreated={(p) => {
          setProjects([p, ...projects]);
          setCurrentProjectId(p.id);
          setCurrentProject(p);
          setTreeKey(k=>k+1);
        }}
      />
    </div>
  )
}

export default App;
