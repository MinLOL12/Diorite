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

**Electron:** `electron/src/main.ts` launches the backend and serves the frontend. The backend is **frozen into a single exe with PyInstaller** (`npm run make:exe` → `backend/dist/diorite-backend/…`), so the packaged app is fully self-contained — no Python on the user's PC. Packaging via `electron-builder` produces the one-click NSIS EXE installer.

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

## 📦 Installer (EXE) — one file for you, one file for users

### Get/make the installer (pick ONE — all produce the same EXE)

| Way | How | What you need installed |
|-----|-----|-------------------------|
| **GitHub — No install (easiest)** | Go to your repo on GitHub → **Actions** tab → **Build Installer** → **Run workflow** → wait ~5 min → download `Diorite-Setup-Windows` artifact. (On a fork, click *Enable workflows* first. Pushing a tag like `v1.0.0` auto-publishes the EXE to Releases.) | **Nothing** |
| **Double-click** | `Build-Diorite-Installer.bat` (repo root) | Node 20+, Python 3.11+ |
| **Terminal** | `npm run make:exe` or `npm run build:installer` | Node 20+, Python 3.11+ |

Output: `dist/installer/Diorite-Setup-<version>-x64.exe` — that ONE file is all you ever share. The EXE is built by GitHub Actions from `.github/workflows/build-installer.yml` (mirrored at `installer/workflows/build-installer.yml` for reference). Push a tag like `v1.0.0` and GitHub automatically attaches it to a Release.

### What a user does with it — two double-clicks, zero tools

1. Double-click `Diorite-Setup-*.exe` → installs itself (**one-click**, no wizard questions), desktop + Start Menu shortcut appears.
2. Double-click the **Diorite** shortcut → app opens.

The backend ships **frozen inside the app** (PyInstaller), the frontend is embedded, and the app downloads its own JDK/Gradle into `%APPDATA%\Diorite` on first use — so end users need **no Python, Node, JDK, or Gradle**. Non-Windows builds (mac DMG, Linux AppImage) use the same `npm run make:exe` on the matching OS.

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
│  ├─ run_backend.py (entry — used by PyInstaller)
│  ├─ diorite-backend.spec (freezes backend to ONE exe)
├─ frontend/
│  ├─ src/{App, main, components/{TopBar,PlayButton,ProjectExplorer,Editor,Terminal,ScaffoldMenu,AIChatPanel,NewProjectModal,StatusBar,Sidebar}, api/client, stores/{projectStore,editorStore}, hooks/useWebSocket}
│  └─ vite.config.ts (proxies /api and /ws to :7331)
├─ electron/
│  ├─ src/{main.ts (spawns backend), preload.ts}
│  └─ package.json
├─ installer/electron-builder.yml (ONE-CLICK NSIS EXE, DMG, AppImage)
├─ assets/{logo.svg, logo.png, icons/{icon.png, icon.ico, icon-256.png}}
├─ .github/workflows/build-installer.yml (cloud build — no local install needed → Actions → Run → EXE)
├─ scripts/{build-installer.js, run-dev.js, install.bat, install.sh}
├─ Build-Diorite-Installer.bat (ONE double-click → EXE)
├─ build-installer.sh (macOS/Linux equivalent)
├─ installer/{electron-builder.yml, workflows/build-installer.yml (mirror), README.md}
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
