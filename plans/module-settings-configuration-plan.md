# Module Plan: Settings and Configuration

## Module scope and intent

- Govern defaults, user preferences, schema versioning, migration, and precedence rules.
- Legacy anchors: [`settings.py`](old_app/src/yacl/services/settings.py), defaults in [`core_defaults.json`](old_app/src/yacl/resources/config/core_defaults.json) and [`user_defaults.json`](old_app/src/yacl/resources/config/user_defaults.json).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Build baseline settings store with clear immutable defaults vs mutable user preferences.

### 2) Key tasks and explicit sequencing

- Define settings domain model.
- Implement load/validate/save flow.
- Wire critical settings into release/install vertical slice behavior.

### 3) Dependencies and prerequisites

- Requires storage adapter and lifecycle startup checks.

### 4) Design decisions and integration decisions

- Explicit precedence order and typed validation replace implicit key handling.

### 5) Data model and API contract impacts

- Introduce settings schema v1 and validation result contract.

### 6) Testing and validation approach

- Unit: defaults merge and validation logic.
- Integration: persistence across restarts.

### 7) Rollout steps and operational guardrails

- Preserve fallback defaults when user config invalid.

### 8) Risks and mitigations

- Risk: invalid config blocks startup.
- Mitigation: safe fallback with warning and non-destructive repair path.

### 9) Completion criteria

- Settings load/save stable and consumed by core workflows.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Expand settings categories tied to cache, DB source usage, and operation policies.

### 2) Key tasks and explicit sequencing

- Add policy settings for release freshness and install retries.
- Add runtime change handling rules for hot-reload vs restart-required fields.

### 3) Dependencies and prerequisites

- Requires release and install modules to consume policy contracts.

### 4) Design decisions and integration decisions

- Separate operational policies from purely presentation preferences.

### 5) Data model and API contract impacts

- Extend schema with policy sections and restart requirement metadata.

### 6) Testing and validation approach

- Integration: policy effects reflected in module behavior.

### 7) Rollout steps and operational guardrails

- Require explicit confirmation for settings that can increase operational risk.

### 8) Risks and mitigations

- Risk: policy misconfiguration degrades reliability.
- Mitigation: constrained ranges and documented safe defaults.

### 9) Completion criteria

- Policy settings are operationally effective and validated.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Implement legacy settings migration with versioned handlers.

### 2) Key tasks and explicit sequencing

- Detect legacy files and schema variants.
- Run dry-run compatibility analysis.
- Apply migration with backup and audit trail.

### 3) Dependencies and prerequisites

- Requires startup lifecycle migration checkpoints and storage migration utilities.

### 4) Design decisions and integration decisions

- Migration is explicit, logged, and reversible through preserved snapshots.

### 5) Data model and API contract impacts

- Add migration metadata: source version, transformed version, warnings.

### 6) Testing and validation approach

- Integration with representative legacy setting files.

### 7) Rollout steps and operational guardrails

- Block destructive migration if validation confidence is below threshold.

### 8) Risks and mitigations

- Risk: subtle setting semantic mismatch.
- Mitigation: compatibility mapping table and manual override support.

### 9) Completion criteria

- Legacy settings reliably migrated or safely reported for manual action.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Add backup-related settings with conservative defaults.

### 2) Key tasks and explicit sequencing

- Introduce backup retention and restore safety options.
- Validate interactions with install and launch policies.

### 3) Dependencies and prerequisites

- Requires backup module operational contracts.

### 4) Design decisions and integration decisions

- Backup safety settings default to strict mode.

### 5) Data model and API contract impacts

- Extend schema with backup policy block and migration rule.

### 6) Testing and validation approach

- Integration: backup policy changes reflected in runtime behavior.

### 7) Rollout steps and operational guardrails

- Keep advanced backup settings hidden until baseline stability confirmed.

### 8) Risks and mitigations

- Risk: overly complex settings reduce usability.
- Mitigation: progressive disclosure and safe defaults.

### 9) Completion criteria

- Backup policy settings stable without increasing user error rates.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Freeze settings schema baseline and publish evolution policy.

### 2) Key tasks and explicit sequencing

- Lock schema and deprecate transitional migration fields.
- Publish compatibility guarantees for future schema changes.

### 3) Dependencies and prerequisites

- Requires broad rollout validation and support issue analysis.

### 4) Design decisions and integration decisions

- Forward-compatible schema evolution with explicit migration path remains mandatory.

### 5) Data model and API contract impacts

- Mark schema as GA baseline with migration hook points.

### 6) Testing and validation approach

- Regression for schema read/write and migration behavior.

### 7) Rollout steps and operational guardrails

- Track settings-related incidents as release gate metrics.

### 8) Risks and mitigations

- Risk: hidden schema drift over maintenance releases.
- Mitigation: schema contract tests in release pipeline.

### 9) Completion criteria

- Settings system stable and governable for post-retirement operations.
