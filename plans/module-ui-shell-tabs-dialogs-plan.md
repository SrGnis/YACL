# Module Plan: UI Shell Tabs and Dialogs

## Module scope and intent

- Reimplement main shell, tab navigation, dialogs, and status surfaces in JavaFX.
- Legacy anchors: [`main_window.py`](old_app/src/yacl/views/main_window.py), tabs under [`views/tabs`](old_app/src/yacl/views/tabs), dialogs under [`views/dialogs`](old_app/src/yacl/views/dialogs).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Deliver JavaFX window shell with core tab scaffold and minimal dialogs needed for install flow.

### 2) Key tasks and explicit sequencing

- Implement root shell layout and status strip.
- Implement game tab first for vertical slice.
- Implement asset selection and progress dialog equivalents.

### 3) Dependencies and prerequisites

- Requires app lifecycle READY signal and initial game workflow contracts.

### 4) Design decisions and integration decisions

- Use view model driven UI state updates, no direct service calls from controls.

### 5) Data model and API contract impacts

- UI state contracts for release list, selected asset, operation progress.

### 6) Testing and validation approach

- Unit: view model state transitions.
- Integration: dialog-to-use-case command wiring.
- E2E: user installs and launches from UI shell.

### 7) Rollout steps and operational guardrails

- Guard against blocking UI thread with background task adapter.

### 8) Risks and mitigations

- Risk: regression in long-operation responsiveness.
- Mitigation: mandatory async operation wrapper and progress binding rules.

### 9) Completion criteria

- Shell renders with game workflow and dialogs functioning without UI freezes.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Expand tab state handling, error surfaces, cancellation UX, and consistency across operations.

### 2) Key tasks and explicit sequencing

- Add standardized transient and sticky error components.
- Add cancellation interaction model for downloads and refresh operations.
- Harmonize tab-disabled state policies during critical operations.

### 3) Dependencies and prerequisites

- Requires eventing and diagnostics contracts to enrich UI feedback.

### 4) Design decisions and integration decisions

- Adopt uniform command result envelope for all tab actions.

### 5) Data model and API contract impacts

- Add UI error category mapping and operation token correlation.

### 6) Testing and validation approach

- Integration: cancellation and retry flows from dialogs.

### 7) Rollout steps and operational guardrails

- Introduce UX behavior consistency checklist in release gate.

### 8) Risks and mitigations

- Risk: inconsistent state across tabs after errors.
- Mitigation: central UI state reset policies tied to operation outcomes.

### 9) Completion criteria

- Cross-tab UX consistency validated in regression suite.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Complete settings tab and migration messaging surfaces.

### 2) Key tasks and explicit sequencing

- Build settings forms and reset-to-default workflow.
- Add migration-readiness summary panel and actionable statuses.
- Add warnings for incompatible legacy data cases.

### 3) Dependencies and prerequisites

- Requires settings schema and migration assessment contracts.

### 4) Design decisions and integration decisions

- Settings UI edits are staged then committed, avoiding immediate side effects.

### 5) Data model and API contract impacts

- Add settings diff preview contract and validation message schema.

### 6) Testing and validation approach

- Unit: form validation, dirty tracking.
- E2E: settings save, restart, and persistence verification.

### 7) Rollout steps and operational guardrails

- Protect destructive settings resets behind explicit confirmation path.

### 8) Risks and mitigations

- Risk: confusing migration warnings.
- Mitigation: concise severity-based message taxonomy with remediation actions.

### 9) Completion criteria

- Settings and migration surfaces complete and validated across supported platforms.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Reintroduce backup tab UX with safer restore interaction model.

### 2) Key tasks and explicit sequencing

- Add backup list, create/delete actions, restore preflight dialog.
- Add restore conflict prompts and post-restore verification feedback.

### 3) Dependencies and prerequisites

- Requires backup domain workflows and restore guardrail policies.

### 4) Design decisions and integration decisions

- Restore path emphasizes risk disclosure and explicit confirmation before write.

### 5) Data model and API contract impacts

- Add backup summary and restore preflight result contracts.

### 6) Testing and validation approach

- E2E: backup create, restore, failure and retry sequences.

### 7) Rollout steps and operational guardrails

- Keep backup feature behind rollout flag until validation thresholds are met.

### 8) Risks and mitigations

- Risk: accidental restore overwrite.
- Mitigation: explicit source-target preview and typed confirmation step.

### 9) Completion criteria

- Backup UX stable with validated restore safety outcomes.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Final UI polish, accessibility pass, and retirement messaging.

### 2) Key tasks and explicit sequencing

- Complete keyboard navigation and focus order verification.
- Finalize launch migration guidance dialogs.

### 3) Dependencies and prerequisites

- Requires packaging channel strategy for user communication timing.

### 4) Design decisions and integration decisions

- Prefer clarity and reliability over visual parity with Tkinter legacy styles.

### 5) Data model and API contract impacts

- Stabilize UI command contract versions for maintenance.

### 6) Testing and validation approach

- E2E smoke matrix across channels.

### 7) Rollout steps and operational guardrails

- Rollout gating on critical UX defect thresholds.

### 8) Risks and mitigations

- Risk: legacy users misinterpret changed interaction patterns.
- Mitigation: contextual hints and migration tips in first-run flows.

### 9) Completion criteria

- UI shell accepted for broad release with no blocking accessibility or workflow defects.
