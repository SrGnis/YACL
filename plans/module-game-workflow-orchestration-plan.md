# Module Plan: Game Workflow Orchestration

## Module scope and intent

- Own the end-to-end user journey: discover release, select asset, install, activate, launch or resume.
- Legacy anchor: broad orchestration in [`game_tab_controller.py`](old_app/src/yacl/controllers/game_tab_controller.py).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Implement first orchestrated use-case chain for one successful install and launch path.

### 2) Key tasks and explicit sequencing

- Define use cases and command boundaries.
- Implement sequence coordinator for discover -> select -> install -> activate -> launch.
- Surface operation status updates to UI through typed progress events.

### 3) Dependencies and prerequisites

- Requires release, install, activation modules with minimal contracts.

### 4) Design decisions and integration decisions

- Use deterministic state machine over ad-hoc controller branching.

### 5) Data model and API contract impacts

- Introduce operation context id and workflow state snapshot.

### 6) Testing and validation approach

- Unit: state transition guard tests.
- Integration: happy-path orchestration with mocked integrations.

### 7) Rollout steps and operational guardrails

- Guard against concurrent conflicting workflows for same installation target.

### 8) Risks and mitigations

- Risk: hidden coupling between stages.
- Mitigation: explicit stage contracts and immutable stage outputs.

### 9) Completion criteria

- Vertical slice completes without manual intervention on supported OS targets.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Add retry, cancellation, resume, and partial failure recovery semantics.

### 2) Key tasks and explicit sequencing

- Add operation journal checkpoints.
- Add cancellation points and rollback actions per stage.
- Add resume logic from journal checkpoints.

### 3) Dependencies and prerequisites

- Requires install pipeline checkpoint persistence and diagnostics correlation ids.

### 4) Design decisions and integration decisions

- Recovery-first design: every stage defines compensating action or safe retry policy.

### 5) Data model and API contract impacts

- Add persisted operation journal schema with stage status and error cause.

### 6) Testing and validation approach

- Integration: interruption during each stage and subsequent resume path.
- E2E: cancel and retry scenarios.

### 7) Rollout steps and operational guardrails

- Enable hardening behaviors by default in internal channel before external.

### 8) Risks and mitigations

- Risk: journal drift from actual filesystem state.
- Mitigation: reconciliation step before resume.

### 9) Completion criteria

- Recovery matrix passes for all checkpoint boundaries.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Bind orchestration behavior to configurable policies and migrated legacy preferences.

### 2) Key tasks and explicit sequencing

- Integrate settings-driven decisions for cache behavior and optional DB sources.
- Map legacy user behavior preferences to modern policy fields.

### 3) Dependencies and prerequisites

- Requires settings migration and compatibility report inputs.

### 4) Design decisions and integration decisions

- Preserve intent of legacy behaviors where practical, not strict UI parity.

### 5) Data model and API contract impacts

- Add policy snapshot into operation context for reproducibility.

### 6) Testing and validation approach

- Integration: behavior changes under policy variants.

### 7) Rollout steps and operational guardrails

- Log effective policy at operation start for support diagnostics.

### 8) Risks and mitigations

- Risk: policy combinations produce undefined behavior.
- Mitigation: policy validation gate and fallback defaults.

### 9) Completion criteria

- Orchestration outcomes stable across supported policy combinations.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Integrate backup-aware checkpoints into game workflow transitions.

### 2) Key tasks and explicit sequencing

- Add optional pre-launch backup prompt policy.
- Add restore-followed-by-launch safe sequence enforcement.

### 3) Dependencies and prerequisites

- Requires backup service readiness and restore completion event.

### 4) Design decisions and integration decisions

- Keep backup coupling minimal through explicit use-case handoff only.

### 5) Data model and API contract impacts

- Add backup precondition status in workflow context when enabled.

### 6) Testing and validation approach

- E2E: restore then activate then launch with consistency checks.

### 7) Rollout steps and operational guardrails

- Feature-flag backup-aware prompts until false-positive rate is acceptable.

### 8) Risks and mitigations

- Risk: user friction from extra prompts.
- Mitigation: policy-driven opt-in defaults and clear rationale text.

### 9) Completion criteria

- No backup-related workflow regressions in stabilization channel.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Finalize orchestration contracts and deprecate legacy assumptions.

### 2) Key tasks and explicit sequencing

- Freeze orchestrator interfaces.
- Document unsupported legacy edge behaviors and modern alternatives.

### 3) Dependencies and prerequisites

- Requires broad channel feedback and defect burn-down.

### 4) Design decisions and integration decisions

- Keep compatibility guidance explicit where behavior changed intentionally.

### 5) Data model and API contract impacts

- Mark operation journal schema version as stable baseline.

### 6) Testing and validation approach

- Regression sweep focused on high-frequency user paths.

### 7) Rollout steps and operational guardrails

- Rollout gates tied to install-to-launch success rate indicators.

### 8) Risks and mitigations

- Risk: latent edge-case failures appear in wider audience.
- Mitigation: staged rollout and fast rollback mechanism.

### 9) Completion criteria

- Stable production workflow success and no critical orchestration incidents.
