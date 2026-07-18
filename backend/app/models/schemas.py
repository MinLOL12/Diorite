from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class LoaderType(str, Enum):
    fabric = "fabric"
    neoforge = "neoforge"
    forge = "forge"
    quilt = "quilt"

class ProjectCreateRequest(BaseModel):
    name: str
    loader: LoaderType
    mc_version: str
    mod_id: Optional[str] = None
    package: Optional[str] = None
    template_id: Optional[str] = None

class ProjectInfo(BaseModel):
    id: str
    name: str
    loader: str
    mc_version: str
    mod_id: str
    path: str
    created_at: datetime
    last_opened: Optional[datetime] = None
    java_version: Optional[int] = None
    template: Optional[str] = None

class FileRequest(BaseModel):
    path: str

class FileContent(BaseModel):
    path: str
    content: str
    is_binary: bool = False

class FileSaveRequest(BaseModel):
    path: str
    content: str

class FileCreateRequest(BaseModel):
    path: str
    is_directory: bool = False
    content: Optional[str] = ""

class FileRenameRequest(BaseModel):
    old_path: str
    new_path: str

class FileTreeNode(BaseModel):
    name: str
    path: str
    type: Literal["file", "directory"]
    children: Optional[List["FileTreeNode"]] = None
    extension: Optional[str] = None

FileTreeNode.model_rebuild()

class BuildRequest(BaseModel):
    tasks: Optional[List[str]] = None  # defaults to ["build"]

class RunRequest(BaseModel):
    tasks: Optional[List[str]] = None  # defaults to ["runClient"]
    stop_existing: bool = True

class ScaffoldBlockRequest(BaseModel):
    name: str
    material: Optional[str] = "STONE"
    creative_tab: Optional[str] = "BUILDING_BLOCKS"

class ScaffoldItemRequest(BaseModel):
    name: str
    stack_size: Optional[int] = 64
    creative_tab: Optional[str] = "INGREDIENTS"

class ScaffoldEntityRequest(BaseModel):
    name: str
    category: Optional[str] = "CREATURE"
    width: float = 0.6
    height: float = 1.8

class ScaffoldScreenRequest(BaseModel):
    name: str

class ScaffoldRecipeRequest(BaseModel):
    name: str
    type: Literal["shaped", "shapeless", "smelting"] = "shaped"

class ScaffoldComponentRequest(BaseModel):
    name: str
    type: str = "Integer"

class AIContextRequest(BaseModel):
    project_id: str
    open_files: List[str] = []
    current_file: Optional[str] = None
    cursor_position: Optional[Dict[str, int]] = None
    prompt: Optional[str] = None

class AIChatRequest(BaseModel):
    project_id: str
    message: str
    open_files: List[str] = []
    current_file: Optional[str] = None
    history: List[Dict[str, str]] = []

class CacheStatus(BaseModel):
    total_size_mb: float
    entries: Dict[str, List[Dict[str, Any]]]

class Settings(BaseModel):
    theme: str = "dark"
    font_size: int = 14
    auto_save: bool = True
    java_home: Optional[str] = None
    gradle_home: Optional[str] = None
    ai_enabled: bool = True
    ai_provider: str = "openai"
    editor_tab_size: int = 4
