# Module Plan Index

This index maps each migration module to its detailed phase-by-phase implementation plan.

## Module to file mapping

| Module                         | Plan file                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------ |
| App Bootstrap and Lifecycle    | [`module-app-bootstrap-lifecycle-plan.md`](plans/module-app-bootstrap-lifecycle-plan.md)         |
| UI Shell Tabs and Dialogs      | [`module-ui-shell-tabs-dialogs-plan.md`](plans/module-ui-shell-tabs-dialogs-plan.md)             |
| Game Workflow Orchestration    | [`module-game-workflow-orchestration-plan.md`](plans/module-game-workflow-orchestration-plan.md) |
| Release Discovery and Metadata | [`module-release-discovery-metadata-plan.md`](plans/module-release-discovery-metadata-plan.md)   |
| Download and Install Pipeline  | [`module-download-install-pipeline-plan.md`](plans/module-download-install-pipeline-plan.md)     |
| Activation and Launch Runtime  | [`module-activation-launch-runtime-plan.md`](plans/module-activation-launch-runtime-plan.md)     |
| Backup and Restore             | [`module-backup-restore-plan.md`](plans/module-backup-restore-plan.md)                           |
| Settings and Configuration     | [`module-settings-configuration-plan.md`](plans/module-settings-configuration-plan.md)           |
| Status Logging and Diagnostics | [`module-status-logging-diagnostics-plan.md`](plans/module-status-logging-diagnostics-plan.md)   |
| Eventing Model                 | [`module-eventing-model-plan.md`](plans/module-eventing-model-plan.md)                           |
| Icon and Theming               | [`module-icon-theming-plan.md`](plans/module-icon-theming-plan.md)                               |
| Build and Release Packaging    | [`module-build-release-packaging-plan.md`](plans/module-build-release-packaging-plan.md)         |

## Alignment notes

- Delivery phases in every module file align with [`Phase 1` to `Phase 5`](plans/java-springboot-javafx-migration-plan.md).
- Module boundaries and sequencing are derived from [`System-by-System Plans`](plans/java-springboot-javafx-migration-plan.md).
- Legacy behavior and constraints are anchored to [`legacy-old-app-high-level-design.md`](plans/legacy-old-app-high-level-design.md).
- Plans keep pragmatic modernization posture: migration compatibility is explicit where needed, strict feature parity is not mandatory.
