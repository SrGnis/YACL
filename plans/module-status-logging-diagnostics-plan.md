# Module Plan: Status Logging and Diagnostics

## Module scope and intent

- Provide unified diagnostics for user-visible status, operational logs, and troubleshooting metadata.
- Legacy anchors: log bridge patterns in [`logging_handler.py`](old_app/src/yacl/utils/logging_handler.py) and event-based status updates.

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Deliver basic unified status stream to UI plus local file logging.

### 2) Key tasks and explicit sequencing

- Define diagnostic event taxonomy baseline.
- Implement status sink consumed by UI shell.
- Implement local log writer and startup diagnostic entries.

### 3) Dependencies and prerequisites

- Requires lifecycle events and core workflow event emission.

### 4) Design decisions and integration decisions

- Structured diagnostic events preferred over unstructured ad-hoc messages.

### 5) Data model and API contract impacts

- Define diagnostic envelope with timestamp, category, severity, correlation id.

### 6) Testing and validation approach

- Unit: event formatting and severity mapping.
- Integration: vertical-slice operations produce correlated diagnostics.

### 7) Rollout steps and operational guardrails

- Default to local-only diagnostics to avoid external telemetry dependency.

### 8) Risks and mitigations

- Risk: noisy status stream hides critical failures.
- Mitigation: severity gating and category filtering.

### 9) Completion criteria

- Users and operators can observe key operation progress and failures.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Add operation correlation, error classification, and troubleshooting clarity.

### 2) Key tasks and explicit sequencing

- Add correlation ID propagation across release/install/launch workflows.
- Define failure signature mapping for common scenarios.

### 3) Dependencies and prerequisites

- Requires eventing model stabilization and orchestrator context ids.

### 4) Design decisions and integration decisions

- Preserve user-friendly messaging while retaining detailed operator diagnostics.

### 5) Data model and API contract impacts

- Extend envelope with remediation hint and subsystem tags.

### 6) Testing and validation approach

- Integration: induced failures produce expected classified diagnostics.

### 7) Rollout steps and operational guardrails

- Add diagnostic completeness checklist to phase gate.

### 8) Risks and mitigations

- Risk: mismatched correlation IDs across modules.
- Mitigation: centralized correlation context provider.

### 9) Completion criteria

- High-priority failure scenarios are traceable end-to-end.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Add migration diagnostics and compatibility assessment reporting.

### 2) Key tasks and explicit sequencing

- Add migration event categories.
- Emit before/after migration summary and warning states.

### 3) Dependencies and prerequisites

- Requires settings/storage migration workflows.

### 4) Design decisions and integration decisions

- Migration diagnostics are mandatory and human-readable.

### 5) Data model and API contract impacts

- Add migration verdict fields and impacted artifact references.

### 6) Testing and validation approach

- Integration: migration dry-run and apply-run diagnostics validation.

### 7) Rollout steps and operational guardrails

- Block silent migration failures; diagnostics must surface to UI and logs.

### 8) Risks and mitigations

- Risk: diagnostic verbosity overwhelms users.
- Mitigation: separate user summary from detailed technical log entries.

### 9) Completion criteria

- Migration outcomes are clearly observable and actionable.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Add backup and restore diagnostic depth for safety-critical operations.

### 2) Key tasks and explicit sequencing

- Add preflight result events and restore stage logging.
- Add integrity check diagnostics for backup snapshots.

### 3) Dependencies and prerequisites

- Requires backup service and UI backup workflow integration.

### 4) Design decisions and integration decisions

- Backup diagnostics include explicit risk context for destructive steps.

### 5) Data model and API contract impacts

- Add backup-specific event tags and restore transaction id.

### 6) Testing and validation approach

- E2E: backup failure scenarios produce complete diagnostics trail.

### 7) Rollout steps and operational guardrails

- Gate backup rollout on diagnosability acceptance criteria.

### 8) Risks and mitigations

- Risk: missing diagnostic step in restore sequence.
- Mitigation: restore stage contract requires mandatory emitted events.

### 9) Completion criteria

- Restore incidents can be triaged from logs without reproducing locally.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Stabilize diagnostics taxonomy and operational playbooks.

### 2) Key tasks and explicit sequencing

- Freeze event taxonomy and severity policy.
- Publish troubleshooting runbooks keyed by diagnostic signatures.

### 3) Dependencies and prerequisites

- Requires production incident feedback from staged channels.

### 4) Design decisions and integration decisions

- Favor taxonomy stability to support support tooling and documentation.

### 5) Data model and API contract impacts

- Mark diagnostic envelope version as stable baseline.

### 6) Testing and validation approach

- Regression for diagnostic contract compatibility.

### 7) Rollout steps and operational guardrails

- Promote channels only after diagnostics coverage thresholds are met.

### 8) Risks and mitigations

- Risk: taxonomy churn causes support confusion.
- Mitigation: governed change process and deprecation windows.

### 9) Completion criteria

- Diagnostics module supports stable operations during and after legacy retirement.
