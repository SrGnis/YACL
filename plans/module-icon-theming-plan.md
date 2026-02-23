# Module Plan: Icon and Theming

## Module scope and intent

- Transition visual assets from Tk-specific theming to JavaFX-compatible icon and styling system.
- Legacy anchors: [`icon_service.py`](old_app/src/yacl/services/icon_service.py), Tk theme assets under [`resources/assets/themes`](old_app/src/yacl/resources/assets/themes).

## Phase 1: Foundation and vertical slice

### 1) Concrete scope

- Provide baseline icon loading and minimal consistent styling for core shell/game flow.

### 2) Key tasks and explicit sequencing

- Define JavaFX resource loading strategy for icons.
- Implement baseline style tokens and shared UI classes.
- Replace essential legacy icon usages for vertical slice screens.

### 3) Dependencies and prerequisites

- Requires UI shell component structure and packaging resource inclusion.

### 4) Design decisions and integration decisions

- Keep asset pipeline toolkit-agnostic where practical, but render through JavaFX-native styling.

### 5) Data model and API contract impacts

- Define icon key registry and style token catalog.

### 6) Testing and validation approach

- Unit: icon lookup and fallback behavior.
- Integration: style application across major shell components.

### 7) Rollout steps and operational guardrails

- Include fallback icon behavior when asset missing.

### 8) Risks and mitigations

- Risk: broken resources in packaged builds.
- Mitigation: build-time asset validation checks.

### 9) Completion criteria

- Core UI screens render with consistent icons and baseline theme.

## Phase 2: Core workflow hardening

### 1) Concrete scope

- Expand styling consistency, dark/light baseline support, and visual error states.

### 2) Key tasks and explicit sequencing

- Add state-based style rules for progress, warning, and failure states.
- Normalize spacing/typography tokens across tabs/dialogs.

### 3) Dependencies and prerequisites

- Requires finalized UI component library in shell module.

### 4) Design decisions and integration decisions

- Avoid over-customization; prioritize readability and operational clarity.

### 5) Data model and API contract impacts

- Extend token catalog with semantic status colors.

### 6) Testing and validation approach

- Visual regression checks for key states and dialogs.

### 7) Rollout steps and operational guardrails

- Gate theme changes on readability/accessibility checklist pass.

### 8) Risks and mitigations

- Risk: theme regressions reduce accessibility.
- Mitigation: contrast standards and keyboard focus visibility requirements.

### 9) Completion criteria

- Visual state consistency verified for core operations.

## Phase 3: Settings and migration readiness

### 1) Concrete scope

- Integrate persisted user visual preferences where supported by modern design scope.

### 2) Key tasks and explicit sequencing

- Add settings binding for supported theme preference options.
- Define migration mapping from legacy visual settings where meaningful.

### 3) Dependencies and prerequisites

- Requires settings schema for appearance preferences.

### 4) Design decisions and integration decisions

- Preserve only practical preference compatibility; avoid strict legacy theme parity.

### 5) Data model and API contract impacts

- Add appearance settings schema fields and migration mapping.

### 6) Testing and validation approach

- Integration: preference persistence and restart behavior.

### 7) Rollout steps and operational guardrails

- Hide unsupported legacy appearance options with clear migration note.

### 8) Risks and mitigations

- Risk: users expect full legacy theme behavior.
- Mitigation: explicit compatibility statement in migration guidance.

### 9) Completion criteria

- Appearance preferences behave predictably within supported modern scope.

## Phase 4: Backup reintroduction and stabilization

### 1) Concrete scope

- Ensure backup workflows have clear risk-state visual language.

### 2) Key tasks and explicit sequencing

- Add dedicated visual cues for destructive backup actions.
- Validate dialog styling consistency for restore confirmations.

### 3) Dependencies and prerequisites

- Requires backup UI and diagnostics categories for status mapping.

### 4) Design decisions and integration decisions

- Use high-clarity warning semantics for backup restore states.

### 5) Data model and API contract impacts

- Add semantic style tokens for safety-critical action states.

### 6) Testing and validation approach

- Visual and UX validation for restore warning flows.

### 7) Rollout steps and operational guardrails

- Block release if destructive-action visuals do not meet clarity criteria.

### 8) Risks and mitigations

- Risk: visual ambiguity causes unsafe user choices.
- Mitigation: consistent warning hierarchy and confirmation affordances.

### 9) Completion criteria

- Backup-related visuals support safe decision making.

## Phase 5: Rollout and legacy retirement

### 1) Concrete scope

- Finalize asset set, remove obsolete Tk theme dependencies, and lock style governance.

### 2) Key tasks and explicit sequencing

- Remove legacy Tk-specific theme artifacts from active packaging inputs.
- Freeze icon and style token catalogs for GA baseline.

### 3) Dependencies and prerequisites

- Requires build pipeline resource packaging finalization.

### 4) Design decisions and integration decisions

- Keep theming maintainable with limited token surface and documented usage.

### 5) Data model and API contract impacts

- Mark appearance config and token catalog versions as stable.

### 6) Testing and validation approach

- Final visual regression and accessibility sweep.

### 7) Rollout steps and operational guardrails

- Promote channels only after visual regressions are resolved.

### 8) Risks and mitigations

- Risk: residual legacy asset references break packaging.
- Mitigation: static asset reference checks in build pipeline.

### 9) Completion criteria

- Stable modern visual system in place with legacy theming retired.
