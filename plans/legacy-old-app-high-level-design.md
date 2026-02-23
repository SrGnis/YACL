# Legacy `old_app` High-Level Design (Current Python/Tkinter Application)

This document captures the **current-state** high-level design of the legacy launcher implemented in `old_app` (Python + Tkinter), based on repository evidence and the prior analysis draft.

## 1) Purpose and scope

- The legacy application is a desktop launcher for Cataclysm variants that supports:
  - Release discovery/search
  - Download and installation
  - Activation/switching between installed versions
  - Launch/resume workflows
  - Save backup/restore operations
- The product intent is described in `old_app/README.md`.
- Runtime entry path:
  - `old_app/src/yacl/main.py`
  - then `old_app/src/yacl/application.py`
- Packaging/distribution targets executable binaries (build tooling around setuptools + Nuitka).

**Assumptions / Gaps**

- README feature narrative appears partially outdated relative to implemented backup capabilities visible in source controllers/models.
- No formal external product requirements document was found beyond repository docs.

## 2) Quick summary

- Boot sequence initializes core infrastructure (paths, settings, events, downloader, icon service), then opens Tk root and constructs tabbed main UI.
- Cross-component coordination is primarily event-driven via Blinker-backed event service.
- Main lifecycle is centralized in `YACLApplication` methods:
  - `initialize()`
  - `run()`
  - `shutdown()`
- Primary user tabs:
  - Game
  - Backups
  - Settings
- Core domain managers:
  - Release manager
  - Installation manager
  - Backup manager

**Assumptions / Gaps**

- Exact sequencing details for every initialization side effect are inferred from code structure and may vary slightly by error path.

## 3) User-facing behavior

- **Game tab workflows**
  - Select game type/channel/variant.
  - Search/filter releases.
  - Select release asset when multiple candidates exist.
  - Install selected build.
  - Activate installed version.
  - Launch or resume game process.
- **Backups tab workflows**
  - List backups.
  - Create backup from current save context.
  - Delete backup.
  - Restore backup into active save location.
- **Settings tab workflows**
  - Toggle launcher behavior and DB/caching-related options.
  - Save settings.
  - Reset settings to defaults.
- **Status and messaging**
  - Status/log pane surfaces progress and operational messages.
  - User-facing error/status notifications are routed through UI messaging/event patterns.
- **Dialogs**
  - Asset selection dialog for install decisions.
  - Download progress dialog for long-running transfers.

**Assumptions / Gaps**

- Some UX semantics (exact button labels, microcopy, and disabled-state rules) were inferred from view/controller code and may differ slightly by platform/theme.

## 4) System context

- External integrations:
  - GitHub Releases API for release metadata/assets.
  - Remote cataclysm-db artifacts/endpoints for additional release database data.
- Local resources:
  - Filesystem storage for installs, saves, backups, config, cache, and logs.
- Process control:
  - Launcher spawns OS processes for game executables.
- Platform coverage:
  - Linux and Windows support indicated by docs and launch/install branching.

**Assumptions / Gaps**

- macOS behavior is not a documented or evidenced primary target in analyzed files.

## 5) Architecture overview

The application follows a layered, MVC-influenced, event-driven desktop architecture:

- **Bootstrap/Lifecycle**: `YACLApplication` wires services, managers, controllers, and root UI.
- **View layer**: Tk windows, tabs, and dialogs render interaction surfaces.
- **Controller layer**: Tab-specific controllers orchestrate user actions, background work, and state updates.
- **Domain layer**: Release/Installation/Backup managers with model entities encapsulate core launcher logic.
- **Infrastructure layer**: Events, settings, paths, downloader, icon service, and DB-access services provide shared capabilities.
- **Observability bridge**: Logging/status events are propagated to UI status output.

Text diagram:

```text
main.py -> YACLApplication
           |
           +--> Infra Services (paths/settings/events/downloader/icon/cataclysm-db)
           +--> Domain Managers (release/install/backup)
           +--> Controllers (game/backups/settings)
           +--> Views (main window + tabs + dialogs)
                    |
                    +--> User actions/events <--> controllers/managers

Logging --> UI status stream
```

**Assumptions / Gaps**

- Architecture boundaries are mostly conventional rather than strictly enforced by framework constraints.

## 6) Component inventory

### App entry and lifecycle

- **Modules**: `old_app/src/yacl/main.py`, `old_app/src/yacl/application.py`
- **Responsibility**: Startup/shutdown orchestration, dependency wiring, and UI loop initiation.
- **Key classes/functions**: `YACLApplication` lifecycle methods.
- **Inputs/outputs**:
  - Input: runtime environment, config files, command invocation.
  - Output: initialized app state, active Tk main window, logs/status.
- **Dependencies**: services, managers, window manager, controllers.
- **Complexity/risk**: High coupling point; failures here block all app functionality.

### Windowing and shell UI

- **Modules**: `old_app/src/yacl/ui/window_manager.py`, `old_app/src/yacl/views/main_window.py`, `old_app/src/yacl/ui/startup_window.py`
- **Responsibility**: Root window creation, startup/splash flow, tab container composition, status area.
- **Inputs/outputs**: user interactions in Tk widgets; emits UI events and visual state updates.
- **Dependencies**: Tkinter, theme assets, controller callbacks.
- **Complexity/risk**: Medium; UI thread constraints and widget lifecycle ordering are sensitive.

### Tabs and dialog views

- **Modules**:
  - Tabs: `old_app/src/yacl/views/tabs/game_tab.py`, `backup_tab.py`, `settings_tab.py`
  - Dialogs: `old_app/src/yacl/views/dialogs/asset_install_selection_dialog.py`, `download_progress_dialog.py`
- **Responsibility**: Concrete UI controls for each workflow.
- **Inputs/outputs**: user selections/commands; display lists/progress/errors.
- **Dependencies**: base widget abstractions, controller APIs.
- **Complexity/risk**: Medium; state synchronization across async operations.

### Controllers

- **Modules**: `old_app/src/yacl/controllers/game_tab_controller.py`, `backup_tab_controller.py`, `settings_tab_controller.py`
- **Responsibility**: Orchestrate tab actions, call managers/services, translate domain outcomes into UI updates.
- **Inputs/outputs**:
  - Input: UI events/actions.
  - Output: view model updates, dialogs, status/error events.
- **Dependencies**: managers + event service + settings.
- **Complexity/risk**: High in game tab controller due to breadth (search/install/launch/activate).

### Release subsystem

- **Modules**: `old_app/src/yacl/models/release_manager.py`, `release.py`, `old_app/src/yacl/utils/release_search.py`, `old_app/src/yacl/services/cataclysm_db.py`
- **Responsibility**: Fetch/cache/normalize/filter release metadata from external sources.
- **Inputs/outputs**:
  - Input: channel/game selection, cache freshness policy.
  - Output: release/asset candidates for install operations.
- **Dependencies**: downloader/network services, cache files, settings.
- **Complexity/risk**: High; external API drift and cache consistency are key risks.

### Installation subsystem

- **Modules**: `old_app/src/yacl/models/installation_manager.py`, `installation.py`
- **Responsibility**: Download, extract, track, activate, and launch installations.
- **Inputs/outputs**:
  - Input: selected release asset and destination paths.
  - Output: installed game files + installation metadata + active installation state.
- **Dependencies**: downloader, file operations, platform-specific launch behavior.
- **Complexity/risk**: High; file/process operations and recovery after partial installs.

### Backup subsystem

- **Modules**: `old_app/src/yacl/models/backup_manager.py`, `backup.py`
- **Responsibility**: Enumerate/create/delete/restore backup snapshots for saves.
- **Inputs/outputs**:
  - Input: active installation/save location and backup commands.
  - Output: backup directories/archives and restore outcomes.
- **Dependencies**: file operations, installation context.
- **Complexity/risk**: Medium-high; data-loss risk if restore/delete operations fail mid-step.

### Infrastructure services

- **Modules**:
  - Events: `old_app/src/yacl/services/events.py`
  - Settings: `old_app/src/yacl/services/settings.py`
  - Paths: `old_app/src/yacl/services/paths.py`
  - Downloader: `old_app/src/yacl/services/downloader.py`
  - Icons: `old_app/src/yacl/services/icon_service.py`
  - DB fetch integration: `old_app/src/yacl/services/cataclysm_db.py`
- **Responsibility**: Shared cross-cutting concerns.
- **Inputs/outputs**: config, network requests, local paths, event emissions.
- **Complexity/risk**: Medium; broad blast radius when behavior changes.

### Utilities

- **Modules**: `old_app/src/yacl/utils/file_ops.py`, `helpers.py`, `logging_handler.py`
- **Responsibility**: reusable file helpers, formatting/support utilities, log-to-UI plumbing.
- **Complexity/risk**: Medium; utility bugs can produce systemic side effects.

**Assumptions / Gaps**

- Responsibilities are summarized at high level; not every helper function is individually cataloged.

## 7) Data model and storage

- **Configuration JSON**
  - Core and user settings initialized from bundled defaults:
    - `old_app/src/yacl/resources/config/core_defaults.json`
    - `old_app/src/yacl/resources/config/user_defaults.json`
- **Release cache**
  - Local JSON files for cached release payloads plus index/metadata tracking.
- **Installation metadata**
  - Per-installation metadata file (`installation.json`) describing installation state/details.
- **Backup storage**
  - Backups persisted as filesystem directories containing archived save data.
- **Path layout root**
  - User-scoped root under `~/yacl` with subdirectories for installs/saves/backups/config/cache/logs.
- **Database model**
  - No relational database usage observed; persistent state is file-based (JSON + directories/files).

**Assumptions / Gaps**

- Exact on-disk schema fields may evolve; this section focuses on structural storage patterns rather than full key-level specs.

## 8) Key data flows

### Startup sequence

- **Trigger**: User launches executable/entry script.
- **Components**: `main.py` -> `YACLApplication` -> services/managers/windowing.
- **Read/write data**:
  - Reads defaults and existing user config/cache.
  - Creates required directories/files when missing.
- **External calls**: Optional early network readiness/deferred fetch behavior depending on settings/actions.
- **Failure/retry**: Startup exceptions are logged and surfaced; app may continue in degraded mode where feasible.

### Release retrieval (remote vs cache freshness)

- **Trigger**: Game tab search/refresh or startup preload action.
- **Components**: game controller -> release manager -> cataclysm-db/GitHub integration.
- **Read/write data**:
  - Reads cache index/entries and freshness markers.
  - Writes refreshed cache payloads and timestamps.
- **External calls**: REST/JSON GET to remote release sources.
- **Failure/retry**:
  - Retries/timeouts in downloader path (high-level).
  - Cache fallback used when remote unavailable/stale tolerance allows.

### Install flow (download -> extract -> metadata -> activate)

- **Trigger**: User selects release asset and confirms install.
- **Components**: game controller -> downloader/dialog -> installation manager/file ops.
- **Read/write data**:
  - Reads release/asset URL + install settings.
  - Writes downloaded artifact, extracted files, and `installation.json`.
  - Updates active installation linkage/state.
- **External calls**: Artifact download over HTTPS.
- **Failure/retry**:
  - Download retries/progress error reporting.
  - Partial install cleanup/recovery behavior is best-effort.

### Launch/resume flow

- **Trigger**: User clicks launch/resume for active installation.
- **Components**: game controller -> installation manager/process launch utilities.
- **Read/write data**:
  - Reads active installation metadata and executable path.
  - May write last-run/status/log records.
- **External calls**: Local OS process spawn.
- **Failure/retry**:
  - Launch errors surfaced to UI/status.
  - Retry is user-initiated (relaunch after correction).

### Backup create/restore flow

- **Trigger**: User initiates backup or restore in Backups tab.
- **Components**: backup controller -> backup manager -> file operations.
- **Read/write data**:
  - Create: reads save data; writes backup snapshot directory/archive.
  - Restore: reads chosen snapshot; writes into active save location.
- **External calls**: None expected (local filesystem operations).
- **Failure/retry**:
  - Errors emitted to UI/status.
  - User can retry operations; restore correctness depends on source snapshot integrity.

**Assumptions / Gaps**

- Fine-grained retry policy values (counts/backoff) are not fully enumerated in this high-level summary.

## 9) Integrations & protocols

- **Protocols/formats**
  - HTTP(S) REST endpoints returning JSON payloads.
  - Primary integrations: GitHub Releases + cataclysm-db artifacts.
- **Authentication**
  - Default operation appears unauthenticated against public endpoints.
  - Optional token usage may be supported via environment configuration (e.g., GitHub token), if present.
- **Request/response shape (high level)**
  - Requests: release list or artifact metadata/resource URLs.
  - Responses: release entries, assets, tags/channels, and downloadable artifacts.
- **Reliability controls**
  - Timeouts/retries in network layer; cache fallback path for resilience.
- **Idempotency/order considerations**
  - Fetch operations are effectively idempotent reads.
  - Install/activate operations are order-sensitive (download/extract before activation/launch).
- **Error mapping**
  - Transport/data errors translated to status logs and user-visible error messages.

**Assumptions / Gaps**

- Full endpoint matrix and exact JSON schema contracts are not exhaustively documented in repository docs.

## 10) Configuration and environments

- **Configuration sources**
  - Bundled defaults (core/user) in packaged resources.
  - User/core config files persisted under launcher data paths.
  - Runtime platform detection branches behavior (Linux/Windows logic).
  - Optional environment-based token for API requests (if configured).
- **Profiles**
  - No formal dev/test/prod profile system observed in legacy app runtime configuration.
- **Feature toggles**
  - User settings expose toggles impacting launcher behavior and cache/DB interactions.
- **Secrets handling**
  - No dedicated secret vault integration observed.
  - Secrets likely limited to optional API token via environment/user context.

**Assumptions / Gaps**

- Exact precedence rules among defaults/env/user files are inferred at high level and may include edge-case overrides.

## 11) Non-functional requirements

- **Responsiveness**
  - Long-running tasks (download/fetch/install) are offloaded from main UI thread using background/threaded execution patterns.
- **Resilience**
  - Retry mechanisms and cache fallback reduce dependence on continuous network availability.
- **Offline tolerance**
  - Cached release data supports partial offline operations (e.g., browsing previously fetched metadata).
  - New installs requiring remote artifacts remain network-dependent.
- **Cross-platform constraints**
  - Behavior includes Linux/Windows path/process handling branches.
- **Security posture (current reality)**
  - Basic HTTPS usage and local filesystem permissions.
  - No advanced hardening/telemetry-driven security controls evident.

**Assumptions / Gaps**

- Performance SLAs and explicit reliability targets are not formally specified in repository artifacts.

## 12) Observability & diagnostics

- **Logging**
  - Application logs are written to local log destinations with configurable/used levels.
- **UI status stream**
  - Event/log bridge feeds status updates into UI status pane for user-visible diagnostics.
- **Startup diagnostics**
  - Initialization steps and failures are logged for troubleshooting.
- **Telemetry stack**
  - No full metrics/tracing/centralized telemetry system observed.

**Assumptions / Gaps**

- Log retention/rotation policy is not clearly documented in the inspected high-level files.

## 13) Deployment & packaging

- **Entry point packaging**
  - setuptools entry point is used for launcher invocation.
- **Build process**
  - Nuitka-based build flow packages Python app and resources.
- **Distribution outputs**
  - Packaged artifacts include archive formats (e.g., zip/tar.gz) with OS-specific handling.
- **Runtime prerequisites**
  - Dependencies and build prerequisites documented in:
    - `old_app/BUILDING.md`
    - `old_app/requirements.txt`
- **Update/data impact (high level)**
  - Launcher/user data under user home path is conceptually separate from packaged binaries.
  - Updates to binaries typically should preserve existing user installs/config/backups unless migration logic changes.

**Assumptions / Gaps**

- Exact release pipeline automation and signing/notarization steps are not fully visible in provided high-level evidence.

## 14) Dependencies and third-party libraries

- **Core runtime libraries identified**
  - `requests` (HTTP)
  - `blinker` (event signaling)
  - `cairosvg` + `pillow` (icon/image processing)
  - Tkinter (standard library GUI)
- **Packaging/build dependencies**
  - setuptools/build tooling and Nuitka-related stack.
- **Theming/resources**
  - Azure ttk theme submodule/assets included under resources.
- **Licensing/third-party implications**
  - Project license file exists (`old_app/LICENSE`).
  - Third-party dependency licenses must be validated per dependency metadata/distribution obligations.

**Assumptions / Gaps**

- Complete SPDX-level bill of materials and full third-party license inventory were not generated in this document.

## Evidence references

Key files used to ground this high-level design:

- `old_app/README.md`
- `old_app/src/yacl/main.py`
- `old_app/src/yacl/application.py`
- `old_app/src/yacl/controllers/game_tab_controller.py`
- `old_app/src/yacl/controllers/backup_tab_controller.py`
- `old_app/src/yacl/controllers/settings_tab_controller.py`
- `old_app/src/yacl/models/release_manager.py`
- `old_app/src/yacl/models/installation_manager.py`
- `old_app/src/yacl/models/backup_manager.py`
- `old_app/src/yacl/services/cataclysm_db.py`
- `old_app/src/yacl/services/downloader.py`
- `old_app/src/yacl/services/settings.py`
- `old_app/src/yacl/services/paths.py`
- `old_app/src/yacl/services/events.py`
- `old_app/src/yacl/views/main_window.py`
- `old_app/src/yacl/views/tabs/game_tab.py`
- `old_app/src/yacl/views/tabs/backup_tab.py`
- `old_app/src/yacl/views/tabs/settings_tab.py`
- `old_app/src/yacl/views/dialogs/asset_install_selection_dialog.py`
- `old_app/src/yacl/views/dialogs/download_progress_dialog.py`
- `old_app/BUILDING.md`
- `old_app/requirements.txt`
- `old_app/setup.py`
- `old_app/build.py`
