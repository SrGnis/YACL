# Module Plan: Build and Release Packaging

## Module scope and intent

- Replace Python `setup.py` and Nuitka-based packaging with Java build, runtime packaging, and release channels.
- Legacy anchors: [`setup.py`](old_app/setup.py), [`build.py`](old_app/build.py), build notes in [`BUILDING.md`](old_app/BUILDING.md).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Establish baseline Java build pipeline and local runnable packaging for vertical slice.

### 2) Key tasks and explicit sequencing

- Define build toolchain and module build boundaries.
- Produce local package artifact for internal validation.
- Verify required runtime resources included.

### 3) Dependencies and prerequisites

- Requires module structure and resource loading conventions.

### 4) Design decisions and integration decisions

- Prioritize reproducible local builds before distribution optimization.

### 5) Data model and API contract impacts

- Define artifact metadata manifest with version and commit identity.

### 6) Testing and validation approach

- Integration: build artifact boots and runs vertical slice flow.

### 7) Rollout steps and operational guardrails

- Internal-only artifact distribution in this phase.

### 8) Risks and mitigations

- Risk: missing runtime resources in packaged artifact.
- Mitigation: packaging smoke tests and resource manifest checks.

### 9) Completion criteria

- Repeatable internal package build and launch established.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Add reproducibility controls, artifact verification, and OS build matrix expansion.

### 2) Key tasks and explicit sequencing

- Add deterministic build configuration.
- Add artifact hashing and verification outputs.
- Expand packaging validations for Linux and Windows targets.

### 3) Dependencies and prerequisites

- Requires stable runtime module inputs and resource catalog.

### 4) Design decisions and integration decisions

- Build metadata and verification outputs treated as release artifacts.

### 5) Data model and API contract impacts

- Add release manifest schema with checksums and compatibility metadata.

### 6) Testing and validation approach

- Integration: packaged artifact install and run on target OS matrix.

### 7) Rollout steps and operational guardrails

- Keep strict artifact verification mandatory for promotion.

### 8) Risks and mitigations

- Risk: non-deterministic builds complicate incident response.
- Mitigation: pinned build inputs and repeat-build verification.

### 9) Completion criteria

- Verified reproducible artifacts across supported platforms.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Implement upgrade packaging path that preserves user data and performs migration safely.

### 2) Key tasks and explicit sequencing

- Define upgrade install behavior for existing users.
- Add first-run migration invocation integration.
- Validate data directory preservation across upgrades.

### 3) Dependencies and prerequisites

- Requires migration framework and lifecycle migration checks.

### 4) Design decisions and integration decisions

- Installer/packager avoids writing into user data until runtime migration logic confirms safety.

### 5) Data model and API contract impacts

- Add installer runtime handoff contract for migration-required flag.

### 6) Testing and validation approach

- E2E: legacy-to-modern upgrade path with representative user data fixtures.

### 7) Rollout steps and operational guardrails

- Controlled upgrade pilot before broad channel exposure.

### 8) Risks and mitigations

- Risk: upgrade flow corrupts existing metadata.
- Mitigation: pre-upgrade backup and rollback instructions bundled.

### 9) Completion criteria

- Upgrade path validated with preserved user data and deterministic migration entry.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Ensure packages include full backup feature dependencies and operational checks.

### 2) Key tasks and explicit sequencing

- Validate backup-specific resources and dependencies in packaged builds.
- Add release checklist items for restore safety validation.

### 3) Dependencies and prerequisites

- Requires backup feature stabilization and diagnostics readiness.

### 4) Design decisions and integration decisions

- Backup feature inclusion must align with channel flags and release confidence.

### 5) Data model and API contract impacts

- Extend release manifest with feature-flag defaults per channel.

### 6) Testing and validation approach

- E2E packaged build tests for backup create and restore workflows.

### 7) Rollout steps and operational guardrails

- Keep backup-enabled packages limited until restore reliability targets met.

### 8) Risks and mitigations

- Risk: packaging mismatch with runtime feature flags.
- Mitigation: manifest-driven feature toggle validation at startup.

### 9) Completion criteria

- Backup-capable packages validated and safely channel-scoped.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Finalize channel strategy, publish migration/rollback guidance, and retire legacy distribution.

### 2) Key tasks and explicit sequencing

- Execute phased channels internal -> limited external -> broad.
- Publish migration guide and rollback guide tied to package versions.
- Remove legacy package pipeline from active release path after stability gate.

### 3) Dependencies and prerequisites

- Requires all functional modules at acceptable stability thresholds.

### 4) Design decisions and integration decisions

- Keep rollback availability until modern launcher stability criteria are sustained.

### 5) Data model and API contract impacts

- Finalize release channel metadata and retirement marker in distribution catalog.

### 6) Testing and validation approach

- Channel-specific smoke and regression suites before each promotion.

### 7) Rollout steps and operational guardrails

- Promotion gates tied to incident thresholds and rollback readiness.

### 8) Risks and mitigations

- Risk: premature legacy retirement increases support burden.
- Mitigation: explicit stability gates and overlap window with rollback option.

### 9) Completion criteria

- Modern packaging pipeline is primary, stable, and legacy distribution retired safely.
