package com.yacl.ui.shell;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.yacl.lifecycle.LifecycleSnapshot;
import com.yacl.lifecycle.LifecycleState;
import com.yacl.lifecycle.LifecycleStatusProvider;
import java.time.Instant;
import org.junit.jupiter.api.Test;

class UiShellViewModelFactoryTest {

    @Test
    void createShellModelBuildsExpectedTabScaffoldAndStatusFromLifecycle() {
        LifecycleStatusProvider lifecycle = () -> new LifecycleSnapshot(LifecycleState.READY, false, "READY",
                Instant.parse("2026-01-01T00:00:00Z"));

        UiShellViewModelFactory factory = new UiShellViewModelFactory(lifecycle);
        UiShellViewModel model = factory.createShellModel();

        assertEquals("YACL Launcher", model.title());
        assertEquals("READY", model.statusText());
        assertEquals(3, model.tabs().size());

        assertEquals(UiShellTabId.GAME, model.tabs().getFirst().id());
        assertTrue(model.tabs().getFirst().enabled());

        assertEquals(UiShellTabId.SETTINGS, model.tabs().get(1).id());
        assertFalse(model.tabs().get(1).enabled());

        assertEquals(UiShellTabId.BACKUP, model.tabs().get(2).id());
        assertFalse(model.tabs().get(2).enabled());
    }

    @Test
    void createShellModelMarksStatusAsDegradedWhenLifecycleIsDegraded() {
        LifecycleStatusProvider lifecycle = () -> new LifecycleSnapshot(
                LifecycleState.READY,
                true,
                "READY (degraded: optional connectivity unavailable)",
                Instant.parse("2026-01-01T00:00:00Z"));

        UiShellViewModelFactory factory = new UiShellViewModelFactory(lifecycle);
        UiShellViewModel model = factory.createShellModel();

        assertTrue(model.statusText().contains("[DEGRADED]"));
    }
}
