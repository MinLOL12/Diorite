import shutil
import re
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from ..core.config import get_projects_dir, get_cache_dir, DEFAULT_JAVA_VERSIONS
from .template_service import TemplateService
from .cache_service import CacheService
from ..models.schemas import ProjectInfo

class ProjectService:
    def __init__(self):
        self.projects_root = get_projects_dir()
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self.template_service = TemplateService()
        self.cache_service = CacheService()

    def _sanitize_name(self, name: str) -> str:
        # Keep alphanumeric, dash, underscore, space -> replace space with dash for id but keep name original
        return re.sub(r'[^a-zA-Z0-9_\- ]', '', name).strip()

    def _mod_id_from_name(self, name: str) -> str:
        mod_id = re.sub(r'[^a-z0-9_]', '', name.lower().replace(' ', '_').replace('-', '_'))
        if not mod_id:
            mod_id = "examplemod"
        if mod_id[0].isdigit():
            mod_id = "mod_" + mod_id
        # mod id must be lowercase alphanumeric + underscore, 2+ chars
        if len(mod_id) < 2:
            mod_id = mod_id + "mod"
        return mod_id[:64]

    def list_projects(self) -> List[ProjectInfo]:
        projects = []
        for p in self.projects_root.iterdir():
            if not p.is_dir():
                continue
            meta_file = p / ".diorite" / "project.json"
            if meta_file.exists():
                try:
                    data = json.loads(meta_file.read_text())
                    projects.append(ProjectInfo(**data))
                except Exception:
                    # Fallback infer
                    projects.append(ProjectInfo(
                        id=p.name,
                        name=p.name,
                        loader="fabric",
                        mc_version="1.21.1",
                        mod_id=p.name.lower(),
                        path=str(p),
                        created_at=datetime.fromtimestamp(p.stat().st_ctime),
                        last_opened=None
                    ))
            else:
                # No meta, infer minimal
                projects.append(ProjectInfo(
                    id=p.name,
                    name=p.name,
                    loader="fabric",
                    mc_version="1.21.1",
                    mod_id=p.name.lower(),
                    path=str(p),
                    created_at=datetime.fromtimestamp(p.stat().st_ctime),
                ))
        # Sort by last opened descending then created
        projects.sort(key=lambda x: (x.last_opened or x.created_at), reverse=True)
        return projects

    def get_project(self, project_id: str) -> Optional[ProjectInfo]:
        for proj in self.list_projects():
            if proj.id == project_id:
                return proj
        return None

    def create_project(self, name: str, loader: str, mc_version: str, mod_id: str = None, package: str = None, template_id: str = None) -> ProjectInfo:
        safe_name = self._sanitize_name(name)
        if not safe_name:
            raise ValueError("Invalid project name")

        mod_id = mod_id or self._mod_id_from_name(safe_name)
        mod_id = self._mod_id_from_name(mod_id)  # ensure sanitized
        package = package or f"com.example.{mod_id}"
        # project id = name with dashes
        project_id = re.sub(r'\s+', '-', safe_name.lower())
        project_id = re.sub(r'[^a-z0-9\-]', '', project_id)
        if not project_id:
            project_id = mod_id

        project_path = self.projects_root / project_id
        # If exists, append number
        counter = 1
        base_id = project_id
        while project_path.exists():
            counter += 1
            project_id = f"{base_id}-{counter}"
            project_path = self.projects_root / project_id

        # Determine template
        if not template_id:
            # Try to find matching template via loader + version
            desired = f"{loader}-{mc_version}"
            available = [t["id"] for t in self.template_service.list_templates()]
            if desired in available:
                template_id = desired
            else:
                # fallback: any template with same loader
                matching = [t for t in self.template_service.list_templates() if t["loader"] == loader]
                if matching:
                    # Prefer closest version
                    template_id = matching[0]["id"]
                else:
                    # fallback first available
                    all_t = self.template_service.list_templates()
                    if not all_t:
                        raise RuntimeError("No templates available")
                    template_id = all_t[0]["id"]

        # Check cache - this is what makes second project fast
        cache_result = self.cache_service.ensure_for_project(mc_version, loader)

        # Prepare replacements
        replacements = {
            "MOD_ID": mod_id,
            "MOD_NAME": safe_name,
            "PACKAGE": package,
            "MC_VERSION": mc_version,
            "LOADER": loader,
        }

        # Copy template (fast because cache already exists after first)
        start = time.time()
        self.template_service.copy_template(template_id, project_path, replacements)
        elapsed = time.time() - start

        # Create .diorite meta
        meta_dir = project_path / ".diorite"
        meta_dir.mkdir(parents=True, exist_ok=True)
        proj_info = ProjectInfo(
            id=project_id,
            name=safe_name,
            loader=loader,
            mc_version=mc_version,
            mod_id=mod_id,
            path=str(project_path),
            created_at=datetime.now(),
            last_opened=datetime.now(),
            java_version=DEFAULT_JAVA_VERSIONS.get(mc_version, 21),
            template=template_id
        )
        (meta_dir / "project.json").write_text(json.dumps(proj_info.model_dump(mode='json'), indent=2, default=str))
        # Save cache info
        (meta_dir / "cache.json").write_text(json.dumps(cache_result, indent=2))

        # Log
        (meta_dir / "creation.log").write_text(f"Created project {project_id} from template {template_id} in {elapsed:.2f}s\nCache: {json.dumps(cache_result, indent=2)}\n")

        return proj_info

    def delete_project(self, project_id: str) -> bool:
        project_path = self.projects_root / project_id
        if not project_path.exists():
            raise FileNotFoundError(f"Project {project_id} not found")
        # Safety: ensure inside projects root
        try:
            project_path.resolve().relative_to(self.projects_root.resolve())
        except ValueError:
            raise ValueError("Invalid project path")
        shutil.rmtree(project_path)
        return True

    def touch_last_opened(self, project_id: str):
        meta_file = self.projects_root / project_id / ".diorite" / "project.json"
        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text())
                data["last_opened"] = datetime.now().isoformat()
                meta_file.write_text(json.dumps(data, indent=2))
            except Exception:
                pass

    def get_project_stats(self, project_id: str) -> dict:
        project_path = self.projects_root / project_id
        if not project_path.exists():
            raise FileNotFoundError(f"Project {project_id} not found")
        total_files = 0
        total_size = 0
        java_files = 0
        for p in project_path.rglob("*"):
            if p.is_file():
                if ".gradle" in str(p) or "build" in p.parts:
                    continue
                total_files += 1
                try:
                    total_size += p.stat().st_size
                except:
                    pass
                if p.suffix == ".java":
                    java_files += 1
        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024*1024), 2),
            "java_files": java_files,
            "path": str(project_path)
        }
