package com.yacl.ui.shell;

import com.yacl.lifecycle.LifecycleSnapshot;
import java.util.List;

/**
 * Minimal shell state contract consumed by Phase 1 JavaFX scaffolding.
 */
public record UiShellViewModel(
        String title,
        String statusText,
        LifecycleSnapshot lifecycle,
        List<UiShellTabSpec> tabs) {
}
