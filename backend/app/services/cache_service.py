import os
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List
from ..core.config import get_cache_dir, DEFAULT_JAVA_VERSIONS

class CacheService:
    def __init__(self):
        self.cache_dir = get_cache_dir()
        self.meta_file = self.cache_dir / "cache_meta.json"
        self._load_meta()

    def _load_meta(self):
        if self.meta_file.exists():
            try:
                self.meta = json.loads(self.meta_file.read_text())
            except:
                self.meta = {}
        else:
            self.meta = {}

    def _save_meta(self):
        try:
            self.meta_file.write_text(json.dumps(self.meta, indent=2))
        except:
            pass

    def _cache_path(self, category: str, version: str) -> Path:
        return self.cache_dir / category / version

    def is_cached(self, category: str, version: str) -> bool:
        p = self._cache_path(category, version)
        return p.exists() and any(p.iterdir())

    def ensure_cached(self, category: str, version: str, simulate_download: bool = True) -> dict:
        """
        Ensure a cached entry exists. If not, simulate downloading.
        Returns dict with path, cached(bool), size
        """
        path = self._cache_path(category, version)
        was_cached = self.is_cached(category, version)

        if not was_cached:
            path.mkdir(parents=True, exist_ok=True)
            # Simulate download by creating marker files
            if simulate_download:
                # In real implementation, download actual binaries here
                marker = path / ".cached"
                marker.write_text(json.dumps({
                    "category": category,
                    "version": version,
                    "timestamp": time.time(),
                    "simulated": True
                }))
                # Create dummy substructure to mimic real cache
                if category == "java":
                    (path / "bin").mkdir(exist_ok=True)
                    (path / "bin" / ("java.exe" if os.name == "nt" else "java")).write_text("fake java")
                elif category == "gradle":
                    (path / "lib").mkdir(exist_ok=True)
                elif category == "minecraft":
                    (path / f"{version}.jar").write_text(f"fake minecraft {version} jar")
                elif category == "loaders":
                    (path / f"{version}.jar").write_text(f"fake loader {version}")

            key = f"{category}/{version}"
            self.meta[key] = {
                "category": category,
                "version": version,
                "path": str(path),
                "cached_at": time.time(),
                "size_mb": self._dir_size_mb(path)
            }
            self._save_meta()
            return {"path": str(path), "cached": False, "was_cached": False, "size_mb": self.meta[key]["size_mb"]}
        else:
            key = f"{category}/{version}"
            size = self._dir_size_mb(path)
            if key not in self.meta:
                self.meta[key] = {"category": category, "version": version, "path": str(path), "cached_at": path.stat().st_mtime, "size_mb": size}
                self._save_meta()
            return {"path": str(path), "cached": True, "was_cached": True, "size_mb": size}

    def _dir_size_mb(self, path: Path) -> float:
        total = 0
        try:
            for p in path.rglob("*"):
                if p.is_file():
                    total += p.stat().st_size
        except:
            pass
        return round(total / (1024*1024), 2)

    def get_status(self) -> dict:
        total = 0
        entries: Dict[str, List[dict]] = {}
        for category_dir in self.cache_dir.iterdir():
            if not category_dir.is_dir():
                continue
            cat = category_dir.name
            entries[cat] = []
            for version_dir in category_dir.iterdir():
                if version_dir.is_dir():
                    size = self._dir_size_mb(version_dir)
                    total += size
                    entries[cat].append({
                        "version": version_dir.name,
                        "path": str(version_dir),
                        "size_mb": size,
                        "cached_at": version_dir.stat().st_mtime
                    })
        return {"total_size_mb": round(total, 2), "entries": entries}

    def clear_category(self, category: str, version: str = None):
        if version:
            p = self._cache_path(category, version)
            if p.exists():
                shutil.rmtree(p)
                self.meta.pop(f"{category}/{version}", None)
        else:
            p = self.cache_dir / category
            if p.exists():
                shutil.rmtree(p)
                p.mkdir(parents=True, exist_ok=True)
                # clean meta
                for k in list(self.meta.keys()):
                    if k.startswith(f"{category}/"):
                        del self.meta[k]
        self._save_meta()

    def clear_all(self):
        for sub in self.cache_dir.iterdir():
            if sub.is_dir():
                shutil.rmtree(sub)
                sub.mkdir(parents=True, exist_ok=True)
        self.meta = {}
        self._save_meta()

    def ensure_for_project(self, mc_version: str, loader: str, loader_version: str = None) -> dict:
        """
        Ensure all required caches for a given project (java, gradle, minecraft, loader, mappings)
        """
        java_ver = DEFAULT_JAVA_VERSIONS.get(mc_version, 21)
        results = {}
        results["java"] = self.ensure_cached("java", str(java_ver))
        results["gradle"] = self.ensure_cached("gradle", "8.8")  # typical modern gradle
        results["minecraft"] = self.ensure_cached("minecraft", mc_version)
        results["mappings"] = self.ensure_cached("mappings", f"{mc_version}-{loader}")
        if loader_version:
            results["loaders"] = self.ensure_cached("loaders", f"{loader}-{loader_version}")
        else:
            results["loaders"] = self.ensure_cached("loaders", f"{loader}-{mc_version}")
        return results
