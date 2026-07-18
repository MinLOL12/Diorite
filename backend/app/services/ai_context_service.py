import os
import json
import re
from pathlib import Path
from typing import List, Dict
from ..core.config import get_projects_dir
from .file_service import FileService

class AIContextService:
    def __init__(self):
        self.projects_root = get_projects_dir()
        self.file_service = FileService()

    def build_context(self, project_id: str, open_files: List[str] = None, current_file: str = None, cursor_pos: Dict = None) -> dict:
        if open_files is None:
            open_files = []

        project_path = self.projects_root / project_id
        if not project_path.exists():
            raise FileNotFoundError(f"Project {project_id} not found")

        # Load project meta
        meta_file = project_path / ".diorite" / "project.json"
        project_meta = {}
        if meta_file.exists():
            try:
                project_meta = json.loads(meta_file.read_text())
            except:
                pass

        # Project structure (top 2 levels + src)
        structure = self._get_structure_summary(project_path)

        # Dependencies: parse gradle.properties, build.gradle
        dependencies = self._parse_dependencies(project_path)

        # Symbols: crude parsing of open files for classes, methods
        symbols = {}
        for f in open_files[:10]:  # limit
            try:
                fp = project_path / f
                if fp.exists() and fp.suffix == ".java" and fp.stat().st_size < 200*1024:
                    content = fp.read_text(encoding='utf-8', errors='ignore')
                    symbols[f] = self._extract_symbols(content)
            except Exception:
                continue

        # Current file content with cursor context
        current_content = None
        current_snippet = None
        if current_file:
            try:
                cf = project_path / current_file
                if cf.exists() and cf.stat().st_size < 500*1024:
                    current_content = cf.read_text(encoding='utf-8', errors='ignore')
                    if cursor_pos:
                        line = cursor_pos.get("line", 0)
                        # Provide 20 lines around cursor
                        lines = current_content.splitlines()
                        start = max(0, line-10)
                        end = min(len(lines), line+10)
                        current_snippet = "\n".join(lines[start:end])
            except Exception:
                pass

        # Recently edited
        recent = self.file_service.get_recent(project_id)

        # Mappings info
        mappings_info = project_meta.get("template", "") + " mappings inferred"

        context = {
            "project": project_meta,
            "structure": structure,
            "dependencies": dependencies,
            "open_files": open_files[:20],
            "current_file": current_file,
            "current_snippet": current_snippet,
            "recent_files": recent[:10],
            "symbols": symbols,
            "minecraft_version": project_meta.get("mc_version", "unknown"),
            "loader": project_meta.get("loader", "unknown"),
            "mappings": mappings_info,
            "mod_id": project_meta.get("mod_id", ""),
            "context_tokens_estimate": self._estimate_tokens(structure, symbols, current_snippet)
        }

        return context

    def _get_structure_summary(self, project_path: Path) -> str:
        lines = []
        # Walk but limited
        for root, dirs, files in os.walk(project_path):
            # Skip ignored
            dirs[:] = [d for d in dirs if d not in (".gradle", "build", ".git", ".idea", "run", "logs", "out")]
            rel_root = os.path.relpath(root, project_path)
            if rel_root == ".":
                depth = 0
            else:
                depth = rel_root.count(os.sep) + 1
            if depth > 4:
                dirs[:] = []
                continue
            indent = "  " * depth
            if rel_root != ".":
                lines.append(f"{indent}{Path(root).name}/")
            sub_indent = "  " * (depth+1)
            # Limit files per dir
            for f in sorted(files)[:15]:
                lines.append(f"{sub_indent}{f}")
            if len(lines) > 150:
                lines.append("... truncated ...")
                break
        return "\n".join(lines[:200])

    def _parse_dependencies(self, project_path: Path) -> dict:
        deps = {"gradle_props": {}, "fabric_mod_json": {}}
        gp = project_path / "gradle.properties"
        if gp.exists():
            try:
                for line in gp.read_text().splitlines():
                    line=line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k,v=line.split("=",1)
                        deps["gradle_props"][k.strip()]=v.strip()
            except:
                pass
        mod_json = project_path / "src" / "main" / "resources" / "fabric.mod.json"
        if not mod_json.exists():
            # search any fabric.mod.json
            for p in project_path.rglob("fabric.mod.json"):
                mod_json = p
                break
        if mod_json and mod_json.exists():
            try:
                deps["fabric_mod_json"]=json.loads(mod_json.read_text())
            except:
                pass
        return deps

    def _extract_symbols(self, content: str) -> dict:
        classes = re.findall(r'class\s+(\w+)', content)
        interfaces = re.findall(r'interface\s+(\w+)', content)
        methods = re.findall(r'(public|private|protected).*\s(\w+)\s*\([^)]*\)\s*\{?', content)
        method_names = [m[1] for m in methods[:20]]
        imports = re.findall(r'import\s+([\w\.]+);', content)
        return {
            "classes": classes[:10],
            "interfaces": interfaces[:10],
            "methods": method_names,
            "imports": imports[:20]
        }

    def _estimate_tokens(self, structure, symbols, snippet) -> int:
        # Rough estimate
        total_chars = len(structure) + (len(str(symbols))*2)
        if snippet:
            total_chars+=len(snippet)
        return total_chars // 4

    def generate_scaffold_prompt(self, scaffold_type: str, context: dict) -> str:
        base = f"""You are Diorite AI, specialized in Minecraft {context.get('loader')} {context.get('minecraft_version')} modding.
Project: {context.get('project', {}).get('name')} modId: {context.get('mod_id')}
Open files: {context.get('open_files')}
Structure:
{context.get('structure')[:2000]}

Generate {scaffold_type} code following best practices for {context.get('loader')} {context.get('minecraft_version')}.
"""
        return base
