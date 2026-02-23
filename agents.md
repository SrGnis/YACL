# YACL Project Agent Best Practices

This document defines practical best practices for contributors and AI agents working in this repository.

## 1. Product and migration intent

- Use [`plans/java-springboot-javafx-migration-plan.md`](plans/java-springboot-javafx-migration-plan.md) as the implementation direction source of truth.
- Use [`plans/legacy-old-app-high-level-design.md`](plans/legacy-old-app-high-level-design.md) as the baseline behavior and constraint reference.
- Follow pragmatic modernization:
  - preserve critical user workflows
  - keep migration compatibility explicit
  - do not require strict feature-parity for every legacy detail

## 2. Repository working rules

- Keep migration planning artifacts under [`plans/`](plans).
- Treat [`old_app/`](old_app) as legacy evidence unless a task explicitly requires changes there.
- Prefer additive documentation and explicit rationale over implicit assumptions.
- Keep file naming predictable and discoverable.

## 3. Architecture principles to preserve

Align work with target boundaries documented in [`plans/java-springboot-javafx-migration-plan.md`](plans/java-springboot-javafx-migration-plan.md):

- UI boundary: JavaFX presentation and view-state only.
- App core boundary: Spring Boot lifecycle, wiring, use-case orchestration.
- Domain boundary: workflow logic and business rules.
- Integration boundary: external API adapters and normalization.
- Storage boundary: file persistence, schema versioning, migration handlers.
- Platform boundary: OS-specific launch/process behavior.

Do not collapse these boundaries with direct cross-layer shortcuts.

## 4. Plan-first delivery discipline

- For significant changes, update plan docs before implementation.
- Keep work aligned to delivery phases:
  - Phase 1 foundation and vertical slice
  - Phase 2 workflow hardening
  - Phase 3 migration readiness
  - Phase 4 backup reintroduction and stabilization
  - Phase 5 rollout and legacy retirement
- Each phase description should include:
  - scope
  - sequenced tasks
  - dependencies
  - design and integration decisions
  - data and contract impacts
  - testing strategy
  - rollout guardrails
  - risks and mitigations
  - measurable completion criteria

## 5. Data and schema governance

- Assume file-based persistence remains primary in near-term migration.
- Version every durable schema explicitly.
- Add migration handlers for schema changes, including:
  - compatibility checks
  - dry-run capability
  - backup before write
  - deterministic migration logs
- Favor forward-compatible evolution over key-for-key legacy replication.

## 6. Workflow reliability standards

- Model long operations as staged workflows with explicit checkpoints.
- Design for interruption safety and resumability.
- Ensure idempotent cleanup logic.
- Separate critical failure categories from transient retryable failures.
- Prevent destructive actions without preflight validation.

## 7. Eventing and observability standards

- Prefer typed scoped events over broad global signaling.
- Use correlation IDs across multi-stage operations.
- Emit structured diagnostics with category, severity, and context.
- Keep user-facing status messages concise and actionable.
- Ensure logs are sufficient to diagnose install, launch, migration, and restore failures.

## 8. UI and UX guardrails

- Keep UI responsive during network/file operations.
- Move long-running tasks off the UI thread.
- Provide clear progress and cancellation behavior.
- Use consistent risk communication for destructive operations.
- Prioritize clarity, accessibility, and predictable workflows over visual parity with legacy Tkinter themes.

## 9. Testing expectations

Use layered validation:

- unit tests for business rules, mapping logic, state transitions
- integration tests for adapters, persistence, and cross-module contracts
- end-to-end tests for critical user journeys:
  - release discovery to install to activate to launch
  - migration startup checks
  - backup create and restore when reintroduced

Include fault-injection scenarios for interruption, partial failures, and recovery.

## 10. Rollout and operational safety

- Use phased exposure internal then limited external then broad release.
- Keep rollback strategy available until stability criteria are met.
- Gate promotions on observable reliability signals and incident severity.
- Publish migration and rollback guidance with each release channel transition.

## 11. Documentation quality bar

- Keep docs implementation-oriented at architectural execution level.
- Avoid low-level class-by-class design in migration plan docs unless explicitly requested.
- Tie claims to evidence files where possible.
- Update indexes when adding new module-level docs.

## 12. Preferred decision heuristics

When trade-offs appear, prioritize in this order:

1. data safety and recoverability
2. workflow reliability for core player path
3. diagnosability and operational clarity
4. maintainable module boundaries
5. UX consistency and accessibility
6. feature breadth and visual refinement
