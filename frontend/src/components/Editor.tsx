import { useEffect, useState } from 'react';
import EditorMonaco from '@monaco-editor/react';
import { useEditorStore } from '../stores/editorStore';
import { useProjectStore } from '../stores/projectStore';
import { api } from '../api/client';
import { X, Circle } from 'lucide-react';

export function Editor() {
  const { openFiles, activeFilePath, setActiveFile, updateFileContent, markDirty, closeFile } = useEditorStore();
  const { currentProjectId } = useProjectStore();
  const activeFile = openFiles.find(f => f.path === activeFilePath);
  const [saving, setSaving] = useState(false);

  const saveCurrent = async () => {
    if (!activeFile || !currentProjectId) return;
    setSaving(true);
    try {
      await api.saveFile(currentProjectId, activeFile.path, activeFile.content);
      markDirty(activeFile.path, false);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveCurrent();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [activeFile, currentProjectId]);

  // Auto save if setting enabled (we'll auto save after 1s debounce)
  useEffect(() => {
    if (!activeFile?.dirty) return;
    const id = setTimeout(() => saveCurrent(), 1000);
    return () => clearTimeout(id);
  }, [activeFile?.content]);

  if (!currentProjectId) {
    return <div className="editor empty">Create a project to start coding. Zero setup — templates include Gradle, Java, mappings.</div>;
  }

  if (openFiles.length === 0) {
    return <div className="editor empty">Open a file from the explorer. Try src/main/java/.../ExampleMod.java</div>
  }

  return (
    <div className="editor-container">
      <div className="tabs">
        {openFiles.map(f => (
          <div key={f.path} className={`tab ${f.path === activeFilePath ? 'active' : ''}`} onClick={() => setActiveFile(f.path)}>
            <span className="tab-name">{f.path.split('/').pop()}</span>
            {f.dirty && <Circle size={8} fill="#5ad" className="dirty" />}
            <button className="tab-close" onClick={(e) => { e.stopPropagation(); closeFile(f.path); }}>
              <X size={12} />
            </button>
          </div>
        ))}
      </div>
      <div className="monaco-wrapper">
        {activeFile && (
          <EditorMonaco
            height="100%"
            language={activeFile.language}
            value={activeFile.content}
            theme="vs-dark"
            onChange={(val) => {
              if (val !== undefined) updateFileContent(activeFile.path, val, true);
            }}
            options={{
              fontSize: 14,
              fontFamily: 'JetBrains Mono, monospace',
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 4,
              wordWrap: 'on',
            }}
          />
        )}
      </div>
      <div className="editor-status">
        <span>{activeFile?.path}</span>
        <span>{saving ? 'Saving...' : activeFile?.dirty ? 'Unsaved' : 'Saved'}</span>
      </div>
    </div>
  )
}
