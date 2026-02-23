# Module Plan: Download and Install Pipeline

## Module scope and intent

- Implement staged, checkpointed, recoverable install path: fetch, validate, extract, register, activate handoff.
- Legacy anchors: [`installation_manager.py`](old_app/src/yacl/models/installation_manager.py), downloader service in [`downloader.py`](old_app/src/yacl/services/downloader.py).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Deliver single-path install pipeline for one artifact type with progress updates.

### 2) Key tasks and explicit sequencing

- Implement staged execution contract.
- Wire fetch and extract for baseline artifact flow.
- Register installation metadata and handoff to activation module.

### 3) Dependencies and prerequisites

- Requires release asset contract, paths service, and storage write adapters.

### 4) Design decisions and integration decisions

- Pipeline stage outputs are explicit immutable records.

### 5) Data model and API contract impacts

- Define installation metadata v1 and stage checkpoint shape.

### 6) Testing and validation approach

- Unit: stage success and failure handling.
- Integration: end-to-end install on test filesystem layout.

### 7) Rollout steps and operational guardrails

- Keep cleanup conservative; do not delete unrelated directories.

### 8) Risks and mitigations

- Risk: partial extraction leaves broken install.
- Mitigation: per-stage temporary workspace and commit-on-success strategy.

### 9) Completion criteria

- Pipeline installs and registers playable build in vertical slice.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Add checksums, retry policy, interruption recovery, rollback, and idempotent cleanup.

### 2) Key tasks and explicit sequencing

- Add artifact validation stage.
- Add retry/backoff fetch wrapper.
- Add resume from checkpoint and rollback policy by stage.

### 3) Dependencies and prerequisites

- Requires operation journal support and diagnostics correlation IDs.

### 4) Design decisions and integration decisions

- Separate transient transfer failures from permanent artifact incompatibility failures.

### 5) Data model and API contract impacts

- Extend checkpoint schema with validation evidence and rollback state.

### 6) Testing and validation approach

- Integration: fault injection during each stage.
- E2E: interruption and resume with consistent final metadata.

### 7) Rollout steps and operational guardrails

- Enforce disk-space preflight before download and extraction.

### 8) Risks and mitigations

- Risk: cleanup removes user-owned content by path confusion.
- Mitigation: strict managed-path registry and safe-delete guards.

### 9) Completion criteria

- Recovery and rollback paths pass stage-level fault injection suite.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Integrate policy settings and legacy installation metadata migration.

### 2) Key tasks and explicit sequencing

- Map legacy installation metadata to new schema.
- Add migration validation for active installation pointers.

### 3) Dependencies and prerequisites

- Requires settings and storage migration utilities.

### 4) Design decisions and integration decisions

- Incompatible metadata triggers re-registration flow instead of blind trust.

### 5) Data model and API contract impacts

- Add installation schema version and migration audit fields.

### 6) Testing and validation approach

- Integration fixtures from legacy install directories and metadata variants.

### 7) Rollout steps and operational guardrails

- Backup legacy metadata before migration update.

### 8) Risks and mitigations

- Risk: active installation pointer mismatch after migration.
- Mitigation: reconcile against filesystem executable discovery.

### 9) Completion criteria

- Migrated installations remain launchable or are clearly flagged with remediation.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Coordinate install and backup operations to avoid data contention.

### 2) Key tasks and explicit sequencing

- Add mutual exclusion policy for restore-write windows.
- Add queueing for non-critical install maintenance operations.

### 3) Dependencies and prerequisites

- Requires backup lifecycle signals.

### 4) Design decisions and integration decisions

- Safety-first lock hierarchy between install writes and restore writes.

### 5) Data model and API contract impacts

- Add operation lock state markers to checkpoint metadata.

### 6) Testing and validation approach

- Integration: install attempt during restore.

### 7) Rollout steps and operational guardrails

- Prevent install start when restore critical section is active.

### 8) Risks and mitigations

- Risk: deadlock between restore and install locks.
- Mitigation: single lock coordinator with timeout + failure policy.

### 9) Completion criteria

- No data corruption from install/backup concurrency in stress tests.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Finalize production-grade pipeline policies and support runbook.

### 2) Key tasks and explicit sequencing

- Freeze pipeline stage contracts.
- Publish recovery runbook and known failure signatures.

### 3) Dependencies and prerequisites

- Requires broad-channel install telemetry and incident learnings.

### 4) Design decisions and integration decisions

- Keep transparent failure reporting over silent retries.

### 5) Data model and API contract impacts

- Lock installation metadata schema baseline for GA.

### 6) Testing and validation approach

- Release candidate regression across OS matrix and artifact variants.

### 7) Rollout steps and operational guardrails

- Rollout gate on installation success rates and corruption-free metrics.

### 8) Risks and mitigations

- Risk: environment-specific extraction issues in wild.
- Mitigation: targeted compatibility fallback handlers with diagnostics.

### 9) Completion criteria

- Pipeline meets rollout reliability thresholds and legacy retirement criteria.
