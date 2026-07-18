# Diorite — Zero-Setup Minecraft Modding IDE

![Diorite Logo](assets/logo.png)

> **Like Cursor / Replit, but for Minecraft Java mods.** No JDK, Gradle, mappings, or mod loader setup. Create project → Write code → Press Play → See it in Minecraft.

---

## ✨ Purpose

Minecraft modding has a much higher barrier to entry than normal programming. Before writing a single line of code, users often need to install a JDK, Gradle, mappings, a mod loader, configure an IDE, create run configurations, and make sure every version is compatible.

**Diorite removes that entirely.** It feels like opening Cursor or Replit:
- Frontend is a modern code editor with project explorer, terminal output, logs, and a **Play button**.
- Backend manages every part of the dev environment: projects, files, dependencies, Gradle, Minecraft launching, caching, and exposes everything through an API.
- Users never manually configure Java, Gradle, mappings, or run tasks.

---

## 🏗 Architecture

Modular services, each in `backend/app/services/`:

| Service | Responsibility |
|---------|---------------|
| `project_service.py` | Create from templates, list, delete, stats. Second Fabric 1.21.x project in seconds via cache reuse. |
| `file_service.py` | File tree, read/write, create/rename/delete, recent tracking, path-traversal safe. Backend is source of truth. |
| `build_service.py` | One-action build: save open files, invoke Gradle, watch output, report errors real-time, launch MC if succeeds. |
| `process_manager.py` | Owns Minecraft processes: knows if client running, stop/restart, crash detection, orphan cleanup. Run feels like game engine. |
| `cache_service.py` | `~/.diorite/cache/{java,gradle,minecraft,mappings,loaders}`. Once version downloaded, reused by every project. |
| `template_service.py` | Maintained templates (Fabric 1.21.1, 1.20.1, NeoForge 1.21.1, Forge 1.20.1...). Copies working Gradle project with deps, mappings, run configs. Tokens `{{MOD_ID}}`, `{{MOD_NAME}}` etc. |
| `ai_context_service.py` | Project-aware AI, not plain text. Builds context from open files, structure, symbols (classes/methods/imports), MC version, mappings, deps, recent edits. Efficient. |
| `settings_service.py` | User settings theme, font, java_home, ai_enabled etc stored in `~/.diorite/settings.json`. Also `scaffold_service.py` for block/item/entity/screen/recipe/data component generation. |

**Backend:** FastAPI + WebSockets (`/ws/{build,logs,process}/{projectId}`) streaming build progress, compiler diagnostics, runtime logs, crashes live to frontend — not waiting for finish.

**Frontend:** React + Vite + Monaco Editor (Cursor-like dark theme). Components:
- `TopBar` + `PlayButton` (green Play, instant)
- `ProjectExplorer` (tree, create file/folder)
- `Editor` (Monaco tabs, auto-save, dirty indicators)
- `Terminal` (xterm-style, live WS logs)
- `ScaffoldMenu` (New Block/Item/Entity/Screen/Recipe/Data Component — generates files+registration)
- `AIChatPanel` (project-aware, shows context used)
- `NewProjectModal` (loader + MC version selector, templates preview, cache hint)

**Electron:** `electron/src/main.ts` spawns backend (Python) and serves frontend. Packaging via `electron-builder` NSIS for EXE installer.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (`pip install -r backend/requirements.txt`)
- Node 20+ (for frontend & electron)

### Dev Mode (no installer)

```bash
# Terminal 1: backend at :7331
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 7331 --reload

# Terminal 2: frontend at :7332
cd frontend
npm install
npm run dev

# Or via root:
npm install
npm run dev  # uses concurrently to run both
```

Open http://127.0.0.1:7332 — backend: http://127.0.0.1:7331/docs

### Creating a project
1. Click **+ New Project**
2. Choose Name, Mod ID, Loader (Fabric/NeoForge/Forge/Quilt), MC version (1.21.1 ...)
3. Backend copies matching maintained template into `~/.diorite/projects/<id>` using cached Java/Gradle/MC/mappings (fast)
4. Write code in Monaco, open files tracked for AI context, auto-save.

### Play button
- Saves open files
- Invokes Gradle task (`build` or `runClient`)
- Streams output live via WebSocket to Console
- Reports errors real-time
- Launches Minecraft client with mod loaded
- Backend tracks process — Stop/Restart, crash detect, cleanup orphans

### Scaffold actions
In left sidebar: **New Minecraft...** → Block/Item/Entity/Screen/Recipe/Data Component
Generates Java files, JSON models, blockstates, registrations — convenience on top of normal source files, not visual editor replacement.

---

## 📦 Installer (EXE)

Builds an EXE installer users can run:

```bash
# Build everything then NSIS installer
node scripts/build-installer.js

# Or manually:
npm run build:installer
# Output: dist/installer/Diorite-Setup-0.1.0-x64.exe
```

What installer does:
- Installs Electron app + embedded backend + frontend
- NSIS: choose dir, desktop shortcut, start menu
- Creates `%APPDATA%\Diorite` with cache structure
- User runs EXE → zero setup, same flow.

For Windows cross-build on Linux, use Wine or build on Windows host. The config in `installer/electron-builder.yml` targets NSIS x64, DMG for macOS, AppImage for Linux.

---

## 🔌 API

- `GET /api/projects` — list
- `POST /api/projects {name, loader, mc_version, mod_id, template_id}` — create from template (cache ensured)
- `GET /api/templates` — list Fabric/NeoForge etc
- `GET /api/projects/{id}/files/tree` + `/content?path=` + `/save` + `/create` + `/rename` + DELETE
- `POST /api/projects/{id}/build {tasks}` — build
- `POST /api/projects/{id}/run {tasks}` — Play: build + launch
- `GET/POST /api/processes` + `/projects/{id}/process/stop` `/restart` — process manager
- `GET /api/cache/status` + `POST /api/cache/clear` — cache
- `POST /api/ai/context` & `/chat` — project-aware AI context (open files, structure, symbols, version, mappings, deps, recent)
- `POST /api/projects/{id}/scaffold/{block,item,entity,screen,recipe,component}` — workflows
- `WS /ws/{build,logs,process}/{projectId}` + `/ws/global` — live streaming
- `GET /` + `/api/health` + `/docs`

---

## 🎨 Logo

- `assets/logo.png` generated — modern minimalist D with Minecraft diorite texture (white+black specks), emerald accent `#a8f0c6`, dark `#0e0e0f` bg.
- `assets/logo.svg` — vector version
- `assets/icons/icon.png` + `icon.ico` (NSIS installer) + `icon-512.png`

Feel: Cursor/Replit but Minecraft — premium, tech, zero friction.

---

## 🧩 Extensibility

Modular architecture allows adding without redesign:
- Additional loaders (add template in `backend/templates/` and meta)
- More MC versions (drop template, cache handles reuse)
- Collaborative editing (extend `file_service` + WebSockets `files:{project}`)
- Plugin system (settings + dynamic route inclusion)
- Cloud workspaces (replace `get_user_data_root` with remote)
- Automated testing (add `test_service.py` invoking Gradle `test`)

---

## 📂 Structure

```
Diorite/
├─ backend/
│  ├─ app/
│  │  ├─ main.py (FastAPI entry)
│  │  ├─ core/{config, websocket_manager, gradle_runner}
│  │  ├─ models/schemas.py
│  │  ├─ services/{project,file,build,process_manager,cache,template,ai_context,settings,scaffold}_service.py
│  │  └─ api/routes/{projects,files,builds,processes,cache,templates,ai,scaffolds,settings}.py
│  └─ templates/ (auto-generated Fabric/NeoForge/Forge builtins with {{MOD_ID}} tokens)
├─ frontend/
│  ├─ src/{App, main, components/{TopBar,PlayButton,ProjectExplorer,Editor,Terminal,ScaffoldMenu,AIChatPanel,NewProjectModal,StatusBar,Sidebar}, api/client, stores/{projectStore,editorStore}, hooks/useWebSocket}
│  └─ vite.config.ts (proxies /api and /ws to :7331)
├─ electron/
│  ├─ src/{main.ts (spawns backend), preload.ts}
│  └─ package.json
├─ installer/electron-builder.yml (NSIS EXE, DMG, AppImage)
├─ assets/{logo.svg, logo.png, icons/{icon.png, icon.ico, icon-256.png}}
├─ scripts/{build-installer.js, run-dev.js}
└─ README.md
```

---

## 🎯 Design Goals

Every decision reduces time between idea and in-game:
- Cache → second project seconds
- Templates → working Gradle project immediately, no version hell
- Backend file truth → no local config drift
- One Play button → save + build + launch, no Gradle CLI
- Live WS logs → like IDE terminal, see errors, stack traces immediately
- Process manager → Run feels like game engine, not scripts
- Project-aware AI → higher quality, efficient, uses open files + symbols + version etc
- Scaffold menu → common modding workflows as actions generating files+registrations
- Modular services → easy to add loader, version, collab, plugins, cloud, tests
- Overall Cursor-like but specialized for Minecraft Java

---

## 📜 License

MIT — see LICENSE (if present). Feel free to fork for custom loaders.

---

Built with ❤️ for Minecraft modders tired of setup. Diorite = diorite block is crafted instantly from cobble + nether quartz — this IDE crafts mod dev environment instantly.
