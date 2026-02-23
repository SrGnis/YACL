package com.yacl.bootstrap;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class AppLifecycleCoordinatorTest {

    @Test
    void startupRunsInExpectedOrderAndReachesReady() {
        List<String> calls = new ArrayList<>();

        AppLifecycleCoordinator coordinator = new AppLifecycleCoordinator(
                () -> calls.add("paths"),
                () -> calls.add("settings"),
                () -> calls.add("ui"),
                () -> ConnectivityStatus.AVAILABLE);

        coordinator.startup();

        assertEquals(List.of("paths", "settings", "ui"), calls);
        assertEquals(LifecycleState.READY, coordinator.currentSnapshot().state());
        assertFalse(coordinator.currentSnapshot().degradedMode());
    }

    @Test
    void startupEntersDegradedModeWhenOptionalConnectivityUnavailable() {
        AppLifecycleCoordinator coordinator = new AppLifecycleCoordinator(
                () -> {
                },
                () -> {
                },
                () -> {
                },
                () -> ConnectivityStatus.UNAVAILABLE);

        coordinator.startup();

        assertEquals(LifecycleState.READY, coordinator.currentSnapshot().state());
        assertTrue(coordinator.currentSnapshot().degradedMode());
    }

    @Test
    void shutdownTransitionMovesToShuttingDown() {
        AppLifecycleCoordinator coordinator = new AppLifecycleCoordinator(
                () -> {
                },
                () -> {
                },
                () -> {
                },
                () -> ConnectivityStatus.AVAILABLE);

        coordinator.startup();
        coordinator.initiateShutdown();

        assertEquals(LifecycleState.SHUTTING_DOWN, coordinator.currentSnapshot().state());
    }
}
