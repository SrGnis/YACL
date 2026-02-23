package com.yacl.ui.shell;

/**
 * Minimal tab metadata contract for Phase 1 shell scaffolding.
 */
public record UiShellTabSpec(UiShellTabId id, String title, boolean enabled) {
}
