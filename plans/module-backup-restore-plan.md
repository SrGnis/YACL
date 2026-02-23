# Module Plan: Backup and Restore

## Module scope and intent

- Reintroduce backup create, list, delete, and restore with stronger safety guardrails.
- Legacy anchors: [`backup_manager.py`](old_app/src/yacl/models/backup_manager.py), backup tab controller and view.
- Sequencing note: intentionally deferred in early delivery phases per migration strategy.

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Define target backup contracts and storage compatibility strategy only.

### 2) Key tasks and explicit sequencing

- Document legacy backup layout assumptions.
- Define backup metadata schema and restore preflight contract.

### 3) Dependencies and prerequisites

- Requires installation path conventions and settings policy placeholders.

### 4) Design decisions and integration decisions

- Keep compatibility with existing backup storage layout.

### 5) Data model and API contract impacts

- Introduce backup metadata schema draft and compatibility markers.

### 6) Testing and validation approach

- Unit: schema validation tests only.

### 7) Rollout steps and operational guardrails

- No user-facing backup actions in this phase.

### 8) Risks and mitigations

- Risk: under-specification causes rework later.
- Mitigation: explicit contract baseline agreed before implementation.

### 9) Completion criteria

- Backup domain contract baseline approved and versioned.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Implement backend backup operations without full UI exposure.

### 2) Key tasks and explicit sequencing

- Implement enumerate/create/delete/restore service interfaces.
- Add restore preflight validation and dry-run checks.
- Add integrity verification for created snapshots.

### 3) Dependencies and prerequisites

- Requires file storage adapter and diagnostics service integration.

### 4) Design decisions and integration decisions

- Restore uses transactional staging area where practical.

### 5) Data model and API contract impacts

- Add backup manifest with source install reference and integrity status.

### 6) Testing and validation approach

- Integration: backup create and restore against fixture save datasets.

### 7) Rollout steps and operational guardrails

- Keep feature off by default outside internal validation channels.

### 8) Risks and mitigations

- Risk: restore path can overwrite active saves incorrectly.
- Mitigation: mandatory preflight and explicit restore target validation.

### 9) Completion criteria

- Backend backup workflows pass integrity and restore safety tests.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Add migration support for legacy backup index/layout metadata.

### 2) Key tasks and explicit sequencing

- Detect existing backup directories.
- Build compatibility index without rewriting snapshot content.

### 3) Dependencies and prerequisites

- Requires migration framework and path mapping from settings module.

### 4) Design decisions and integration decisions

- Non-destructive import first; no forced conversion of existing backups.

### 5) Data model and API contract impacts

- Add imported-legacy marker and validation status fields.

### 6) Testing and validation approach

- Integration fixtures from legacy backup folder structures.

### 7) Rollout steps and operational guardrails

- Backup index import logs full audit trail.

### 8) Risks and mitigations

- Risk: mixed legacy/new backup records confusion.
- Mitigation: explicit source labeling and filtered views.

### 9) Completion criteria

- Legacy backups discoverable and safe for controlled restore testing.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Enable full backup tab UX and operational guardrails.

### 2) Key tasks and explicit sequencing

- Turn on create/delete/restore UI actions.
- Add restore confirmation and conflict handling workflow.
- Add post-restore verification and recovery messaging.

### 3) Dependencies and prerequisites

- Requires UI shell backup tab and eventing contracts.

### 4) Design decisions and integration decisions

- Restore confirmation must include source snapshot identity and target path.

### 5) Data model and API contract impacts

- Add restore operation record with start/end status.

### 6) Testing and validation approach

- E2E: full backup lifecycle including failure and rollback cases.

### 7) Rollout steps and operational guardrails

- Progressive enablement: internal -> limited external -> broad.

### 8) Risks and mitigations

- Risk: high user impact from restore defects.
- Mitigation: strict rollout gate and rapid rollback switch.

### 9) Completion criteria

- Backup UX and restore flows stable under staged rollout validation.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Mature backup operations and finalize support expectations.

### 2) Key tasks and explicit sequencing

- Freeze backup schema and operation contracts.
- Publish restore incident handling playbook.

### 3) Dependencies and prerequisites

- Requires stabilization metrics from phased release channels.

### 4) Design decisions and integration decisions

- Prioritize correctness and recoverability over operation speed.

### 5) Data model and API contract impacts

- Mark backup metadata schema as GA baseline with forward migration path.

### 6) Testing and validation approach

- Regression suite for restore correctness and data integrity.

### 7) Rollout steps and operational guardrails

- Broad rollout only after no critical restore incidents in limited channel.

### 8) Risks and mitigations

- Risk: latent edge snapshot formats from old environments.
- Mitigation: compatibility parser fallback and safe refusal policy.

### 9) Completion criteria

- Backup feature accepted for broad release and sustained operations.
