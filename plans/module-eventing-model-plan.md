# Module Plan: Eventing Model

## Module scope and intent

- Replace global Blinker-style signaling with typed scoped events between app core and UI.
- Legacy anchor: broad signaling in [`events.py`](old_app/src/yacl/services/events.py).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Implement minimal typed event bus for vertical-slice workflows.

### 2) Key tasks and explicit sequencing

- Define event categories and payload contracts.
- Implement publisher/subscriber interfaces with scope boundaries.
- Connect core workflow progress events to UI consumers.

### 3) Dependencies and prerequisites

- Requires game orchestration and diagnostics baseline contracts.

### 4) Design decisions and integration decisions

- Events are typed and versioned; no free-form global signal channels.

### 5) Data model and API contract impacts

- Define event envelope and per-event payload schema.

### 6) Testing and validation approach

- Unit: event serialization and subscriber filtering.
- Integration: event flow from operation start to UI state update.

### 7) Rollout steps and operational guardrails

- Keep event categories minimal to limit early coupling.

### 8) Risks and mitigations

- Risk: accidental recreation of global coupling patterns.
- Mitigation: enforce bounded context ownership per event category.

### 9) Completion criteria

- Vertical slice runs with typed events and no dependency on legacy event model.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Expand event contracts for retry, cancellation, and recovery lifecycle.

### 2) Key tasks and explicit sequencing

- Add operation lifecycle event series.
- Add failure-classification event variants.
- Add backpressure handling for high-frequency progress events.

### 3) Dependencies and prerequisites

- Requires install hardening and diagnostics correlation IDs.

### 4) Design decisions and integration decisions

- Distinguish domain events from UI-only presentation events.

### 5) Data model and API contract impacts

- Add correlation and causation fields for event chains.

### 6) Testing and validation approach

- Integration: ordering guarantees and duplicate suppression.

### 7) Rollout steps and operational guardrails

- Event schema compatibility checks as release gate.

### 8) Risks and mitigations

- Risk: event storm impacts UI responsiveness.
- Mitigation: throttled progress events and bounded queues.

### 9) Completion criteria

- Eventing remains reliable under concurrent operations.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Emit migration readiness and migration outcome events.

### 2) Key tasks and explicit sequencing

- Add migration begin/progress/result event contracts.
- Map migration events to diagnostics and UI summary surfaces.

### 3) Dependencies and prerequisites

- Requires settings/storage migration workflows.

### 4) Design decisions and integration decisions

- Migration events must preserve clear causality to startup lifecycle events.

### 5) Data model and API contract impacts

- Extend event schema with migration artifact references.

### 6) Testing and validation approach

- Integration: migration flow emits complete event chain.

### 7) Rollout steps and operational guardrails

- Block release if mandatory migration events are missing in test scenarios.

### 8) Risks and mitigations

- Risk: consumers mis-handle new event variants.
- Mitigation: versioned schema and default-safe event handling.

### 9) Completion criteria

- Migration observability complete through eventing layer.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Add backup lifecycle events and restore safety events.

### 2) Key tasks and explicit sequencing

- Define backup create/delete/restore event taxonomy.
- Integrate restore critical-section events with launch/install guardrails.

### 3) Dependencies and prerequisites

- Requires backup module and lifecycle arbitration logic.

### 4) Design decisions and integration decisions

- Backup events classified as safety-critical with strict contract validation.

### 5) Data model and API contract impacts

- Add backup transaction ids and integrity status fields.

### 6) Testing and validation approach

- Integration: restore event ordering under failure injection.

### 7) Rollout steps and operational guardrails

- Gate backup rollout on verified event coverage and ordering behavior.

### 8) Risks and mitigations

- Risk: missed restore completion event leaves system blocked.
- Mitigation: timeout recovery and reconciliation on startup.

### 9) Completion criteria

- Backup operations reliably represented by typed event sequences.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Stabilize eventing contracts as long-term internal API.

### 2) Key tasks and explicit sequencing

- Freeze schema versions and deprecate transitional event types.
- Publish module event contract catalog.

### 3) Dependencies and prerequisites

- Requires all module channels to adopt stable event contracts.

### 4) Design decisions and integration decisions

- Controlled evolution through versioned additions, not breaking rewrites.

### 5) Data model and API contract impacts

- Mark event envelope v1 as baseline for maintenance.

### 6) Testing and validation approach

- Contract compatibility tests in CI for all producer-consumer pairs.

### 7) Rollout steps and operational guardrails

- Promotion blocked on contract test pass and event coverage metrics.

### 8) Risks and mitigations

- Risk: hidden consumer dependencies on deprecated fields.
- Mitigation: deprecation telemetry and staged removal windows.

### 9) Completion criteria

- Eventing model supports stable release operations without legacy bus dependencies.
