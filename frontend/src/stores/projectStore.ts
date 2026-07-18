import { create } from 'zustand';

interface Project {
  id: string;
  name: string;
  loader: string;
  mc_version: string;
  mod_id: string;
  path: string;
}

interface ProjectState {
  projects: Project[];
  currentProjectId: string | null;
  currentProject: Project | null;
  setProjects: (p: Project[]) => void;
  setCurrentProjectId: (id: string | null) => void;
  setCurrentProject: (p: Project | null) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProjectId: localStorage.getItem('diorite_current_project') || null,
  currentProject: null,
  setProjects: (projects) => set({ projects }),
  setCurrentProjectId: (id) => {
    if (id) localStorage.setItem('diorite_current_project', id);
    else localStorage.removeItem('diorite_current_project');
    set({ currentProjectId: id });
  },
  setCurrentProject: (currentProject: Project | null) => set({ currentProject }),
}));
