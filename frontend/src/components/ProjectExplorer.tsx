import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useProjectStore } from '../stores/projectStore';
import { useEditorStore } from '../stores/editorStore';
import { ChevronRight, ChevronDown, File, Folder, FilePlus, FolderPlus } from 'lucide-react';

interface TreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: TreeNode[];
  extension?: string;
}

function FileNode({ node, depth = 0, onFileClick }: { node: TreeNode, depth?: number, onFileClick: (path: string) => void }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isDir = node.type === 'directory';

  return (
    <div className="file-node">
      <div
        className={`file-row ${isDir ? 'dir' : 'file'}`}
        style={{ paddingLeft: 8 + depth * 16 }}
        onClick={() => {
          if (isDir) setExpanded(!expanded);
          else onFileClick(node.path);
        }}
      >
        {isDir ? (
          <span className="chevron">{expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
        ) : <span className="chevron empty" />}
        {isDir ? <Folder size={14} /> : <File size={14} />}
        <span className="file-name">{node.name}</span>
      </div>
      {isDir && expanded && node.children && (
        <div className="children">
          {node.children.map(child => (
            <FileNode key={child.path || child.name} node={child} depth={depth+1} onFileClick={onFileClick} />
          ))}
        </div>
      )}
    </div>
  )
}

export function ProjectExplorer() {
  const { currentProjectId } = useProjectStore();
  const { addOpenFile, setRecent } = useEditorStore();
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [contextPath, setContextPath] = useState<string>('');

  const loadTree = async () => {
    if (!currentProjectId) return;
    setLoading(true);
    try {
      const data = await api.getTree(currentProjectId);
      setTree(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTree();
    if (currentProjectId) {
      api.readFile(currentProjectId, '').catch(()=>{}); // warmup
      // load recent
      fetch(`http://127.0.0.1:7331/api/projects/${currentProjectId}/files/recent`).then(r=>r.json()).then(d=> setRecent(d.recent || [])).catch(()=>{});
    }
  }, [currentProjectId]);

  const handleFileClick = async (path: string) => {
    if (!currentProjectId) return;
    try {
      const data = await api.readFile(currentProjectId, path);
      if (!data.is_binary) {
        addOpenFile({ path, content: data.content, dirty: false, language: 'java' });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateFile = async (isDir: boolean) => {
    if (!currentProjectId) return;
    const name = prompt(`New ${isDir ? 'folder' : 'file'} path (relative):`);
    if (!name) return;
    try {
      await api.createFile(currentProjectId, name, isDir, isDir ? '' : '// new file\n');
      loadTree();
    } catch (e:any) {
      alert(e.message);
    }
  };

  if (!currentProjectId) {
    return <div className="explorer empty">No project selected. Create or select one.</div>
  }

  return (
    <div className="explorer">
      <div className="explorer-header">
        <span>EXPLORER</span>
        <div className="actions">
          <button title="New file" onClick={() => handleCreateFile(false)}><FilePlus size={14} /></button>
          <button title="New folder" onClick={() => handleCreateFile(true)}><FolderPlus size={14} /></button>
          <button title="Refresh" onClick={loadTree}>↻</button>
        </div>
      </div>
      <div className="explorer-tree">
        {loading ? <div className="loading">Loading...</div> : tree?.children?.map(child => (
          <FileNode key={child.path} node={child} onFileClick={handleFileClick} />
        ))}
      </div>
    </div>
  )
}
