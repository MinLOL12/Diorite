from pathlib import Path
from typing import List
import os
import shutil
from ..models.schemas import FileTreeNode
from ..core.config import get_projects_dir

class FileService:
    def __init__(self):
        self.projects_root = get_projects_dir()

    def resolve_project_path(self, project_id: str) -> Path:
        # project_id is folder name; sanitize
        safe_id = "".join(c for c in project_id if c.isalnum() or c in ("-", "_"))
        path = self.projects_root / project_id
        if not path.exists():
            # Try safe_id fallback
            path = self.projects_root / safe_id
        return path.resolve()

    def _resolve_within(self, project_root: Path, relative: str) -> Path:
        # Prevent path traversal
        rel = Path(relative)
        # Remove leading / or \
        if rel.is_absolute():
            rel = Path(*rel.parts[1:])
        full = (project_root / rel).resolve()
        # Ensure within project_root
        try:
            full.relative_to(project_root.resolve())
        except ValueError:
            # If relative goes outside, clamp to root
            raise ValueError(f"Path traversal detected: {relative}")
        return full

    def get_tree(self, project_id: str, max_depth: int = 10) -> FileTreeNode:
        project_root = self.resolve_project_path(project_id)
        if not project_root.exists():
            raise FileNotFoundError(f"Project {project_id} not found")

        def build_tree(path: Path, rel_path: str, depth: int) -> FileTreeNode:
            is_dir = path.is_dir()
            node_type = "directory" if is_dir else "file"
            ext = path.suffix if not is_dir else None
            node = FileTreeNode(
                name=path.name,
                path=rel_path,
                type=node_type,
                extension=ext
            )
            if is_dir and depth < max_depth:
                try:
                    children = []
                    for child in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        # Skip large ignored dirs
                        if child.name in (".gradle", "build", ".idea", "run", "logs", "out"):
                            continue
                        child_rel = f"{rel_path}/{child.name}" if rel_path else child.name
                        children.append(build_tree(child, child_rel, depth+1))
                    node.children = children
                except PermissionError:
                    node.children = []
            return node

        # root node
        root = FileTreeNode(
            name=project_root.name,
            path="",
            type="directory",
            children=[]
        )
        for child in sorted(project_root.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if child.name in (".gradle", "build"):
                continue
            root.children.append(build_tree(child, child.name, 1))
        return root

    def list_files(self, project_id: str, dir_path: str = "") -> List[dict]:
        project_root = self.resolve_project_path(project_id)
        target = self._resolve_within(project_root, dir_path) if dir_path else project_root
        if not target.exists() or not target.is_dir():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        result = []
        for p in target.iterdir():
            result.append({
                "name": p.name,
                "path": str(p.relative_to(project_root)),
                "type": "directory" if p.is_dir() else "file",
                "size": p.stat().st_size if p.is_file() else 0,
            })
        return sorted(result, key=lambda x: (x["type"] == "file", x["name"]))

    def read_file(self, project_id: str, file_path: str) -> dict:
        project_root = self.resolve_project_path(project_id)
        full = self._resolve_within(project_root, file_path)
        if not full.exists() or full.is_dir():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Binary check
        try:
            data = full.read_bytes()
            # Try decode
            try:
                text = data.decode('utf-8')
                is_binary = False
            except UnicodeDecodeError:
                # Binary
                return {"content": "", "is_binary": True, "size": len(data)}
        except Exception as e:
            raise e

        return {"content": text, "is_binary": False, "size": len(data), "path": file_path}

    def write_file(self, project_id: str, file_path: str, content: str) -> dict:
        project_root = self.resolve_project_path(project_id)
        full = self._resolve_within(project_root, file_path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding='utf-8')
        return {"path": file_path, "size": len(content)}

    def create_file_or_dir(self, project_id: str, path: str, is_directory: bool, content: str = "") -> dict:
        project_root = self.resolve_project_path(project_id)
        full = self._resolve_within(project_root, path)
        if full.exists():
            raise FileExistsError(f"Path already exists: {path}")
        if is_directory:
            full.mkdir(parents=True, exist_ok=True)
        else:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content or "", encoding='utf-8')
        return {"path": path, "type": "directory" if is_directory else "file"}

    def rename(self, project_id: str, old_path: str, new_path: str) -> dict:
        project_root = self.resolve_project_path(project_id)
        old_full = self._resolve_within(project_root, old_path)
        new_full = self._resolve_within(project_root, new_path)
        if not old_full.exists():
            raise FileNotFoundError(f"Source not found: {old_path}")
        if new_full.exists():
            raise FileExistsError(f"Destination exists: {new_path}")
        new_full.parent.mkdir(parents=True, exist_ok=True)
        old_full.rename(new_full)
        return {"old": old_path, "new": new_path}

    def delete(self, project_id: str, path: str) -> dict:
        project_root = self.resolve_project_path(project_id)
        full = self._resolve_within(project_root, path)
        if not full.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        if full.is_dir():
            shutil.rmtree(full)
        else:
            full.unlink()
        return {"deleted": path}

    def touch_recent(self, project_id: str, file_path: str):
        # Update settings or recent tracking
        # Simple: create .diorite/recent file
        project_root = self.resolve_project_path(project_id)
        meta_dir = project_root / ".diorite"
        meta_dir.mkdir(exist_ok=True)
        recent_file = meta_dir / "recent.txt"
        try:
            existing = []
            if recent_file.exists():
                existing = recent_file.read_text().splitlines()
            # Move to top
            if file_path in existing:
                existing.remove(file_path)
            existing.insert(0, file_path)
            existing = existing[:100]
            recent_file.write_text("\n".join(existing))
        except Exception:
            pass

    def get_recent(self, project_id: str) -> List[str]:
        project_root = self.resolve_project_path(project_id)
        recent_file = project_root / ".diorite" / "recent.txt"
        if recent_file.exists():
            return recent_file.read_text().splitlines()[:20]
        return []
