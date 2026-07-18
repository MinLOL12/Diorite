import { create } from 'zustand';

interface OpenFile {
  path: string;
  content: string;
  dirty: boolean;
  language: string;
}

interface EditorState {
  openFiles: OpenFile[];
  activeFilePath: string | null;
  recentFiles: string[];
  addOpenFile: (file: OpenFile) => void;
  updateFileContent: (path: string, content: string, dirty?: boolean) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string | null) => void;
  markDirty: (path: string, dirty: boolean) => void;
  setRecent: (files: string[]) => void;
}

function detectLang(path: string): string {
  if (path.endsWith('.java')) return 'java';
  if (path.endsWith('.json')) return 'json';
  if (path.endsWith('.toml')) return 'toml';
  if (path.endsWith('.gradle')) return 'groovy';
  if (path.endsWith('.properties')) return 'properties';
  if (path.endsWith('.md')) return 'markdown';
  if (path.endsWith('.xml')) return 'xml';
  return 'plaintext';
}

export const useEditorStore = create<EditorState>((set, get) => ({
  openFiles: [],
  activeFilePath: null,
  recentFiles: [],
  addOpenFile: (file) => {
    const exists = get().openFiles.find(f => f.path === file.path);
    if (exists) {
      set({ activeFilePath: file.path });
      // update content if newer?
      if (exists.content !== file.content && !exists.dirty) {
        set(state => ({
          openFiles: state.openFiles.map(f => f.path === file.path ? { ...f, content: file.content } : f)
        }));
      }
      return;
    }
    const withLang = { ...file, language: detectLang(file.path) };
    set(state => ({
      openFiles: [...state.openFiles, withLang],
      activeFilePath: file.path
    }));
  },
  updateFileContent: (path, content, dirty) => {
    set(state => ({
      openFiles: state.openFiles.map(f => f.path === path ? { ...f, content, dirty: dirty !== undefined ? dirty : true } : f)
    }));
  },
  closeFile: (path) => {
    const { openFiles, activeFilePath } = get();
    const filtered = openFiles.filter(f => f.path !== path);
    let newActive = activeFilePath;
    if (activeFilePath === path) {
      newActive = filtered.length > 0 ? filtered[filtered.length - 1].path : null;
    }
    set({ openFiles: filtered, activeFilePath: newActive });
  },
  setActiveFile: (path) => set({ activeFilePath: path }),
  markDirty: (path, dirty) => {
    set(state => ({
      openFiles: state.openFiles.map(f => f.path === path ? { ...f, dirty } : f)
    }));
  },
  setRecent: (recentFiles) => set({ recentFiles })
}));
