# Module Plan: Activation and Launch Runtime

## Module scope and intent

- Manage active installation selection and cross-platform launch process lifecycle.
- Legacy anchors: activation/launch logic in [`installation_manager.py`](old_app/src/yacl/models/installation_manager.py), platform branching described in [`legacy-old-app-high-level-design.md`](plans/legacy-old-app-high-level-design.md).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Provide activation switch and launch command for one supported executable layout.

### 2) Key tasks and explicit sequencing

- Implement active installation selector.
- Implement executable resolution and launch invocation wrapper.
- Wire launch status feedback back to UI diagnostics stream.

### 3) Dependencies and prerequisites

- Requires installation metadata registration and paths abstraction.

### 4) Design decisions and integration decisions

- Isolate OS-specific launch details behind platform adapter boundary.

### 5) Data model and API contract impacts

- Add active installation record and launch session id contract.

### 6) Testing and validation approach

- Unit: executable resolution rules.
- Integration: launch invocation with mocked process adapter.

### 7) Rollout steps and operational guardrails

- Disallow launch when activation state invalid or stale.

### 8) Risks and mitigations

- Risk: launching wrong executable due to path ambiguity.
- Mitigation: deterministic executable selection rules and validation.

### 9) Completion criteria

- Active install can be launched and resume state reflected to UI.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Harden process tracking, failure diagnostics, and resume detection.

### 2) Key tasks and explicit sequencing

- Add process lifecycle observer and exit code mapping.
- Add launch preflight checks for path/executable permissions.
- Add resume detection after unexpected termination.

### 3) Dependencies and prerequisites

- Requires diagnostics service and eventing contracts.

### 4) Design decisions and integration decisions

- Launch preflight emits structured failure categories before spawn attempt.

### 5) Data model and API contract impacts

- Add launch diagnostic event schema and termination reason fields.

### 6) Testing and validation approach

- Integration: launch failures across representative permission/path cases.

### 7) Rollout steps and operational guardrails

- Enable strict preflight checks in internal channel first.

### 8) Risks and mitigations

- Risk: over-strict checks block valid edge environments.
- Mitigation: severity tiers and override path with diagnostics.

### 9) Completion criteria

- Launch failures are diagnosable and mapped to actionable user messages.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Migrate active-install pointers and launch preferences from legacy metadata.

### 2) Key tasks and explicit sequencing

- Map legacy active state to new schema.
- Validate executable path compatibility.

### 3) Dependencies and prerequisites

- Requires installation migration outputs and settings policy migration.

### 4) Design decisions and integration decisions

- Favor safe deactivation over risky auto-activation when validation uncertain.

### 5) Data model and API contract impacts

- Add active-state migration marker and confidence level.

### 6) Testing and validation approach

- Integration: migrated active install launch viability checks.

### 7) Rollout steps and operational guardrails

- Auto-rollback to inactive state if migrated launch fails critical validation.

### 8) Risks and mitigations

- Risk: user perceives lost active selection.
- Mitigation: explicit migration notice and one-click reactivation path.

### 9) Completion criteria

- Migrated activation states either valid or safely recoverable.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Ensure launch operations coordinate with backup restore windows.

### 2) Key tasks and explicit sequencing

- Block launch while restore critical section active.
- Add explicit post-restore revalidation before relaunch.

### 3) Dependencies and prerequisites

- Requires backup restore state events.

### 4) Design decisions and integration decisions

- Enforce strict no-launch policy during restore writes.

### 5) Data model and API contract impacts

- Add launch-block reason contract linked to backup state.

### 6) Testing and validation approach

- E2E: restore then launch checks on supported platforms.

### 7) Rollout steps and operational guardrails

- Keep restore-launch guardrails non-configurable for safety.

### 8) Risks and mitigations

- Risk: false-positive launch block.
- Mitigation: restore state timeout and operator diagnostics.

### 9) Completion criteria

- No launch while restore write window active and no unsafe bypasses.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Stabilize cross-platform launch matrix and finalize runtime support policy.

### 2) Key tasks and explicit sequencing

- Freeze platform adapter contract.
- Document known unsupported launch edge cases.

### 3) Dependencies and prerequisites

- Requires rollout telemetry and packaging validation artifacts.

### 4) Design decisions and integration decisions

- Keep launch runtime self-contained and decoupled from UI toolkit choices.

### 5) Data model and API contract impacts

- Finalize launch event categories and diagnostic payload version.

### 6) Testing and validation approach

- Broad E2E launch matrix per OS, install variant, and migration scenario.

### 7) Rollout steps and operational guardrails

- Gate broad rollout on launch success and crash rate metrics.

### 8) Risks and mitigations

- Risk: edge OS differences discovered late.
- Mitigation: staged channel exposure and rapid hotfix path.

### 9) Completion criteria

- Activation and launch runtime stable for legacy retirement.
