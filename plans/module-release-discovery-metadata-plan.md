# Module Plan: Release Discovery and Metadata

## Module scope and intent

- Unify GitHub and cataclysm-db sourced metadata into one release catalog subsystem.
- Legacy anchors: [`release_manager.py`](old_app/src/yacl/models/release_manager.py), [`cataclysm_db.py`](old_app/src/yacl/services/cataclysm_db.py), search helpers in [`release_search.py`](old_app/src/yacl/utils/release_search.py).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Provide minimal catalog API returning normalized release entries for the vertical slice.

### 2) Key tasks and explicit sequencing

- Implement source adapters with normalized mapping.
- Implement basic cache read/write path.
- Expose release search by core fields needed by game workflow.

### 3) Dependencies and prerequisites

- Requires downloader/network abstraction and file storage adapters.

### 4) Design decisions and integration decisions

- Adapter isolation hides source-specific JSON shape variance.

### 5) Data model and API contract impacts

- Introduce normalized `ReleaseSummary` and `ReleaseAsset` contracts.

### 6) Testing and validation approach

- Unit: source payload normalization tests.
- Integration: cache fallback when source unreachable.

### 7) Rollout steps and operational guardrails

- Treat remote fetch as optional at startup; cache fallback is first-class.

### 8) Risks and mitigations

- Risk: upstream schema drift.
- Mitigation: contract validation and source-specific parsing isolation.

### 9) Completion criteria

- Catalog returns consistent normalized entries with cache fallback.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Add freshness policy, stale-data behavior, and ranking/filter quality improvements.

### 2) Key tasks and explicit sequencing

- Implement freshness policy engine.
- Add stale cache semantics with explicit user-visible metadata.
- Improve search ranking and filter combinations.

### 3) Dependencies and prerequisites

- Requires settings-controlled policy configuration.

### 4) Design decisions and integration decisions

- Policy-driven freshness instead of hard-coded TTL logic.

### 5) Data model and API contract impacts

- Add cache metadata fields: fetch timestamp, source health, staleness reason.

### 6) Testing and validation approach

- Integration: stale and fresh cache branch behavior.

### 7) Rollout steps and operational guardrails

- Log source health transitions to diagnostics.

### 8) Risks and mitigations

- Risk: aggressive refresh causes rate limiting.
- Mitigation: capped refresh intervals and exponential backoff.

### 9) Completion criteria

- Search and freshness behavior deterministic under simulated source outages.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Migrate legacy cache layout and settings into new catalog storage schema.

### 2) Key tasks and explicit sequencing

- Build cache migration utility with dry-run mode.
- Map legacy config toggles to catalog policy fields.

### 3) Dependencies and prerequisites

- Requires migration framework from settings/storage modules.

### 4) Design decisions and integration decisions

- Preserve valuable cache content when safe; rebuild only when incompatible.

### 5) Data model and API contract impacts

- Version cache schema and add migration result markers.

### 6) Testing and validation approach

- Integration fixture set from representative legacy cache snapshots.

### 7) Rollout steps and operational guardrails

- Automatic backup of legacy cache metadata before migration writes.

### 8) Risks and mitigations

- Risk: migrated cache introduces incorrect release data.
- Mitigation: post-migration validation against live spot checks.

### 9) Completion criteria

- Legacy cache migration outcomes reproducible and reversible.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Ensure release catalog behavior remains stable when backup workflows add I/O load.

### 2) Key tasks and explicit sequencing

- Add concurrency guard tuning for simultaneous catalog reads and backup operations.

### 3) Dependencies and prerequisites

- Requires diagnostics and eventing modules for contention visibility.

### 4) Design decisions and integration decisions

- Prioritize install-related metadata operations over non-critical refresh work.

### 5) Data model and API contract impacts

- Add operation priority hints in internal catalog request contract.

### 6) Testing and validation approach

- Integration: concurrent backup + release refresh stress tests.

### 7) Rollout steps and operational guardrails

- Defer non-critical refresh under high I/O pressure.

### 8) Risks and mitigations

- Risk: stale listing under contention.
- Mitigation: explicit stale indicator and manual refresh path.

### 9) Completion criteria

- Stable user-facing catalog behavior under backup stress conditions.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Finalize catalog contracts and retire legacy catalog assumptions.

### 2) Key tasks and explicit sequencing

- Lock source adapter interfaces.
- Publish support diagnostics playbook for catalog failures.

### 3) Dependencies and prerequisites

- Requires production validation in staged rollout channels.

### 4) Design decisions and integration decisions

- Maintain compatibility strategy through schema versioning, not field-level parity.

### 5) Data model and API contract impacts

- Freeze catalog schema version for initial GA baseline.

### 6) Testing and validation approach

- Regression for release retrieval across channels and game types.

### 7) Rollout steps and operational guardrails

- Promote channels only when catalog error rate remains within release thresholds.

### 8) Risks and mitigations

- Risk: unseen edge payloads in external sources.
- Mitigation: tolerant parser fallback with diagnostics and safe filtering.

### 9) Completion criteria

- Catalog reliability acceptable for broad release and legacy deprecation.
