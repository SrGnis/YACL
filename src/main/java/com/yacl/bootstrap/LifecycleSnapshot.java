package com.yacl.bootstrap;

import java.time.Instant;

/**
 * In-memory lifecycle snapshot for Phase 1.
 */
public record LifecycleSnapshot(
        LifecycleState state,
        boolean degradedMode,
        String detail,
        Instant updatedAt) {
}
