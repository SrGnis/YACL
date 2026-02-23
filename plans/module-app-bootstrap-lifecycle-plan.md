# Module Plan: App Bootstrap and Lifecycle

## Module scope and intent

- New responsibility: process startup, dependency wiring, lifecycle transitions, graceful shutdown, degraded mode entry.
- Legacy anchors: [`YACLApplication`](old_app/src/yacl/application.py), startup route in [`main.py`](old_app/src/yacl/main.py).
- Primary boundary: UI launch and workflow services consume lifecycle state; they do not own initialization orchestration.

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Create deterministic startup sequence for JavaFX shell + embedded Spring Boot core.
- Implement startup checks for filesystem path readiness and baseline settings load.

### 2) Key tasks and explicit sequencing

- Define lifecycle state model `BOOTING -> READY -> SHUTTING_DOWN`.
- Wire startup coordinator first, then initialize settings/paths, then initialize UI shell.
- Add controlled shutdown hook after vertical-slice game flow is connected.

### 3) Dependencies and prerequisites

- Requires initial module skeleton and dependency injection boundary from app core.
- Depends on initial settings repository and paths adapter availability.

### 4) Design decisions and integration decisions

- Prefer explicit startup phases over implicit lazy initialization.
- Fail hard only on critical path failures; non-critical integration readiness enters degraded mode.

### 5) Data model and API contract impacts

- Introduce lifecycle snapshot record persisted in runtime memory only for Phase 1.
- Expose minimal lifecycle query contract consumed by UI shell status banner.

### 6) Testing and validation approach

- Unit: lifecycle state transition validation and startup sequence ordering tests.
- Integration: startup with missing optional network availability enters degraded mode.
- E2E: application starts, installs one release, and exits cleanly.

### 7) Rollout steps and operational guardrails

- Keep startup diagnostics verbose for early channels.
- Prevent automatic destructive migration actions during startup.

### 8) Risks and mitigations

- Risk: startup deadlocks from cross-module init coupling.
- Mitigation: single startup coordinator and strict ordering contract.

### 9) Completion criteria

- Observable deterministic startup sequence in logs.
- App reaches READY state under normal and offline scenarios.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Add startup timeout governance and shutdown drain behavior for active tasks.

### 2) Key tasks and explicit sequencing

- Add startup phase timers and thresholds.
- Add shutdown pre-stop handshake with long-running operations.
- Add recovery path for interrupted previous session marker.

### 3) Dependencies and prerequisites

- Requires operation tracking from install and release modules.

### 4) Design decisions and integration decisions

- Shutdown favors data integrity over speed; blocks exit until critical writes are safe.

### 5) Data model and API contract impacts

- Persist last-session termination marker and recovery-needed flag.

### 6) Testing and validation approach

- Integration: forced exit during install then restart recovery path check.
- E2E: safe shutdown while background fetch is active.

### 7) Rollout steps and operational guardrails

- Enable hardened shutdown policy first in internal channel.

### 8) Risks and mitigations

- Risk: user-perceived slow exits.
- Mitigation: progress feedback plus capped graceful wait fallback.

### 9) Completion criteria

- No metadata corruption in repeated forced interruption test matrix.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Integrate legacy metadata migration checkpoints into startup.

### 2) Key tasks and explicit sequencing

- Add dry-run migration check.
- Add pre-write backup of legacy config artifacts.
- Add explicit migration result surfacing in startup status.

### 3) Dependencies and prerequisites

- Requires schema versioning policy from settings/storage modules.

### 4) Design decisions and integration decisions

- Migration decisions are explicit and auditable at startup; no hidden key remapping.

### 5) Data model and API contract impacts

- Add migration report object and compatibility verdict contract.

### 6) Testing and validation approach

- Integration tests with representative legacy directory fixtures.

### 7) Rollout steps and operational guardrails

- Block write migration when compatibility confidence checks fail.

### 8) Risks and mitigations

- Risk: false-positive incompatibility blocks legitimate users.
- Mitigation: override path with warning and preserved backup snapshot.

### 9) Completion criteria

- Migration readiness summary visible on startup and logged deterministically.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Ensure lifecycle participates in backup-safe windows during restore operations.

### 2) Key tasks and explicit sequencing

- Add lifecycle lock to prevent concurrent shutdown with critical restore write window.
- Add startup guard for incomplete restore marker.

### 3) Dependencies and prerequisites

- Requires backup module restore state exposure.

### 4) Design decisions and integration decisions

- Lifecycle arbitration service owns conflict policy between restore and app exit.

### 5) Data model and API contract impacts

- Add restore-in-progress marker contract.

### 6) Testing and validation approach

- Integration: shutdown request during restore path.

### 7) Rollout steps and operational guardrails

- Gate full rollout on restore interruption simulations.

### 8) Risks and mitigations

- Risk: stuck lock state after crash.
- Mitigation: startup lock expiry and repair routine.

### 9) Completion criteria

- No unhandled shutdown/restore race failures in chaos scenarios.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Finalize lifecycle telemetry events and legacy launcher coexistence handling.

### 2) Key tasks and explicit sequencing

- Add rollout-channel lifecycle event tagging.
- Add one-time legacy retirement notice orchestration.
- Freeze lifecycle contract for post-release maintenance.

### 3) Dependencies and prerequisites

- Depends on packaging channel strategy and diagnostics aggregation.

### 4) Design decisions and integration decisions

- Keep local-first diagnostics; no runtime dependency on remote service.

### 5) Data model and API contract impacts

- Lifecycle event categories finalized as stable internal contract.

### 6) Testing and validation approach

- E2E: install upgrade path from legacy environment through modern launcher startup.

### 7) Rollout steps and operational guardrails

- Canary, limited external, broad rollout with rollback trigger conditions.

### 8) Risks and mitigations

- Risk: retirement messaging confuses users.
- Mitigation: simple stateful one-time messaging tied to migration detection.

### 9) Completion criteria

- Stable startup and shutdown behavior across rollout channels with no priority incidents.
